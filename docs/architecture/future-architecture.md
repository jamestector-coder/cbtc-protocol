# Future Architecture – Roadmap and Design Directions (cBTC)

**Version:** v0.1  
**Status:** Exploratory / Non-normative  
**Scope:** From regtest MVP to real-world deployments

This document outlines **possible future directions** for the cBTC protocol:
how it could evolve from a regtest MVP into a production-grade, Bitcoin-native
working capital system.

Nothing in this document is normative for MVP v0.1.  
It exists to guide discussion, research, and contributions.

---

## 1. Current Baseline (MVP v0.1)

The MVP demonstrates:

- cBTC **minting** via Mint Channels on Bitcoin regtest
- deterministic **70 / 20 / 10** split:
  - 70% principal
  - 20% Redemption Pool
  - 10% yield
- cBTC issuance at **30,000 cBTC per 1 BTC**
- **global solvency invariant**:
  - Redemption Pool BTC ≥ 50% of floor liability
- **deterministic redemptions** with haircuts
- **off-chain ledger** for cBTC mint/burn events

All of this is coordinated by simple Python scripts and Bitcoin Core wallets.

---

## 2. Long-Term Objectives

A full cBTC implementation should aim for:

1. **Bitcoin nativeness**
   - No external chains
   - No fiat pegs
   - No oracles

2. **Self-custody**
   - CPs always hold their principal and yield
   - Redemption Pool is controlled by robust, multi-party arrangements

3. **Scalability**
   - cBTC transfers should be cheap and fast
   - Prefer off-chain or L2 rails (Lightning, Taproot Assets, etc.)

4. **Minimized trust**
   - Clear, limited trust assumptions
   - Maximal use of Bitcoin Script and cryptography
   - Transparent, verifiable rules

5. **Composability**
   - cBTC should be easy to integrate into wallets, L2s, and Bitcoin-native apps

---

## 3. Representation of cBTC

Several representations are plausible:

### 3.1 Lightning / Taproot Assets

- cBTC represented as a **Taproot Asset** (TA) on top of Bitcoin
- Transfers occur over:
  - Lightning channels
  - Taproot Assets-over-Lightning
- Pros:
  - Low-fee, high-speed cBTC transfers
  - Strong alignment with Bitcoin-native ecosystem
- Challenges:
  - Integration complexity
  - Dependency on TA tooling and standards

### 3.2 Federated Mints (e.g. Fedimint-like)

- cBTC issued by a federation of guardians
- Users hold blind bearer tokens representing cBTC
- Pros:
  - Strong privacy
  - Familiar model for Bitcoiners
- Challenges:
  - Federation trust assumptions
  - More complex governance

### 3.3 On-Chain Commitments + Off-Chain Accounting

- cBTC ledger remains off-chain
- Periodic **on-chain commitments** of total supply and pool balances
- Pros:
  - Simple design
  - Easy to audit
- Challenges:
  - Less composable than Lightning-native assets

Future versions of cBTC may combine these approaches.

---

## 4. Custody and Key Management

### 4.1 Principal and Yield

- Always controlled by the **Collateral Provider (CP)**
- Future improvements:
  - Script-enforced timelocks for principal
  - Script-enforced vesting for yield
  - Optional multi-sig on CP side for institutional users

### 4.2 Redemption Pool

Several options:

1. **Simple multi-sig**
   - Controlled by a set of known operators
   - Manual or semi-automated redemptions

2. **Federated custody**
   - Fedimint-style guardians
   - Deterministic redemption rules baked into federation code

3. **Multi-coordinator + threshold signing**
   - Multiple independent coordinators propose redemptions
   - Threshold signature required to move funds

Any future deployment MUST:
- keep Redemption Pool funds segregated,
- enforce that funds are used **only** for redemptions.

---

## 5. Coordinators and Decentralization

In MVP v0.1:

- A single coordinator process:
  - computes coverage,
  - calculates redemption rates,
  - appends to ledger.

Future architecture could include:

1. **Multiple independent coordinators**
   - All running the same open-source logic
   - Cross-checking each other’s state and quotes

2. **Consensus over state**
   - Use of simple Byzantine-fault-tolerant protocols
   - Or lightweight commit chains to agree on:
     - outstanding cBTC
     - Redemption Pool state

3. **Client-side validation**
   - Wallets verify:
     - coverage math
     - rates
     - event history

The goal is to minimize any single “trusted party” role.

---

## 6. Fee Model and Sustainability

Redemptions and minting incur:

- Bitcoin transaction fees
- Coordinator / infrastructure costs

Possible fee models:

1. **Spread on redemption rate**
   - Slightly lower effective redemption rate than theoretical maximum
   - Difference accumulates as a fee buffer

2. **Minting fees**
   - Small surcharge on deposits
   - Part allocated to:
     - Redemption Pool
     - maintenance / dev

3. **Time-based fees**
   - Small ongoing fee paid by CPs
   - Could be rolled into yield design

Any fee mechanism MUST:
- not break core solvency invariants,
- remain transparent and predictable.

---

## 7. Governance and Upgradability

cBTC aims to avoid:
- opaque governance,
- arbitrary parameter changes.

Future governance considerations:

1. **Parameter locks**
   - Fix critical invariants (e.g. 50% floor, 30% LTV) in code
   - Make changes slow and opt-in

2. **Versioned deployments**
   - New deployments for each major change (v1, v2, …)
   - Users choose which version to use

3. **Multi-stakeholder review**
   - Formal specs
   - Public reviews from Bitcoin devs and economists

Upgrades should prioritize **predictability** over flexibility.

---

## 8. Testing and Formal Verification

Future goals:

1. **Extensive simulation**
   - Multiple CPs
   - Various redemption patterns
   - Adversarial scenarios

2. **Property-based testing**
   - Invariants:
     - solvency
     - supply conservation
     - non-mixing of collateral

3. **Formal methods**
   - Model the state machine and invariants in a formal language
   - Prove that certain classes of failures are impossible

---

## 9. Roadmap (Indicative, Non-Binding)

Short–medium term:

1. Strengthen regtest MVP
   - more tests, docs, and scenarios
2. Experimental testnet deployment
   - with small values
3. Lightning / Taproot Assets exploration
   - prototype cBTC transfer mechanisms

Medium–long term:

4. Federated or threshold-controlled Redemption Pool
5. Production-grade coordinator implementation
   - Rust / Go / C++
6. External security and economic audits

All roadmap items are subject to change based on feedback and research.

---

## 10. Summary

The future architecture of cBTC should:

- remain **Bitcoin-native**,
- preserve **self-custody**,
- enforce **solvency via simple rules**,
- and scale via **off-chain or L2 transport layers**.

This document is a starting point for discussion, not a final blueprint.
Contributions, critiques, and alternative designs are welcome.
