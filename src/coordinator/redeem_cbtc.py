#!/usr/bin/env python3
# ------------------------------------------------------------
# cBTC Protocol – Redemption (EXPERIMENTAL)
#
# Interactively:
# - Reads current ledger and Redemption Pool BTC
# - Asks for a cBTC amount to redeem
# - Computes redemption rate according to coverage tiers:
#
#   Tier 1 – Full floor:
#       absolute_coverage >= 60%
#       → try full floor (0.00001 BTC/cBTC)
#       → if that would drop coverage < 50%, haircut to keep ≥ 50%
#
#   Tier 2 – Haircuts:
#       50% <= absolute_coverage < 60%
#       → try full floor
#       → if that would drop coverage < 50%, haircut to land at 50%
#
#   Tier 3 – Protection mode:
#       absolute_coverage < 50%
#       → strictly pro-rata:
#           btc_paid = P * (R / O)
#         which keeps coverage constant
#
# - Executes redemption on-chain from Redemption Pool wallet
# - Appends a "redeem" event to data/ledger.json
#
# ⚠️ For regtest/testing only. Not production-ready.
# ------------------------------------------------------------

from decimal import Decimal, getcontext
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from pathlib import Path
import datetime
import json

getcontext().prec = 18

# --- CONSTANTS -------------------------------------------------------------

FLOOR_RATE = Decimal("0.00001")  # BTC per 1 cBTC

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


def save_ledger(data):
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)


def sum_minted_and_redeemed_mC(events):
    """
    Returns:
      total_minted_mC   – integer milli-cBTC
      total_redeemed_mC – integer milli-cBTC

    Compatible with:
      - older events with "minted_cbtc" / "burned_cbtc" only
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
    cbtc = (Decimal(mC) / Decimal("1000")).quantize(Decimal("0.001"))
    return f"{cbtc:.3f}"


# --- MAIN ------------------------------------------------------------------

def main():
    # --- Load ledger and compute outstanding -------------------------------
    ledger = load_ledger()
    events = ledger.get("events", [])

    total_minted_mC, total_redeemed_mC = sum_minted_and_redeemed_mC(events)
    outstanding_mC = total_minted_mC - total_redeemed_mC

    outstanding_cbtc = (Decimal(outstanding_mC) / Decimal("1000")).quantize(Decimal("0.001"))
    outstanding_str = format_cbtc_from_mC(outstanding_mC)

    # --- Get Redemption Pool BTC ------------------------------------------
    red_client = make_wallet_client(REDEMPTION_WALLET_NAME)
    red_balance_btc = Decimal(str(red_client.getbalance()))

    print("\n=== cBTC Redemption (Regtest MVP) ===")
    print(f"Ledger file:           {str(LEDGER_PATH)}")
    print("--------------------------------------")
    print(f"Total minted cBTC:     {format_cbtc_from_mC(total_minted_mC)}")
    print(f"Total redeemed cBTC:   {format_cbtc_from_mC(total_redeemed_mC)}")
    print(f"Estimated outstanding: {outstanding_str}")
    print("--------------------------------------")
    print(f"Redemption Pool BTC:   {red_balance_btc:.8f}")

    if outstanding_mC <= 0:
        print("\n[ERROR] No outstanding cBTC to redeem.")
        return

    # --- Ask user for redemption amount -----------------------------------
    raw_amount = input("Enter amount of cBTC to redeem (e.g. 3000 or 250.500): ").strip()
    try:
        requested_cbtc = Decimal(raw_amount)
    except Exception:
        print(f"[ERROR] Invalid cBTC amount: {raw_amount}")
        return

    if requested_cbtc <= 0:
        print("[ERROR] Redemption amount must be > 0.")
        return

    # Quantize to 3 decimal places
    requested_cbtc = requested_cbtc.quantize(Decimal("0.001"))
    requested_mC = int((requested_cbtc * Decimal("1000")).quantize(Decimal("1")))

    if requested_mC > outstanding_mC:
        print("[ERROR] Requested amount exceeds outstanding cBTC.")
        return

    # --- Basic quantities --------------------------------------------------
    O = outstanding_cbtc                      # total outstanding (Decimal)
    R = requested_cbtc                        # requested redemption (Decimal)
    F = FLOOR_RATE                            # floor rate (BTC / cBTC)
    P = red_balance_btc                       # Redemption Pool BTC

    L_before = (O * F).quantize(Decimal("0.00000001"))  # floor liability before

    if L_before <= 0:
        print("\n[ERROR] Invalid liability state (L_before <= 0).")
        return

    absolute_coverage_before = P / L_before

    # Determine tier from absolute coverage
    if absolute_coverage_before >= Decimal("0.60"):
        tier = "Tier 1 – Full floor"
    elif absolute_coverage_before >= Decimal("0.50"):
        tier = "Tier 2 – Haircuts"
    else:
        tier = "Tier 3 – Protection mode (pro-rata)"

    # --- Compute post-redemption base quantities --------------------------
    O_after = (O - R).quantize(Decimal("0.001"))
    if O_after < 0:
        print("[ERROR] Redemption amount exceeds outstanding cBTC (post-check).")
        return

    if O_after > 0:
        L_after = (O_after * F).quantize(Decimal("0.00000001"))
    else:
        L_after = Decimal("0")

    btc_needed_full = (R * F).quantize(Decimal("0.00000001"))

    # --- Decide payout and rate based on tier -----------------------------
    btc_paid = Decimal("0")
    redemption_rate = Decimal("0")
    absolute_coverage_after = None

    # Helper: compute coverage after a given payout when O_after > 0
    def compute_coverage_after(payout: Decimal) -> Decimal:
        if O_after <= 0:
            return Decimal("0")
        P_after = (P - payout).quantize(Decimal("0.00000001"))
        if L_after <= 0:
            return Decimal("0")
        return P_after / L_after

    # --- Tier 1 & Tier 2: full floor if safe, else haircut to ≥ 50% -------
    if tier.startswith("Tier 1") or tier.startswith("Tier 2"):
        if O_after <= 0:
            # Redeeming all outstanding cBTC: no future liability.
            # Pay up to full floor, capped by pool.
            btc_paid = min(btc_needed_full, P)
            redemption_rate = (btc_paid / R).quantize(Decimal("0.00000001"))
            absolute_coverage_after = Decimal("0")
        else:
            # Try full floor first
            P_after_full = (P - btc_needed_full).quantize(Decimal("0.00000001"))

            if P_after_full < 0:
                # Can't afford full floor, must haircut
                can_pay_full = False
            else:
                cov_after_full = compute_coverage_after(btc_needed_full)
                can_pay_full = (cov_after_full >= Decimal("0.50"))

            if can_pay_full:
                # Full floor is safe
                btc_paid = btc_needed_full
                redemption_rate = F
                absolute_coverage_after = compute_coverage_after(btc_paid)
            else:
                # Haircut so that coverage_after = 50%
                # coverage_after = (P - btc_paid) / L_after = 0.5
                # => btc_paid = P - 0.5 * L_after
                if L_after <= 0:
                    # No remaining liability but we couldn't pay full floor.
                    # In that weird edge case, just pay what's left in the pool
                    # proportionally (which will empty it).
                    btc_paid = P
                else:
                    btc_paid_candidate = (P - Decimal("0.5") * L_after).quantize(Decimal("0.00000001"))
                    if btc_paid_candidate < 0:
                        btc_paid_candidate = Decimal("0")
                    # Never pay more than full floor or more than the pool
                    btc_paid = min(btc_paid_candidate, btc_needed_full, P)

                if btc_paid > 0:
                    redemption_rate = (btc_paid / R).quantize(Decimal("0.00000001"))
                else:
                    redemption_rate = Decimal("0")
                absolute_coverage_after = compute_coverage_after(btc_paid)

    # --- Tier 3: strictly pro-rata ----------------------------------------
    else:
        # absolute_coverage_before < 50%
        # Pro-rata rule:
        #    btc_paid = P * (R / O)
        # Ensures coverage_after == coverage_before (constant coverage).
        if O <= 0:
            print("\n[ERROR] Invalid outstanding (O <= 0) in Tier 3.")
            return

        share = (R / O)
        btc_paid = (P * share).quantize(Decimal("0.00000001"))

        # Cap at pool for sanity
        if btc_paid > P:
            btc_paid = P

        if R > 0:
            redemption_rate = (btc_paid / R).quantize(Decimal("0.00000001"))
        else:
            redemption_rate = Decimal("0")

        # Coverage after should be equal to coverage before if O_after > 0
        if O_after > 0 and L_after > 0:
            absolute_coverage_after = compute_coverage_after(btc_paid)
        else:
            absolute_coverage_after = Decimal("0")

    # Sanity: never pay negative or more than pool
    if btc_paid < 0:
        btc_paid = Decimal("0")
    if btc_paid > P:
        btc_paid = P

    # --- Quote summary -----------------------------------------------------
    print("\n--- Redemption Quote ---")
    print(f"Tier:                  {tier}")
    print(f"Requested redemption:  {requested_cbtc:.3f} cBTC")
    print(f"Redemption Pool BTC:   {P:.8f}")
    print(f"Floor liability (pre): {L_before:.8f}")
    print(f"Absolute coverage (pre): {(absolute_coverage_before * Decimal('100')).quantize(Decimal('0.0001'))}%")
    print("--------------------------------------")
    print(f"Redemption rate:       {redemption_rate:.8f} BTC per cBTC")
    print(f"Total BTC to be paid:  {btc_paid:.8f}")

    if absolute_coverage_after is not None and L_after > 0 and O_after > 0:
        print(f"Floor liability (post): {L_after:.8f}")
        print(f"Absolute coverage (post): {(absolute_coverage_after * Decimal('100')).quantize(Decimal('0.0001'))}%")
    else:
        print("Floor liability (post): 0.00000000")
        print("Absolute coverage (post): N/A (no remaining liability or not defined)")

    print("------------------------")

    # --- Ask for confirmation ---------------------------------------------
    confirm = input("Proceed with on-chain redemption and ledger update? (yes/no): ").strip().lower()
    if confirm not in ("yes", "y"):
        print("[INFO] Redemption cancelled.")
        return

    # --- Execute on-chain redemption --------------------------------------
    recv_addr = input("Enter BTC address to receive redemption BTC (regtest address): ").strip()
    if not recv_addr:
        print("[ERROR] No address provided.")
        return

    try:
        txid = red_client.sendtoaddress(recv_addr, float(btc_paid))
    except JSONRPCException as e:
        print(f"[ERROR] sendtoaddress failed: {e}")
        return

    # --- Append redeem event to ledger ------------------------------------
    burned_cbtc = requested_cbtc.quantize(Decimal("0.001"))
    burned_mC = int((burned_cbtc * Decimal("1000")).quantize(Decimal("1")))
    btc_paid_str = f"{btc_paid:.8f}"

    event = {
        "type": "redeem",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "burned_cbtc": f"{burned_cbtc:.3f}",
        "burned_mC": burned_mC,
        "btc_paid": btc_paid_str,
        "redemption_rate": f"{redemption_rate:.8f}",
        "tier": tier,
        "txid": txid,
        "coverage_before": f"{(absolute_coverage_before * Decimal('100')).quantize(Decimal('0.0001'))}%",
    }

    if absolute_coverage_after is not None and L_after > 0 and O_after > 0:
        event["coverage_after"] = f"{(absolute_coverage_after * Decimal('100')).quantize(Decimal('0.0001'))}%"
    else:
        event["coverage_after"] = "N/A"

    ledger["events"].append(event)
    save_ledger(ledger)

    print("\n[RESULT] Redemption executed and logged.")
    print(f"         Redemption txid: {txid}")
    print(f"         Burned cBTC:     {burned_cbtc:.3f}")
    print(f"         BTC paid out:    {btc_paid_str}")
    print("\n[NOTE] Event appended to data/ledger.json")
    print("       (off-chain cBTC burn accounting for regtest simulations).")
    print("==========================================\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[ERROR] {e}")
