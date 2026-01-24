# cBTC Protocol – Overview

cBTC is a Bitcoin-native working capital protocol built around **deterministic credit creation** rather than price pegs or liquidations.

The protocol issues cBTC through **Minting Channels**, where BTC is locked and split under predefined rules.

---

## Core Parameters (MVP v0.1)

### Minting
- Deposit range: **0.05 – 5 BTC**
- Issuance rate: **30,000 cBTC per BTC deposited**

### Collateral Split
Each deposit `D` is split as follows:

- **70% Principal**
  - Conceptually time-locked
- **20% Redemption Pool**
  - Global, shared across all cBTC
- **10% Yield Pool**
  - Prefunded yield, isolated per channel

---

## Redemption Model

- All cBTC is redeemable against a **global Redemption Pool**
- Floor redemption rate:
  - `1 cBTC = 0.00001 BTC`
- Actual redemption rate depends on coverage

Redemptions:
- Burn cBTC (off-chain ledger)
- Pay BTC from the Redemption Pool (on-chain)
- Never touch principal or yield

---

## Solvency & Coverage

Definitions:

- **Outstanding cBTC** = minted − redeemed
- **Floor liability** = outstanding cBTC × 0.00001 BTC
- **Coverage** = Redemption Pool BTC ÷ floor liability

Coverage tiers:

- ≥ 70% → Full floor redemptions
- 50–70% → Haircut zone
- < 50% → Redemptions throttled / proportional

The MVP enforces **post-redemption coverage ≥ 50%**.

---

## MVP Scope

This implementation:
- runs entirely on Bitcoin regtest
- uses an auditable off-chain ledger
- prioritizes correctness over optimization

It is designed as a **research and validation tool**, not a production system.
