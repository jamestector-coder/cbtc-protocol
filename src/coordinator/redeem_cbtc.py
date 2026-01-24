#!/usr/bin/env python3
# ------------------------------------------------------------
# cBTC Protocol – Redemption / Burn Coordinator (EXPERIMENTAL)
#
# This script simulates a cBTC redemption on Bitcoin regtest:
#
# - Reads data/ledger.json to compute outstanding cBTC.
# - Queries the Redemption Pool wallet balance via RPC.
# - Uses the same math as calc_redemption_rate.py to compute
#   a safe redemption rate so that post-redemption coverage
#   never falls below 50%.
# - Optionally sends BTC from REDEMPTION_POOL to a user-provided
#   BTC address (on-chain) and logs a "redeem" event in the ledger.
#
# ⚠️ WARNING:
# - Experimental and for educational use only.
# - DO NOT use on mainnet.
#
# Dependencies:
#   pip install python-bitcoinrpc
#
# Assumptions:
# - Bitcoin Core is running in regtest with RPC enabled.
# - Wallet REDEMPTION_POOL already exists.
# - data/ledger.json exists and follows the format:
#     { "events": [ { ... }, ... ] }
# - calc_redemption_rate.py is in the same folder.
#
# Usage (from repo root):
#   python src/coordinator/redeem_cbtc.py
# ------------------------------------------------------------

from decimal import Decimal, getcontext
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from pathlib import Path
import json
import datetime

# Import the redemption rate calculator from the same directory
from calc_redemption_rate import calc_redemption_rate, FLOOR_RATE

getcontext().prec = 16

# --- RPC CONFIG ------------------------------------------------------------

RPC_USER = "cbtc"
RPC_PASSWORD = "cbtcpassword"
RPC_PORT = 18443
RPC_HOST = "127.0.0.1"

REDEMPTION_WALLET_NAME = "REDEMPTION_POOL"

# --- LEDGER CONFIG ---------------------------------------------------------

# Resolve repo root (cbtc-protocol/) from this file location:
# .../cbtc-protocol/src/coordinator/redeem_cbtc.py
REPO_ROOT = Path(__file__).resolve().parents[2]
LEDGER_PATH = REPO_ROOT / "data" / "ledger.json"


def load_ledger():
    """
    Load the JSON ledger from LEDGER_PATH.
    If it does not exist or is invalid, return an empty ledger.
    """
    if not LEDGER_PATH.exists():
        return {"events": []}

    try:
        with LEDGER_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if "events" not in data or not isinstance(data["events"], list):
            return {"events": []}
        return data
    except Exception:
        return {"events": []}


def save_ledger(data):
    """
    Save the JSON ledger to LEDGER_PATH.
    """
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)


def append_ledger_event(event):
    """
    Append a single event to the ledger and persist it.
    """
    ledger = load_ledger()
    ledger["events"].append(event)
    save_ledger(ledger)


def compute_supply_from_ledger(ledger: dict):
    """
    Compute total minted and redeemed/burned cBTC from the ledger.

    Returns:
        total_minted_cbtc (Decimal),
        total_redeemed_cbtc (Decimal),
        outstanding_cbtc (Decimal)
    """
    total_minted = Decimal("0")
    total_redeemed = Decimal("0")

    for ev in ledger.get("events", []):
        ev_type = ev.get("type")
        if ev_type == "mint":
            minted = Decimal(str(ev.get("minted_cbtc", "0")))
            total_minted += minted
        elif ev_type == "redeem":
            burned = Decimal(str(ev.get("burned_cbtc", "0")))
            total_redeemed += burned

    outstanding = total_minted - total_redeemed
    if outstanding < 0:
        outstanding = Decimal("0")

    return total_minted, total_redeemed, outstanding


# --- RPC HELPERS -----------------------------------------------------------


def make_wallet_client(wallet_name: str) -> AuthServiceProxy:
    """
    Create an RPC client bound to a specific wallet.
    """
    url = f"http://{RPC_USER}:{RPC_PASSWORD}@{RPC_HOST}:{RPC_PORT}/wallet/{wallet_name}"
    return AuthServiceProxy(url)


def check_regtest(client: AuthServiceProxy) -> None:
    """
    Ensure we are running on regtest, not mainnet.
    """
    info = client.getblockchaininfo()
    chain = info.get("chain")
    if chain != "regtest":
        raise RuntimeError(f"Expected regtest chain, but node is on: {chain}")


# --- MAIN REDEMPTION LOGIC -------------------------------------------------


def main():
    # 1. Load ledger and compute supply numbers
    ledger = load_ledger()
    total_minted, total_redeemed, outstanding = compute_supply_from_ledger(ledger)

    print("\n=== cBTC Redemption (Regtest MVP) ===")
    print(f"Ledger file:           {LEDGER_PATH}")
    print("--------------------------------------")
    print(f"Total minted cBTC:     {total_minted}")
    print(f"Total redeemed cBTC:   {total_redeemed}")
    print(f"Estimated outstanding: {outstanding}")
    print("--------------------------------------")

    if outstanding <= 0:
        print("[ERROR] No outstanding cBTC to redeem.")
        return

    # 2. Ask user how much they want to redeem
    raw_q = input("Enter amount of cBTC to redeem (e.g. 3000): ").strip()
    try:
        redeem_q = Decimal(raw_q)
    except Exception:
        print(f"[ERROR] Invalid redemption amount: {raw_q}")
        return

    if redeem_q <= 0:
        print("[ERROR] Redemption amount must be positive.")
        return

    if redeem_q > outstanding:
        print("[ERROR] Cannot redeem more cBTC than outstanding.")
        return

    # 3. Connect to Redemption Pool and fetch BTC balance
    red_client = make_wallet_client(REDEMPTION_WALLET_NAME)
    check_regtest(red_client)

    redemption_pool_btc = Decimal(str(red_client.getbalance()))

    # 4. Compute redemption rate using the reference function
    result = calc_redemption_rate(
        outstanding_cbtc=outstanding,
        redemption_pool_btc=redemption_pool_btc,
        redeem_q=redeem_q
    )

    rate = result["rate"]
    btc_paid = result["btc_paid"]
    cov_before = result["coverage_before"]
    cov_after = result["coverage_after"]
    tier = result["tier"]

    # 5. Show summary to user
    print("\n--- Redemption Quote ---")
    print(f"Requested redemption:  {redeem_q} cBTC")
    print(f"Redemption Pool BTC:   {redemption_pool_btc}")
    print(f"Coverage before:       {cov_before:.4%}")
    print(f"Tier:                  {tier}")
    print("--------------------------------------")
    print(f"Redemption rate:       {rate} BTC per cBTC")
    print(f"Total BTC to be paid:  {btc_paid}")
    print("--------------------------------------")
    print(f"Coverage after:        {cov_after:.4%}")
    print("------------------------")

    if btc_paid <= 0:
        print("[WARNING] Computed BTC to be paid is 0. Redemption is not possible under current conditions.")
        return

    # 6. Ask for confirmation
    confirm = input("Proceed with on-chain redemption and ledger update? (yes/no): ").strip().lower()
    if confirm not in ("yes", "y"):
        print("[INFO] Redemption aborted by user. No changes made.")
        return

    # 7. Ask for a BTC address to send BTC to (on regtest)
    user_address = input("Enter BTC address to receive redemption BTC (regtest address): ").strip()
    if not user_address:
        print("[ERROR] No address provided. Aborting redemption.")
        return

    # 8. Send BTC from Redemption Pool to the provided address
    try:
        txid = red_client.sendtoaddress(user_address, float(btc_paid))
    except JSONRPCException as e:
        print(f"[ERROR] sendtoaddress failed: {e}")
        return

    # 9. Log redemption event in ledger
    event = {
        "type": "redeem",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "redeemed_cbtc": str(redeem_q),
        "burned_cbtc": str(redeem_q),  # assuming full burn
        "rate_btc_per_cbtc": str(rate),
        "btc_paid": str(btc_paid),
        "coverage_before": str(cov_before),
        "coverage_after": str(cov_after),
        "tier": tier,
        "redemption_pool_balance_before": str(redemption_pool_btc),
        "txid": txid,
        "recipient_address": user_address,
    }
    append_ledger_event(event)

    print("\n[RESULT] Redemption executed and logged.")
    print(f"         Redemption txid: {txid}")
    print(f"         Burned cBTC:     {redeem_q}")
    print(f"         BTC paid out:    {btc_paid}")
    print("\n[NOTE] Event appended to data/ledger.json")
    print("       (off-chain cBTC burn accounting for regtest simulations).")
    print("==========================================\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[ERROR] {e}")
