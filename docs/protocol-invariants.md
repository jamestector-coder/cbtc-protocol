# cBTC Protocol – Invariants

This document defines the **non-negotiable invariants** of the cBTC protocol.

An invariant is a rule that **must always hold true**, regardless of
implementation details, coordination mechanisms, or future extensions.

If any invariant is violated, the protocol is considered broken.

---

## 1. Issuance Invariants

1. cBTC issuance occurs **only** at Minting Channel creation.
2. Minted cBTC amount is fixed at issuance time and never increases later.
3. Issuance formula:
   - `Minted cBTC = 30,000 × deposited BTC`
4. No refinancing, rollover, or dynamic leverage is allowed.
5. Total outstanding cBTC equals the sum of all unredeemed issuance events.

---

## 2. Collateral Segregation Invariants

1. Deposited BTC is always split deterministically:
   - 70% → Principal
   - 20% → Redemption Pool
   - 10% → Yield allocation
2. These three roles are **strictly segregated**.
3. Funds assigned to one role must never be reused for another role.

---

## 3. Principal Protection Invariants

1. Principal BTC is **never** used to:
   - pay redemptions,
   - cover losses,
   - subsidize yield.
2. Principal is not subject to liquidation.
3. Principal loss is not a protocol mechanism.
4. Principal may only be released to its owner according to channel rules.

---

## 4. Yield Invariants

1. Yield is **prefunded** at Minting Channel creation.
2. Yield is isolated per Minting Channel.
3. Yield distribution is **time-based**, not price-based.
4. Yield cannot be rehypothecated or lent.
5. Unvested yield is forfeited upon early channel closure.
6. Forfeited yield strengthens the Redemption Pool.
7. Yield forfeiture never affects principal.

---

## 5. Redemption Invariants

1. cBTC is redeemable **only for BTC**.
2. Redemptions are paid **exclusively** from the Redemption Pool.
3. cBTC is burned upon redemption.
4. Principal and yield collateral are never used for redemption.
5. Redemption rules are deterministic and publicly verifiable.
6. Redemption pricing must always preserve post-redemption coverage ≥ 50% of
   full-floor liability.

---

## 6. Solvency Invariants

1. A global Redemption Pool backs all outstanding cBTC.
2. Redemption Pool coverage is evaluated against maximum redemption liability:
   - `Liability = outstanding cBTC × 0.00001 BTC`
3. Redemption rates follow deterministic tiers based on coverage.
4. Issuance halts automatically if solvency thresholds are breached.
5. No discretionary intervention or emergency governance exists.
6. Global coverage is defined as P / (O · f) with a hard lower bound of 50%
   enforced by redemption pricing.


---

## 7. Liquidation and Oracle Invariants

1. The protocol has **no liquidations**.
2. The protocol uses **no price oracles**.
3. No fiat reference prices are required.
4. Risk management relies on time, prefunding, and conservative issuance.

---

## 8. Custody and Trust Invariants

1. The protocol does not require custodians to hold user funds.
2. Ownership is enforced by Bitcoin keys and scripts.
3. Users retain custody of their principal at all times.
4. Coordination mechanisms must not introduce hidden trust assumptions.

---

## 9. Supply Discipline Invariants

1. There is no discretionary monetary policy.
2. cBTC supply expands only through issuance.
3. cBTC supply contracts only through redemption and burn.
4. Supply rules are deterministic and transparent.

---

## 10. Scope Invariants

1. This document defines **protocol-level guarantees**, not implementation details.
2. MVP shortcuts must not violate any invariant listed above.
3. Future upgrades must preserve all invariants unless explicitly deprecated.

---

## Final Note

These invariants define what cBTC **is**.

Any implementation that violates them is **not** a valid implementation
of the cBTC protocol.
