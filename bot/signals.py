import pandas as pd


def gerar_sinais(
    df: pd.DataFrame,
    hora_inicio: int = 4,
    hora_fim: int = 13,
    gatilho_z: float = 2.0,
    limite_inclinacao: float = 0.00040,
    limite_adx: float = 25.0,
) -> pd.DataFrame:
    df = df.copy()

    df["Hora"] = df.index.hour
    df["SMA_200_Slope"] = df["SMA_200"].diff(5).abs()
    df["Sinal_Ze"] = "NEUTRO"

    janela = (df["Hora"] >= hora_inicio) & (df["Hora"] <= hora_fim)
    slope_ok = df["SMA_200_Slope"] <= limite_inclinacao
    adx_ok = df["ADX_14"] < limite_adx

    cond_compra = (df["Z_Score"] <= -gatilho_z) & janela & slope_ok & adx_ok
    cond_venda = (df["Z_Score"] >= gatilho_z) & janela & slope_ok & adx_ok

    df.loc[cond_compra, "Sinal_Ze"] = "COMPRA"
    df.loc[cond_venda, "Sinal_Ze"] = "VENDA"

    return df
