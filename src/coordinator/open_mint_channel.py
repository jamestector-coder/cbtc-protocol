#!/usr/bin/env python3
# ------------------------------------------------------------
# cBTC Protocol – Open Minting Channel (EXPERIMENTAL)
#
# This script:
# - Connects to a specified CP wallet (default: CP1)
# - Checks that it has enough BTC to deposit
# - Splits the deposit D into:
#     - 70% Principal
#     - 20% Redemption Pool
#     - 10% Yield Pool
# - Sends BTC to:
#     - CP Principal address (within the same CP wallet)
#     - REDEMPTION_POOL wallet
#     - YIELD_POOL wallet
# - Calculates minted cBTC = 30,000 * D
#   (with 3 decimal places, and stores minted_mC = milli-cBTC)
# - Appends a "mint" event to data/ledger.json
#
# ⚠️ WARNING:
# - Experimental and for regtest MVP only.
# - DO NOT use on mainnet.
#
# Usage:
#   python src/coordinator/open_mint_channel.py <deposit_btc> [CP_WALLET_NAME]
#
# Examples:
#   python src/coordinator/open_mint_channel.py 1.0
#       -> uses CP1 by default
#
#   python src/coordinator/open_mint_channel.py 0.5 CP2
#       -> uses CP2 as the collateral provider wallet
#
# Dependencies:
#   pip install python-bitcoinrpc
# ------------------------------------------------------------

from decimal import Decimal, getcontext
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from pathlib import Path
import datetime
import json
import sys

# Match precision with other coordinator scripts
getcontext().prec = 18

# --- PROTOCOL CONSTANTS ----------------------------------------------------

MIN_DEPOSIT = Decimal("0.05")
MAX_DEPOSIT = Decimal("5.0")

ISSUANCE_RATE = Decimal("30000")   # cBTC per BTC
PRINCIPAL_PCT = Decimal("0.70")
REDEMPTION_PCT = Decimal("0.20")
YIELD_PCT = Decimal("0.10")

# --- RPC CONFIG ------------------------------------------------------------

RPC_USER = "cbtc"
RPC_PASSWORD = "cbtcpassword"
RPC_PORT = 18443
RPC_HOST = "127.0.0.1"

REDEMPTION_WALLET_NAME = "REDEMPTION_POOL"
YIELD_WALLET_NAME = "YIELD_POOL"

# --- LEDGER CONFIG ---------------------------------------------------------

# Resolve repo root (cbtc-protocol/) from this file location:
# .../cbtc-protocol/src/coordinator/open_mint_channel.py
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


# --- MAIN LOGIC ------------------------------------------------------------

def main():
    # --- Parse CLI arguments -----------------------------------------------
    if len(sys.argv) < 2:
        print("Usage: python src/coordinator/open_mint_channel.py <deposit_btc> [CP_WALLET_NAME]")
        sys.exit(1)

    raw_deposit = sys.argv[1]
    cp_wallet_name = sys.argv[2] if len(sys.argv) >= 3 else "CP1"

    try:
        deposit_btc = Decimal(raw_deposit)
    except Exception:
        print(f"[ERROR] Invalid deposit amount: {raw_deposit}")
        sys.exit(1)

    if deposit_btc < MIN_DEPOSIT or deposit_btc > MAX_DEPOSIT:
        print(f"[ERROR] Deposit must be between {MIN_DEPOSIT} and {MAX_DEPOSIT} BTC.")
        sys.exit(1)

    # --- Connect to node & wallets -----------------------------------------
    # Use CP wallet to check regtest chain
    general_client = make_wallet_client(cp_wallet_name)
    check_regtest(general_client)

    # CP wallet:
    cp_client = make_wallet_client(cp_wallet_name)
    # Pool wallets:
    red_client = make_wallet_client(REDEMPTION_WALLET_NAME)
    yld_client = make_wallet_client(YIELD_WALLET_NAME)

    # --- Check CP balance ---------------------------------------------------
    cp_balance = Decimal(str(cp_client.getbalance()))
    print(f"[INFO] CP wallet: {cp_wallet_name}")
    print(f"[INFO] {cp_wallet_name} balance: {cp_balance} BTC")

    if cp_balance < deposit_btc:
        print(f"[ERROR] {cp_wallet_name} balance {cp_balance} BTC is less than requested deposit {deposit_btc} BTC.")
        sys.exit(1)

    # --- Compute splits -----------------------------------------------------
    D = deposit_btc
    principal = (D * PRINCIPAL_PCT).quantize(Decimal("0.00000001"))
    redemption_share = (D * REDEMPTION_PCT).quantize(Decimal("0.00000001"))
    yield_share = (D * YIELD_PCT).quantize(Decimal("0.00000001"))

    print(f"[INFO] Opening Minting Channel with deposit D = {D} BTC")
    print(f"[INFO] Principal:        {principal:.8f} BTC (70%)")
    print(f"[INFO] Redemption pool: {redemption_share:.8f} BTC (20%)")
    print(f"[INFO] Yield pool:      {yield_share:.8f} BTC (10%)")

    # --- Derive destinations -----------------------------------------------
    # Principal: stays in CP wallet, but moved to a labeled address
    principal_address = cp_client.getnewaddress(f"{cp_wallet_name}_PRINCIPAL", "bech32")
    # Redemption: goes to REDEMPTION_POOL wallet
    red_address = red_client.getnewaddress("REDEMPTION_POOL", "bech32")
    # Yield: goes to YIELD_POOL wallet
    yld_address = yld_client.getnewaddress("YIELD_POOL", "bech32")

    print(f"[INFO] Principal address:   {principal_address}")
    print(f"[INFO] Redemption address:  {red_address}")
    print(f"[INFO] Yield address:       {yld_address}")

    # --- Construct the transaction from CP wallet --------------------------
    # We use sendmany so that:
    #  - Inputs come from CP wallet
    #  - Outputs go to CP principal + Redemption Pool + Yield Pool

    outputs = {
        principal_address: float(principal),
        red_address: float(redemption_share),
        yld_address: float(yield_share),
    }

    try:
        txid = cp_client.sendmany(
            "",              # empty string means: use default account (descriptor wallet)
            outputs,
            0,               # minconf
            "cBTC Minting Channel"
        )
    except JSONRPCException as e:
        print(f"[ERROR] sendmany failed: {e}")
        sys.exit(1)

    # --- Compute minted cBTC (3 decimal places) ----------------------------
    minted_cbtc = (D * ISSUANCE_RATE).quantize(Decimal("0.001"))
    minted_mC = int((minted_cbtc * Decimal("1000")).quantize(Decimal("1")))

    print("\n[RESULT] Minting Channel opened successfully.")
    print(f"         Transaction ID: {txid}")
    print(f"         Minted cBTC:    {minted_cbtc:.3f} cBTC")
    print(f"         CP wallet used: {cp_wallet_name}")

    # --- Append event to ledger --------------------------------------------
    event = {
        "type": "mint",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "cp_wallet": cp_wallet_name,
        "deposit_btc": str(D),
        "principal_btc": str(principal),
        "redemption_btc": str(redemption_share),
        "yield_btc": str(yield_share),
        "minted_cbtc": f"{minted_cbtc:.3f}",
        "minted_mC": minted_mC,
        "txid": txid,
    }
    append_ledger_event(event)

    print("\n[NOTE] Event appended to data/ledger.json")
    print("       (off-chain cBTC accounting for regtest simulations).")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[ERROR] {e}")
