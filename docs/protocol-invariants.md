# cBTC Protocol – Invariants (MVP v0.1)

This document defines the **rules that must never be violated** by the cBTC protocol.

These invariants are enforced in the MVP via scripts and deterministic math.

---

## Invariant 1 – Issuance Rate

- cBTC issuance is fixed:
  - **30,000 cBTC per 1 BTC deposited**
- Issuance does not depend on price, oracle data, or market conditions

---

## Invariant 2 – Collateral Split

For every deposit `D`:

- Principal = `0.70 × D`
- Redemption Pool = `0.20 × D`
- Yield Pool = `0.10 × D`

The sum must never exceed `D`.

---

## Invariant 3 – Redemption Pool Solvency

Let:

- `O` = outstanding cBTC
- `R` = Redemption Pool BTC

Then:

- Floor liability = `O × 0.00001 BTC`
- Coverage = `R / floor liability`

The protocol must enforce:

- **Coverage ≥ 50% after any redemption**

---

## Invariant 4 – Redemptions

- Redemptions:
  - burn cBTC
  - pay BTC only from the Redemption Pool
- Principal and Yield are never used for redemptions

---

## Invariant 5 – No Liquidations

- Minting Channels are never liquidated
- Principal is never seized due to price movements
- Risk is absorbed via:
  - prefunded redemption reserves
  - deterministic haircuts

---

## Invariant 6 – Auditability

- All mint and redeem events must be:
  - logged in an append-only ledger
  - reproducible from source data
