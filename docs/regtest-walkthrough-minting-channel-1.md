# Regtest Walkthrough – Minting Channel #1

This document reproduces the **first full cBTC Minting Channel lifecycle**
on Bitcoin Core regtest.

All steps were executed manually using Bitcoin Core RPC.
No custom code was used.

---

## 1. Initial conditions

Wallets used:

- FUNDING (miner / funding wallet)
- CP1 (Collateral Provider)
- REDEMPTION_POOL
- YIELD_POOL

Initial balances:

- CP1: 1.30000000 BTC
- FUNDING: mined regtest coins
- REDEMPTION_POOL: 0 BTC
- YIELD_POOL: 0 BTC

---

## 2. Protocol parameters

Minting Channel parameters:

- Deposit (D): 1.30000000 BTC
- Loan-to-Value (LTV): 30%
- Minted cBTC: 30,000 × D = 39,000 cBTC

BTC allocation:

- Principal (70%): 0.91000000 BTC
- Redemption Pool (15%): 0.19500000 BTC
- Yield Pool (15%): 0.19500000 BTC

Redemption floor:

- 1 cBTC = 0.00001 BTC
- Maximum redemption liability: 0.39000000 BTC

---

## 3. Opening the Minting Channel

A single on-chain transaction was created from the CP1 wallet
with three outputs:

- 0.91000000 BTC → CP1_PRINCIPAL address
- 0.19500000 BTC → REDEMPTION_POOL
- 0.19500000 BTC → YIELD_POOL

The transaction was mined and confirmed.

### Post-mint balances

- CP1:
  - Principal UTXO: 0.91000000 BTC
  - Small change output for fees
- REDEMPTION_POOL: 0.19500000 BTC
- YIELD_POOL: 0.19500000 BTC

Minted off-chain supply:

- CP1 credited with 39,000 cBTC
- Total outstanding cBTC supply: 39,000

Initial redemption coverage:

- Redemption Pool: 0.19500000 BTC
- Liability: 0.39000000 BTC
- Coverage ratio: 50%

---

## 4. Early Minting Channel closure

The Minting Channel was closed **before the minimum duration**.

According to protocol rules:

- Principal remains with CP1
- All unvested yield is forfeited
- Yield is transferred to the Redemption Pool

### Yield forfeiture

The entire YIELD_POOL balance was sent to the REDEMPTION_POOL
in a single transaction.

Transaction fee was subtracted from the yield amount.

### Post-forfeiture balances

- YIELD_POOL: 0.00000000 BTC
- REDEMPTION_POOL: 0.38998900 BTC (slightly below 0.39 BTC due to fees)

Updated coverage:

- Outstanding cBTC: 39,000
- Max liability: 0.39000000 BTC
- Coverage ratio: ≈ 99.997%

This places the system in **full redemption tier**.

---

## 5. Redemption simulation

A redemption of **10,000 cBTC** was simulated.

Redemption calculation:

- 10,000 × 0.00001 BTC = 0.10000000 BTC

### On-chain action

- 0.10 BTC (minus fee) was sent from REDEMPTION_POOL
  to a CP1 redemption address.

### Post-redemption balances

- CP1 BTC balance increased by ~0.10 BTC
- REDEMPTION_POOL balance decreased accordingly

Off-chain accounting:

- cBTC burned: 10,000
- Remaining cBTC balance (CP1): 29,000
- Total outstanding cBTC: 29,000

Updated liability:

- 29,000 × 0.00001 = 0.29000000 BTC

Redemption Pool remained sufficiently funded.

---

## 6. Invariants demonstrated

This walkthrough confirms the following protocol invariants:

1. Minted cBTC = 30,000 × deposit (D)
2. BTC split (70/15/15) is enforced on-chain
3. Principal is never touched during redemption
4. Yield is forfeited on early channel closure
5. Redemptions are paid exclusively from the Redemption Pool
6. cBTC supply contracts through redemption and burn
7. No liquidations or price oracles are required

---

## 7. Status

- Minting Channel #1: CLOSED (early)
- Protocol behavior: VERIFIED on regtest
- Implementation: Manual (code automation pending)
