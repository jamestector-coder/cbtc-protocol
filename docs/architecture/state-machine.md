# cBTC State Machine – Protocol Specification

**Version:** v0.1  
**Status:** Experimental  
**Scope:** Bitcoin regtest MVP → future testnet/mainnet implementations

This document defines the **state machine** governing the lifecycle of cBTC,
from issuance to final burn.

The state machine describes **what can happen**, **when**, and **under which conditions**.
It is independent of any specific implementation.

---

## 1. Purpose

The cBTC state machine formalizes:

- how cBTC comes into existence,
- how it circulates,
- how it is redeemed,
- how it is permanently removed from supply.

This ensures:
- determinism,
- auditability,
- and protocol correctness.

---

## 2. High-Level Lifecycle

The lifecycle of cBTC consists of four primary states:

┌──────────────┐
│ UNISSUED │
└──────┬───────┘
│ open_mint_channel
▼
┌──────────────┐
│ ISSUED │
│ (Circulating)│
└──────┬───────┘
│ redeem_cbtc
▼
┌──────────────┐
│ BURNED │
└──────────────┘

There is **no transition backward** once cBTC is burned.

---

## 3. States

### 3.1 UNISSUED

**Description**  
cBTC does not yet exist.

**Properties**
- Total supply = 0
- No claims exist on the Redemption Pool

**Allowed Transitions**
- `open_mint_channel`

---

### 3.2 ISSUED (Circulating)

**Description**  
cBTC exists and may circulate among holders.

**Properties**
- Backed by:
  - principal (70%)
  - Redemption Pool BTC (20%)
  - yield (10%)
- Outstanding supply is tracked in the ledger
- cBTC is transferable off-chain (MVP)

**Allowed Transitions**
- `redeem_cbtc` (partial or full)

**Forbidden Transitions**
- Conversion back to principal
- Re-minting without new BTC

---

### 3.3 BURNED

**Description**  
cBTC has been redeemed and permanently removed from supply.

**Properties**
- No longer counted as outstanding
- Cannot be reused or reissued
- Redemption Pool BTC is reduced accordingly

**Allowed Transitions**
- None (terminal state)

---

## 4. Transitions

### 4.1 `open_mint_channel`

**From:** `UNISSUED`  
**To:** `ISSUED`

**Trigger**
- A Collateral Provider deposits BTC on-chain.

**Conditions**
- Deposit between `0.05 BTC` and `5 BTC`
- CP controls sufficient confirmed BTC
- Protocol not in restricted issuance mode

**Effects**
- BTC split deterministically:
  - 70% → principal
  - 20% → Redemption Pool
  - 10% → yield
- New cBTC is issued:
  - `30,000 cBTC per 1 BTC deposited`
- Ledger records mint event
- Outstanding supply increases

---

### 4.2 `redeem_cbtc`

**From:** `ISSUED`  
**To:** `BURNED` (partial or full)

**Trigger**
- A cBTC holder requests redemption.

**Conditions**
- Requested amount ≤ outstanding supply
- Redemption respects coverage and solvency invariants
- Valid Bitcoin address provided

**Effects**
- cBTC is burned (ledger update)
- BTC is paid from Redemption Pool
- Coverage is recomputed
- Post-redemption coverage ≥ 50%

---

## 5. Global Invariants (Always Enforced)

At every state and transition, the following MUST hold:

### 5.1 Solvency Invariant
Redemption Pool BTC ≥ 50% × floor liability

### 5.2 Supply Conservation
Outstanding cBTC = Total minted − Total burned

### 5.3 No Collateral Mixing
- Principal is never used for redemption
- Yield is never used for redemption
- Redemption Pool BTC is only used for redemption

---

## 6. State Transitions Table

| Current State | Action | Next State | Allowed |
|-------------|--------|-----------|--------|
| UNISSUED | open_mint_channel | ISSUED | ✅ |
| ISSUED | redeem_cbtc (partial) | ISSUED | ✅ |
| ISSUED | redeem_cbtc (full) | BURNED | ✅ |
| BURNED | any | — | ❌ |

---

## 7. Failure Modes

If a transition cannot satisfy invariants:

- The transition MUST fail
- No partial state changes are allowed
- No collateral may be moved

Examples:
- Redemption rejected due to solvency limits
- Issuance restricted under low coverage

---

## 8. Determinism and Auditability

All state transitions are:

- deterministic,
- auditable via ledger events,
- verifiable using:
  - on-chain BTC balances,
  - off-chain cBTC accounting.

Any observer can independently reconstruct the state.

---

## 9. Relationship to Implementation

In MVP v0.1:

- State is represented implicitly via:
  - Bitcoin Core wallets (BTC)
  - `ledger.json` (cBTC)
- Transitions are executed by coordinator scripts
- Enforcement is logical, not script-enforced

Future versions may:
- encode transitions in scripts,
- enforce invariants on-chain,
- decentralize coordination.

---

## 10. Summary

The cBTC state machine is intentionally simple:

- No recursive states
- No hidden transitions
- No discretionary overrides

This simplicity ensures:
- predictability,
- safety,
- and long-term extensibility.

The state machine is the foundation upon which
all future cBTC implementations must be built.