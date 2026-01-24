# cBTC Protocol – Overview

cBTC is a Bitcoin-native working capital protocol. It allows Bitcoin holders
to issue a circulating Bitcoin-denominated asset (cBTC) by locking BTC under
deterministic, conservative rules.

The protocol avoids fiat pegs, price oracles, liquidations, and custodial risk,
and relies on Bitcoin itself as the enforcement layer.

---

## Core parameters

cBTC is issued through **Minting Channels** with fixed rules:

- Maximum loan-to-value (LTV): **30%**
- Collateral split per Minting Channel:
  - **70% Principal** – retained by the depositor and intended to be time-locked
  - **20% Redemption Pool** – global reserve for cBTC redemptions
  - **10% Prefunded Yield** – isolated, time-based yield

Minted cBTC amount:

- `Minted cBTC = 30,000 × deposited BTC`

This corresponds to a redemption floor of:

- `1 cBTC = 0.00001 BTC`

Per 1 BTC of deposit:

- Maximum redemption liability at floor: **0.30 BTC**
- Initial Redemption Pool contribution: **0.20 BTC**
- Prefunded Yield: **0.10 BTC**

So each new channel starts with an **initial coverage** of:

- `Coverage = 0.20 / 0.30 ≈ 66.67%`

If yield is fully forfeited, total potential contribution to the Redemption Pool
per channel is 0.30 BTC, i.e. up to **100% coverage** for that channel’s cBTC.

---

## Redemption

- cBTC is redeemable exclusively for BTC.
- Redemptions are paid **only** from the global Redemption Pool.
- Redemption is always available, subject to deterministic rules.
- cBTC is burned upon redemption.
- Principal and yield collateral are never used for redemption.

Redemption rates depend on global coverage:

- Let:
  - `O` = outstanding cBTC (before redemption)
  - `P` = BTC in Redemption Pool (before redemption)
  - `f` = full redemption floor = 0.00001 BTC per cBTC
  - `q` = cBTC redeemed in this transaction

After a redemption at rate `r` (BTC per cBTC):

- `P' = P − r·q`
- `O' = O − q`
- `L' = f · O'` (full-floor liability after redemption)

To enforce **minimum 50% coverage**, the protocol restricts `r` so that:

- `Coverage_after = P' / L' ≥ 0.5`

The resulting safe redemption rate is:

- `r_safe(q) = (P − 0.5 · f · (O − q)) / q`

and the protocol sets:

- `r(q) = min(f, r_safe(q))`

This means:

- When the system is well-capitalized, `r(q) = f` and users receive
  **1 cBTC = 0.00001 BTC**.
- When coverage is tighter, the rate is reduced just enough to keep
  **post-redemption coverage ≥ 50%**.

---

## Yield

- Yield is **prefunded** at channel creation (10% of the deposit).
- Yield is isolated per Minting Channel.
- Yield distribution is **non-linear** and **time-based**.
- Yield cannot be rehypothecated or lent.
- If a channel is closed early:
  - unvested yield is forfeited,
  - forfeited yield strengthens the Redemption Pool,
  - principal is never touched.

This mechanism aligns incentives toward longer commitments while keeping the
system conservative.

---

## Risk and solvency model

The protocol manages risk through:

- conservative issuance (30% LTV),
- prefunded reserves (20% Redemption Pool, 10% Yield),
- explicit time commitments,
- global solvency thresholds.

Global coverage is defined as:

- `Coverage = P / (O · f)`

where:
- `P` = BTC in Redemption Pool,
- `O` = outstanding cBTC,
- `f` = 0.00001 BTC per cBTC.

Rules:

- New minting is allowed only if **Coverage ≥ 50%**.
- Redemptions are priced so that **Coverage_after ≥ 50%**.
- In extreme scenarios (`Coverage < 50%`), new minting halts and only
  conservative (e.g. pro-rata) redemptions may be allowed.

There are:
- no liquidations,
- no margin calls,
- no discretionary interventions.

---

## Scope of this repository

This repository focuses on a **regtest MVP** implementation used to:

- demonstrate core protocol invariants,
- simulate Minting Channel lifecycles,
- validate redemption and solvency behavior,
- invite review and experimentation.

Advanced integrations (Lightning, Taproot Assets, decentralization)
are future research areas and are **not** part of the current MVP.
