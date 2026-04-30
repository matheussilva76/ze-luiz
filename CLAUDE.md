# CLAUDE.md — Projeto Zé Luiz

## Visão Geral

Bot de backtest forex com interface Streamlit. Estratégia de **reversão à média intraday** usando Z-Score como gatilho principal. Não executa ordens reais — apenas simulação histórica com parâmetros ajustáveis via UI.

---

## Estrutura do Projeto

```
ze-luiz/
├── app.py              # Interface Streamlit (dashboard principal)
├── database.py         # Persistência SQLite dos resultados
├── requirements.txt
├── Dockerfile
├── railway.toml        # Deploy via Railway PaaS (porta 8501)
└── bot/
    ├── data.py         # Coleta OHLCV via yfinance
    ├── indicators.py   # EMA, SMA, ADX, Z-Score, log-retornos
    ├── signals.py      # Geração de sinais COMPRA/VENDA/NEUTRO
    ├── garch.py        # Filtro de volatilidade GARCH(1,1)
    └── backtest.py     # Motor de simulação com gestão de risco
```

---

## Pipeline de Dados

```
yfinance (1h, 730 dias) → calcular_indicadores() → gerar_sinais() → rodar_garch() → rodar_backtest()
```

---

## Pares Suportados

| Par | pip_size | valor_pip |
|-----|----------|-----------|
| EURUSD, GBPUSD, AUDUSD, NZDUSD, USDCHF | 0.0001 | $10.00 |
| USDJPY | 0.01 | $6.50 |

---

## Indicadores (`bot/indicators.py`)

- `EMA_9` — EMA de 9 períodos
- `SMA_20` — SMA de 20 períodos (referência do Z-Score)
- `SMA_200` — SMA de 200 períodos (filtro de tendência estrutural)
- `ADX_14` — pandas-ta, mede força da tendência
- `Z_Score` — `(Close - SMA_20) / StdDev_20`
- `Retorno_Bruto` — log-retorno percentual
- `Retorno_Ajustado` — igual ao Bruto (gap overnight ainda não implementado)

---

## Lógica de Sinais (`bot/signals.py`)

Todos os filtros devem ser verdadeiros simultaneamente:

**COMPRA:**
- Z_Score ≤ −gatilho_z (default: −2.0)
- Hora dentro da janela `[hora_inicio, hora_fim]` (default: 4–13 UTC)
- `SMA_200_Slope` ≤ limite_inclinacao (default: 0.00040) — SMA 200 plana
- `ADX_14` < limite_adx (default: 25) — sem tendência forte

**VENDA:** espelhado com Z_Score ≥ +gatilho_z

---

## Gestão de Risco (`bot/backtest.py`)

### ConfigBacktest (defaults)

| Parâmetro | Default | Descrição |
|-----------|---------|-----------|
| `capital_inicial` | $1.000 | Capital de simulação |
| `spread_pips` | 1.5 | Custo de transação por trade |
| `lote_pesado` | 0.10 | Lote alinhado à tendência (SMA_200) |
| `lote_leve` | 0.05 | Lote contra-tendência |
| `alvo_pips` | 55 | Take-profit |
| `stop_pips` | 40 | Stop-loss inicial |
| `max_perdas_diarias` | 2 | Limite de stops por dia |

### Trailing Stop Escalonado

| Nível | Trigger | Novo Stop |
|-------|---------|-----------|
| 1 | +30 pips favor | Entrada − 10 pips |
| 2 | +45 pips favor | Entrada + 5 pips |

### Position Sizing por Contexto

- `lote_pesado` quando trade alinhado à SMA_200 (BUY acima / SELL abaixo)
- `lote_leve` quando contra a SMA_200

---

## Filtro GARCH (`bot/garch.py`)

- Modelo: GARCH(1,1) via biblioteca `arch`
- Input: `Retorno_Ajustado`
- Output: volatilidade condicional prevista (1 barra à frente)
- Gate: `vol_prevista ≤ limite_volatilidade` → status `ATIVO` ou `STANDBY`
- Default threshold: 8%

---

## Métricas de Resultado

Calculadas em `ResultadoBacktest`:

- `total_trades` — trades fechados (lucro ≠ 0)
- `win_rate` — % de trades positivos
- `lucro_liquido` — saldo_final − capital_inicial
- `drawdown_maximo` — pior queda da curva de equity (USD)
- `mfe_medio` — média do Maximum Favorable Excursion (pips)
- `mae_medio` — média do Maximum Adverse Excursion (pips)

**Métricas ausentes:** Sharpe Ratio, Sortino, Profit Factor, Calmar Ratio — ver `request_feature.md`.

---

## Persistência (`database.py`)

SQLite em `ze_luiz_resultados.db`. Armazena todos os backtests com parâmetros completos e resultados para comparação histórica.

---

## Interface (`app.py`)

Framework: Streamlit. Três abas:
1. **Resultado** — métricas, status GARCH, MFE/MAE
2. **Gráficos** — equity curve, drawdown, preço + indicadores, Z-Score, distribuição de trades
3. **Histórico** — tabela de todos os backtests salvos no SQLite

Todos os parâmetros de `ConfigBacktest` e `gerar_sinais()` são ajustáveis via sidebar.

---

## Deploy

- Docker + Railway PaaS
- Porta: 8501
- Streamlit em modo headless (`--server.headless true`)

---

## Convenções do Projeto

- Idioma do código: português (variáveis, funções, colunas de DataFrame)
- Idioma dos comentários e documentação: português
- Dados sempre em DataFrame pandas indexado por timestamp (UTC)
- Funções puras — cada módulo recebe e retorna DataFrame sem efeitos colaterais
- Não há execução de ordens reais; todo output é simulação
