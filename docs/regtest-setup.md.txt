# cBTC Regtest Setup Guide

This document explains how to set up a local Bitcoin Core **regtest**
environment to experiment with the cBTC protocol.

⚠️ WARNING  
This setup is for **regtest only**.  
Do NOT use on mainnet or with real funds.

---

## 1. Install Bitcoin Core

Download Bitcoin Core from:
https://bitcoincore.org/

Install it normally.

---

## 2. Configure Bitcoin Core for regtest

### 2.1 Locate `bitcoin.conf`

On Windows, go to:

C:\Users<YOUR_USERNAME>\AppData\Roaming\Bitcoin

sql
Copy code

If the folder does not exist, create it manually.

Inside that folder, create a file called:

bitcoin.conf

yaml
Copy code

---

### 2.2 Minimal `bitcoin.conf` content

Paste the following:

```ini
regtest=1
server=1
txindex=1
fallbackfee=0.0001

rpcuser=cbtc
rpcpassword=cbtcpassword
rpcport=18443

Save the file.

3. Start Bitcoin Core

Start Bitcoin Core (GUI).

Verify regtest mode:

Help → Debug window → Console

Run:

getblockchaininfo


You should see:

"chain": "regtest"

4. Create wallets

Bitcoin Core does not create a default wallet automatically.

In the console, create the following wallets:

createwallet "FUNDING"
createwallet "CP1"
createwallet "REDEMPTION_POOL"
createwallet "YIELD_POOL"


Verify:

listwallets

5. Mine Bitcoin (regtest)
5.1 Get a mining address
loadwallet "FUNDING"
getnewaddress "MINER" "bech32"


Copy the address.

5.2 Mine blocks
generatetoaddress 110 <MINER_ADDRESS>


This matures the coinbase rewards.

Verify balance:

getbalance

6. Fund CP1
6.1 Get CP1 address
loadwallet "CP1"
getnewaddress "CP1_FUNDS" "bech32"

6.2 Send BTC from FUNDING to CP1
loadwallet "FUNDING"
sendtoaddress <CP1_FUNDS_ADDRESS> 1.31


Mine one block to confirm:

getnewaddress "MINER" "bech32"
generatetoaddress 1 <MINER_ADDRESS>


Verify CP1 balance:

loadwallet "CP1"
getbalance

7. Result

You now have:

A regtest Bitcoin Core node

Four wallets:

FUNDING

CP1

REDEMPTION_POOL

YIELD_POOL

Matured BTC for testing

CP1 funded and ready to open a Minting Channel

See:
docs/regtest-walkthrough-minting-channel-1.md
for the full protocol simulation.