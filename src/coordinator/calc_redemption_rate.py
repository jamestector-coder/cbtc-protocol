#!/usr/bin/env python3
"""
cBTC – Redemption Rate Calculator (Regtest / Research Tool)

This script computes the safe redemption rate for a given redemption request
so that post-redemption coverage never falls below 50%.

⚠️ Experimental research tool.
Use for simulations and reasoning only.

Protocol parameters:
- Redemption floor f = 0.00001 BTC per cBTC
- Minimum coverage after redemption = 50%
"""

from decimal import Decimal, getcontext

getcontext().prec = 16

# ---- Protocol constants ----
FLOOR_RATE = Decimal("0.00001")   # BTC per cBTC
MIN_COVERAGE = Decimal("0.50")    # 50%

def calc_redemption_rate(outstanding_cbtc, redemption_pool_btc, redeem_q):
    """
    Returns:
        rate (BTC per cBTC),
        btc_paid,
        coverage_before,
        coverage_after,
        tier_label
    """

    O = Decimal(outstanding_cbtc)
    P = Decimal(redemption_pool_btc)
    q = Decimal(redeem_q)

    if q <= 0:
        raise ValueError("Redeemed cBTC must be positive")

    if q > O:
        raise ValueError("Cannot redeem more cBTC than outstanding")

    # Liability at full floor
    L_before = O * FLOOR_RATE
    coverage_before = P / L_before if L_before > 0 else Decimal("0")

    # Safe rate derived from:
    # (P - r*q) / (f*(O - q)) >= 0.5
    numerator = P - (MIN_COVERAGE * FLOOR_RATE * (O - q))
    r_safe = numerator / q

    # Final applied rate
    r = min(FLOOR_RATE, r_safe)

    if r < 0:
        r = Decimal("0")

    btc_paid = r * q

    # After redemption
    P_after = P - btc_paid
    O_after = O - q
    L_after = O_after * FLOOR_RATE if O_after > 0 else Decimal("0")
    coverage_after = P_after / L_after if L_after > 0 else Decimal("0")

    # Tier classification (UX / docs only)
    if coverage_before >= Decimal("0.70"):
        tier = "Tier 1 – Full floor zone"
    elif coverage_before >= Decimal("0.50"):
        tier = "Tier 2 – Haircut zone"
    else:
        tier = "Tier 3 – Insolvency zone"

    return {
        "rate": r,
        "btc_paid": btc_paid,
        "coverage_before": coverage_before,
        "coverage_after": coverage_after,
        "tier": tier
    }


# ---- Example usage ----
if __name__ == "__main__":
    # Example scenario (edit freely)
    OUTSTANDING_CBTC = Decimal("83000")
    REDEMPTION_POOL = Decimal("0.484989")
    REDEEM_Q = Decimal("15000")

    result = calc_redemption_rate(
        outstanding_cbtc=OUTSTANDING_CBTC,
        redemption_pool_btc=REDEMPTION_POOL,
        redeem_q=REDEEM_Q
    )

    print("\n=== cBTC Redemption Simulation ===")
    print(f"Outstanding cBTC:     {OUTSTANDING_CBTC}")
    print(f"Redemption Pool BTC:  {REDEMPTION_POOL}")
    print(f"Redeem request:       {REDEEM_Q} cBTC")
    print("---------------------------------")
    print(f"Coverage before:      {result['coverage_before']:.4%}")
    print(f"Tier:                 {result['tier']}")
    print("---------------------------------")
    print(f"Redemption rate:      {result['rate']} BTC per cBTC")
    print(f"BTC paid out:         {result['btc_paid']}")
    print("---------------------------------")
    print(f"Coverage after:       {result['coverage_after']:.4%}")
    print("=================================\n")
