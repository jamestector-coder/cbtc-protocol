#!/usr/bin/env python3
# ------------------------------------------------------------
# cBTC Protocol – Status / Coverage Report (EXPERIMENTAL)
#
# This script reports the current state of the cBTC regtest MVP:
# - Total minted cBTC (from data/ledger.json)
# - (Future) Total redeemed/burned cBTC
# - Estimated outstanding cBTC
# - Redemption Pool BTC (via RPC)
# - Full-floor liability
# - Global coverage and tier
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
# ------------------------------------------------------------

from decimal import Decimal, getcontext
from bitcoinrpc.authproxy import AuthServiceProxy
from pathlib import Path
import json

getcontext().prec = 16

# --- PROTOCOL CONSTANTS ----------------------------------------------------

FLOOR_RATE = Decimal("0.00001")  # BTC per cBTC at full floor

# --- RPC CONFIG ------------------------------------------------------------

RPC_USER = "cbtc"
RPC_PASSWORD = "cbtcpassword"
RPC_PORT = 18443
RPC_HOST = "127.0.0.1"

REDEMPTION_WALLET_NAME = "REDEMPTION_POOL"

# --- LEDGER CONFIG ---------------------------------------------------------

# Resolve repo root (cbtc-protocol/) from this file location:
# .../cbtc-protocol/src/coordinator/status.py
REPO_ROOT = Path(__file__).resolve().parents[2]
LEDGER_PATH = REPO_ROOT / "data" / "ledger.json"


# --- LEDGER HELPERS --------------------------------------------------------


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


def compute_supply_from_ledger(ledger: dict):
    """
    Compute total minted and redeemed cBTC from the ledger.

    For now, we only have "mint" events.
    This function is future-proofed to handle "redeem" events later.

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
            # Future: if we log redemptions as burns
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


# --- MAIN STATUS LOGIC -----------------------------------------------------


def main():
    # 1. Load ledger and compute supply numbers
    ledger = load_ledger()
    total_minted, total_redeemed, outstanding = compute_supply_from_ledger(ledger)

    # 2. Connect to Redemption Pool wallet and fetch BTC balance
    red_client = make_wallet_client(REDEMPTION_WALLET_NAME)
    check_regtest(red_client)

    redemption_pool_btc = Decimal(str(red_client.getbalance()))

    # 3. Compute full-floor liability and coverage
    liability_floor = outstanding * FLOOR_RATE

    if liability_floor > 0:
        coverage = redemption_pool_btc / liability_floor
    else:
        coverage = Decimal("0")

    # 4. Determine tier (same rough logic as in calc_redemption_rate)
    if coverage >= Decimal("0.70"):
        tier = "Tier 1 – Full floor zone"
    elif coverage >= Decimal("0.50"):
        tier = "Tier 2 – Haircut zone"
    elif coverage > Decimal("0"):
        tier = "Tier 3 – Insolvency zone"
    else:
        tier = "No outstanding cBTC / no liability"

    # 5. Pretty-print status
    print("\n=== cBTC Protocol Status (Regtest MVP) ===")
    print(f"Ledger file:           {LEDGER_PATH}")
    print("------------------------------------------")
    print(f"Total minted cBTC:     {total_minted}")
    print(f"Total redeemed cBTC:   {total_redeemed}")
    print(f"Estimated outstanding: {outstanding}")
    print("------------------------------------------")
    print(f"Redemption Pool BTC:   {redemption_pool_btc}")
    print(f"Floor liability BTC:   {liability_floor}")
    if liability_floor > 0:
        print(f"Coverage:              {coverage:.4%}")
    else:
        print(f"Coverage:              n/a (no liability)")
    print(f"Tier:                  {tier}")
    print("==========================================\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[ERROR] {e}")
