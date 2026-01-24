# cBTC Regtest Setup Guide (MVP v0.1)

This document explains how to set up a local **Bitcoin Core regtest**
environment to experiment with the **cBTC Protocol – MVP v0.1**.

⚠️ **WARNING**  
This setup is for **Bitcoin regtest only**.  
Do **NOT** use mainnet, testnet, or real funds.

---

## 1. Install Bitcoin Core

Download Bitcoin Core from the official website:

https://bitcoincore.org/

Install it normally (GUI version is recommended for beginners).

---

## 2. Configure Bitcoin Core for regtest

### 2.1 Locate `bitcoin.conf`

On **Windows**, navigate to:

C:\Users<YOUR_USERNAME>\AppData\Roaming\Bitcoin


If the `Bitcoin` folder does not exist, create it manually.

Inside this folder, create a new file called:

bitcoin.conf


---

### 2.2 Minimal `bitcoin.conf` content

Open `bitcoin.conf` in a text editor and paste **exactly** the following:

```ini
regtest=1
server=1
txindex=1
fallbackfee=0.0001

rpcuser=cbtc
rpcpassword=cbtcpassword
rpcport=18443
Save the file.

3. Start Bitcoin Core in regtest mode
Start Bitcoin Core (GUI).

Once it opens, go to:

Help → Debug window → Console
Verify that you are running in regtest mode:

getblockchaininfo
You should see:

"chain": "regtest"
If not, stop and check your bitcoin.conf.

4. Create required wallets
Bitcoin Core no longer creates a default wallet automatically.

In the Console, create the following wallets:

createwallet "FUNDING"
createwallet "CP1"
createwallet "REDEMPTION_POOL"
createwallet "YIELD_POOL"

Note:
Additional CP wallets (e.g. CP2, CP3…) can be created at any time using:
createwallet "CP2"
createwallet "CP3"
Each CP wallet can independently open Minting Channels.

Verify that they exist:

listwallets
You should see all four wallet names.

5. Mine Bitcoin (regtest)
5.1 Get a mining address
Load the FUNDING wallet and generate a mining address:

loadwallet "FUNDING"
getnewaddress "MINER" "bech32"
Copy the returned address.

5.2 Mine blocks to generate BTC
Mine 110 blocks to that address:

generatetoaddress 110 <MINER_ADDRESS>
This matures the coinbase rewards (100-block maturity rule).

Verify that BTC is available:
getbalance
You should now see a positive balance in the FUNDING wallet.

6. Fund the CP1 wallet
6.1 Get a CP1 funding address
loadwallet "CP1"
getnewaddress "CP1_FUNDS" "bech32"
Copy the returned address.

6.2 Send BTC from FUNDING to CP1
Switch back to the FUNDING wallet and send BTC:
loadwallet "FUNDING"
sendtoaddress <CP1_FUNDS_ADDRESS> 1.31
(You can choose any amount ≥ 0.05 BTC; 1.31 is used in examples.)

6.3 Confirm the transaction
Mine one block to confirm:

getnewaddress "MINER" "bech32"
generatetoaddress 1 <MINER_ADDRESS>
Verify CP1 balance:

loadwallet "CP1"
getbalance

7. Result
You now have:
A local Bitcoin Core node running in regtest

Four wallets:
FUNDING
CP1
REDEMPTION_POOL
YIELD_POOL

Matured BTC available for testing

CP1 funded and ready to open Minting Channels

8. Next Steps (MVP v0.1)
From the repository root:

python src/coordinator/open_mint_channel.py 0.5
python src/coordinator/status.py
python src/coordinator/redeem_cbtc.py

Minting Channels may be opened from any CP wallet:
python src/coordinator/open_mint_channel.py 0.5 CP2
python src/coordinator/open_mint_channel.py 0.8 CP3

These scripts allow you to:
open Minting Channels,
observe global protocol coverage,
redeem cBTC safely while preserving solvency invariants.


For protocol rules and guarantees, see:
docs/protocol-overview.md
docs/protocol-invariants.md