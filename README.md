# cBTC Protocol – Regtest MVP v0.1

cBTC is a **Bitcoin-native working capital protocol** that allows Bitcoin holders to lock BTC under deterministic rules and issue a Bitcoin-backed asset (cBTC), **without fiat pegs, price oracles, or liquidations**.

This repository contains **MVP v0.1**, implemented on **Bitcoin regtest**, focusing on correctness, transparency, and reproducibility.

> ⚠️ Experimental software  
> This project is **not production-ready** and must only be used on Bitcoin regtest or test environments.

---

## What This MVP Demonstrates

This MVP proves that the core cBTC mechanics work:

### ✔ Minting Channels
- Any Collateral Provider (CP) can deposit BTC (`0.05–5 BTC`) using their own wallet
  (e.g. CP1, CP2, CP3…)
- Deposits are split deterministically:
  - **70%** Principal (time-locked conceptually)
  - **20%** Global Redemption Pool
  - **10%** Yield Pool
- cBTC issuance rate:
  - **30,000 cBTC per 1 BTC deposited**
- Minting is logged in an auditable off-chain ledger

### ✔ Global Solvency & Coverage
- A global **Redemption Pool** backs all outstanding cBTC
- Coverage is continuously computed:
  - Floor liability = `outstanding cBTC × 0.00001 BTC`
- Coverage tiers determine redemption behavior
- Baseline healthy coverage is 66.67% (derived from standard minting split)

### ✔ Deterministic Redemptions
- cBTC holders can redeem cBTC for BTC
- Redemption rate is computed to ensure:
  - **Post-redemption coverage ≥ 50%**
- Redemptions:
  - Burn cBTC (off-chain)
  - Pay BTC from the Redemption Pool (on-chain)

### ✔ Fully Reproducible
- Anyone can:
  - Run Bitcoin Core in regtest
  - Create wallets
  - Mint cBTC
  - Redeem cBTC
  - Verify coverage math

---

## What This MVP Does *Not* Include (Yet)

- Lightning integration
- Taproot Assets representation
- On-chain enforcement of mint caps
- Multi-party custody or threshold signing
- Production security assumptions

These are **explicitly out of scope** for MVP v0.1.

---

## Repository Structure

cbtc-protocol/
├── data/
│ └── ledger.json # Off-chain cBTC ledger (mint / redeem events)
├── docs/
│ ├── protocol-overview.md # High-level protocol explanation
│ ├── protocol-invariants.md # Rules that must always hold
│ └── regtest-setup.md # How to reproduce the MVP
├── src/
│ └── coordinator/
│ ├── open_mint_channel.py
│ ├── redeem_cbtc.py
│ ├── status.py
│ └── calc_redemption_rate.py
└── README.md

---

## Getting Started

See [`docs/regtest-setup.md`](docs/regtest-setup.md) for a complete, step-by-step guide to:

- install Bitcoin Core
- configure regtest
- create wallets
- mine funds
- run the cBTC scripts

---

## Status

**MVP v0.1 – Functional & Auditable (Regtest)**

Next milestones:
- clean reset scenario
- Lightning / Taproot Assets design
- multi-CP stress simulations
- economic stress testing

---

## License

MIT License.