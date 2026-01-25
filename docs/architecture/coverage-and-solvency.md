# Coverage and Solvency – Protocol Specification (cBTC)

**Version:** v0.1  
**Status:** Experimental  
**Scope:** Bitcoin regtest MVP → future testnet/mainnet implementations

This document specifies how **coverage**, **solvency**, and **issuance limits**
are defined and enforced in the cBTC protocol.

Coverage and solvency rules are the **core safety constraints** of cBTC.

---

## 1. Purpose

The cBTC protocol is designed to:

- allow BTC-backed credit issuance,
- without liquidations,
- without price oracles,
- while remaining solvent under stress.

This is achieved by enforcing **simple, global, deterministic solvency rules**
based solely on BTC reserves and outstanding cBTC.

---

## 2. Definitions

| Term | Definition |
|----|-----------|
| Outstanding cBTC | Total minted cBTC minus total redeemed (burned) cBTC |
| Redemption Pool BTC | Total BTC held in the global Redemption Pool |
| Floor redemption rate | `0.00001 BTC per 1 cBTC` |
| Floor liability | `outstanding cBTC × floor redemption rate` |
| Coverage ratio | `Redemption Pool BTC ÷ floor liability` |

All values are public and auditable.

---

## 3. Fundamental Solvency Invariant

The protocol enforces a single global invariant:

Redemption Pool BTC ≥ 50% × floor liability

Equivalently:

Coverage ratio ≥ 50%

This invariant **must never be violated**.

It has priority over:
- minting requests,
- redemption requests,
- yield considerations,
- UX considerations.

---

## 4. Why 50%?

The 50% floor is chosen to ensure:

- partial but meaningful liquidity under stress,
- graceful degradation instead of collapse,
- predictable behavior during redemption surges.

At 50% coverage:
- every cBTC holder can still redeem **at least half** of the floor value,
- no single redemption can exhaust the pool.

This replaces liquidations with **deterministic haircutting**.

---

## 5. Coverage at Issuance

Minting Channels allocate deposits as follows:

| Component | Share |
|--------|------|
| Principal | 70% |
| Redemption Pool | 20% |
| Yield | 10% |

Given:
Issued cBTC = 30% LTV

The resulting coverage after minting is approximately:

coverage ≈ 20% / 30% ≈ 66.67%

Therefore:

- **Minting alone cannot violate solvency**
- New issuance always starts above the 50% floor

---

## 6. Coverage Dynamics

Coverage changes only through two actions:

### 6.1 Minting
- Increases outstanding cBTC
- Increases Redemption Pool BTC proportionally
- Coverage remains stable (~66.7%)

### 6.2 Redemption
- Decreases outstanding cBTC
- Decreases Redemption Pool BTC
- Coverage must be explicitly protected

Redemption is the **only operation that can threaten solvency**, and is therefore constrained.

---

## 7. Coverage Zones

Coverage is interpreted in discrete zones.

### Zone 1 – Healthy
Coverage ≥ 60%

- Full floor redemption rate applies
- Issuance allowed
- Redemptions unrestricted

---

### Zone 2 – Defensive
50% ≤ Coverage < 60%

- Redemption haircuts apply
- Redemption rates dynamically adjust
- Issuance MAY be restricted or monitored
- Solvency preserved

---

### Zone 3 – Critical
Coverage < 50%
- Protocol enters protection mode
- Redemptions are:
  - halted, or
  - strictly pro-rata
- New issuance MUST be restricted

The exact handling is implementation-defined but MUST preserve the invariant.

---

## 8. Issuance Restrictions

Issuance rules depend on coverage:

| Coverage | Issuance |
|------|--------|
| ≥ 60% | Allowed |
| 50–60% | Allowed with caution or soft limits |
| < 50% | Restricted / halted |

This ensures that credit expansion does not continue while reserves are stressed.

---

## 9. Determinism and Transparency

Coverage is computed from **public, objective values**:

- Redemption Pool BTC balance (on-chain)
- Outstanding cBTC (ledger)

No subjective inputs are used:
- no price feeds
- no governance votes
- no discretionary actions

Anyone can recompute coverage independently.

---

## 10. What Solvency Rules Do NOT Do

Solvency enforcement does NOT:

- liquidate collateral
- touch principal or yield
- seize funds
- require trust in operators
- rely on market prices

All enforcement occurs via **rate adjustment and issuance restriction**.

---

## 11. Attack Considerations

### Run on the Pool
- Limited by 50% post-redemption floor
- Early redeemers do not gain unfair advantage

### Credit Spiral
- Prevented by issuance restrictions under low coverage

### Manipulation
- Coverage depends only on BTC balances and cBTC supply

---

## 12. Future Extensions (Non-Normative)

Possible future improvements include:

- on-chain commitments to outstanding cBTC supply
- cryptographic proofs of ledger integrity
- multi-sig or threshold-controlled Redemption Pool
- automatic issuance throttling curves

None are required for MVP v0.1 correctness.

---

## 13. Summary

Coverage and solvency in cBTC are enforced through:

- a single global invariant,
- deterministic redemption math,
- conservative issuance rules,
- and strict separation of collateral types.

This replaces liquidation-based risk management with
**predictable, reserve-based solvency control**.