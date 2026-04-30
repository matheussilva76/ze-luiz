import numpy as np
import pandas as pd
import pandas_ta as ta


def calcular_indicadores(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["EMA_9"] = df["Close"].ewm(span=9, adjust=False).mean()
    df["SMA_20"] = df["Close"].rolling(window=20).mean()
    df["SMA_200"] = df["Close"].rolling(window=200).mean()

    df.ta.adx(length=14, append=True)

    df["Retorno_Bruto"] = np.log(df["Close"] / df["Close"].shift(1)) * 100
    df["Retorno_Overnight"] = 0.0
    df["Retorno_Ajustado"] = df["Retorno_Bruto"]

    df.dropna(subset=["SMA_200", "Retorno_Bruto", "ADX_14"], inplace=True)

    df["Desvio_20"] = df["Close"].rolling(window=20).std()
    df["Z_Score"] = (df["Close"] - df["SMA_20"]) / df["Desvio_20"]

    df.dropna(subset=["Z_Score"], inplace=True)
    return df
