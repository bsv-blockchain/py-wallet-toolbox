# Mainnet Send/Receive Guide

Use this guide when you want to move **real BSV** with the Python wallet-toolbox demo. Every mistake can cost money—slow down and verify each step.

---

## ⚠️ Before You Start

- Real funds are involved. Begin with **0.001 BSV or less**.
- Back up your mnemonic phrase before touching mainnet.
- Never test with money you cannot afford to lose.

---

## 📋 Prep Checklist

1. **Copy `.env` from the example and edit it:**

   ```bash
   cd toolbox/py-wallet-toolbox/examples/brc100_wallet_demo
   cp env.example .env
   nano .env
   ```

   ```
   BSV_NETWORK=main
   BSV_MNEMONIC=word1 word2 ... word12
   ```

2. **Ensure dependencies are installed and the venv is active:**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Protect the mnemonic.** Write it down, store it offline, and test that you can read it later.

---

## 💰 Step 1 – Show Your Mainnet Address

Run `python wallet_demo.py`, initialize the wallet (menu **1**), then pick menu **4** to display:

- Network warning (should say mainnet).
- Receive address (should start with `1`).
- Explorer link (`https://whatsonchain.com/address/...`).

Copy the address exactly.

---

## 💸 Step 2 – Fund the Wallet

Send a tiny amount of BSV to the copied address via one of the following:

- **Exchange withdrawal** (Binance, OKX, etc.).
- **Another wallet** you own.
- **Peer-to-peer** transfer from a friend.

Always double-check the address before confirming.

---

## 🔍 Step 3 – Confirm Arrival

1. Open `https://whatsonchain.com/address/<your address>` and monitor the transaction.
2. Wait for at least **one confirmation** (≈10 minutes).
3. Re-run menu **4** in the demo to view the updated balance when the confirmation lands.

---

## 🚀 Step 4 – Internalize Received Transactions (Optional)

If you receive BSV from an external wallet or faucet and want the toolbox to track that UTXO:

1. Locate the TXID on <https://whatsonchain.com/>.
2. Choose menu **25. Internalize external transaction -> internalizeAction** inside the demo.
3. Paste Atomic BEEF hex (if you already built it) **or** press Enter so the demo downloads the necessary data via Wallet Services.
4. Specify the output indexes that belong to you and keep the default basket unless you have a custom one.
5. Finish the prompts—the wallet will run `internalize_action`, sync the outputs, and they will appear under menu **17. List outputs**.

This feature is ideal for faucet funding, settlement transactions, or any externally constructed payment that should become part of the wallet’s tracked state.

---

## 📤 Outbound Transfers

Spending from mainnet still requires a scripted flow that mirrors the TypeScript reference (`create_action` → `sign_action` → `internalize_action`). Until the interactive menu grows to cover it, either:

1. Export the mnemonic into a production wallet for day-to-day payments, or
2. Write a small driver script that reuses the toolbox APIs exactly like the TS SDK.

---

## ❓ FAQ

- **Nothing shows up on the explorer.**  
  Confirm the withdrawal succeeded, ensure the address is correct, and wait longer.
- **Mnemonic lost.**  
  Funds are unrecoverable. Always have multiple offline backups.
- **Switch back to testnet.**  
  Edit `.env` and set `BSV_NETWORK=test`, then restart the demo.

---

## 🔒 Security Best Practices

1. **Safeguard the mnemonic:** paper backup, safe storage, redundant copies.
2. **Never:** screenshot the phrase, sync it to cloud storage, or share it with anyone.
3. **Do:** keep separate wallets for testing vs. production, rehearse with small amounts, and periodically verify backups.

---

## 📚 Helpful Links

- Mainnet explorer: <https://whatsonchain.com/>
- BSV info: <https://bitcoinsv.com/>
- Wallet toolbox README: `../../README.md`

---

## 🆘 Support

Open an issue at <https://github.com/bitcoin-sv/py-wallet-toolbox/issues> if you get stuck.

---

**Disclaimer:** This guide is educational. You are solely responsible for your funds and compliance with local laws.

