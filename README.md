# cBTC Protocol – Regtest MVP

cBTC is a Bitcoin-native working capital protocol that allows Bitcoin holders
to lock BTC under deterministic rules and issue a Bitcoin-backed asset (cBTC)
without fiat pegs, price oracles, or liquidations.

This repository contains:

- A **regtest-based MVP** to simulate Minting Channels, redemption, and yield.
- Early coordinator logic and experiments interacting with **Bitcoin Core**.
- Documentation and walkthroughs so others can reproduce and review the protocol behavior.

> ⚠️ This is experimental software and **not** production-ready.  
> Use only on Bitcoin regtest or test networks.

---

## Project Structure

- `docs/` – Documentation
  - `protocol-overview.md` – High-level summary of the protocol
  - `regtest-setup.md` – How to run Bitcoin Core in regtest
  - `regtest-walkthrough-minting-channel-1.md` – Full lifecycle walkthrough
  - `whitepaper/` – Whitepaper PDFs or markdown

- `src/` – Source code
  - `coordinator/` – Planned coordinator logic (Minting Channels, redemptions)

- `scripts/` – Helper scripts and examples
  - `regtest/` – Commands and notes to bootstrap a local regtest environment

---

## Goals

1. Provide a **minimal working prototype** of cBTC on Bitcoin regtest.
2. Make it easy for others to **clone, run, and verify** the protocol behavior.
3. Serve as a foundation for more advanced implementations
   (e.g. Lightning, Taproot Assets).

---

## Current Status

- ✔️ Core protocol invariants verified manually on Bitcoin regtest
- ✔️ Minting Channel lifecycle demonstrated (open, early close, redemption)
- ✔️ Deterministic BTC splits and redemption behavior validated
- ⏳ Automation scripts in progress
- ⏳ No Lightning or Taproot integration yet

---

## Getting Started (Regtest)

Start here:

1. **Regtest setup**  
   👉 [`docs/regtest-setup.md`](docs/regtest-setup.md)

2. **Minting Channel walkthrough**  
   👉 [`docs/regtest-walkthrough-minting-channel-1.md`](docs/regtest-walkthrough-minting-channel-1.md)

These documents show:
- how wallets are created,
- how BTC is split on-chain (70 / 15 / 15),
- how early closure forfeits yield,
- how redemptions are paid exclusively from the Redemption Pool,
- how solvency is preserved.

---

## Contributing

Contributions, reviews, and critical feedback are welcome.

- Open issues to:
  - ask questions,
  - challenge assumptions,
  - propose alternative designs.
- Submit pull requests for:
  - code,
  - documentation,
  - additional regtest scenarios.

A `CONTRIBUTING.md` file will be added as the project evolves.

---

## License

This project is licensed under the MIT License.  
See [`LICENSE`](LICENSE) for details.
