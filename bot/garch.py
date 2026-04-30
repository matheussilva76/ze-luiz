import warnings
import numpy as np
import pandas as pd
from arch import arch_model


def rodar_garch(df: pd.DataFrame, limite_volatilidade: float = 0.08):
    warnings.filterwarnings("ignore")

    retornos = df["Retorno_Ajustado"].dropna()
    modelo = arch_model(retornos, vol="Garch", p=1, q=1, rescale=True)
    resultado = modelo.fit(disp="off")

    df = df.copy()
    df["Volatilidade_GARCH"] = resultado.conditional_volatility

    previsao = resultado.forecast(horizon=1)
    vol_prevista = float(np.sqrt(previsao.variance.values[-1, 0]))

    ativo = vol_prevista <= limite_volatilidade
    status = "ATIVO" if ativo else "STANDBY"

    return df, vol_prevista, status
