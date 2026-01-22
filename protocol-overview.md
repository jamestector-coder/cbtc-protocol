# cBTC Protocol – Overview

cBTC is a Bitcoin-native working capital protocol. It issues cBTC through Minting Channels, where Bitcoin is locked under deterministic rules:

- Max loan-to-value: 30%
- Collateral split per Minting Channel:
  - 70% principal (time-locked)
  - 15% Redemption Pool
  - 15% prefunded yield

Redemption:
- Uses a global Redemption Pool.
- Always available.
- Applies deterministic haircuts based on reserve coverage.

Yield:
- Prefunded, non-linear, and time-based.
- Isolated per Minting Channel.
- Forfeited yield strengthens the Redemption Pool.

This repo focuses on a **regtest MVP** implementation for experimentation and review.
