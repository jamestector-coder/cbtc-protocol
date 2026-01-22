#!/usr/bin/env python3
# ------------------------------------------------------------
# cBTC Protocol – Minting Channel Coordinator (EXPERIMENTAL)
#
# This script demonstrates how to open a cBTC Minting Channel
# using Bitcoin Core on regtest.
#
# ⚠️ WARNING:
# - This code is experimental and for educational purposes only.
# - DO NOT use on mainnet.
# - No security hardening has been performed.
#
# Dependencies:
# - Python 3.10+
# - Bitcoin Core (regtest mode, RPC enabled)
# - python-bitcoinrpc library
#
# Install dependency with:
#   pip install python-bitcoinrpc
#
# Description:
# - Selects UTXOs from a Collateral Provider wallet
# - Splits BTC into:
#     70% principal (time-locked later)
#     15% Redemption Pool
#     15% Yield allocation
# - Broadcasts a single on-chain transaction
# - Credits minted cBTC in an off-chain ledger (MVP)
#
# This is NOT a full protocol implementation.
# ------------------------------------------------------------

from decimal import Decimal
from bitcoinrpc.authproxy import AuthServiceProxy

RPC_USER = "youruser"
RPC_PASS = "yourpass"
RPC_PORT = 18443  # regtest default
RPC_HOST = "127.0.0.1"

def get_rpc(wallet=None):
    base = f"http://{RPC_USER}:{RPC_PASS}@{RPC_HOST}:{RPC_PORT}"
    if wallet:
        return AuthServiceProxy(base + f"/wallet/{wallet}")
    return AuthServiceProxy(base)

def open_mint_channel(cp_wallet: str, deposit_amount_btc: Decimal):
    # --- 1. Basic math ---
    D = Decimal(deposit_amount_btc)
    principal_amount  = (D * Decimal("0.70")).quantize(Decimal("0.00000001"))
    redemption_amount = (D * Decimal("0.15")).quantize(Decimal("0.00000001"))
    yield_amount      = (D * Decimal("0.15")).quantize(Decimal("0.00000001"))
    minted_cbtc       = int(D * Decimal("30000"))

    print(f"Opening Minting Channel for {cp_wallet} with D = {D} BTC")
    print(f"Principal:  {principal_amount} BTC")
    print(f"Redemption: {redemption_amount} BTC")
    print(f"Yield:      {yield_amount} BTC")
    print(f"Minted cBTC: {minted_cbtc}")

    # --- 2. RPC handles ---
    cp_rpc      = get_rpc(cp_wallet)
    red_rpc     = get_rpc("REDEMPTION_POOL")
    yield_rpc   = get_rpc("YIELD_POOL")

    # --- 3. Build destination addresses ---
    # MVP: plain bech32 addresses; later we replace principal/yield with timelocked scripts
    principal_addr  = cp_rpc.getnewaddress("CP_PRINCIPAL", "bech32")
    redemption_addr = red_rpc.getnewaddress("REDEMPTION_POOL", "bech32")
    yield_addr      = yield_rpc.getnewaddress("YIELD_POOL", "bech32")

    # --- 4. Select inputs from CP wallet ---
    utxos = cp_rpc.listunspent(1, 9999999, [])
    utxos = sorted(utxos, key=lambda u: u["amount"], reverse=True)

    needed = D
    selected = []
    total_in = Decimal("0.0")

    for u in utxos:
        selected.append({"txid": u["txid"], "vout": u["vout"]})
        total_in += Decimal(str(u["amount"]))
        if total_in >= needed:
            break

    if total_in < needed:
        raise RuntimeError("Not enough balance to fund Minting Channel")

    # crude fee estimate for MVP:
    fee = Decimal("0.0001")
    change = (total_in - D - fee).quantize(Decimal("0.00000001"))
    if change < 0:
        raise RuntimeError("Fee calculation error, change negative")

    change_addr = cp_rpc.getrawchangeaddress()

    # --- 5. Create raw transaction ---
    outputs = {
        redemption_addr: float(redemption_amount),
        yield_addr:      float(yield_amount),
        change_addr:     float(change),
        principal_addr:  float(principal_amount),
    }

    raw_tx = cp_rpc.createrawtransaction(selected, outputs)
    funded_tx = cp_rpc.fundrawtransaction(raw_tx)  # optional – Core can adjust change/fee
    signed_tx = cp_rpc.signrawtransactionwithwallet(funded_tx["hex"])
    if not signed_tx.get("complete"):
        raise RuntimeError("Transaction not fully signed")

    txid = cp_rpc.sendrawtransaction(signed_tx["hex"])
    print(f"Minting Channel txid: {txid}")

    # --- 6. Record channel metadata (pseudo) ---
    channel = {
        "cp_wallet": cp_wallet,
        "deposit_btc": str(D),
        "principal_amount": str(principal_amount),
        "redemption_amount": str(redemption_amount),
        "yield_amount": str(yield_amount),
        "minted_cbtc": minted_cbtc,
        "principal_address": principal_addr,
        "redemption_address": redemption_addr,
        "yield_address": yield_addr,
        "txid": txid,
        "status": "pending_confirmation",
    }
    # Here you’d insert 'channel' into a SQLite DB or JSON file.
    # save_channel_to_db(channel)

    # --- 7. Credit cBTC to CP in off-chain ledger (MVP) ---
    # For now, assume we keep a simple internal ledger:
    # credit_cbtc_to_cp(cp_wallet, minted_cbtc)

    return channel
