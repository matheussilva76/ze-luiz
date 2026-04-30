import numpy as np
import pandas as pd
from ta.trend import ADXIndicator


def calcular_indicadores(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["EMA_9"] = df["Close"].ewm(span=9, adjust=False).mean()
    df["SMA_20"] = df["Close"].rolling(window=20).mean()
    df["SMA_200"] = df["Close"].rolling(window=200).mean()

    adx = ADXIndicator(df["High"], df["Low"], df["Close"], window=14, fillna=False)
    df["ADX_14"] = adx.adx()

    df["Retorno_Bruto"] = np.log(df["Close"] / df["Close"].shift(1)) * 100
    df["Retorno_Overnight"] = 0.0
    df["Retorno_Ajustado"] = df["Retorno_Bruto"]

    df.dropna(subset=["SMA_200", "Retorno_Bruto", "ADX_14"], inplace=True)

    df["Desvio_20"] = df["Close"].rolling(window=20).std()
    df["Z_Score"] = (df["Close"] - df["SMA_20"]) / df["Desvio_20"]

    df.dropna(subset=["Z_Score"], inplace=True)
    return df
