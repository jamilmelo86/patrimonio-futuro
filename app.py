"""Patrimônio Futuro — Simulador de Crescimento Patrimonial."""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

# --- Config ---
st.set_page_config(
    page_title="Patrimônio Futuro — Mithril Capital",
    page_icon="🎯",
    layout="wide",
)

GOLD = "#BF9B30"
DARK_GOLD = "#8C7220"
GREEN = "#28A745"

# --- Header ---
st.title("Patrimônio Futuro")
st.markdown("Simule a evolução do seu patrimônio com aportes mensais e juros compostos.")
st.markdown("---")

# --- Inputs ---
col_input1, col_input2 = st.columns(2)

with col_input1:
    patrimonio_atual = st.number_input(
        "Patrimônio atual (R$)",
        min_value=0.0,
        value=1_000_000.0,
        step=50_000.0,
        format="%.2f",
    )
    aporte_mensal = st.number_input(
        "Aporte mensal (R$)",
        min_value=0.0,
        value=5_000.0,
        step=500.0,
        format="%.2f",
    )

with col_input2:
    taxa_anual = st.number_input(
        "Taxa de crescimento anual (%)",
        min_value=0.0,
        max_value=100.0,
        value=10.0,
        step=0.5,
        format="%.2f",
    )
    meta_patrimonio = st.number_input(
        "Meta de patrimônio (R$, 0 = sem meta)",
        min_value=0.0,
        value=0.0,
        step=100_000.0,
        format="%.2f",
    )
    taxa_renda = st.number_input(
        "Taxa de renda passiva mensal (%)",
        min_value=0.0,
        max_value=5.0,
        value=0.6,
        step=0.1,
        format="%.2f",
        help="Percentual mensal que pode ser sacado sem consumir o patrimônio.",
    )

# --- Cálculo mês a mês ---
taxa_mensal = (1 + taxa_anual / 100) ** (1 / 12) - 1
horizonte_meses = 20 * 12

patrimonio = []
aportes_acumulados = []
rendimentos_acumulados = []

p = patrimonio_atual
total_aportado = 0.0
mes_meta_atingida = None

for mes in range(horizonte_meses + 1):
    patrimonio.append(p)
    aportes_acumulados.append(patrimonio_atual + total_aportado)
    rendimentos_acumulados.append(p - patrimonio_atual - total_aportado)

    if meta_patrimonio > 0 and mes_meta_atingida is None and p >= meta_patrimonio:
        mes_meta_atingida = mes

    if mes < horizonte_meses:
        rendimento = p * taxa_mensal
        p = p + rendimento + aporte_mensal
        total_aportado += aporte_mensal

# --- Marcos: 5, 10, 15, 20 anos ---
marcos = [5, 10, 15, 20]
marcos_meses = [m * 12 for m in marcos]

st.markdown("---")

# --- Métricas principais ---
st.markdown("### Projeção por Período")

cols = st.columns(len(marcos))
for i, (ano, mes_idx) in enumerate(zip(marcos, marcos_meses)):
    with cols[i]:
        valor = patrimonio[mes_idx]
        aportado = aportes_acumulados[mes_idx]
        rendimento = rendimentos_acumulados[mes_idx]
        renda_mensal = valor * (taxa_renda / 100)
        st.metric(f"Em {ano} anos", f"R$ {valor:,.0f}".replace(",", "."))
        st.caption(f"Aportado: R$ {aportado:,.0f}".replace(",", "."))
        st.caption(f"Rendimentos: R$ {rendimento:,.0f}".replace(",", "."))
        st.caption(f"Renda passiva: R$ {renda_mensal:,.0f}/mês".replace(",", "."))

# --- Meta ---
if meta_patrimonio > 0:
    st.markdown("---")
    if mes_meta_atingida is not None:
        anos = mes_meta_atingida // 12
        meses_rest = mes_meta_atingida % 12
        tempo_str = f"{anos} anos" if meses_rest == 0 else f"{anos} anos e {meses_rest} meses"
        st.success(f"Meta de R$ {meta_patrimonio:,.0f} atingida em **{tempo_str}**.".replace(",", "."))
    else:
        st.warning(f"A meta de R$ {meta_patrimonio:,.0f} não é atingida em 20 anos com os parâmetros atuais.".replace(",", "."))

st.markdown("---")

# --- Gráfico de evolução ---
st.markdown("### Evolução do Patrimônio")

meses_lista = list(range(horizonte_meses + 1))
anos_lista = [m / 12 for m in meses_lista]

fig = go.Figure()

# Área de aportes acumulados (base)
fig.add_trace(go.Scatter(
    x=anos_lista,
    y=aportes_acumulados,
    name="Capital investido",
    fill="tozeroy",
    fillcolor="rgba(191, 155, 48, 0.2)",
    line=dict(color=DARK_GOLD, width=1),
    hovertemplate="Ano %{x:.1f}<br>Capital: R$ %{y:,.0f}<extra></extra>",
))

# Linha do patrimônio total
fig.add_trace(go.Scatter(
    x=anos_lista,
    y=patrimonio,
    name="Patrimônio total",
    fill="tonexty",
    fillcolor="rgba(191, 155, 48, 0.4)",
    line=dict(color=GOLD, width=3),
    hovertemplate="Ano %{x:.1f}<br>Patrimônio: R$ %{y:,.0f}<extra></extra>",
))

# Linha da meta
if meta_patrimonio > 0:
    fig.add_hline(
        y=meta_patrimonio,
        line_dash="dash",
        line_color=GREEN,
        line_width=2,
        annotation_text=f"Meta: R$ {meta_patrimonio:,.0f}".replace(",", "."),
        annotation_position="top left",
        annotation_font_color=GREEN,
    )
    if mes_meta_atingida is not None:
        fig.add_trace(go.Scatter(
            x=[mes_meta_atingida / 12],
            y=[patrimonio[mes_meta_atingida]],
            mode="markers+text",
            marker=dict(size=12, color=GREEN, symbol="star"),
            text=[f"{mes_meta_atingida // 12}a {mes_meta_atingida % 12}m"],
            textposition="top center",
            textfont=dict(color=GREEN, size=12),
            name="Meta atingida",
            hovertemplate="Meta atingida<br>Ano %{x:.1f}<br>R$ %{y:,.0f}<extra></extra>",
        ))

# Marcadores nos marcos de 5, 10, 15, 20 anos
fig.add_trace(go.Scatter(
    x=[m / 12 for m in marcos_meses],
    y=[patrimonio[m] for m in marcos_meses],
    mode="markers+text",
    marker=dict(size=10, color=GOLD, symbol="diamond"),
    text=[f"R$ {patrimonio[m]/1e6:.1f}M" for m in marcos_meses],
    textposition="top center",
    textfont=dict(color=GOLD, size=11),
    name="Marcos",
    hovertemplate="Ano %{x:.0f}<br>R$ %{y:,.0f}<extra></extra>",
))

fig.update_layout(
    xaxis_title="Anos",
    yaxis_title="Patrimônio (R$)",
    yaxis_tickformat=",.",
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    height=500,
    margin=dict(l=20, r=20, t=40, b=40),
)

st.plotly_chart(fig, use_container_width=True)

# --- Tabela detalhada ---
with st.expander("Tabela detalhada (anual)"):
    dados_tabela = []
    for ano in range(1, 21):
        m = ano * 12
        dados_tabela.append({
            "Ano": ano,
            "Patrimônio": f"R$ {patrimonio[m]:,.0f}".replace(",", "."),
            "Capital Investido": f"R$ {aportes_acumulados[m]:,.0f}".replace(",", "."),
            "Rendimentos": f"R$ {rendimentos_acumulados[m]:,.0f}".replace(",", "."),
            "Renda Passiva/mês": f"R$ {patrimonio[m] * (taxa_renda / 100):,.0f}".replace(",", "."),
        })

    df = pd.DataFrame(dados_tabela)
    st.dataframe(df, use_container_width=True, hide_index=True)
