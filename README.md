crypto_agent  
An automated crypto trading agent for backtesting, paper trading, and risk-controlled live execution.

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)  
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)  
[![Status](https://img.shields.io/badge/Status-Active-success.svg)]()

Overview
`crypto_agent` is a modular, data-driven cryptocurrency trading bot designed to run 24/7 on any server or VPS.  
It provides full support for backtesting, paper-trading, and (optionally) live trading** on real exchanges using the [CCXT](https://github.com/ccxt/ccxt) library.

The goal: maximize reward while minimizing risk through disciplined, rule-based automation — not prediction or luck.

## ⚙️ Features
✅ **Multi-exchange support** — Coinbase, Binance, Kraken, etc.  
✅ **EMA + RSI strategy** — Simple, extendable technical model.  
✅ **Risk management built-in** — Fixed fractional sizing, stop loss, take profit.  
✅ **Two main modes**  
  - 🧪 `backtest` → run strategy on historical data  
  - 💵 `paper` → live simulation using real-time candles  
✅ **Logging & visualization** — CSV trade/equity logs + live equity charts  
✅ **Ready for deployment** — Works with `systemd`, `tmux`, or Docker for 24/7 uptime  


