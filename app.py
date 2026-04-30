import warnings
warnings.filterwarnings("ignore")

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import json

from bot.data import baixar_dados
from bot.indicators import calcular_indicadores
from bot.garch import rodar_garch
from bot.signals import gerar_sinais
from bot.backtest import rodar_backtest, ConfigBacktest
from database import inicializar_db, salvar_resultado, listar_resultados, deletar_resultado

inicializar_db()

# ── Página ──────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Zé Luiz – Bot de Daytrade",
    page_icon="📈",
    layout="wide",
)

st.markdown("""
<style>
    .metric-card {
        background: #1e1e2e;
        border-radius: 10px;
        padding: 18px 22px;
        border-left: 4px solid #7c3aed;
    }
    .metric-card h3 { margin: 0; font-size: 0.85rem; color: #a1a1b5; }
    .metric-card p  { margin: 4px 0 0; font-size: 1.6rem; font-weight: 700; }
    .green { color: #22c55e; }
    .red   { color: #ef4444; }
    .purple{ color: #a855f7; }
</style>
""", unsafe_allow_html=True)

st.title("📈 Zé Luiz – Bot de Daytrade Forex")
st.caption("Backtest com Z-Score + ADX + GARCH | Motor V6.3")

# ── Sidebar – Parâmetros ─────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Parâmetros")

    st.subheader("Ativo")
    TICKERS_DISPONIVEIS = ["AUDUSD=X", "EURUSD=X", "GBPUSD=X", "NZDUSD=X", "USDJPY=X", "USDCHF=X"]
    ticker = st.selectbox("Par de moedas", TICKERS_DISPONIVEIS)

    st.subheader("Janela Operacional")
    hora_inicio = st.slider("Hora início", 0, 23, 4)
    hora_fim    = st.slider("Hora fim",    0, 23, 13)

    st.subheader("Sinais")
    gatilho_z       = st.slider("Gatilho Z-Score",      0.5, 4.0, 2.0, 0.1)
    limite_adx      = st.slider("Limite ADX (tendência)", 10, 50, 25)
    limite_inclinacao = st.number_input(
        "Slope SMA 200 (decimal)", value=0.00040, format="%.5f", step=0.00005
    )

    st.subheader("GARCH")
    limite_vol = st.slider("Limite de volatilidade (%)", 0.01, 0.30, 0.08, 0.01)

    st.subheader("Gestão Financeira")
    capital       = st.number_input("Capital inicial (USD)", value=1000.0, step=100.0)
    alvo_pips     = st.slider("Alvo (pips)",  10, 150, 55)
    stop_pips     = st.slider("Stop (pips)",  10, 150, 40)
    lote_pesado   = st.number_input("Lote pesado", value=0.10, step=0.01, format="%.2f")
    lote_leve     = st.number_input("Lote leve",   value=0.05, step=0.01, format="%.2f")
    spread_pips   = st.number_input("Spread (pips)", value=1.5, step=0.1, format="%.1f")
    max_perdas    = st.slider("Máx. perdas diárias", 1, 10, 2)

    rodar = st.button("▶ Rodar Backtest", type="primary", use_container_width=True)

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab_resultado, tab_graficos, tab_historico = st.tabs(
    ["📊 Resultado", "📉 Gráficos", "🗂️ Histórico"]
)

# ── Execução do Backtest ─────────────────────────────────────────────────────
if rodar:
    with st.spinner("Baixando dados e rodando backtest…"):
        try:
            df = baixar_dados(ticker)
            pip_size   = df.attrs["pip_size"]
            valor_pip  = df.attrs["valor_pip"]

            df = calcular_indicadores(df)
            df, vol_prevista, status_garch = rodar_garch(df, limite_vol)
            df = gerar_sinais(df, hora_inicio, hora_fim, gatilho_z, limite_inclinacao, limite_adx)

            cfg = ConfigBacktest(
                capital_inicial=capital,
                valor_pip_padrao=valor_pip,
                pip_size=pip_size,
                spread_pips=spread_pips,
                lote_pesado=lote_pesado,
                lote_leve=lote_leve,
                alvo_pips=alvo_pips,
                stop_pips=stop_pips,
                max_perdas_diarias=max_perdas,
            )
            df_bt, resultado = rodar_backtest(df, cfg)

            st.session_state["df_bt"]        = df_bt
            st.session_state["resultado"]    = resultado
            st.session_state["vol_prevista"] = vol_prevista
            st.session_state["status_garch"] = status_garch
            st.session_state["ticker"]       = ticker
            st.session_state["capital"]      = capital

            # Salva no banco
            trades_df = pd.DataFrame(resultado.trades) if resultado.trades else pd.DataFrame()
            params = {
                "hora_inicio": hora_inicio, "hora_fim": hora_fim,
                "gatilho_z": gatilho_z, "limite_adx": limite_adx,
                "limite_inclinacao": limite_inclinacao, "limite_vol": limite_vol,
                "capital": capital, "alvo_pips": alvo_pips, "stop_pips": stop_pips,
                "lote_pesado": lote_pesado, "lote_leve": lote_leve,
                "spread_pips": spread_pips, "max_perdas": max_perdas,
            }
            salvar_resultado(
                ticker=ticker,
                parametros=params,
                total_trades=resultado.total_trades,
                win_rate=resultado.win_rate,
                lucro_liquido=resultado.lucro_liquido,
                drawdown_maximo=float(df_bt["Drawdown"].min()),
                mfe_medio=float(trades_df["mfe"].mean()) if not trades_df.empty else 0,
                mae_medio=float(trades_df["mae"].mean()) if not trades_df.empty else 0,
                vol_prevista=vol_prevista,
                status_garch=status_garch,
            )
            st.success("✅ Backtest concluído e salvo!")

        except Exception as e:
            st.error(f"❌ Erro: {e}")
            st.stop()

# ── Tab: Resultado ────────────────────────────────────────────────────────────
with tab_resultado:
    if "resultado" not in st.session_state:
        st.info("Configure os parâmetros na barra lateral e clique em **Rodar Backtest**.")
    else:
        res    = st.session_state["resultado"]
        df_bt  = st.session_state["df_bt"]
        vol    = st.session_state["vol_prevista"]
        status = st.session_state["status_garch"]
        cap    = st.session_state["capital"]

        lucro       = res.lucro_liquido
        drawdown    = float(df_bt["Drawdown"].min())
        trades_df   = pd.DataFrame(res.trades) if res.trades else pd.DataFrame()
        mfe_m = float(trades_df["mfe"].mean()) if not trades_df.empty else 0
        mae_m = float(trades_df["mae"].mean()) if not trades_df.empty else 0

        cor_lucro   = "green" if lucro >= 0 else "red"
        cor_status  = "green" if status == "ATIVO" else "red"

        # Cards de métricas
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Total de Trades", res.total_trades)
        with c2:
            st.metric("Win Rate", f"{res.win_rate:.1f}%")
        with c3:
            st.metric("Lucro Líquido", f"$ {lucro:+.2f}",
                      delta=f"{lucro/cap*100:+.1f}%" if cap else None)
        with c4:
            st.metric("Drawdown Máx.", f"$ {drawdown:.2f}")

        st.divider()

        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("🌡️ GARCH – Clima de Mercado")
            badge = "🟢 ATIVO" if status == "ATIVO" else "🔴 STANDBY"
            st.markdown(f"**Status:** {badge}")
            st.metric("Volatilidade prevista", f"{vol:.4f}%")

        with col_b:
            st.subheader("📡 Telemetria MFE / MAE")
            st.metric("MFE médio (potencial)", f"{mfe_m:.1f} pips")
            st.metric("MAE médio (susto)",     f"{mae_m:.1f} pips")

        if not trades_df.empty:
            st.divider()
            st.subheader("📋 Detalhamento dos Trades")

            col_p, col_l = st.columns(2)
            with col_p:
                st.metric("Mão Pesada (0.10)",
                          len(trades_df[trades_df["lote"] == lote_pesado]),
                          delta=f"$ {trades_df[trades_df['lote'] == lote_pesado]['lucro'].sum():.2f}")
            with col_l:
                st.metric("Mão Leve (0.05)",
                          len(trades_df[trades_df["lote"] == lote_leve]),
                          delta=f"$ {trades_df[trades_df['lote'] == lote_leve]['lucro'].sum():.2f}")

# ── Tab: Gráficos ─────────────────────────────────────────────────────────────
with tab_graficos:
    if "df_bt" not in st.session_state:
        st.info("Rode o backtest primeiro.")
    else:
        df_bt      = st.session_state["df_bt"]
        res        = st.session_state["resultado"]
        ticker_sel = st.session_state["ticker"]
        trades_df  = pd.DataFrame(res.trades) if res.trades else pd.DataFrame()

        plt.style.use("dark_background")

        # Gráfico 1 – Equity Curve
        fig1, ax = plt.subplots(figsize=(14, 4))
        ax.plot(df_bt.index, df_bt["Equity_Curve"], color="#a855f7", linewidth=2)
        ax.axhline(st.session_state["capital"], color="#6b7280", linestyle="--", linewidth=1)
        ax.fill_between(df_bt.index, df_bt["Equity_Curve"],
                        st.session_state["capital"],
                        where=df_bt["Equity_Curve"] >= st.session_state["capital"],
                        alpha=0.15, color="#22c55e")
        ax.fill_between(df_bt.index, df_bt["Equity_Curve"],
                        st.session_state["capital"],
                        where=df_bt["Equity_Curve"] < st.session_state["capital"],
                        alpha=0.15, color="#ef4444")
        ax.set_title(f"Curva de Patrimônio – {ticker_sel}", fontweight="bold")
        ax.set_ylabel("Saldo (USD)")
        ax.grid(alpha=0.2)
        st.pyplot(fig1)
        plt.close(fig1)

        # Gráfico 2 – Drawdown
        fig2, ax = plt.subplots(figsize=(14, 3))
        ax.fill_between(df_bt.index, df_bt["Drawdown"], 0, color="#ef4444", alpha=0.5)
        ax.set_title("Drawdown", fontweight="bold")
        ax.set_ylabel("USD")
        ax.grid(alpha=0.2)
        st.pyplot(fig2)
        plt.close(fig2)

        # Gráfico 3 – GARCH + preço (últimos 60 dias)
        col1, col2 = st.columns(2)

        with col1:
            fig3, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6),
                                             gridspec_kw={"height_ratios": [3, 1]}, sharex=True)
            recente = df_bt.tail(720)
            ax1.plot(recente.index, recente["Close"],   color="#e2e8f0", linewidth=1, label="Preço")
            ax1.plot(recente.index, recente["EMA_9"],   color="#f97316", linewidth=1, label="EMA 9")
            ax1.plot(recente.index, recente["SMA_200"], color="#3b82f6", linewidth=1.5, label="SMA 200")
            ax1.set_title(f"{ticker_sel} – Últimas 30 dias (H1)", fontweight="bold")
            ax1.legend(fontsize=8)
            ax1.grid(alpha=0.2)
            ax2.plot(recente.index, recente["ADX_14"], color="#a855f7", linewidth=1)
            ax2.axhline(25, color="#ef4444", linestyle="--", alpha=0.7)
            ax2.set_ylabel("ADX")
            ax2.grid(alpha=0.2)
            plt.tight_layout()
            st.pyplot(fig3)
            plt.close(fig3)

        with col2:
            if not trades_df.empty:
                fig4, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 6))
                ax1.hist(trades_df["lucro"], bins=25, color="#7c3aed", edgecolor="#1e1e2e")
                ax1.axvline(0, color="#ef4444", linestyle="--", linewidth=2)
                ax1.set_title("Distribuição de Resultados (USD)", fontweight="bold")
                ax1.set_xlabel("Resultado ($)")
                ax1.grid(alpha=0.2)

                sc = ax2.scatter(trades_df["mae"], trades_df["mfe"],
                                 c=trades_df["lucro"], cmap="RdYlGn", alpha=0.7, s=60)
                ax2.axhline(alvo_pips, color="#3b82f6", linestyle=":", label=f"Alvo ({alvo_pips}p)")
                ax2.axvline(stop_pips, color="#f97316", linestyle=":", label=f"Stop ({stop_pips}p)")
                ax2.set_title("MFE vs MAE", fontweight="bold")
                ax2.set_xlabel("MAE (pips)")
                ax2.set_ylabel("MFE (pips)")
                ax2.legend(fontsize=8)
                ax2.grid(alpha=0.2)
                plt.colorbar(sc, ax=ax2, label="Lucro ($)")
                plt.tight_layout()
                st.pyplot(fig4)
                plt.close(fig4)

        # Z-Score
        fig5, ax = plt.subplots(figsize=(14, 3))
        ax.plot(df_bt.tail(200).index, df_bt.tail(200)["Z_Score"], color="#a855f7", linewidth=1)
        ax.axhline(gatilho_z,  color="#ef4444", linestyle="--", label=f"Venda (+{gatilho_z})")
        ax.axhline(-gatilho_z, color="#22c55e", linestyle="--", label=f"Compra (-{gatilho_z})")
        ax.axhline(0, color="#6b7280", linewidth=0.5)
        ax.set_title("Z-Score (últimas 200 barras)", fontweight="bold")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.2)
        st.pyplot(fig5)
        plt.close(fig5)

# ── Tab: Histórico ────────────────────────────────────────────────────────────
with tab_historico:
    st.subheader("🗂️ Histórico de Backtests")

    historico = listar_resultados(50)
    if not historico:
        st.info("Nenhum backtest salvo ainda.")
    else:
        for item in historico:
            cor = "🟢" if item["lucro_liquido"] >= 0 else "🔴"
            with st.expander(
                f"{cor} #{item['id']} | {item['rodado_em']} | {item['ticker']} | "
                f"Lucro: $ {item['lucro_liquido']:+.2f} | Win Rate: {item['win_rate']:.1f}%"
            ):
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Trades",    item["total_trades"])
                col2.metric("Win Rate",  f"{item['win_rate']:.1f}%")
                col3.metric("Lucro",     f"$ {item['lucro_liquido']:+.2f}")
                col4.metric("Drawdown",  f"$ {item['drawdown_maximo']:.2f}")

                col5, col6, col7 = st.columns(3)
                col5.metric("MFE médio", f"{item['mfe_medio']:.1f} pips")
                col6.metric("MAE médio", f"{item['mae_medio']:.1f} pips")
                col7.metric("GARCH",     item["status_garch"])

                params = json.loads(item["parametros"])
                st.json(params)

                if st.button(f"🗑️ Deletar #{item['id']}", key=f"del_{item['id']}"):
                    deletar_resultado(item["id"])
                    st.rerun()
