import sys, time, math, os, datetime as dt
import pandas as pd
import numpy as np
import ccxt
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
import matplotlib.pyplot as plt

# ============== CONFIG ==============
CONFIG = {
    "exchange_id": "coinbase",          # Coinbase Advanced Trade via CCXT
    "symbol": "BTC/USD",
    "timeframe": "1h",
    "lookback_candles": 800,
    "poll_seconds": 60,
    "fee_rate": 0.0004,                 # 0.04% taker fee estimate
    "risk_per_trade": 0.01,             # risk 1% of equity per trade
    "stop_loss_pct": 0.02,              # 2% SL
    "take_profit_pct": 0.03,            # 3% TP
    "initial_cash": 10000.0,
    "precision_cash": 2,
    "precision_amt": 6,
    "rsi_period": 14,
    "ema_fast": 50,
    "ema_slow": 200,
}

# Folders
LOG_DIR = "logs"
CHART_DIR = "charts"
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(CHART_DIR, exist_ok=True)

# ============== HELPERS ==============
def now_utc():
    return dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc)

def ts_str():
    return now_utc().strftime("%Y%m%d_%H%M%S")

def get_exchange(exchange_id):
    ex_class = getattr(ccxt, exchange_id)
    return ex_class({"enableRateLimit": True})

def fetch_ohlcv(exchange, symbol, timeframe, limit):
    data = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(data, columns=["ts","open","high","low","close","volume"])
    df["ts"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
    return df.set_index("ts")

def add_indicators(df):
    df = df.copy()
    df["ema_fast"] = EMAIndicator(df["close"], window=CONFIG["ema_fast"]).ema_indicator()
    df["ema_slow"] = EMAIndicator(df["close"], window=CONFIG["ema_slow"]).ema_indicator()
    df["rsi"] = RSIIndicator(df["close"], window=CONFIG["rsi_period"]).rsi()
    return df

def generate_signals(df):
    """Return a column 'signal': 1 = long, -1 = flat/exit."""
    df = df.copy()
    df["signal"] = 0
    trend_up = df["ema_fast"] > df["ema_slow"]
    buy_cond = trend_up & (df["rsi"] > 55)
    sell_cond = (~trend_up) | (df["rsi"] < 45)
    df.loc[buy_cond, "signal"] = 1
    df.loc[sell_cond, "signal"] = -1
    return df

def plot_equity(equity_df: pd.DataFrame, out_png: str, title: str):
    plt.figure(figsize=(10, 5))
    plt.plot(equity_df.index, equity_df["equity"])
    plt.title(title)
    plt.xlabel("Time")
    plt.ylabel("Equity ($)")
    plt.tight_layout()
    plt.savefig(out_png)
    plt.close()

# ============== BACKTEST ==============
def backtest(df):
    cash = CONFIG["initial_cash"]
    coin = 0.0
    entry_price = None
    fee_rate = CONFIG["fee_rate"]

    equity_rows = []
    trade_rows = []

    for t, row in df.iterrows():
        price = float(row["close"])

        # evaluate SL/TP if in position
        if coin > 0 and entry_price is not None:
            if price <= entry_price * (1 - CONFIG["stop_loss_pct"]):
                exit_value = coin * price
                fee = exit_value * fee_rate
                cash += (exit_value - fee)
                trade_rows.append([t, "SELL", price, coin, "sl", cash])
                coin = 0.0
                entry_price = None
            elif price >= entry_price * (1 + CONFIG["take_profit_pct"]):
                exit_value = coin * price
                fee = exit_value * fee_rate
                cash += (exit_value - fee)
                trade_rows.append([t, "SELL", price, coin, "tp", cash])
                coin = 0.0
                entry_price = None

        # act on signal at close
        if row["signal"] == 1 and coin == 0:
            equity = cash + coin * price
            risk_amt = equity * CONFIG["risk_per_trade"]
            sl_price = price * (1 - CONFIG["stop_loss_pct"])
            risk_per_coin = price - sl_price
            size = 0.0 if risk_per_coin <= 0 else min((risk_amt / risk_per_coin), (equity * 0.95) / price)
            size = max(0.0, size)
            cost = size * price
            fee = cost * fee_rate
            if cost + fee <= cash and size > 0:
                cash -= (cost + fee)
                coin += size
                entry_price = price
                trade_rows.append([t, "BUY", price, size, "signal", cash])

        elif row["signal"] == -1 and coin > 0:
            exit_value = coin * price
            fee = exit_value * fee_rate
            cash += (exit_value - fee)
            trade_rows.append([t, "SELL", price, coin, "signal", cash])
            coin = 0.0
            entry_price = None

        equity_rows.append([t, cash + coin * price])

    eq = pd.DataFrame(equity_rows, columns=["ts", "equity"]).set_index("ts")
    total_return = (eq["equity"].iloc[-1] / eq["equity"].iloc[0]) - 1
    dd = (eq["equity"].cummax() - eq["equity"]) / eq["equity"].cummax()
    max_dd = dd.max()
    trades = int((df["signal"].diff().fillna(0) != 0).sum() // 2)

    # ---- save CSVs + chart
    stamp = ts_str()
    trades_df = pd.DataFrame(trade_rows, columns=["ts","side","price","size","reason","cash"])
    trades_csv = os.path.join(LOG_DIR, f"backtest_trades_{stamp}.csv")
    equity_csv = os.path.join(LOG_DIR, f"backtest_equity_{stamp}.csv")
    trades_df.to_csv(trades_csv, index=False)
    eq.to_csv(equity_csv)
    plot_equity(eq, os.path.join(CHART_DIR, f"backtest_equity_{stamp}.png"),
                f"Backtest Equity — {CONFIG['symbol']} {CONFIG['timeframe']}")

    print(f"Backtest results ({CONFIG['symbol']} {CONFIG['timeframe']}):")
    print(f"  Start: {eq.index[0]}  End: {eq.index[-1]}")
    print(f"  Final equity: ${eq['equity'].iloc[-1]:.2f}  |  Return: {total_return*100:.2f}%")
    print(f"  Max drawdown: {max_dd*100:.2f}%")
    print(f"  ~Round trips: {trades}")
    print(f"Saved: {trades_csv}")
    print(f"Saved: {equity_csv}")
    print(f"Saved chart: {os.path.join(CHART_DIR, f'backtest_equity_{stamp}.png')}")

# ============== PAPER TRADING ==============
class PaperBroker:
    def __init__(self, cash):
        self.cash = cash
        self.coin = 0.0
        self.entry_price = None
        self.fee = CONFIG["fee_rate"]

    def buy(self, price, t):
        equity = self.cash + self.coin * price
        risk_amt = equity * CONFIG["risk_per_trade"]
        sl_price = price * (1 - CONFIG["stop_loss_pct"])
        risk_per_coin = price - sl_price
        size = 0.0 if risk_per_coin <= 0 else min((risk_amt / risk_per_coin), (equity * 0.95) / price)
        size = math.floor(size * (10**CONFIG["precision_amt"])) / (10**CONFIG["precision_amt"])
        cost = size * price
        fee = cost * self.fee
        if cost + fee <= self.cash and size > 0:
            self.cash -= (cost + fee)
            self.coin += size
            self.entry_price = price
            log_trade(t, "BUY", price, size, "signal", self.cash)
            print(f"[BUY] {size} @ {price:.2f}  cash={self.cash:.2f} coin={self.coin:.6f}")

    def sell_all(self, price, t, reason="exit"):
        if self.coin <= 0: 
            return
        value = self.coin * price
        fee = value * self.fee
        self.cash += (value - fee)
        log_trade(t, "SELL", price, self.coin, reason, self.cash)
        print(f"[SELL-{reason.upper()}] {self.coin} @ {price:.2f}  cash={self.cash:.2f}")
        self.coin = 0.0
        self.entry_price = None

    def equity(self, price):
        return self.cash + self.coin * price

# Paper CSV paths (stable names, append each run)
PAPER_TRADES_CSV = os.path.join(LOG_DIR, "paper_trades.csv")
PAPER_EQUITY_CSV = os.path.join(LOG_DIR, "paper_equity.csv")
PAPER_EQUITY_PNG = os.path.join(CHART_DIR, "paper_equity.png")

def log_trade(ts, side, price, size, reason, cash_after):
    row = pd.DataFrame([[ts, side, price, size, reason, cash_after]],
                       columns=["ts","side","price","size","reason","cash"])
    header = not os.path.exists(PAPER_TRADES_CSV)
    row.to_csv(PAPER_TRADES_CSV, mode="a", header=header, index=False)

def log_equity(ts, equity):
    row = pd.DataFrame([[ts, equity]], columns=["ts","equity"])
    header = not os.path.exists(PAPER_EQUITY_CSV)
    row.to_csv(PAPER_EQUITY_CSV, mode="a", header=header, index=False)

def refresh_paper_chart():
    try:
        df = pd.read_csv(PAPER_EQUITY_CSV, parse_dates=["ts"])
        df = df.sort_values("ts")
        df = df.set_index("ts")
        plot_equity(df, PAPER_EQUITY_PNG, f"Paper Equity — {CONFIG['symbol']} {CONFIG['timeframe']}")
    except Exception as e:
        # Silent chart failure shouldn’t kill the loop
        print("Chart update skipped:", e)

def paper_trade_loop():
    ex = get_exchange(CONFIG["exchange_id"])
    broker = PaperBroker(CONFIG["initial_cash"])
    last_candle_time = None

    print(f"Starting paper-trade on {CONFIG['exchange_id']} {CONFIG['symbol']} {CONFIG['timeframe']}")
    while True:
        try:
            df = fetch_ohlcv(ex, CONFIG["symbol"], CONFIG["timeframe"], CONFIG["lookback_candles"])
            df = add_indicators(df)
            df = generate_signals(df)
            # Use the last *closed* candle
            last = df.iloc[-2]  # -1 is forming
            t = last.name
            price = float(last["close"])

            if last_candle_time != t:
                last_candle_time = t

                # SL/TP checks first
                if broker.coin > 0 and broker.entry_price:
                    if price <= broker.entry_price * (1 - CONFIG["stop_loss_pct"]):
                        broker.sell_all(price, t, reason="sl")
                    elif price >= broker.entry_price * (1 + CONFIG["take_profit_pct"]):
                        broker.sell_all(price, t, reason="tp")

                # Signals
                if last["signal"] == 1 and broker.coin == 0:
                    broker.buy(price, t)
                elif last["signal"] == -1 and broker.coin > 0:
                    broker.sell_all(price, t, reason="signal")

                eq_val = broker.equity(price)
                log_equity(t, eq_val)
                refresh_paper_chart()
                print(f"[{t}] price={price:.2f} equity=${eq_val:.2f}")

            time.sleep(CONFIG["poll_seconds"])
        except KeyboardInterrupt:
            print("Stopping paper loop.")
            break
        except Exception as e:
            print("Error:", e)
            time.sleep(5)

# ============== ENTRYPOINT ==============
if __name__ == "__main__":
    mode = sys.argv[1].lower() if len(sys.argv) > 1 else "backtest"
    ex = get_exchange(CONFIG["exchange_id"])
    hist = fetch_ohlcv(ex, CONFIG["symbol"], CONFIG["timeframe"], CONFIG["lookback_candles"])
    hist = add_indicators(hist)
    hist = generate_signals(hist)

    if mode == "backtest":
        backtest(hist)
    elif mode == "paper":
        paper_trade_loop()
    else:
        print("Usage: python crypto_agent.py [backtest|paper]")
