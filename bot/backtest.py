import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import List


@dataclass
class ConfigBacktest:
    capital_inicial: float = 1000.0
    valor_pip_padrao: float = 10.0
    pip_size: float = 0.0001
    spread_pips: float = 1.5
    lote_pesado: float = 0.10
    lote_leve: float = 0.05
    alvo_pips: float = 55.0
    stop_pips: float = 40.0
    max_perdas_diarias: int = 2
    nivel1_trigger_pips: float = 30.0
    nivel1_stop_pips: float = 10.0
    nivel2_trigger_pips: float = 45.0
    nivel2_stop_pips: float = 5.0


@dataclass
class ResultadoBacktest:
    trades: List[dict] = field(default_factory=list)
    lucros: List[float] = field(default_factory=list)
    equity: List[float] = field(default_factory=list)
    saldo_final: float = 0.0

    @property
    def total_trades(self):
        return len([l for l in self.lucros if l != 0])

    @property
    def vitorias(self):
        return len([l for l in self.lucros if l > 1.0])

    @property
    def win_rate(self):
        return (self.vitorias / self.total_trades * 100) if self.total_trades > 0 else 0

    @property
    def lucro_liquido(self):
        return self.saldo_final - self._capital_inicial

    def set_capital_inicial(self, v):
        self._capital_inicial = v


def rodar_backtest(df: pd.DataFrame, cfg: ConfigBacktest) -> tuple[pd.DataFrame, ResultadoBacktest]:
    alvo_dec = cfg.alvo_pips * cfg.pip_size
    stop_dec = cfg.stop_pips * cfg.pip_size

    posicao = 0
    preco_entrada = 0.0
    stop_loss = 0.0
    take_profit = 0.0
    nivel_protecao = 0
    lote_ativo = 0.0
    mfe_atual = 0.0
    mae_atual = 0.0
    ultimo_dia = None
    perdas_no_dia = 0

    saldo = cfg.capital_inicial
    resultado = ResultadoBacktest(saldo_final=cfg.capital_inicial)
    resultado.set_capital_inicial(cfg.capital_inicial)

    lucros_candle = []
    equity_candle = []

    for i in range(len(df)):
        row = df.iloc[i]
        dia = row.name.date()
        lucro = 0.0

        if dia != ultimo_dia:
            perdas_no_dia = 0
            ultimo_dia = dia

        if posicao != 0:
            alto = row["High"]
            baixo = row["Low"]
            custo_spread = cfg.spread_pips * cfg.valor_pip_padrao * lote_ativo

            if posicao == 1:
                pips_favor = (alto - preco_entrada) / cfg.pip_size
                pips_contra = (preco_entrada - baixo) / cfg.pip_size
            else:
                pips_favor = (preco_entrada - baixo) / cfg.pip_size
                pips_contra = (alto - preco_entrada) / cfg.pip_size

            if pips_favor > mfe_atual:
                mfe_atual = pips_favor
            if pips_contra > mae_atual:
                mae_atual = pips_contra

            # Proteção escalonada
            if posicao == 1:
                if nivel_protecao < 2 and alto >= preco_entrada + cfg.nivel2_trigger_pips * cfg.pip_size:
                    stop_loss = preco_entrada + cfg.nivel2_stop_pips * cfg.pip_size
                    nivel_protecao = 2
                elif nivel_protecao < 1 and alto >= preco_entrada + cfg.nivel1_trigger_pips * cfg.pip_size:
                    stop_loss = preco_entrada - cfg.nivel1_stop_pips * cfg.pip_size
                    nivel_protecao = 1
            else:
                if nivel_protecao < 2 and baixo <= preco_entrada - cfg.nivel2_trigger_pips * cfg.pip_size:
                    stop_loss = preco_entrada - cfg.nivel2_stop_pips * cfg.pip_size
                    nivel_protecao = 2
                elif nivel_protecao < 1 and baixo <= preco_entrada - cfg.nivel1_trigger_pips * cfg.pip_size:
                    stop_loss = preco_entrada + cfg.nivel1_stop_pips * cfg.pip_size
                    nivel_protecao = 1

            # Verificar saída
            if posicao == 1:
                if baixo <= stop_loss:
                    pips = (stop_loss - preco_entrada) / cfg.pip_size
                    lucro = (pips * cfg.valor_pip_padrao * lote_ativo) - custo_spread
                    posicao = 0
                elif alto >= take_profit:
                    lucro = (cfg.alvo_pips * cfg.valor_pip_padrao * lote_ativo) - custo_spread
                    posicao = 0
            else:
                if alto >= stop_loss:
                    pips = (preco_entrada - stop_loss) / cfg.pip_size
                    lucro = (pips * cfg.valor_pip_padrao * lote_ativo) - custo_spread
                    posicao = 0
                elif baixo <= take_profit:
                    lucro = (cfg.alvo_pips * cfg.valor_pip_padrao * lote_ativo) - custo_spread
                    posicao = 0

            if posicao == 0:
                saldo += lucro
                if lucro < 0:
                    perdas_no_dia += 1
                resultado.trades.append({
                    "lucro": lucro,
                    "estagio": nivel_protecao,
                    "lote": lote_ativo,
                    "mfe": mfe_atual,
                    "mae": mae_atual,
                })

        sinal = str(row.get("Sinal_Ze", "NEUTRO"))

        if posicao == 0 and perdas_no_dia < cfg.max_perdas_diarias:
            if sinal == "COMPRA":
                posicao = 1
                preco_entrada = float(row["Close"])
                stop_loss = preco_entrada - stop_dec
                take_profit = preco_entrada + alvo_dec
                nivel_protecao = 0
                mfe_atual = mae_atual = 0.0
                lote_ativo = cfg.lote_pesado if preco_entrada > float(row["SMA_200"]) else cfg.lote_leve
            elif sinal == "VENDA":
                posicao = -1
                preco_entrada = float(row["Close"])
                stop_loss = preco_entrada + stop_dec
                take_profit = preco_entrada - alvo_dec
                nivel_protecao = 0
                mfe_atual = mae_atual = 0.0
                lote_ativo = cfg.lote_pesado if preco_entrada < float(row["SMA_200"]) else cfg.lote_leve

        lucros_candle.append(lucro)
        equity_candle.append(saldo)

    resultado.lucros = lucros_candle
    resultado.equity = equity_candle
    resultado.saldo_final = saldo

    df = df.copy()
    df["Lucro_Real_USD"] = lucros_candle
    df["Equity_Curve"] = equity_candle
    df["Drawdown"] = df["Equity_Curve"] - df["Equity_Curve"].cummax()

    return df, resultado
