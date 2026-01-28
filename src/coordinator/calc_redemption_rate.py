#!/usr/bin/env python3
# ------------------------------------------------------------
# cBTC Protocol – Redemption Rate Simulator (EXPERIMENTAL)
#
# This script simulates a redemption event **without** touching
# Bitcoin Core or the on-chain wallets.
#
# It:
# - asks for:
#     - Outstanding cBTC
#     - Redemption Pool BTC
#     - Requested redemption cBTC
# - computes:
#     - floor liability
#     - absolute coverage (pre & post)
#     - redemption tier:
#         Tier 1 – Full floor     (coverage ≥ 60%)
#         Tier 2 – Haircuts       (50% ≤ coverage < 60%)
#         Tier 3 – Protection     (coverage < 50%)
# - applies the same logic as redeem_cbtc.py:
#     - Tier 1 & 2:
#         try full floor payout;
#         if that would push coverage < 50%, haircut so
#         coverage_after = 50%
#     - Tier 3:
#         strictly pro-rata:
#             btc_paid = P * (R / O)
#
# ⚠️ For reasoning and testing only. Not production code.
# ------------------------------------------------------------

from decimal import Decimal, getcontext

getcontext().prec = 18

FLOOR_RATE = Decimal("0.00001")  # BTC per 1 cBTC

BASELINE_COVERAGE = (Decimal("0.20") / Decimal("0.30"))  # ≈ 66.67%


def main():
    print("=== cBTC Redemption Simulation ===")

    # --- Inputs -----------------------------------------------------------
    raw_outstanding = input("Outstanding cBTC (e.g. 30000): ").strip()
    raw_red_pool = input("Redemption Pool BTC (e.g. 0.20000000): ").strip()
    raw_redeem = input("Requested redemption cBTC (e.g. 15000): ").strip()

    try:
        O = Decimal(raw_outstanding)
        P = Decimal(raw_red_pool)
        R = Decimal(raw_redeem)
    except Exception:
        print("[ERROR] Invalid numeric input.")
        return

    if O <= 0:
        print("[ERROR] Outstanding cBTC must be > 0.")
        return
    if P < 0:
        print("[ERROR] Redemption Pool BTC must be ≥ 0.")
        return
    if R <= 0:
        print("[ERROR] Redemption request must be > 0.")
        return
    if R > O:
        print("[ERROR] Redemption request cannot exceed outstanding cBTC.")
        return

    # --- Base quantities --------------------------------------------------
    F = FLOOR_RATE
    L_before = (O * F).quantize(Decimal("0.00000001"))
    if L_before <= 0:
        print("[ERROR] Invalid liability (L_before <= 0).")
        return

    absolute_coverage_before = P / L_before

    # Tier classification by absolute coverage
    if absolute_coverage_before >= Decimal("0.60"):
        tier = "Tier 1 – Full floor"
    elif absolute_coverage_before >= Decimal("0.50"):
        tier = "Tier 2 – Haircuts"
    else:
        tier = "Tier 3 – Protection mode (pro-rata)"

    # After redemption:
    O_after = (O - R).quantize(Decimal("0.001"))
    if O_after < 0:
        print("[ERROR] Redemption amount exceeds outstanding cBTC (post-check).")
        return

    if O_after > 0:
        L_after = (O_after * F).quantize(Decimal("0.00000001"))
    else:
        L_after = Decimal("0")

    btc_needed_full = (R * F).quantize(Decimal("0.00000001"))

    # Helper for coverage_after
    def compute_coverage_after(payout: Decimal) -> Decimal:
        if O_after <= 0 or L_after <= 0:
            return Decimal("0")
        P_after = (P - payout).quantize(Decimal("0.00000001"))
        return P_after / L_after

    btc_paid = Decimal("0")
    redemption_rate = Decimal("0")
    absolute_coverage_after = None

    # --- Tier 1 & 2 logic -------------------------------------------------
    if tier.startswith("Tier 1") or tier.startswith("Tier 2"):
        if O_after <= 0:
            # Redeeming all outstanding: no future liability.
            btc_paid = min(btc_needed_full, P)
            redemption_rate = (btc_paid / R).quantize(Decimal("0.00000001"))
            absolute_coverage_after = Decimal("0")
        else:
            # Try full floor
            P_after_full = (P - btc_needed_full).quantize(Decimal("0.00000001"))
            if P_after_full < 0:
                can_pay_full = False
            else:
                cov_after_full = compute_coverage_after(btc_needed_full)
                can_pay_full = (cov_after_full >= Decimal("0.50"))

            if can_pay_full:
                btc_paid = btc_needed_full
                redemption_rate = F
                absolute_coverage_after = compute_coverage_after(btc_paid)
            else:
                # Haircut so coverage_after = 50%
                if L_after <= 0:
                    # Edge case: no remaining liability, just pay pool
                    btc_paid = P
                else:
                    btc_paid_candidate = (P - Decimal("0.5") * L_after).quantize(Decimal("0.00000001"))
                    if btc_paid_candidate < 0:
                        btc_paid_candidate = Decimal("0")
                    btc_paid = min(btc_paid_candidate, btc_needed_full, P)

                if btc_paid > 0:
                    redemption_rate = (btc_paid / R).quantize(Decimal("0.00000001"))
                else:
                    redemption_rate = Decimal("0")
                absolute_coverage_after = compute_coverage_after(btc_paid)

    # --- Tier 3: strictly pro-rata ----------------------------------------
    else:
        # coverage < 50%
        # BTC payout is proportional to share of outstanding:
        #    btc_paid = P * (R / O)
        share = (R / O)
        btc_paid = (P * share).quantize(Decimal("0.00000001"))
        if btc_paid > P:
            btc_paid = P

        if R > 0:
            redemption_rate = (btc_paid / R).quantize(Decimal("0.00000001"))
        else:
            redemption_rate = Decimal("0")

        if O_after > 0 and L_after > 0:
            absolute_coverage_after = compute_coverage_after(btc_paid)
        else:
            absolute_coverage_after = Decimal("0")

    # Sanity
    if btc_paid < 0:
        btc_paid = Decimal("0")
    if btc_paid > P:
        btc_paid = P

    # --- Print results ----------------------------------------------------
    abs_cov_before_pct = (absolute_coverage_before * Decimal("100")).quantize(Decimal("0.0001"))
    baseline_pct = (BASELINE_COVERAGE * Decimal("100")).quantize(Decimal("0.0001"))
    norm_before = (absolute_coverage_before / BASELINE_COVERAGE * Decimal("100")).quantize(Decimal("0.0001"))

    print("\n---------------------------------")
    print(f"Tier:                 {tier}")
    print(f"Outstanding cBTC:     {O}")
    print(f"Redemption Pool BTC:  {P:.8f}")
    print(f"Floor liability (pre): {L_before:.8f}")
    print(f"Absolute coverage (pre): {abs_cov_before_pct}%")
    print(f"Baseline coverage:      {baseline_pct}% (treated as 100% health)")
    print(f"Normalized coverage:    {norm_before}% of baseline")
    print("---------------------------------")
    print(f"Requested redemption: {R} cBTC")
    print(f"Redemption rate:      {redemption_rate:.8f} BTC per cBTC")
    print(f"BTC paid out:         {btc_paid:.8f}")

    if absolute_coverage_after is not None and L_after > 0 and O_after > 0:
        abs_cov_after_pct = (absolute_coverage_after * Decimal("100")).quantize(Decimal("0.0001"))
        norm_after = (absolute_coverage_after / BASELINE_COVERAGE * Decimal("100")).quantize(Decimal("0.0001"))
        print(f"Floor liability (post): {L_after:.8f}")
        print(f"Absolute coverage (post): {abs_cov_after_pct}%")
        print(f"Normalized coverage (post): {norm_after}% of baseline")
    else:
        print("Floor liability (post): 0.00000000")
        print("Absolute coverage (post): N/A")

    print("=================================\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[ERROR] {e}")
