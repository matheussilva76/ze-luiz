import warnings
warnings.filterwarnings("ignore")

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json

from bot.data import baixar_dados
from bot.indicators import calcular_indicadores
from bot.garch import rodar_garch
from bot.signals import gerar_sinais
from bot.backtest import rodar_backtest, ConfigBacktest
from database import inicializar_db, salvar_resultado, listar_resultados, deletar_resultado

inicializar_db()

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ZÉ LUIZ | QUANT TERMINAL",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Palette ───────────────────────────────────────────────────────────────────
BG      = "#0d1117"
SURF    = "#161b22"
BORDER  = "#21262d"
BORDER2 = "#30363d"
TEXT    = "#e6edf3"
MUTED   = "#8b949e"
GREEN   = "#3fb950"
RED     = "#f85149"
BLUE    = "#58a6ff"
PURPLE  = "#bc8cff"
YELLOW  = "#d29922"
ORANGE  = "#e3b341"

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&display=swap');

.stApp {{background:{BG};font-family:'JetBrains Mono','Courier New',monospace;}}
#MainMenu,footer,header{{visibility:hidden;}}
.main .block-container{{padding:1.2rem 1.8rem;max-width:100%;}}

/* ── Header ── */
.qt-hdr{{
    display:flex;align-items:center;justify-content:space-between;
    background:{SURF};border:1px solid {BORDER};border-top:3px solid {PURPLE};
    border-radius:0 0 12px 12px;padding:14px 24px;margin-bottom:22px;
}}
.qt-brand{{font-size:1.05rem;font-weight:700;color:{TEXT};letter-spacing:.15em;text-transform:uppercase;}}
.qt-brand em{{color:{PURPLE};font-style:normal;}}
.qt-sub{{font-size:.58rem;color:{MUTED};letter-spacing:.2em;text-transform:uppercase;margin-top:3px;}}
.qt-meta{{display:flex;gap:28px;align-items:center;}}
.qt-item{{text-align:right;}}
.qt-lbl{{font-size:.55rem;color:{MUTED};text-transform:uppercase;letter-spacing:.12em;}}
.qt-val{{font-size:.9rem;font-weight:600;color:{TEXT};}}

/* ── Badges ── */
.bdg{{display:inline-block;padding:2px 10px;border-radius:20px;font-size:.6rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;}}
.bdg-g{{background:rgba(63,185,80,.12);border:1px solid {GREEN};color:{GREEN};}}
.bdg-r{{background:rgba(248,81,73,.12);border:1px solid {RED};color:{RED};}}
.bdg-y{{background:rgba(210,153,34,.12);border:1px solid {YELLOW};color:{YELLOW};}}
.bdg-b{{background:rgba(88,166,255,.12);border:1px solid {BLUE};color:{BLUE};}}
.bdg-p{{background:rgba(188,140,255,.12);border:1px solid {PURPLE};color:{PURPLE};}}

/* ── KPI Cards ── */
.kpi{{background:{SURF};border:1px solid {BORDER};border-radius:8px;padding:14px 16px;position:relative;overflow:hidden;height:100%;}}
.kpi::before{{content:'';position:absolute;top:0;left:0;right:0;height:2px;}}
.kpi.g::before{{background:{GREEN};}}
.kpi.r::before{{background:{RED};}}
.kpi.b::before{{background:{BLUE};}}
.kpi.p::before{{background:{PURPLE};}}
.kpi.y::before{{background:{YELLOW};}}
.kpi.o::before{{background:{ORANGE};}}
.kpi-lbl{{font-size:.56rem;color:{MUTED};text-transform:uppercase;letter-spacing:.15em;margin-bottom:8px;}}
.kpi-val{{font-size:1.3rem;font-weight:700;color:{TEXT};line-height:1.1;}}
.kpi-val.pos{{color:{GREEN};}}
.kpi-val.neg{{color:{RED};}}
.kpi-sub{{font-size:.65rem;color:{MUTED};margin-top:5px;}}

/* ── Section label ── */
.sec{{font-size:.56rem;color:{MUTED};text-transform:uppercase;letter-spacing:.2em;
    border-left:3px solid {PURPLE};padding-left:10px;margin:20px 0 12px 0;}}

/* ── Sidebar ── */
section[data-testid="stSidebar"]{{background:{SURF}!important;border-right:1px solid {BORDER}!important;}}
div[data-testid="stSidebar"] label{{color:{MUTED}!important;font-size:.63rem!important;text-transform:uppercase!important;letter-spacing:.1em!important;}}
div[data-testid="stSidebar"] .stMarkdown p{{color:{MUTED};font-size:.6rem;text-transform:uppercase;letter-spacing:.12em;}}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"]{{background:{SURF};border:1px solid {BORDER};border-radius:8px;padding:4px;gap:2px;}}
.stTabs [data-baseweb="tab"]{{background:transparent;color:{MUTED};font-size:.63rem;text-transform:uppercase;letter-spacing:.12em;border-radius:6px;padding:8px 20px;font-family:'JetBrains Mono',monospace;}}
.stTabs [aria-selected="true"]{{background:{BG}!important;color:{TEXT}!important;border-bottom:2px solid {PURPLE}!important;}}

/* ── Button ── */
.stButton>button{{background:{SURF};border:1px solid {GREEN};color:{GREEN};
    font-family:'JetBrains Mono',monospace;font-weight:700;font-size:.7rem;
    text-transform:uppercase;letter-spacing:.15em;border-radius:6px;transition:all .2s;padding:10px;}}
.stButton>button:hover{{background:rgba(63,185,80,.08);box-shadow:0 0 12px rgba(63,185,80,.2);}}

/* ── Misc ── */
hr{{border-color:{BORDER}!important;margin:12px 0!important;}}
div[data-testid="stExpander"]{{background:{SURF};border:1px solid {BORDER}!important;border-radius:8px;}}
div[data-testid="stExpander"] summary{{color:{MUTED};font-size:.72rem;text-transform:uppercase;letter-spacing:.08em;}}
.stAlert{{background:{SURF}!important;border:1px solid {BORDER}!important;color:{TEXT}!important;}}
.stSpinner>div{{border-top-color:{PURPLE}!important;}}
</style>
""", unsafe_allow_html=True)


# ── Plotly layout helper ──────────────────────────────────────────────────────
def _layout(title="", h=None, **kw):
    axis = dict(gridcolor=BORDER, linecolor=BORDER2, showgrid=True,
                zeroline=False, tickfont=dict(size=9))
    d = dict(
        paper_bgcolor=BG, plot_bgcolor=BG,
        font=dict(color=MUTED, family="JetBrains Mono, Courier New", size=10),
        margin=dict(l=0, r=8, t=36 if title else 18, b=0),
        xaxis={**axis}, yaxis={**axis},
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=BORDER,
                    borderwidth=1, font=dict(size=9), orientation="h",
                    yanchor="bottom", y=1.02, xanchor="left", x=0),
        hoverlabel=dict(bgcolor=SURF, bordercolor=BORDER,
                        font_color=TEXT, font_family="JetBrains Mono"),
    )
    if title:
        d["title"] = dict(
            text=f"<span style='color:{MUTED};font-size:9px;text-transform:uppercase;"
                 f"letter-spacing:2px'>{title}</span>",
            x=0, xref="paper", pad=dict(l=4),
        )
    if h:
        d["height"] = h
    d.update(kw)
    return d


_CFG = {"displayModeBar": False, "responsive": True}


def kpi_html(label, value, color="b", sub="", pos=None):
    val_cls = " pos" if pos is True else (" neg" if pos is False else "")
    sub_html = f"<div class='kpi-sub'>{sub}</div>" if sub else ""
    return (f"<div class='kpi {color}'>"
            f"<div class='kpi-lbl'>{label}</div>"
            f"<div class='kpi-val{val_cls}'>{value}</div>"
            f"{sub_html}</div>")


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"<div style='font-size:.68rem;color:{PURPLE};text-transform:uppercase;"
                f"letter-spacing:.15em;font-weight:700;padding:8px 0 14px;'>⚙ Parâmetros</div>",
                unsafe_allow_html=True)

    st.markdown(f"<p>Instrumento</p>", unsafe_allow_html=True)
    ticker = st.selectbox(
        "Par", ["AUDUSD=X", "EURUSD=X", "GBPUSD=X", "NZDUSD=X", "USDJPY=X", "USDCHF=X"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown(f"<p>Janela Operacional (UTC)</p>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    hora_inicio = c1.number_input("Início", 0, 23, 4, label_visibility="visible")
    hora_fim    = c2.number_input("Fim",    0, 23, 13, label_visibility="visible")

    st.markdown("---")
    st.markdown(f"<p>Sinais</p>", unsafe_allow_html=True)
    gatilho_z         = st.slider("Gatilho Z-Score", 0.5, 4.0, 2.0, 0.1)
    limite_adx        = st.slider("Limite ADX", 10, 50, 25)
    limite_inclinacao = st.number_input("Slope SMA-200", value=0.00040,
                                        format="%.5f", step=0.00005)

    st.markdown("---")
    st.markdown(f"<p>GARCH Volatility Gate</p>", unsafe_allow_html=True)
    limite_vol = st.slider("Limite Vol (%)", 0.01, 0.30, 0.08, 0.01)

    st.markdown("---")
    st.markdown(f"<p>Risk Management</p>", unsafe_allow_html=True)
    capital     = st.number_input("Capital (USD)", value=1000.0, step=100.0)
    c1, c2      = st.columns(2)
    alvo_pips   = c1.slider("Alvo pips", 10, 150, 55)
    stop_pips   = c2.slider("Stop pips", 10, 150, 40)
    c1, c2      = st.columns(2)
    lote_pesado = c1.number_input("Lote pesado", value=0.10, step=0.01, format="%.2f")
    lote_leve   = c2.number_input("Lote leve",   value=0.05, step=0.01, format="%.2f")
    spread_pips = st.number_input("Spread (pips)", value=1.5, step=0.1, format="%.1f")
    max_perdas  = st.slider("Max perdas / dia", 1, 10, 2)

    st.markdown("---")
    rodar = st.button("▶  EXECUTAR BACKTEST", use_container_width=True)


# ── Backtest execution ────────────────────────────────────────────────────────
if rodar:
    with st.spinner("Baixando dados e executando modelo..."):
        try:
            df = baixar_dados(ticker)
            pip_size  = df.attrs["pip_size"]
            valor_pip = df.attrs["valor_pip"]
            df = calcular_indicadores(df)
            df, vol_prevista, status_garch = rodar_garch(df, limite_vol)
            df = gerar_sinais(df, hora_inicio, hora_fim, gatilho_z,
                              limite_inclinacao, limite_adx)
            cfg = ConfigBacktest(
                capital_inicial=capital, valor_pip_padrao=valor_pip,
                pip_size=pip_size, spread_pips=spread_pips,
                lote_pesado=lote_pesado, lote_leve=lote_leve,
                alvo_pips=alvo_pips, stop_pips=stop_pips,
                max_perdas_diarias=max_perdas,
            )
            df_bt_new, resultado = rodar_backtest(df, cfg)

            st.session_state.update({
                "df_bt": df_bt_new, "resultado": resultado,
                "vol_prevista": vol_prevista, "status_garch": status_garch,
                "ticker": ticker, "capital": capital,
                "alvo_pips": alvo_pips, "stop_pips": stop_pips,
                "lote_pesado": lote_pesado, "lote_leve": lote_leve,
                "gatilho_z": gatilho_z,
            })

            trades_df = pd.DataFrame(resultado.trades) if resultado.trades else pd.DataFrame()
            salvar_resultado(
                ticker=ticker,
                parametros={
                    "hora_inicio": hora_inicio, "hora_fim": hora_fim,
                    "gatilho_z": gatilho_z, "limite_adx": limite_adx,
                    "limite_inclinacao": limite_inclinacao, "limite_vol": limite_vol,
                    "capital": capital, "alvo_pips": alvo_pips, "stop_pips": stop_pips,
                    "lote_pesado": lote_pesado, "lote_leve": lote_leve,
                    "spread_pips": spread_pips, "max_perdas": max_perdas,
                },
                total_trades=resultado.total_trades,
                win_rate=resultado.win_rate,
                lucro_liquido=resultado.lucro_liquido,
                drawdown_maximo=float(df_bt_new["Drawdown"].min()),
                mfe_medio=float(trades_df["mfe"].mean()) if not trades_df.empty else 0,
                mae_medio=float(trades_df["mae"].mean()) if not trades_df.empty else 0,
                vol_prevista=vol_prevista,
                status_garch=status_garch,
            )
            st.rerun()
        except Exception as e:
            st.error(f"❌  {e}")
            st.stop()


# ── Read session state ────────────────────────────────────────────────────────
res        = st.session_state.get("resultado")
df_bt      = st.session_state.get("df_bt")
vol_prev   = st.session_state.get("vol_prevista", 0.0)
status_g   = st.session_state.get("status_garch", "—")
ticker_sel = st.session_state.get("ticker", ticker)
cap_sel    = st.session_state.get("capital", capital)
gz_sel     = st.session_state.get("gatilho_z", gatilho_z)
alvo_sel   = st.session_state.get("alvo_pips", alvo_pips)
stop_sel   = st.session_state.get("stop_pips", stop_pips)
lp_sel     = st.session_state.get("lote_pesado", lote_pesado)
ll_sel     = st.session_state.get("lote_leve", lote_leve)

garch_badge = (
    f'<span class="bdg bdg-g">● ATIVO</span>'    if status_g == "ATIVO"    else
    f'<span class="bdg bdg-r">● STANDBY</span>'  if status_g == "STANDBY"  else
    f'<span class="bdg bdg-y">— AGUARDANDO</span>'
)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="qt-hdr">
  <div>
    <div class="qt-brand"><em>ZÉ LUIZ</em> · QUANT TERMINAL</div>
    <div class="qt-sub">Mean Reversion &nbsp;·&nbsp; Z-Score + ADX + GARCH &nbsp;·&nbsp; Forex Intraday H1 &nbsp;·&nbsp; v7.0</div>
  </div>
  <div class="qt-meta">
    <div class="qt-item">
      <div class="qt-lbl">Instrumento</div>
      <div class="qt-val">{ticker_sel.replace('=X','')}</div>
    </div>
    <div class="qt-item">
      <div class="qt-lbl">GARCH</div>
      <div class="qt-val">{garch_badge}</div>
    </div>
    <div class="qt-item">
      <div class="qt-lbl">Vol. Prevista</div>
      <div class="qt-val">{'%.4f%%' % vol_prev if vol_prev else '—'}</div>
    </div>
    <div class="qt-item">
      <div class="qt-lbl">Capital</div>
      <div class="qt-val">$ {cap_sel:,.0f}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_painel, tab_graficos, tab_historico = st.tabs(
    ["  PAINEL  ", "  GRÁFICOS  ", "  HISTÓRICO  "]
)

# ═════════════════════════════════════════════════════════════════════════════
# TAB 1 — PAINEL
# ═════════════════════════════════════════════════════════════════════════════
with tab_painel:
    if not res:
        st.markdown(f"""
        <div style="text-align:center;padding:100px 0;">
          <div style="font-size:3rem;color:{BORDER2};margin-bottom:18px;">◈</div>
          <div style="font-size:.7rem;color:{MUTED};text-transform:uppercase;letter-spacing:.25em;">
            Configure os parâmetros e execute o backtest
          </div>
        </div>""", unsafe_allow_html=True)
    else:
        lucro     = res.lucro_liquido
        drawdown  = float(df_bt["Drawdown"].min())
        trades_df = pd.DataFrame(res.trades) if res.trades else pd.DataFrame()
        mfe_m     = float(trades_df["mfe"].mean()) if not trades_df.empty else 0
        mae_m     = float(trades_df["mae"].mean()) if not trades_df.empty else 0

        # ── KPI row ───────────────────────────────────────────────────────────
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.markdown(kpi_html("Total Trades", res.total_trades, "b"), unsafe_allow_html=True)
        c2.markdown(kpi_html("Win Rate", f"{res.win_rate:.1f}%",
                             "g" if res.win_rate >= 50 else "r",
                             pos=res.win_rate >= 50), unsafe_allow_html=True)
        c3.markdown(kpi_html("Lucro Líquido",
                             f"{'+'if lucro>=0 else''}${lucro:,.2f}",
                             "g" if lucro >= 0 else "r",
                             sub=f"{lucro/cap_sel*100:+.1f}% do capital",
                             pos=lucro >= 0), unsafe_allow_html=True)
        c4.markdown(kpi_html("Drawdown Máx.", f"${drawdown:,.2f}", "r",
                             sub=f"{abs(drawdown)/cap_sel*100:.1f}% do capital",
                             pos=False), unsafe_allow_html=True)
        c5.markdown(kpi_html("MFE Médio", f"{mfe_m:.1f} pips", "g",
                             sub="potencial por trade", pos=True), unsafe_allow_html=True)
        c6.markdown(kpi_html("MAE Médio", f"{mae_m:.1f} pips", "y",
                             sub="exposição adversa"), unsafe_allow_html=True)

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        # ── Equity + Drawdown chart ───────────────────────────────────────────
        st.markdown('<div class="sec">Curva de Patrimônio & Drawdown</div>',
                    unsafe_allow_html=True)

        fig_eq = make_subplots(
            rows=2, cols=1, shared_xaxes=True,
            row_heights=[0.70, 0.30], vertical_spacing=0.02,
        )
        axis_style = dict(gridcolor=BORDER, linecolor=BORDER2,
                          showgrid=True, zeroline=False, tickfont=dict(size=9))

        # Baseline
        base = [cap_sel] * len(df_bt)
        fig_eq.add_trace(go.Scatter(
            x=df_bt.index, y=base,
            line=dict(width=0), showlegend=False, hoverinfo="skip",
        ), row=1, col=1)
        # Green fill (above baseline)
        fig_eq.add_trace(go.Scatter(
            x=df_bt.index, y=df_bt["Equity_Curve"].clip(lower=cap_sel),
            fill="tonexty", fillcolor="rgba(63,185,80,0.08)",
            line=dict(width=0), showlegend=False, hoverinfo="skip",
        ), row=1, col=1)
        # Red fill (below baseline)
        fig_eq.add_trace(go.Scatter(
            x=df_bt.index, y=base,
            line=dict(width=0), showlegend=False, hoverinfo="skip",
        ), row=1, col=1)
        fig_eq.add_trace(go.Scatter(
            x=df_bt.index, y=df_bt["Equity_Curve"].clip(upper=cap_sel),
            fill="tonexty", fillcolor="rgba(248,81,73,0.08)",
            line=dict(width=0), showlegend=False, hoverinfo="skip",
        ), row=1, col=1)
        # Equity line
        fig_eq.add_trace(go.Scatter(
            x=df_bt.index, y=df_bt["Equity_Curve"],
            name="Equity", line=dict(color=PURPLE, width=2),
            hovertemplate="<b>%{x|%d/%m %H:%M}</b><br>Saldo: $%{y:,.2f}<extra></extra>",
        ), row=1, col=1)
        # Baseline dashed
        fig_eq.add_hline(y=cap_sel, line=dict(color=MUTED, width=1, dash="dash"),
                         row=1, col=1)

        # Drawdown
        fig_eq.add_trace(go.Scatter(
            x=df_bt.index, y=df_bt["Drawdown"],
            name="Drawdown", line=dict(color=RED, width=1),
            fill="tozeroy", fillcolor="rgba(248,81,73,0.12)",
            hovertemplate="<b>%{x|%d/%m %H:%M}</b><br>DD: $%{y:,.2f}<extra></extra>",
        ), row=2, col=1)

        fig_eq.update_layout(**_layout(h=460,
            xaxis2={**axis_style}, yaxis2={**axis_style},
        ))
        fig_eq.update_yaxes(tickprefix="$", tickformat=",.0f", row=1, col=1)
        fig_eq.update_yaxes(tickprefix="$", tickformat=",.2f", row=2, col=1)
        st.plotly_chart(fig_eq, use_container_width=True, config=_CFG)

        # ── Trade charts ──────────────────────────────────────────────────────
        if not trades_df.empty:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown('<div class="sec">P&L por Trade</div>',
                            unsafe_allow_html=True)
                colors = [GREEN if l > 0 else RED for l in trades_df["lucro"]]
                fig_bar = go.Figure(go.Bar(
                    x=list(range(1, len(trades_df) + 1)),
                    y=trades_df["lucro"],
                    marker_color=colors,
                    marker_line_width=0,
                    hovertemplate="Trade %{x}<br>P&L: $%{y:,.2f}<extra></extra>",
                ))
                fig_bar.add_hline(y=0, line=dict(color=MUTED, width=1))
                fig_bar.update_layout(**_layout("Resultado Individual por Trade", h=300))
                fig_bar.update_yaxes(tickprefix="$")
                fig_bar.update_xaxes(title_text="Nº do Trade", title_font=dict(size=9))
                st.plotly_chart(fig_bar, use_container_width=True, config=_CFG)

            with col2:
                st.markdown('<div class="sec">MFE vs MAE — Qualidade dos Trades</div>',
                            unsafe_allow_html=True)
                colors_s = [GREEN if l > 0 else RED for l in trades_df["lucro"]]
                fig_sc = go.Figure()
                fig_sc.add_trace(go.Scatter(
                    x=trades_df["mae"], y=trades_df["mfe"],
                    mode="markers",
                    marker=dict(color=colors_s, size=7, opacity=0.8,
                                line=dict(color=BORDER, width=1)),
                    hovertemplate="MAE: %{x:.1f}p<br>MFE: %{y:.1f}p<extra></extra>",
                ))
                fig_sc.add_hline(y=alvo_sel,
                                 line=dict(color=BLUE, width=1, dash="dot"),
                                 annotation_text=f"Alvo {alvo_sel}p",
                                 annotation_font_color=BLUE,
                                 annotation_font_size=9)
                fig_sc.add_vline(x=stop_sel,
                                 line=dict(color=ORANGE, width=1, dash="dot"),
                                 annotation_text=f"Stop {stop_sel}p",
                                 annotation_font_color=ORANGE,
                                 annotation_font_size=9)
                fig_sc.update_layout(**_layout("MFE vs MAE", h=300))
                fig_sc.update_xaxes(title_text="MAE (pips adversos)", title_font=dict(size=9))
                fig_sc.update_yaxes(title_text="MFE (pips favoráveis)", title_font=dict(size=9))
                st.plotly_chart(fig_sc, use_container_width=True, config=_CFG)

            # ── Lot breakdown ─────────────────────────────────────────────────
            st.markdown('<div class="sec">Performance por Lote</div>',
                        unsafe_allow_html=True)
            hv = trades_df[trades_df["lote"] == lp_sel]
            lv = trades_df[trades_df["lote"] == ll_sel]
            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(kpi_html("Lote Pesado · Trades", len(hv), "p"),
                        unsafe_allow_html=True)
            c2.markdown(kpi_html("Lote Pesado · P&L",
                                 f"${hv['lucro'].sum():+,.2f}", "p",
                                 pos=hv["lucro"].sum() >= 0), unsafe_allow_html=True)
            c3.markdown(kpi_html("Lote Leve · Trades", len(lv), "b"),
                        unsafe_allow_html=True)
            c4.markdown(kpi_html("Lote Leve · P&L",
                                 f"${lv['lucro'].sum():+,.2f}", "b",
                                 pos=lv["lucro"].sum() >= 0), unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# TAB 2 — GRÁFICOS
# ═════════════════════════════════════════════════════════════════════════════
with tab_graficos:
    if not res:
        st.markdown(f"""
        <div style="text-align:center;padding:100px 0;">
          <div style="font-size:.7rem;color:{MUTED};text-transform:uppercase;letter-spacing:.25em;">
            Execute o backtest para visualizar os gráficos
          </div>
        </div>""", unsafe_allow_html=True)
    else:
        recente = df_bt.tail(720)
        tck     = ticker_sel.replace("=X", "")
        axis_style = dict(gridcolor=BORDER, linecolor=BORDER2,
                          showgrid=True, zeroline=False, tickfont=dict(size=9))

        # ── Price + ADX ───────────────────────────────────────────────────────
        st.markdown('<div class="sec">Preço & Indicadores — Últimas 720 Barras (H1)</div>',
                    unsafe_allow_html=True)

        fig_px = make_subplots(
            rows=2, cols=1, shared_xaxes=True,
            row_heights=[0.72, 0.28], vertical_spacing=0.02,
        )
        fig_px.add_trace(go.Scatter(
            x=recente.index, y=recente["Close"],
            name="Close", line=dict(color=TEXT, width=1.2),
            hovertemplate="%{x|%d/%m %H:%M} — %{y:.5f}<extra></extra>",
        ), row=1, col=1)
        fig_px.add_trace(go.Scatter(
            x=recente.index, y=recente["EMA_9"],
            name="EMA 9", line=dict(color=ORANGE, width=1, dash="dot"),
            hovertemplate="EMA9: %{y:.5f}<extra></extra>",
        ), row=1, col=1)
        fig_px.add_trace(go.Scatter(
            x=recente.index, y=recente["SMA_200"],
            name="SMA 200", line=dict(color=BLUE, width=1.5),
            hovertemplate="SMA200: %{y:.5f}<extra></extra>",
        ), row=1, col=1)

        # Entry markers
        if "Sinal_Ze" in recente.columns:
            compras = recente[recente["Sinal_Ze"] == "COMPRA"]
            vendas  = recente[recente["Sinal_Ze"] == "VENDA"]
            if not compras.empty:
                fig_px.add_trace(go.Scatter(
                    x=compras.index, y=compras["Close"],
                    mode="markers", name="Compra",
                    marker=dict(symbol="triangle-up", color=GREEN, size=9,
                                line=dict(color=BG, width=1)),
                    hovertemplate="COMPRA<br>%{x|%d/%m %H:%M}<br>%{y:.5f}<extra></extra>",
                ), row=1, col=1)
            if not vendas.empty:
                fig_px.add_trace(go.Scatter(
                    x=vendas.index, y=vendas["Close"],
                    mode="markers", name="Venda",
                    marker=dict(symbol="triangle-down", color=RED, size=9,
                                line=dict(color=BG, width=1)),
                    hovertemplate="VENDA<br>%{x|%d/%m %H:%M}<br>%{y:.5f}<extra></extra>",
                ), row=1, col=1)

        # ADX
        fig_px.add_trace(go.Scatter(
            x=recente.index, y=recente["ADX_14"],
            name="ADX 14", line=dict(color=PURPLE, width=1.2),
            hovertemplate="ADX: %{y:.1f}<extra></extra>",
        ), row=2, col=1)
        fig_px.add_hline(y=25, line=dict(color=RED, width=1, dash="dash"),
                         annotation_text="ADX 25", annotation_font_color=RED,
                         annotation_font_size=8, row=2, col=1)

        fig_px.update_layout(**_layout(f"{tck} — H1", h=500,
                                       xaxis2={**axis_style},
                                       yaxis2={**axis_style}))
        fig_px.update_yaxes(tickformat=".5f", row=1, col=1)
        fig_px.update_yaxes(title_text="ADX", title_font=dict(size=8), row=2, col=1)
        st.plotly_chart(fig_px, use_container_width=True, config=_CFG)

        # ── Z-Score ───────────────────────────────────────────────────────────
        st.markdown('<div class="sec">Z-Score — Últimas 200 Barras</div>',
                    unsafe_allow_html=True)

        z200 = df_bt.tail(200)
        fig_z = go.Figure()
        fig_z.add_hrect(y0=-gz_sel, y1=gz_sel,
                        fillcolor="rgba(88,166,255,0.04)", line_width=0)
        fig_z.add_hline(y=gz_sel,
                        line=dict(color=RED, width=1.2, dash="dash"),
                        annotation_text=f"Venda ≥ +{gz_sel:.1f}σ",
                        annotation_font_color=RED, annotation_font_size=9)
        fig_z.add_hline(y=-gz_sel,
                        line=dict(color=GREEN, width=1.2, dash="dash"),
                        annotation_text=f"Compra ≤ -{gz_sel:.1f}σ",
                        annotation_font_color=GREEN, annotation_font_size=9)
        fig_z.add_hline(y=0, line=dict(color=MUTED, width=0.8))
        fig_z.add_trace(go.Scatter(
            x=z200.index, y=z200["Z_Score"],
            name="Z-Score", line=dict(color=PURPLE, width=1.5),
            fill="tozeroy", fillcolor="rgba(188,140,255,0.05)",
            hovertemplate="%{x|%d/%m %H:%M}<br>Z: %{y:.2f}σ<extra></extra>",
        ))
        fig_z.update_layout(**_layout("Z-Score (Desvios da SMA-20)", h=260))
        fig_z.update_yaxes(ticksuffix="σ")
        st.plotly_chart(fig_z, use_container_width=True, config=_CFG)


# ═════════════════════════════════════════════════════════════════════════════
# TAB 3 — HISTÓRICO
# ═════════════════════════════════════════════════════════════════════════════
with tab_historico:
    st.markdown('<div class="sec">Registro de Backtests</div>', unsafe_allow_html=True)

    historico = listar_resultados(50)
    if not historico:
        st.markdown(f"""
        <div style="text-align:center;padding:80px 0;">
          <div style="font-size:.7rem;color:{MUTED};text-transform:uppercase;letter-spacing:.25em;">
            Nenhum backtest registrado ainda
          </div>
        </div>""", unsafe_allow_html=True)
    else:
        for item in historico:
            lucro_i = item["lucro_liquido"]
            sinal   = "▲" if lucro_i >= 0 else "▼"
            with st.expander(
                f"#{item['id']:03d}  ·  {item['rodado_em']}  ·  "
                f"{item['ticker'].replace('=X','')}  ·  "
                f"P&L: {'+'if lucro_i>=0 else''}${lucro_i:,.2f}  ·  "
                f"Win: {item['win_rate']:.1f}%  ·  "
                f"GARCH: {item['status_garch']}"
            ):
                c1, c2, c3, c4 = st.columns(4)
                c1.markdown(kpi_html("Trades", item["total_trades"], "b"),
                            unsafe_allow_html=True)
                c2.markdown(kpi_html("Win Rate", f"{item['win_rate']:.1f}%",
                                     "g" if item["win_rate"] >= 50 else "r",
                                     pos=item["win_rate"] >= 50),
                            unsafe_allow_html=True)
                c3.markdown(kpi_html("Lucro Líquido",
                                     f"${'+'if lucro_i>=0 else''}{lucro_i:,.2f}",
                                     "g" if lucro_i >= 0 else "r",
                                     pos=lucro_i >= 0),
                            unsafe_allow_html=True)
                c4.markdown(kpi_html("Drawdown Máx.",
                                     f"${item['drawdown_maximo']:,.2f}", "r",
                                     pos=False),
                            unsafe_allow_html=True)

                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

                c5, c6, c7 = st.columns(3)
                c5.markdown(kpi_html("MFE Médio", f"{item['mfe_medio']:.1f}p", "g"),
                            unsafe_allow_html=True)
                c6.markdown(kpi_html("MAE Médio", f"{item['mae_medio']:.1f}p", "y"),
                            unsafe_allow_html=True)
                c7.markdown(kpi_html("GARCH Status", item["status_garch"],
                                     "g" if item["status_garch"] == "ATIVO" else "r"),
                            unsafe_allow_html=True)

                st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
                params = json.loads(item["parametros"])
                st.markdown(
                    f"<div style='font-size:.57rem;color:{MUTED};text-transform:uppercase;"
                    f"letter-spacing:.12em;margin-bottom:6px;'>Parâmetros</div>",
                    unsafe_allow_html=True,
                )
                st.json(params)

                if st.button(f"🗑 Deletar #{item['id']}", key=f"del_{item['id']}"):
                    deletar_resultado(item["id"])
                    st.rerun()
