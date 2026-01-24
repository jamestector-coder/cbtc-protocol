# cBTC Protocol – Threat Model

This document outlines the primary threats, attack surfaces, and failure modes
considered in the design of the cBTC protocol.

The goal is not to claim perfect safety, but to clearly state:
- what is protected,
- what is assumed,
- what could fail,
- and how failures are mitigated or bounded.

---

## 1. Scope and assumptions

### In scope

- Bitcoin protocol security (UTXO model, signatures, consensus)
- On-chain BTC custody and accounting
- Minting Channel lifecycle
- Redemption Pool solvency
- Deterministic issuance and redemption rules
- Honest-but-curious participants

### Out of scope

- Bitcoin consensus failure
- Global cryptographic breaks
- Wallet malware on user machines
- Social engineering attacks
- Regulatory or legal risks

---

## 2. Assets to protect

The protocol aims to protect:

1. Principal BTC deposited by Collateral Providers
2. Redemption Pool BTC backing outstanding cBTC
3. Deterministic issuance and redemption rules
4. Predictability of protocol outcomes

---

## 3. Adversary models

### 3.1 Malicious Collateral Provider (CP)

A CP may attempt to:
- mint more cBTC than allowed,
- reclaim yield early without penalty,
- trigger redemptions that affect principal,
- manipulate accounting.

**Mitigations:**
- Issuance fixed at channel creation
- Prefunded yield
- Yield forfeiture on early closure
- Strict segregation of principal, yield, and redemption collateral

---

### 3.2 Malicious cBTC holder

A cBTC holder may attempt to:
- redeem more BTC than entitled,
- exploit timing or ordering of redemptions,
- front-run redemption events.

**Mitigations:**
- Deterministic redemption formulas
- Transparent redemption tiers
- cBTC burned upon redemption
- No access to principal or yield collateral

---

### 3.3 Redemption Pool depletion attack

An attacker may attempt to:
- drain the Redemption Pool rapidly,
- force insolvency,
- extract value at the expense of later redeemers.

**Mitigations:**
- Conservative issuance (30% LTV)
- Global solvency thresholds
- Deterministic haircuts
- Issuance halt when thresholds are breached
- No reliance on emergency intervention

---

### 3.4 Coordinator failure or misbehavior (MVP)

In early implementations, coordination logic may be centralized.

Risks include:
- incorrect transaction construction,
- incorrect accounting,
- denial of service.

**Mitigations:**
- Bitcoin enforces custody, not coordinators
- Manual regtest verification
- Clear separation between protocol rules and tooling
- Gradual decentralization path

---

## 4. Economic attack surfaces

### 4.1 Price volatility

BTC price volatility does not directly affect protocol mechanics because:
- no fiat prices are referenced,
- no liquidations exist,
- issuance and redemption are BTC-denominated.

Residual risk:
- opportunity cost for participants.

---

### 4.2 Liquidity stress

Under heavy redemption demand:
- redemption rates degrade deterministically,
- early redeemers do not gain privileged access,
- no cascading liquidations occur.

This trades price certainty for predictability.

---

## 5. Timing and ordering attacks

Potential risks:
- front-running redemptions,
- timing channel closures.

Mitigations:
- deterministic formulas,
- transparent pool state,
- no hidden priority rules.

---

## 6. Smart contract and script risks

Future implementations may use:
- timelocks,
- Taproot scripts,
- Lightning channels.

Risks include:
- script bugs,
- incorrect timelock logic.

Mitigations:
- minimal script complexity
- reliance on well-understood Bitcoin primitives
- incremental deployment

---

## 7. Custody risks

The protocol avoids pooled custody of principal.

Residual risks:
- user key loss,
- wallet compromise.

These are inherent to Bitcoin self-custody and not unique to cBTC.

---

## 8. Known limitations

- Early implementations rely on off-chain coordination.
- Fee handling may introduce minor accounting drift.
- Full decentralization is not achieved in the MVP.
- Privacy properties depend on future transport layers.

These limitations are acknowledged and explicit.

---

## 9. Failure modes

If failures occur, they are intentionally bounded:

- No forced liquidations
- No seizure of principal
- No systemic leverage amplification
- Worst case: slower or discounted redemption

---

## 10. Summary

cBTC prioritizes:
- bounded downside,
- explicit failure modes,
- deterministic outcomes.

The protocol is designed to fail **predictably**, not catastrophically.

This threat model will evolve as implementations mature.
