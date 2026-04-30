import yfinance as yf
import pandas as pd


def detect_pip(ticker: str):
    if "JPY" in ticker:
        return 0.01, 6.50
    return 0.0001, 10.00


def baixar_dados(ticker: str) -> pd.DataFrame:
    pip_size, valor_pip = detect_pip(ticker)
    df = yf.download(ticker, period="730d", interval="1h", progress=False)

    if df.empty:
        raise ValueError(f"Sem dados para {ticker}. Verifique o ticker.")

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    if "Volume" in df.columns:
        df.rename(columns={"Volume": "Tick_Volume"}, inplace=True)

    df.dropna(subset=["Close"], inplace=True)
    df.attrs["pip_size"] = pip_size
    df.attrs["valor_pip"] = valor_pip
    df.attrs["ticker"] = ticker
    return df
