# Multiple Collateral Providers (CPs)

The cBTC protocol is designed to support multiple independent Collateral
Providers.

Each CP:
- controls their own Bitcoin wallet,
- opens Minting Channels independently,
- retains custody of their principal and yield.

All CPs:
- contribute to a single global Redemption Pool,
- share the same solvency constraints,
- cannot individually drain or weaken protocol reserves.

This model mirrors real-world credit markets while preserving Bitcoin-native
self-custody and deterministic risk limits.
