# 🧠 crypto_agent  
**An automated crypto trading agent for backtesting, paper trading, and risk-controlled live execution.**

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)  
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)  
[![Status](https://img.shields.io/badge/Status-Active-success.svg)]()

---

## 🚀 Overview
`crypto_agent` is a modular, data-driven cryptocurrency trading bot designed to run 24/7 on any server or VPS.  
It provides full support for **backtesting**, **paper-trading**, and (optionally) **live trading** on real exchanges using the [CCXT](https://github.com/ccxt/ccxt) library.

The goal: **maximize reward while minimizing risk** through disciplined, rule-based automation — not prediction or luck.

---

## ⚙️ Features
✅ **Multi-exchange support** — Coinbase, Binance, Kraken, etc.  
✅ **EMA + RSI strategy** — Simple, extendable technical model.  
✅ **Risk management built-in** — Fixed fractional sizing, stop loss, take profit.  
✅ **Two main modes**  
- 🧪 `backtest` → run strategy on historical data  
- 💵 `paper` → live simulation using real-time candles
    
✅ **Logging & visualization** — CSV trade/equity logs + live equity charts  
✅ **Ready for deployment** — Works with `systemd`, `tmux`, or Docker for 24/7 uptime  

---

## 🧩 Architecture
crypto_agent.py
├── CONFIG ........ strategy & exchange settings
├── data layer .... fetches OHLCV via CCXT
├── indicators .... EMA + RSI (ta library)
├── strategy ...... signal generation & risk logic
├── broker ........ backtest/paper/live trade execution
├── logger ........ CSV + chart outputs
└── service ....... optional systemd/Docker setup

yaml

---

## 🛠️ Installation
```bash
git clone https://github.com/<yourusername>/crypto_agent.git
cd crypto_agent
python3 -m venv venv
source venv/bin/activate
pip install -U pip ccxt pandas numpy ta matplotlib

🧪 Run a Backtest
bash

python3 crypto_agent.py backtest

Outputs:

yaml

Backtest results (BTC/USD 1h):
  Final equity: $10,842.00 | Return: +8.42%
  Max drawdown: 3.22% | Trades: 19
Results stored in:

logs/backtest_trades_*.csv

logs/backtest_equity_*.csv

charts/backtest_equity_*.png

💵 Paper Trading (Simulation)
bash

python3 crypto_agent.py paper
Runs continuously, fetching hourly candles from Coinbase and updating:

logs/paper_trades.csv

logs/paper_equity.csv

charts/paper_equity.png

Stop anytime with Ctrl + C.
Can be deployed as a systemd service or Docker container for 24/7 uptime.

⚖️ Strategy Logic
Condition	Action
EMA50 > EMA200 and RSI > 55	Enter long
EMA50 < EMA200 or RSI < 45	Exit position
Stop Loss	−2 % below entry
Take Profit	+3 % above entry
Risk per Trade	1 % of total equity

🧠 Roadmap
 Per-fill PnL and performance summary

 Multi-pair portfolio support

 Web dashboard / API

 Telegram or Discord alerts

 ML-based signal plugin

🧰 Tech Stack
Python 3.11 +

CCXT (exchange API)

Pandas / NumPy (data)

TA (technical indicators)

Matplotlib (charting)

Optional: systemd, tmux, Docker (deployment)

🌐 Deployment Example (systemd)
bash

sudo systemctl enable crypto-agent.service
sudo systemctl start crypto-agent.service
journalctl -u crypto-agent.service -f
Keeps the bot running 24/7 and restarts automatically on failure.

⚠️ Disclaimer
This project is provided for educational and research purposes only.
Cryptocurrency trading carries substantial risk — use at your own discretion.
Always begin with paper trading before committing any real funds.

📜 License
MIT License © 2025 TACONET7

⭐ If you find this project useful, star the repo and share your results!


