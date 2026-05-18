# Binance Futures Testnet Trading Bot

A production-quality Python CLI application for placing **MARKET** and **LIMIT** futures orders on the **Binance Futures Testnet** (USDT-M Perpetual).

---

## Features

- **MARKET** and **LIMIT** order support
- **BUY** and **SELL** sides
- Full input validation with descriptive error messages
- HMAC-SHA256 request signing
- Rotating file-based logging (all requests, responses, and errors)
- Coloured CLI output with formatted order summaries
- Clean modular architecture
- `.env`-based credential management

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py          # Package metadata
│   ├── client.py            # Binance API wrapper (signing, HTTP, error handling)
│   ├── orders.py            # Order construction and dispatch logic
│   ├── validators.py        # Input validation (symbol, side, type, qty, price)
│   ├── logging_config.py    # Rotating logger setup (file + console)
│   └── cli.py               # Click CLI entry point
├── logs/
│   ├── trading_bot.log      # Full debug log (auto-created)
│   └── errors.log           # Warning/error log (auto-created)
├── .env                     # API credentials (never commit this!)
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Prerequisites

- Python **3.8** or higher
- pip

---

## Setup Instructions

### Step 1 — Get Testnet API Keys

1. Visit [https://testnet.binancefuture.com](https://testnet.binancefuture.com)
2. Log in (GitHub OAuth or email)
3. Go to **Account → API Management**
4. Create a new API key pair
5. Copy your **API Key** and **Secret Key**

### Step 2 — Clone / Download the Project

```bash
# If using git
git clone <repo-url> trading_bot
cd trading_bot

# Or just navigate to the project folder
cd trading_bot
```

### Step 3 — Create a Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate

# On Windows (Command Prompt):
venv\Scripts\activate.bat

# On Windows (PowerShell):
venv\Scripts\Activate.ps1
```

### Step 4 — Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 5 — Configure API Credentials

Edit the `.env` file in the project root:

```env
BINANCE_API_KEY=your_testnet_api_key_here
BINANCE_SECRET_KEY=your_testnet_secret_key_here
```

> ⚠️ Never commit your `.env` file. It is already listed in `.gitignore`.

---

## Running the Bot

All commands are run from the **project root** (`trading_bot/` directory).

### Check Connectivity — Server Time

```bash
python -m bot.cli server-time
```

**Output:**
```
✅  Server Time: 1718123456789 (ms since epoch)
```

---

### Check Account Information

```bash
python -m bot.cli account-info
```

**Output:**
```
╔══════════════════════════════════════╗
║       ACCOUNT INFORMATION            ║
╠══════════════════════════════════════╣
║  Total Balance   : 10000.00000000    ║
║  Available Bal.  : 9998.50000000     ║
║  Unrealised PnL  : 0.00000000        ║
║  Total Margin    : 1.50000000        ║
║  Can Trade       : True              ║
╚══════════════════════════════════════╝
```

---

### Place a MARKET Order

```bash
# BUY MARKET order
python -m bot.cli place-order \
  --symbol BTCUSDT \
  --side BUY \
  --order-type MARKET \
  --quantity 0.001

# SELL MARKET order
python -m bot.cli place-order \
  --symbol ETHUSDT \
  --side SELL \
  --order-type MARKET \
  --quantity 0.01
```

---

### Place a LIMIT Order

```bash
# BUY LIMIT order
python -m bot.cli place-order \
  --symbol BTCUSDT \
  --side BUY \
  --order-type LIMIT \
  --quantity 0.001 \
  --price 60000

# SELL LIMIT order
python -m bot.cli place-order \
  --symbol ETHUSDT \
  --side SELL \
  --order-type LIMIT \
  --quantity 0.1 \
  --price 3500
```

**Output:**
```
╔══════════════════════════════════════════════════════╗
║            ORDER PLACED SUCCESSFULLY ✓               ║
╠══════════════════════════════════════════════════════╣
║  Order ID           : 3462781923                     ║
║  Client Order ID    : abc123xyz789                   ║
║  Symbol             : BTCUSDT                        ║
║  Side               : BUY                            ║
║  Type               : LIMIT                          ║
║  Quantity           : 0.001                          ║
║  Price              : 60000.0                        ║
║  Status             : NEW                            ║
║  Time in Force      : GTC                            ║
║  Avg Fill Price     : 0                              ║
║  Executed Qty       : 0                              ║
║  Timestamp          : 1718123456789                  ║
╚══════════════════════════════════════════════════════╝
```

---

### Get Raw JSON Response

Add `--json-output` to any command:

```bash
python -m bot.cli place-order \
  --symbol BTCUSDT \
  --side BUY \
  --order-type MARKET \
  --quantity 0.001 \
  --json-output
```

---

### View Help

```bash
# General help
python -m bot.cli --help

# Command-specific help
python -m bot.cli place-order --help
python -m bot.cli account-info --help
```

---

## Logging

Logs are automatically saved in the `logs/` directory:

| File | Contents |
|---|---|
| `logs/trading_bot.log` | Full debug log (all requests, responses, events) |
| `logs/errors.log` | Warnings and errors only |

Both files use **rotating handlers** (5 MB max size, 5 backups).

### Example Log Output

```
2024-06-12 10:23:45 | INFO     | trading_bot | Logger initialised — log file: logs/trading_bot.log
2024-06-12 10:23:45 | INFO     | trading_bot.validators | Validating order parameters …
2024-06-12 10:23:45 | DEBUG    | trading_bot.validators | Symbol validated: BTCUSDT
2024-06-12 10:23:45 | DEBUG    | trading_bot.validators | Side validated: BUY
2024-06-12 10:23:45 | DEBUG    | trading_bot.validators | Order type validated: LIMIT
2024-06-12 10:23:45 | DEBUG    | trading_bot.validators | Quantity validated: 0.001
2024-06-12 10:23:45 | DEBUG    | trading_bot.validators | Price validated: 60000.0
2024-06-12 10:23:45 | INFO     | trading_bot.validators | All parameters passed validation: {'symbol': 'BTCUSDT', 'side': 'BUY', 'order_type': 'LIMIT', 'quantity': 0.001, 'price': 60000.0}
2024-06-12 10:23:45 | INFO     | trading_bot.client | BinanceFuturesClient initialised (base_url=https://testnet.binancefuture.com)
2024-06-12 10:23:45 | INFO     | trading_bot.orders | Placing BUY LIMIT order | symbol=BTCUSDT | qty=0.001 | price=60000.0
2024-06-12 10:23:45 | INFO     | trading_bot.client | POST https://testnet.binancefuture.com/fapi/v1/order | params: {'symbol': 'BTCUSDT', 'side': 'BUY', 'type': 'LIMIT', 'quantity': 0.001, 'price': 60000.0, 'timeInForce': 'GTC'}
2024-06-12 10:23:46 | DEBUG    | trading_bot.client | Response [200] from https://testnet.binancefuture.com/fapi/v1/order: {"orderId":3462781923,...}
2024-06-12 10:23:46 | INFO     | trading_bot.orders | Order placed successfully: orderId=3462781923
2024-06-12 10:23:46 | INFO     | trading_bot.cli | Order command completed successfully.
```

---

## Error Handling

| Error Type | Cause | Exit Code |
|---|---|---|
| `ValidationError` | Invalid symbol, side, type, qty, or price | 1 |
| `BinanceAuthError` | Invalid or missing API keys | 1 |
| `BinanceAPIError` | Binance returned an error response | 1 |
| `BinanceNetworkError` | Connection failure or timeout | 1 |

All errors are logged to `logs/errors.log` and printed to stderr with coloured output.

---

## Common Errors & Fixes

| Error | Fix |
|---|---|
| `BINANCE_API_KEY … must be set` | Add keys to `.env` file |
| `Authentication Error [-2014]` | API key is invalid — regenerate from testnet |
| `Binance API Error [-1121]` | Invalid symbol — check spelling (e.g. `BTCUSDT`) |
| `Price is required for LIMIT orders` | Add `--price` flag |
| `Connection failed` | Check internet connection |

---

## Security Notes

- API keys are read from `.env` or environment variables — never hardcoded
- `.env` is in `.gitignore` — never commit it
- Only Testnet keys are used — no real funds at risk
- All requests are signed with HMAC-SHA256

---

## License

MIT — for educational and testing purposes only.
