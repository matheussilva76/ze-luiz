# Request Feature — Melhorias do Zé Luiz

Melhorias identificadas na análise econômica. Organizadas por prioridade e impacto.

---

## Prioridade Alta — Integridade do Backtest

### [RF-01] Validação Out-of-Sample (Walk-Forward)
**Problema:** O bot calibra e testa nos mesmos 730 dias, criando risco alto de overfitting.
**Solução:** Dividir o período histórico em treino (70%) e teste (30%). Implementar walk-forward rolling com janela deslizante (ex: treino 6 meses, teste 1 mês).
**Arquivos afetados:** `bot/backtest.py`, `app.py`
**Impacto:** Elimina o principal viés de avaliação de desempenho.

---

### [RF-02] Spread Variável por Hora do Dia
**Problema:** Spread fixo de 1.5 pips ignora que durante notícias (NFP, FOMC, BCE) spreads chegam a 5–15 pips, destruindo a vantagem esperada da estratégia.
**Solução:** Criar tabela de spread por faixa horária (ex: abertura asiática, europeia, notícias agendadas). Adicionar campo `spread_pips` dinâmico na `ConfigBacktest` ou como série temporal paralela.
**Arquivos afetados:** `bot/backtest.py`, `app.py`
**Impacto:** Reduz resultado otimista do backtest; aproxima simulação da realidade.

---

### [RF-03] Filtro de Calendário Econômico
**Problema:** O bot não filtra janelas de alto impacto (NFP sexta-feira, reuniões FOMC/BCE). Nesses momentos a reversão à média tem confiabilidade muito menor.
**Solução:** Integrar lista de eventos de alto impacto (pode ser CSV estático atualizado mensalmente ou API como `investpy`). Adicionar flag `filtrar_noticias: bool` na sidebar. Bloquear sinais nas 2h antes e 1h depois de cada evento.
**Arquivos afetados:** `bot/signals.py`, `app.py`, novo `bot/calendar.py`
**Impacto:** Reduz trades em condições desfavoráveis à estratégia.

---

### [RF-04] Slippage de Entrada Simulado
**Problema:** O backtest entra no `Close` da barra do sinal. Na prática, a execução ocorre na barra seguinte (Open), já com parte do movimento incorporado.
**Solução:** Adicionar parâmetro `slippage_pips` (default: 1.0). Aplicar ao preço de entrada: `preco_entrada = Open_proxima_barra ± slippage`.
**Arquivos afetados:** `bot/backtest.py`, `app.py`
**Impacto:** Reduz retornos simulados para valores mais realistas.

---

## Prioridade Média — Métricas e Análise

### [RF-05] Métricas Quantitativas Adicionais
**Problema:** As métricas atuais (win rate, lucro líquido, drawdown) são insuficientes para avaliar qualidade de uma estratégia sistematicamente.
**Solução:** Calcular e exibir na aba Resultado:

| Métrica | Fórmula | Referência |
|---------|---------|-----------|
| **Sharpe Ratio** | `(Retorno_Anual - 0.05) / Volatilidade_Anual` | > 1.0 aceitável, > 1.5 bom |
| **Sortino Ratio** | `Retorno_Anual / Downside_Deviation` | Penaliza só downside |
| **Profit Factor** | `Soma_Ganhos / Soma_Perdas` | > 1.5 robusto |
| **Calmar Ratio** | `CAGR / Max_Drawdown` | > 0.5 aceitável |
| **Max Sequência de Perdas** | Maior sequência consecutiva negativa | Risco comportamental |
| **Recovery Factor** | `Lucro_Liquido / Max_Drawdown` | > 2.0 bom |

**Arquivos afetados:** `bot/backtest.py` (`ResultadoBacktest`), `app.py`

---

### [RF-06] Position Sizing Baseado em ATR
**Problema:** Lotes fixos (0.10 / 0.05) ignoram a volatilidade do ativo. Um GBPUSD com 120 pips/dia recebe o mesmo lote que um EURUSD com 30 pips/dia — risco real muito diferente.
**Solução:** Calcular lote como `risco_por_trade_USD / (ATR_14 / pip_size * valor_pip)`. Normalizar risco em USD por trade independente do par.
**Arquivos afetados:** `bot/indicators.py` (adicionar ATR_14), `bot/backtest.py`
**Impacto:** Equaliza o risco real entre diferentes pares e regimes de volatilidade.

---

### [RF-07] Curva de Capital por Ano / Período
**Problema:** A equity curve atual é acumulada no período completo. Difícil identificar em qual ano a estratégia teve bom ou mau desempenho.
**Solução:** Adicionar breakdown anual dos resultados (retorno %, drawdown máximo, win rate, total trades) em tabela na aba Resultado ou Histórico.
**Arquivos afetados:** `app.py`

---

### [RF-08] Análise de Correlação Entre Pares
**Problema:** Rodar o bot em EURUSD e GBPUSD simultaneamente pode duplicar a exposição (alta correlação entre os pares).
**Solução:** Adicionar aba de análise multi-par com matriz de correlação de retornos e alerta quando correlação > 0.7 entre pares selecionados.
**Arquivos afetados:** `app.py`, novo `bot/correlation.py`

---

## Prioridade Baixa — Melhorias de Modelo

### [RF-09] Retorno Ajustado com Gap Overnight
**Problema:** `Retorno_Ajustado` é idêntico a `Retorno_Bruto`. Gaps de abertura de semana (eventos geopolíticos de fim de semana) não são capturados, subestimando o risco de posições abertas.
**Solução:** Detectar gaps entre sessões (diff de timestamp > 4h) e registrar em `Retorno_Overnight` separadamente. Usar retorno ajustado no GARCH.
**Arquivos afetados:** `bot/indicators.py`

---

### [RF-10] GARCH com Gate Gradual (em vez de binário)
**Problema:** O filtro GARCH é on/off num threshold fixo. Em volatilidade crescente mas ainda abaixo do limite, o risco aumenta sem ajuste de lote.
**Solução:** Em vez de bloquear completamente, reduzir o lote proporcionalmente à volatilidade prevista. Ex: `lote_final = lote_base * (1 - vol_prevista / limite_vol)`.
**Arquivos afetados:** `bot/garch.py`, `bot/backtest.py`

---

### [RF-11] Detecção de Regime de Mercado
**Problema:** A estratégia de reversão à média falha sistematicamente em regimes de tendência forte (ex: ciclo de alta do Fed 2022). O ADX filtra parcialmente, mas não detecta tendências macro de longo prazo.
**Solução:** Adicionar classificador de regime simples: calcular slope da SMA_200 em janela longa (50 períodos). Se slope > threshold configurável, classificar como "TENDÊNCIA" e reduzir tamanho de lote ou suspender sinais contra-tendência.
**Arquivos afetados:** `bot/signals.py`, `app.py`

---

### [RF-12] Critério de Kelly para Position Sizing
**Problema:** Lotes fixos não maximizam o crescimento de capital dado o win rate e o ratio risco/retorno observados.
**Solução:** Calcular Kelly Fraction = `(win_rate * alvo_pips - (1 - win_rate) * stop_pips) / alvo_pips`. Usar como multiplicador do lote base. Adicionar "Half Kelly" como opção conservadora.
**Arquivos afetados:** `bot/backtest.py`, `app.py`

---

## Infraestrutura

### [RF-13] Separação de Dados Treino/Teste na UI
**Relacionado a RF-01.** Adicionar slider na sidebar para definir o percentual de dados reservados para out-of-sample. Exibir métricas separadas para período in-sample e out-of-sample.
**Arquivos afetados:** `app.py`, `bot/backtest.py`

---

### [RF-14] Export de Resultados em CSV / Excel
**Problema:** Histórico de backtests está no SQLite mas não há forma de exportar para análise externa.
**Solução:** Botão de download na aba Histórico com `st.download_button()` exportando o DataFrame de trades e a equity curve.
**Arquivos afetados:** `app.py`

---

## Resumo de Impacto

| ID | Descrição | Impacto no Resultado | Complexidade |
|----|-----------|----------------------|--------------|
| RF-01 | Walk-Forward | Alto — elimina overfitting | Alta |
| RF-02 | Spread variável | Alto — reduz resultado irreal | Média |
| RF-03 | Filtro calendário | Alto — evita trades ruins | Média |
| RF-04 | Slippage | Médio — aproxima realidade | Baixa |
| RF-05 | Métricas adicionais | Médio — melhor avaliação | Baixa |
| RF-06 | ATR position sizing | Médio — normaliza risco | Média |
| RF-07 | Breakdown anual | Baixo — visibilidade | Baixa |
| RF-08 | Correlação pares | Médio — evita overexposure | Média |
| RF-09 | Gap overnight | Baixo — GARCH mais preciso | Baixa |
| RF-10 | GARCH gradual | Médio — gestão de risco | Média |
| RF-11 | Detecção de regime | Alto — filtra tendências macro | Alta |
| RF-12 | Kelly Criterion | Médio — sizing ótimo | Média |
| RF-13 | UI treino/teste | Alto — depende de RF-01 | Baixa |
| RF-14 | Export CSV | Baixo — conveniência | Baixa |
