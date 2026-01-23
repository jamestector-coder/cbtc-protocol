# cBTC Protocol – Regtest MVP

cBTC is a Bitcoin-native working capital protocol that allows Bitcoin holders to lock BTC under deterministic rules and issue a Bitcoin-backed asset (cBTC) without fiat pegs, price oracles, or liquidations.

This repository contains:

- A **regtest-based MVP** to simulate Minting Channels, redemption, and yield.
- Coordinator scripts to interact with **Bitcoin Core**.
- Documentation and examples so others can reproduce and extend the setup.

> ⚠️ This is experimental software and **not** production-ready.  
> Use only on Bitcoin regtest or test networks.

---

## Project Structure

- `docs/` – Documentation
  - `protocol-overview.md` – High-level summary of the protocol
  - `regtest-setup.md` – How to run Bitcoin Core in regtest and use the scripts
  - `whitepaper/` – Whitepaper PDFs or markdown

- `src/` – Source code
  - `coordinator/` – Coordinator logic (open/close Minting Channels, redemptions)

- `scripts/` – Helper scripts and examples
  - `regtest/` – Commands and scripts to bootstrap a local regtest environment

---

## Goals

1. Provide a **minimal working prototype** of cBTC on Bitcoin regtest.
2. Make it easy for others to **clone, run, and experiment** with the protocol.
3. Serve as a foundation for more advanced implementations (Lightning, Taproot Assets, etc).

---

## Getting Started (Regtest)

1. Install **Bitcoin Core** (v24+ recommended).
2. Enable `regtest` and `server` mode in `bitcoin.conf`.
3. Start `bitcoind` in regtest.
4. Run the coordinator scripts from `src/coordinator/` to:
   - fund a CP wallet;
   - open a Minting Channel;
   - track cBTC issuance and Redemption Pool state.

Detailed steps are in [`docs/regtest-setup.md`](docs/regtest-setup.md) (to be written).

---

## Contributing

Contributions, reviews, and experiments are welcome.

- Open issues to:
  - ask questions,
  - propose changes,
  - suggest alternative designs.
- Submit pull requests for:
  - code improvements,
  - documentation,
  - test scenarios.

See [`CONTRIBUTING.md`](CONTRIBUTING.md) (to be created) for contribution guidelines.

---

## License

This project is licensed under the MIT License. See [`LICENSE`](LICENSE) for details.
# cbtc-protocol
Bitcoin-native working capital protocol - cBTC regtest MVP and tools
