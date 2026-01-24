#!/usr/bin/env python3
# ------------------------------------------------------------
# cBTC Protocol – Minting Channel Coordinator (EXPERIMENTAL)
#
# This script automates opening a Minting Channel on Bitcoin
# Core regtest, reproducing the manual steps described in:
#   docs/regtest-walkthrough-minting-channel-1.md
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
# Behavior:
# - Uses CP1's UTXOs to fund a Minting Channel of size D (BTC).
# - Splits D into:
#     70% principal (CP1_PRINCIPAL address)
#     20% Redemption Pool
#     10% Yield Pool
# - Sends a single on-chain transaction from CP1.
# - Prints the txid and the minted cBTC amount (off-chain).
# ------------------------------------------------------------

from decimal import Decimal
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

# --- CONFIGURATION ----------------------------------------------------------

RPC_USER = "cbtc"
RPC_PASSWORD = "cbtcpassword"
RPC_PORT = 18443
RPC_HOST = "127.0.0.1"

# Name of the wallets (must already exist in Bitcoin Core)
CP_WALLET_NAME = "CP1"
REDEMPTION_WALLET_NAME = "REDEMPTION_POOL"
YIELD_WALLET_NAME = "YIELD_POOL"

# Deposit amount D in BTC for this Minting Channel (change as needed)
DEPOSIT_AMOUNT_BTC = Decimal("1.3")

# Issuance rate: 30,000 cBTC per 1 BTC deposited
MINT_RATE_PER_BTC = 30000


# --- HELPER FUNCTIONS ------------------------------------------------------


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


def open_mint_channel(deposit_btc: Decimal) -> None:
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

    # Compute the BTC split
        # Compute the BTC split (70% principal, 20% redemption, 10% yield)
    principal_btc = (deposit_btc * Decimal("0.70")).quantize(Decimal("0.00000001"))
    redemption_btc = (deposit_btc * Decimal("0.20")).quantize(Decimal("0.00000001"))
    yield_btc = (deposit_btc * Decimal("0.10")).quantize(Decimal("0.00000001"))

    # Sanity check for rounding
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

    # We will subtract the fee from the principal output to avoid "insufficient funds"
    subtract_fee_from = [principal_address]

    try:
        txid = cp_client.sendmany(
            "",  # dummy account (unused)
            outputs,
            1,                # minconf
            "",               # comment
            subtract_fee_from # subtractfeefrom
        )
    except JSONRPCException as e:
        raise RuntimeError(f"sendmany failed: {e}") from e

    # Compute minted cBTC off-chain
    minted_cbtc = int(deposit_btc * MINT_RATE_PER_BTC)

    print("\n[RESULT] Minting Channel opened successfully.")
    print(f"         Transaction ID: {txid}")
    print(f"         Minted cBTC:    {minted_cbtc} cBTC")
    print("\n[NOTE] Remember: cBTC minting is off-chain accounting at this stage.")
    print("       Record this event in your cBTC ledger (e.g. JSON/SQLite/text).")


def main():
    try:
        open_mint_channel(DEPOSIT_AMOUNT_BTC)
    except Exception as e:
        print(f"[ERROR] {e}")


if __name__ == "__main__":
    main()
