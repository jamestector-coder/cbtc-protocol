# Redemption – Protocol Specification (cBTC)

**Version:** v0.1  
**Status:** Experimental  
**Scope:** Bitcoin regtest MVP → future testnet/mainnet implementations

This document specifies the **Redemption** mechanism of the cBTC protocol.

Redemption is the **only way** cBTC converts back into BTC.

---

## 1. Purpose

The redemption mechanism allows a cBTC holder to:

- exchange cBTC for BTC,
- burn cBTC permanently,
- receive BTC from the global Redemption Pool,
- while **never** touching principal or yield collateral.

Redemption is deterministic, conservative, and designed to preserve global solvency.

---

## 2. Units and Precision

### 2.1 cBTC Units

- **Display unit:** cBTC
- **Precision:** 3 decimal places
- **Smallest unit:** `0.001 cBTC`

Internal accounting SHOULD use integer base units:

1 cBTC = 1,000 milli-cBTC (mC)


### 2.2 BTC Units

- BTC amounts are expressed in BTC
- Bitcoin Core internally uses satoshis

---

## 3. Definitions

| Term | Definition |
|----|-----------|
| Outstanding cBTC | Minted cBTC minus redeemed (burned) cBTC |
| Redemption Pool | BTC reserve used exclusively for redemptions |
| Floor redemption rate | `0.00001 BTC per 1 cBTC` |
| Floor liability | `outstanding cBTC × floor redemption rate` |
| Coverage ratio | `Redemption Pool BTC ÷ floor liability` |

---

## 4. Global Solvency Invariant

The protocol enforces the following invariant:

Post-redemption coverage ≥ 50%

At no point may a redemption reduce the Redemption Pool below **50% of floor liability**.

This invariant has absolute priority over user redemption requests.

---

## 5. Redemption Preconditions

Before a redemption is executed:

1. The requested amount `R` satisfies:

0 < R ≤ outstanding cBTC

2. The Redemption Pool has sufficient BTC to satisfy the request
**under the coverage invariant**.

3. The redemption amount is expressed with **≤ 3 decimal places**.

4. The requester provides a valid Bitcoin address.

---

## 6. Redemption Coverage Tiers (v0.1)

Redemption behavior depends on **coverage before redemption**.

### Tier 1 – Full Floor Zone
Coverage ≥ 60%


- Redemption rate:
1 cBTC = 0.00001 BTC

- No haircut
- Redemptions are processed normally

---

### Tier 2 – Haircut Zone
50% ≤ Coverage < 60%

- Redemption rate is **dynamically reduced**
- Computed so that:

coverage_after = 50%


This ensures solvency is preserved while allowing partial exits.

---

### Tier 3 – Insolvency Protection Zone
Coverage < 50%

- Redemptions are either:
  - halted, or
  - executed strictly pro-rata to remaining BTC

Exact behavior is implementation-defined, but MUST NOT violate the solvency invariant.

---

## 7. Redemption Rate Calculation (Deterministic)

Given:

- `O` = outstanding cBTC
- `P` = Redemption Pool BTC
- `R` = requested redemption cBTC
- `F` = floor redemption rate (`0.00001 BTC`)

### Step 1: Floor Liability
floor_liability = O × F

### Step 2: Coverage Before
coverage_before = P ÷ floor_liability

### Step 3: Redemption Rate

- If `coverage_before ≥ 0.60`:
redemption_rate = F


- Else:
max_payout = P - (0.5 × floor_liability_after)
redemption_rate = max_payout ÷ R

Where:
floor_liability_after = (O - R) × F

This guarantees:
coverage_after = 50%

---

## 8. On-Chain Execution

Redemption uses **one Bitcoin transaction**.

### Inputs
- UTXOs from the Redemption Pool wallet

### Outputs
- BTC payment to the redeemer’s Bitcoin address

Transaction fees are paid by the Redemption Pool.

---

## 9. cBTC Burn (Off-Chain Accounting)

Upon successful redemption:

- The redeemed cBTC is **burned**
- Burn is recorded in the ledger
- Burned cBTC can never re-enter circulation

Example ledger event:

```json
{
  "type": "redeem",
  "timestamp": "ISO-8601 UTC",
  "burned_cbtc": "500.000",
  "burned_mC": 500000,
  "btc_paid": "0.00500000",
  "redemption_rate": "0.00001",
  "txid": "<bitcoin-txid>"
}
10. What Redemption Does NOT Do
Redemption never:
- touches principal collateral
- touches yield collateral
- liquidates positions
- uses price oracles
- requires trust in a custodian
Redemption is strictly reserve-based.

11. Attack Surface Considerations
Bank Run Risk
Addressed via:
- global Redemption Pool
- dynamic haircuts
- 50% post-redemption floor

Front-Running
Mitigated by:
- deterministic rate calculation
- transparent pool balances

Griefing
- Large redemptions cannot drain the pool
- Coverage floor always enforced

12. Future Extensions (Non-Normative)
Future versions may include:
- FIFO or queue-based redemption ordering
- Time-based redemption throttling
- Multi-sig or threshold-controlled Redemption Pool
- On-chain commitments to outstanding supply
None are required for MVP v0.1 correctness.

13. Summary
The redemption mechanism ensures:
- cBTC is always redeemable for BTC,
- redemptions never endanger solvency,
- principal and yield remain untouched,
- no liquidations or discretionary intervention are required.
This makes redemption the core stabilizing mechanism of the cBTC protocol.