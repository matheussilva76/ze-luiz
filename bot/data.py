import yfinance as yf
import pandas as pd


def detect_pip(ticker: str):
    if "JPY" in ticker:
        return 0.01, 6.50
    return 0.0001, 10.00


def baixar_dados(ticker: str) -> pd.DataFrame:
    pip_size, valor_pip = detect_pip(ticker)
    df = yf.download(ticker, period="2y", interval="1h", progress=False, auto_adjust=True)

    if df.empty:
        raise ValueError(f"Sem dados para {ticker}. Verifique o ticker ou tente novamente.")

    # Achata MultiIndex independente da ordem dos níveis
    if isinstance(df.columns, pd.MultiIndex):
        level_values = [df.columns.get_level_values(i) for i in range(df.columns.nlevels)]
        ohlcv = {"Open", "High", "Low", "Close", "Volume"}
        for lv in level_values:
            if ohlcv.intersection(set(lv)):
                df.columns = lv
                break

    if "Volume" in df.columns:
        df.rename(columns={"Volume": "Tick_Volume"}, inplace=True)

    df.dropna(subset=["Open", "High", "Low", "Close"], inplace=True)

    if df.empty:
        raise ValueError(f"Dados vazios após limpeza para {ticker}.")

    df.attrs["pip_size"] = pip_size
    df.attrs["valor_pip"] = valor_pip
    df.attrs["ticker"] = ticker
    return df
