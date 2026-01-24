#!/usr/bin/env python3
# ------------------------------------------------------------
# cBTC Protocol – Minting Channel Coordinator (EXPERIMENTAL)
#
# This script automates opening a Minting Channel on Bitcoin
# Core regtest, reproducing the protocol rules:
#
# - Deposited BTC D must be between 0.05 and 5.0 BTC
# - Split:
#     70% principal (CP1_PRINCIPAL address)
#     20% Redemption Pool
#     10% Yield Pool
# - Minted cBTC = 30,000 × D
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
# - RPC credentials match the values below.
# - Wallets CP1, REDEMPTION_POOL and YIELD_POOL already exist.
#
# Usage (from repo root):
#   python src/coordinator/open_mint_channel.py 1.3
#
# If no amount is given as an argument, the script will prompt
# for a deposit amount interactively.
# ------------------------------------------------------------

from decimal import Decimal, getcontext
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import sys
import json
import datetime
from pathlib import Path

getcontext().prec = 16

# --- RPC CONFIG ------------------------------------------------------------

RPC_USER = "cbtc"
RPC_PASSWORD = "cbtcpassword"
RPC_PORT = 18443
RPC_HOST = "127.0.0.1"

# Name of the wallets (must already exist in Bitcoin Core)
CP_WALLET_NAME = "CP1"
REDEMPTION_WALLET_NAME = "REDEMPTION_POOL"
YIELD_WALLET_NAME = "YIELD_POOL"

# Issuance rate: 30,000 cBTC per 1 BTC deposited
MINT_RATE_PER_BTC = 30000

# Deposit constraints
MIN_DEPOSIT_BTC = Decimal("0.05")
MAX_DEPOSIT_BTC = Decimal("5.0")

# --- LEDGER CONFIG ---------------------------------------------------------

# Resolve repo root (cbtc-protocol/) from this file location:
# .../cbtc-protocol/src/coordinator/open_mint_channel.py
REPO_ROOT = Path(__file__).resolve().parents[2]
LEDGER_PATH = REPO_ROOT / "data" / "ledger.json"


def load_ledger():
    """
    Load the JSON ledger from LEDGER_PATH.
    If it does not exist or is invalid, start a fresh one.
    """
    if not LEDGER_PATH.exists():
        return {"events": []}

    try:
        with LEDGER_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if "events" not in data or not isinstance(data["events"], list):
            # Malformed -> reset to safe default
            return {"events": []}
        return data
    except Exception:
        # On any error, fall back to an empty ledger
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


# --- HELPER FUNCTIONS ------------------------------------------------------


def make_wallet_client(wallet_name):
    """
    Create an RPC client bound to a specific wallet.
    """
    url = f"http://{RPC_USER}:{RPC_PASSWORD}@{RPC_HOST}:{RPC_PORT}/wallet/{wallet_name}"
    return AuthServiceProxy(url)


def check_regtest(client):
    """
    Ensure we are running on regtest, not mainnet.
    """
    info = client.getblockchaininfo()
    chain = info.get("chain")
    if chain != "regtest":
        raise RuntimeError(f"Expected regtest chain, but node is on: {chain}")


def parse_deposit_amount_from_argv():
    """
    If the user provided a deposit amount as a command-line argument,
    parse and return it as a Decimal. Otherwise return None.
    """
    if len(sys.argv) >= 2:
        raw = sys.argv[1]
        try:
            return Decimal(raw)
        except Exception:
            raise RuntimeError(f"Invalid deposit amount argument: {raw}")
    return None


def prompt_for_deposit_amount():
    """
    Interactively ask the user for a deposit amount in BTC.
    """
    raw = input(
        f"Enter deposit amount in BTC (between {MIN_DEPOSIT_BTC} and {MAX_DEPOSIT_BTC}): "
    ).strip()
    try:
        return Decimal(raw)
    except Exception:
        raise RuntimeError(f"Invalid deposit amount: {raw}")


def validate_deposit_amount(deposit_btc):
    """
    Validate that the deposit amount is within the allowed range.
    """
    if deposit_btc < MIN_DEPOSIT_BTC:
        raise RuntimeError(
            f"Deposit {deposit_btc} BTC is below minimum {MIN_DEPOSIT_BTC} BTC."
        )
    if deposit_btc > MAX_DEPOSIT_BTC:
        raise RuntimeError(
            f"Deposit {deposit_btc} BTC exceeds maximum {MAX_DEPOSIT_BTC} BTC."
        )
    return deposit_btc


# --- MAIN LOGIC ------------------------------------------------------------


def open_mint_channel(deposit_btc):
    """
    Open a Minting Channel of size deposit_btc from CP1.

    Splits deposit_btc into:
      - 70% principal
      - 20% Redemption Pool
      - 10% Yield Pool

    Sends a single transaction via CP1 wallet and prints:
      - txid
      - minted cBTC
    """

    deposit_btc = validate_deposit_amount(deposit_btc)

    # RPC clients for each wallet
    cp_client = make_wallet_client(CP_WALLET_NAME)
    redemption_client = make_wallet_client(REDEMPTION_WALLET_NAME)
    yield_client = make_wallet_client(YIELD_WALLET_NAME)

    # Safety: confirm we are on regtest
    check_regtest(cp_client)

    # Check CP1 has enough balance
    cp_balance = Decimal(str(cp_client.getbalance()))
    if cp_balance < deposit_btc:
        raise RuntimeError(
            f"CP1 balance {cp_balance} BTC is less than requested deposit {deposit_btc} BTC."
        )

    print(f"[INFO] CP1 balance: {cp_balance} BTC")
    print(f"[INFO] Opening Minting Channel with deposit D = {deposit_btc} BTC")

    # Compute the BTC split (70% principal, 20% redemption, 10% yield)
    principal_btc = (deposit_btc * Decimal("0.70")).quantize(Decimal("0.00000001"))
    redemption_btc = (deposit_btc * Decimal("0.20")).quantize(Decimal("0.00000001"))
    yield_btc = (deposit_btc * Decimal("0.10")).quantize(Decimal("0.00000001"))

    total_split = principal_btc + redemption_btc + yield_btc
    if total_split > deposit_btc:
        raise RuntimeError(
            f"Split sum {total_split} exceeds deposit {deposit_btc}. Check rounding."
        )

    print(f"[INFO] Principal:        {principal_btc} BTC (70%)")
    print(f"[INFO] Redemption pool: {redemption_btc} BTC (20%)")
    print(f"[INFO] Yield pool:      {yield_btc} BTC (10%)")

    # Generate destination addresses
    principal_address = cp_client.getnewaddress("CP1_PRINCIPAL", "bech32")
    redemption_address = redemption_client.getnewaddress("REDEMPTION_POOL", "bech32")
    yield_address = yield_client.getnewaddress("YIELD_POOL", "bech32")

    print(f"[INFO] Principal address:   {principal_address}")
    print(f"[INFO] Redemption address:  {redemption_address}")
    print(f"[INFO] Yield address:       {yield_address}")

    # Construct the outputs map for sendmany
    outputs = {
        principal_address: float(principal_btc),
        redemption_address: float(redemption_btc),
        yield_address: float(yield_btc),
    }

    # We will subtract the fee from the principal output
    subtract_fee_from = [principal_address]

    try:
        txid = cp_client.sendmany(
            "",              # dummy account (unused)
            outputs,
            1,               # minconf
            "",              # comment
            subtract_fee_from
        )
    except JSONRPCException as e:
        raise RuntimeError(f"sendmany failed: {e}") from e

    # Compute minted cBTC off-chain
    minted_cbtc = int(deposit_btc * MINT_RATE_PER_BTC)

    # Log event to ledger.json
    event = {
        "type": "mint",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "cp_wallet": CP_WALLET_NAME,
        "deposit_btc": str(deposit_btc),
        "principal_btc": str(principal_btc),
        "redemption_btc": str(redemption_btc),
        "yield_btc": str(yield_btc),
        "minted_cbtc": minted_cbtc,
        "txid": txid,
    }
    append_ledger_event(event)

    print("\n[RESULT] Minting Channel opened successfully.")
    print(f"         Transaction ID: {txid}")
    print(f"         Minted cBTC:    {minted_cbtc} cBTC")
    print("\n[NOTE] Event appended to data/ledger.json")
    print("       (off-chain cBTC accounting for regtest simulations).")


def main():
    try:
        # Try command-line argument first
        deposit_arg = parse_deposit_amount_from_argv()
        if deposit_arg is None:
            # Fallback to interactive prompt
            deposit_btc = prompt_for_deposit_amount()
        else:
            deposit_btc = deposit_arg

        open_mint_channel(deposit_btc)
    except Exception as e:
        print(f"[ERROR] {e}")


if __name__ == "__main__":
    main()
