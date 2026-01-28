#!/usr/bin/env python3
# ------------------------------------------------------------
# cBTC Protocol – Status (EXPERIMENTAL)
#
# Shows:
# - total minted cBTC
# - total redeemed (burned) cBTC
# - outstanding cBTC
# - Redemption Pool BTC
# - floor liability
# - absolute coverage (real solvency)
# - normalized coverage (relative to baseline 66.67%)
# - coverage tier:
#     Tier 1 – Full floor     (coverage ≥ 60%)
#     Tier 2 – Haircuts       (50% ≤ coverage < 60%)
#     Tier 3 – Protection     (coverage < 50%)
#
# Compatible with:
# - older events with "minted_cbtc" / "burned_cbtc"
# - newer events with "minted_mC" / "burned_mC"
#
# ⚠️ For regtest/testing only. Not production-ready.
# ------------------------------------------------------------

from decimal import Decimal, getcontext
from bitcoinrpc.authproxy import AuthServiceProxy
from pathlib import Path
import json

getcontext().prec = 18

# --- CONSTANTS -------------------------------------------------------------

FLOOR_RATE = Decimal("0.00001")  # BTC per 1 cBTC

# Baseline coverage at mint:
#  - LTV: 30%
#  - Redemption Pool: 20%
# ⇒ baseline = 0.20 / 0.30 = 2/3 ≈ 66.67%
BASELINE_COVERAGE = (Decimal("0.20") / Decimal("0.30"))

RPC_USER = "cbtc"
RPC_PASSWORD = "cbtcpassword"
RPC_PORT = 18443
RPC_HOST = "127.0.0.1"

REDEMPTION_WALLET_NAME = "REDEMPTION_POOL"

# Resolve repo root (cbtc-protocol/) from this file location:
REPO_ROOT = Path(__file__).resolve().parents[2]
LEDGER_PATH = REPO_ROOT / "data" / "ledger.json"


# --- HELPERS ---------------------------------------------------------------

def make_wallet_client(wallet_name: str) -> AuthServiceProxy:
    url = f"http://{RPC_USER}:{RPC_PASSWORD}@{RPC_HOST}:{RPC_PORT}/wallet/{wallet_name}"
    return AuthServiceProxy(url)


def load_ledger():
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


def sum_minted_and_redeemed_mC(events):
    """
    Returns:
      total_minted_mC   – integer milli-cBTC
      total_redeemed_mC – integer milli-cBTC

    Compatible with:
      - older events with "minted_cbtc" / "burned_cbtc"
      - newer events with "minted_mC" / "burned_mC"
    """
    total_minted_mC = 0
    total_redeemed_mC = 0

    for ev in events:
        ev_type = ev.get("type")

        if ev_type == "mint":
            if "minted_mC" in ev:
                minted_mC = int(ev["minted_mC"])
            else:
                mc_str = ev.get("minted_cbtc", "0")
                minted_cbtc = Decimal(str(mc_str))
                minted_mC = int((minted_cbtc * Decimal("1000")).quantize(Decimal("1")))
            total_minted_mC += minted_mC

        elif ev_type == "redeem":
            if "burned_mC" in ev:
                burned_mC = int(ev["burned_mC"])
            else:
                bc_str = ev.get("burned_cbtc", "0")
                burned_cbtc = Decimal(str(bc_str))
                burned_mC = int((burned_cbtc * Decimal("1000")).quantize(Decimal("1")))
            total_redeemed_mC += burned_mC

    return total_minted_mC, total_redeemed_mC


def format_cbtc_from_mC(mC: int) -> str:
    """
    Convert integer milli-cBTC to a string with 3 decimal places.
    """
    cbtc = (Decimal(mC) / Decimal("1000")).quantize(Decimal("0.001"))
    return f"{cbtc:.3f}"


def main():
    # --- Load ledger data ---------------------------------------------------
    ledger = load_ledger()
    events = ledger.get("events", [])

    total_minted_mC, total_redeemed_mC = sum_minted_and_redeemed_mC(events)
    outstanding_mC = total_minted_mC - total_redeemed_mC

    total_minted_cbtc_str = format_cbtc_from_mC(total_minted_mC)
    total_redeemed_cbtc_str = format_cbtc_from_mC(total_redeemed_mC)
    outstanding_cbtc_str = format_cbtc_from_mC(outstanding_mC)

    outstanding_cbtc = (Decimal(outstanding_mC) / Decimal("1000")).quantize(Decimal("0.001"))

    # --- Get Redemption Pool balance ---------------------------------------
    red_client = make_wallet_client(REDEMPTION_WALLET_NAME)
    red_balance_btc = Decimal(str(red_client.getbalance()))

    # --- Compute floor liability -------------------------------------------
    if outstanding_cbtc > 0:
        floor_liability_btc = (outstanding_cbtc * FLOOR_RATE).quantize(Decimal("0.00000001"))
    else:
        floor_liability_btc = Decimal("0")

    # --- Compute absolute + normalized coverage ----------------------------
    if outstanding_cbtc > 0 and floor_liability_btc > 0:
        absolute_coverage = red_balance_btc / floor_liability_btc
    else:
        absolute_coverage = Decimal("0")

    if absolute_coverage > 0 and BASELINE_COVERAGE > 0:
        normalized_coverage = absolute_coverage / BASELINE_COVERAGE
    else:
        normalized_coverage = Decimal("0")

    # --- Determine tier using absolute coverage ----------------------------
    if outstanding_cbtc == 0:
        tier = "No outstanding cBTC"
    else:
        if absolute_coverage >= Decimal("0.60"):
            tier = "Tier 1 – Full floor (≥ 60%)"
        elif absolute_coverage >= Decimal("0.50"):
            tier = "Tier 2 – Haircuts (50–60%)"
        else:
            tier = "Tier 3 – Protection mode (< 50%)"

    # --- Output -------------------------------------------------------------
    print("\n=== cBTC Protocol Status (Regtest MVP) ===")
    print(f"Ledger file:           {str(LEDGER_PATH)}")
    print("------------------------------------------")
    print(f"Total minted cBTC:     {total_minted_cbtc_str}")
    print(f"Total redeemed cBTC:   {total_redeemed_cbtc_str}")
    print(f"Estimated outstanding: {outstanding_cbtc_str}")
    print("------------------------------------------")
    print(f"Redemption Pool BTC:   {red_balance_btc:.8f}")
    print(f"Floor liability BTC:   {floor_liability_btc:.8f}")

    if outstanding_cbtc > 0 and floor_liability_btc > 0:
        abs_pct = (absolute_coverage * Decimal("100")).quantize(Decimal("0.0001"))
        baseline_pct = (BASELINE_COVERAGE * Decimal("100")).quantize(Decimal("0.0001"))
        norm_pct = (normalized_coverage * Decimal("100")).quantize(Decimal("0.0001"))

        print(f"Absolute coverage:     {abs_pct}%")
        print(f"Baseline coverage:     {baseline_pct}% (treated as 100% health)")
        print(f"Normalized coverage:   {norm_pct}% of baseline")
    else:
        print("Absolute coverage:     N/A")
        print("Baseline coverage:     66.6667% (design target at mint)")
        print("Normalized coverage:   N/A")

    print(f"Tier:                  {tier}")
    print("==========================================\n")


if __name__ == "__main__":
    main()
