# Open Mint Channel – Protocol Specification (cBTC)

**Version:** v0.1  
**Status:** Experimental  
**Scope:** Bitcoin regtest MVP → future testnet/mainnet implementations

This document specifies the **Open Mint Channel** operation in the cBTC protocol.

A Mint Channel is the only mechanism by which new cBTC is issued.

---

## 1. Purpose

The `open_mint_channel` operation allows a Collateral Provider (CP) to:

- lock BTC under deterministic rules,
- contribute BTC to a global Redemption Pool,
- prefund protocol-defined yield,
- and receive newly issued cBTC at a fixed loan-to-value ratio.

This operation is **permissionless**, **non-custodial**, and **Bitcoin-native**.

---

## 2. Units and Precision

### 2.1 cBTC Denomination

- **Display unit:** `cBTC`
- **Precision:** 3 decimal places
- **Smallest unit:** `0.001 cBTC`

Internally, implementations SHOULD represent cBTC amounts using an integer
base unit:

1 cBTC = 1,000 milli-cBTC (mC)

This mirrors Bitcoin’s BTC / satoshi model and avoids floating-point errors.

---

## 3. Function Signature (Conceptual)

```text
open_mint_channel(
    cp_id:            string,
    deposit_btc:      decimal,   # BTC
    min_confirmations: integer = 0
) -> MintResult
Return Object (MintResult)

{
    txid:             string,
    minted_cbtc:      decimal,   # 3 decimal places
    minted_mC:        integer,   # base units
    principal_btc:    decimal,
    redemption_btc:   decimal,
    yield_btc:        decimal,
    coverage_after:   decimal
}

4. Protocol Constants (v0.1)
Parameter	Value
Minimum deposit	0.05 BTC
Maximum deposit	5.0 BTC
Issuance rate	30,000 cBTC / BTC
Loan-to-value	30%
Principal share	70%
Redemption Pool share	20%
Yield share	10%

5. Preconditions
Before opening a Mint Channel, the following MUST be true:

deposit_btc satisfies:

0.05 BTC ≤ deposit_btc ≤ 5.0 BTC
The CP controls a Bitcoin wallet with:

confirmed_balance ≥ deposit_btc
The protocol is not in a restricted issuance state
(as defined by off-chain protocol logic).

The Bitcoin network in use is supported
(regtest for MVP v0.1).

6. Deterministic Allocation
Given a deposit D (in BTC):

principal_btc   = 0.70 × D
redemption_btc  = 0.20 × D
yield_btc       = 0.10 × D

New cBTC issuance:

minted_cbtc = 30,000 × D
minted_mC   = minted_cbtc × 1,000
All calculations MUST be deterministic and reproducible.

7. On-Chain Transaction Structure (v0.1)
The Mint Channel is opened via a single Bitcoin transaction.

Inputs
One or more UTXOs controlled by the CP.

Outputs
Principal Output
- Amount: principal_btc
- Ownership: CP wallet
- Script: standard P2WPKH / P2TR (timelock enforced at protocol level in v0.1)

Redemption Pool Output
- Amount: redemption_btc
- Ownership: Redemption Pool wallet
- Script: standard P2WPKH / P2TR
- Funds are globally shared across all CPs

Yield Output
- Amount: yield_btc
- Ownership: CP wallet
- Script: standard P2WPKH / P2TR
- Yield vesting enforced by protocol logic in v0.1
Transaction fees are paid by the CP.

8. Ledger Event (Off-Chain Accounting)
After successful broadcast, the operation MUST append a mint event
to the protocol ledger:

{
  "type": "mint",
  "timestamp": "ISO-8601 UTC",
  "cp_id": "CP1",
  "deposit_btc": "1.00000000",
  "principal_btc": "0.70000000",
  "redemption_btc": "0.20000000",
  "yield_btc": "0.10000000",
  "minted_cbtc": "30000.000",
  "minted_mC": 30000000,
  "txid": "<bitcoin-txid>"
}
This ledger represents logical cBTC issuance and is auditable.

9. Coverage Implications
Opening a Mint Channel:
- increases outstanding cBTC,
- increases Redemption Pool BTC proportionally,
- preserves global coverage at approximately:

coverage ≈ 0.20 / 0.30 ≈ 66.67%
Therefore, minting alone cannot violate the 50% solvency rule.

Coverage enforcement is handled during redemption, not issuance.

10. Security & Trust Model
- CP retains custody of principal and yield.
- Redemption Pool custody is separated.
- No custodian holds user funds.
- Bitcoin enforces ownership and settlement.
- Global solvency rules are enforced by protocol logic.

11. Future Extensions (Non-Normative)
Future versions may introduce:
- Script-enforced timelocks for principal and yield
- Multi-sig or federated Redemption Pool custody
- Taproot Assets or Lightning-native representations of cBTC
- On-chain proof commitments for issued supply
- Threshold signing and decentralized coordinators
None of these are required for MVP v0.1 correctness.

12. Summary
The open_mint_channel operation defines a deterministic, conservative, and
Bitcoin-native method for issuing cBTC.

It cleanly separates:
- Bitcoin enforcement (ownership, settlement)
- Protocol logic (issuance rules, solvency)
- Accounting (cBTC mint/burn events)
This separation is intentional and foundational to the cBTC design.