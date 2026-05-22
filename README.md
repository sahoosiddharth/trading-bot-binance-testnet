# Binance Futures Testnet — Trading Bot

A clean, well-structured Python CLI application that places orders on the **Binance USDT-M Futures Testnet**.

> **GitHub repo:** https://github.com/sahoosiddharth/trading-bot-binance-testnet
---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py        # package init + public exports
│   ├── client.py          # Binance REST client (signing, HTTP, error handling)
│   ├── orders.py          # order placement logic + rich terminal output
│   ├── validators.py      # input validation
│   └── logging_config.py  # logging setup (file + console)
├── cli.py                 # CLI entry point (argparse)
├── logs/                  # sample log files (runtime logs gitignored)
├── .env.example           # template for credentials
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Get Testnet API Credentials

1. Go to https://testnet.binancefuture.com
2. Log in with your GitHub account
3. Click **"API Key"** → copy your API Key and Secret Key
4. Click the **faucet button** to fund your testnet wallet

> ⚠️ Testnet credentials are separate from your real Binance account.

### 2. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/trading-bot
cd trading-bot
```

### 3. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Set API credentials

```bash
cp .env.example .env
# open .env and paste your keys
```

`.env` format:
```
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here
```

---

## How to Run

### Test connectivity
```bash
python cli.py --ping
```

### Check account balance
```bash
python cli.py --account
```

### Market BUY order
```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

### Limit SELL order
```bash
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 70000
```

### Stop-Market order (bonus)
```bash
python cli.py --symbol BTCUSDT --side BUY --type STOP_MARKET --quantity 0.001 --stop-price 60000
```

### All options
```bash
python cli.py --help
```

---

## Logging

Every run appends to `logs/trading_bot_YYYYMMDD.log`.

| Level | Where |
|-------|-------|
| DEBUG | File only (full params, HTTP status) |
| INFO  | Console + file (order summary, response) |
| ERROR | Console + file (validation errors, API errors) |

Sample logs included:
- `logs/market_order_sample.log`
- `logs/limit_order_sample.log`

---

## Bonus Feature — STOP_MARKET Orders

A third order type is supported as the bonus requirement:

```bash
python cli.py --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.001 --stop-price 58000
```

Triggers a market sell when price drops to 58,000.

---

## Assumptions

- Testnet account must be funded via the dashboard faucet before placing orders
- Default `timeInForce` for LIMIT orders is `GTC` (Good Till Cancelled)
- Bot uses **one-way position mode** (testnet default) — hedge mode not supported
- Quantity precision depends on symbol (BTCUSDT allows up to 3 decimal places)

---

## Requirements

- Python 3.10+
- `requests` — HTTP calls to Binance REST API
- `python-dotenv` — loads `.env` credentials
- `rich` — beautiful terminal output (tables, colors)
