"""Patrimônio Futuro — Simulador de Crescimento Patrimonial."""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from urllib.parse import urlencode
from datetime import date
from io import BytesIO
import base64, pathlib

# --- Config ---
st.set_page_config(
    page_title="Patrimônio Futuro — Mithril Capital",
    page_icon="assets/icon.png",
    layout="wide",
)

# --- Brand tokens ---
GOLD = "#BF9B30"
GOLD_LIGHT = "#D4B44C"
GOLD_DIM = "rgba(191, 155, 48, 0.35)"
GOLD_GLOW = "rgba(191, 155, 48, 0.12)"
STEEL = "#8B9DAF"
STEEL_LIGHT = "#A8B8C8"
CHARCOAL = "#1A1D23"
CHARCOAL_DEEP = "#0F1117"
SURFACE = "#1E222A"
BORDER = "rgba(139, 157, 175, 0.12)"
GREEN = "#34D399"
RED = "#F87171"
AMBER = "#FBBF24"

# --- Logo base64 ---
logo_path = pathlib.Path(__file__).parent / "assets" / "logo_main.png"
if logo_path.exists():
    logo_b64 = base64.b64encode(logo_path.read_bytes()).decode()
else:
    logo_b64 = ""

# --- CSS ---
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=DM+Sans:ital,wght@0,400;0,500;0,600;1,400&display=swap');

/* === Reset & Global === */
*, *::before, *::after {{ box-sizing: border-box; }}

.block-container {{
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    max-width: 1140px;
}}

html, body, [data-testid="stAppViewContainer"] {{
    font-family: 'DM Sans', sans-serif;
    color: #E0E0E0;
}}

header[data-testid="stHeader"] {{
    background: linear-gradient(180deg, {CHARCOAL_DEEP} 0%, transparent 100%);
}}

/* Hide default Streamlit decoration */
[data-testid="stDecoration"] {{ display: none; }}

/* === Scrollbar === */
::-webkit-scrollbar {{ width: 6px; }}
::-webkit-scrollbar-track {{ background: {CHARCOAL_DEEP}; }}
::-webkit-scrollbar-thumb {{ background: rgba(139,157,175,0.25); border-radius: 3px; }}
::-webkit-scrollbar-thumb:hover {{ background: rgba(139,157,175,0.4); }}

/* === App Header === */
.app-header {{
    text-align: center;
    padding: 2rem 0 1.5rem 0;
    animation: fadeInDown 0.8s ease-out;
}}
.app-header img {{
    height: 48px;
    margin-bottom: 1rem;
    filter: brightness(0) invert(1);
    opacity: 0.9;
}}
.app-header h1 {{
    font-family: 'Outfit', sans-serif;
    font-size: 2.4rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: #FFFFFF;
    margin: 0;
}}
.app-header h1 span {{
    background: linear-gradient(135deg, {GOLD} 0%, {GOLD_LIGHT} 50%, {GOLD} 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}}
.app-header .subtitle {{
    font-family: 'DM Sans', sans-serif;
    color: {STEEL};
    font-size: 0.95rem;
    margin-top: 0.5rem;
    letter-spacing: 0.01em;
}}
.app-header .gold-line {{
    width: 48px;
    height: 2px;
    background: linear-gradient(90deg, transparent, {GOLD}, transparent);
    margin: 0.75rem auto 0 auto;
}}

/* === Section Headers === */
.section-header {{
    font-family: 'Outfit', sans-serif;
    font-size: 0.85rem;
    font-weight: 600;
    color: {STEEL};
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-top: 2.5rem;
    margin-bottom: 1.2rem;
    padding-bottom: 0.6rem;
    border-bottom: 1px solid {BORDER};
    display: flex;
    align-items: center;
    gap: 0.5rem;
}}
.section-header::before {{
    content: '';
    width: 3px;
    height: 14px;
    background: {GOLD};
    border-radius: 2px;
    display: inline-block;
}}

/* === Glass Card (container border override) === */
[data-testid="stVerticalBlockBorderWrapper"] {{
    background: {SURFACE} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 16px !important;
    box-shadow: 0 4px 24px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.03);
    backdrop-filter: blur(12px);
}}

/* === Number input styling === */
[data-testid="stNumberInput"] label {{
    font-family: 'DM Sans', sans-serif;
    font-size: 0.82rem;
    color: {STEEL} !important;
    font-weight: 500;
}}
[data-testid="stNumberInput"] input {{
    background: {CHARCOAL_DEEP} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 10px !important;
    color: #E0E0E0 !important;
    font-family: 'Outfit', sans-serif;
    font-weight: 500;
}}
[data-testid="stNumberInput"] input:focus {{
    border-color: {GOLD} !important;
    box-shadow: 0 0 0 2px {GOLD_GLOW} !important;
}}

/* === Captions === */
.stCaption, [data-testid="stCaptionContainer"] {{
    color: {STEEL} !important;
    opacity: 0.7;
}}

/* === Metric Cards === */
.metric-card {{
    background: linear-gradient(145deg, {SURFACE} 0%, rgba(30,34,42,0.7) 100%);
    border: 1px solid {BORDER};
    border-radius: 16px;
    padding: 1.5rem;
    text-align: center;
    position: relative;
    overflow: hidden;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    animation: fadeInUp 0.6s ease-out both;
}}
.metric-card::before {{
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, {GOLD_DIM}, transparent);
    opacity: 0;
    transition: opacity 0.3s ease;
}}
.metric-card:hover {{
    border-color: rgba(191, 155, 48, 0.25);
    box-shadow: 0 8px 32px rgba(191, 155, 48, 0.08);
    transform: translateY(-2px);
}}
.metric-card:hover::before {{
    opacity: 1;
}}
.metric-card .metric-label {{
    font-family: 'Outfit', sans-serif;
    font-size: 0.72rem;
    font-weight: 600;
    color: {STEEL};
    text-transform: uppercase;
    letter-spacing: 0.14em;
    margin-bottom: 0.5rem;
}}
.metric-card .metric-value {{
    font-family: 'Outfit', sans-serif;
    font-size: 1.7rem;
    font-weight: 700;
    background: linear-gradient(135deg, {GOLD_LIGHT}, {GOLD});
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.3rem;
}}
.metric-card .metric-range {{
    font-family: 'DM Sans', sans-serif;
    font-size: 0.7rem;
    color: rgba(139, 157, 175, 0.6);
    margin-bottom: 0.6rem;
}}
.metric-card .metric-detail {{
    font-family: 'DM Sans', sans-serif;
    font-size: 0.78rem;
    color: {STEEL};
    line-height: 1.7;
    opacity: 0.8;
}}

/* Animation delays for metric cards */
.metric-card:nth-child(1) {{ animation-delay: 0.1s; }}
.metric-card:nth-child(2) {{ animation-delay: 0.2s; }}
.metric-card:nth-child(3) {{ animation-delay: 0.3s; }}
.metric-card:nth-child(4) {{ animation-delay: 0.4s; }}

/* === Status Cards (goal, independence) === */
.status-card {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 14px;
    padding: 1.1rem 1.4rem;
    margin: 1rem 0;
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    animation: fadeInUp 0.5s ease-out both;
    animation-delay: 0.5s;
}}
.status-card .status-icon {{
    font-size: 1.2rem;
    flex-shrink: 0;
    margin-top: 0.1rem;
}}
.status-card .status-content {{
    flex: 1;
}}
.status-card .status-content strong {{
    font-family: 'Outfit', sans-serif;
    font-weight: 600;
    color: #FFF;
    display: block;
    margin-bottom: 0.2rem;
}}
.status-card .status-content span {{
    font-size: 0.85rem;
    color: {STEEL};
    line-height: 1.5;
}}
.status-card.success {{ border-left: 3px solid {GREEN}; }}
.status-card.warning {{ border-left: 3px solid {AMBER}; }}
.status-card.gold {{ border-left: 3px solid {GOLD}; }}

/* === Expander === */
[data-testid="stExpander"] {{
    background: {SURFACE};
    border: 1px solid {BORDER} !important;
    border-radius: 14px !important;
}}
[data-testid="stExpander"] summary {{
    font-family: 'Outfit', sans-serif;
    font-weight: 500;
    color: {STEEL_LIGHT};
}}

/* === Download buttons === */
[data-testid="stDownloadButton"] > button {{
    font-family: 'Outfit', sans-serif;
    font-weight: 500;
    border-radius: 10px;
    border: 1px solid {BORDER};
    background: {SURFACE};
    color: {STEEL_LIGHT};
    transition: all 0.25s ease;
}}
[data-testid="stDownloadButton"] > button:hover {{
    border-color: {GOLD};
    color: {GOLD_LIGHT};
    box-shadow: 0 0 16px {GOLD_GLOW};
}}

/* === Link input === */
[data-testid="stTextInput"] input {{
    background: {CHARCOAL_DEEP} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 10px !important;
    color: {STEEL} !important;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.82rem;
}}

/* === Animations === */
@keyframes fadeInDown {{
    from {{ opacity: 0; transform: translateY(-20px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes fadeInUp {{
    from {{ opacity: 0; transform: translateY(16px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes shimmer {{
    0% {{ background-position: -200% center; }}
    100% {{ background-position: 200% center; }}
}}
</style>
""", unsafe_allow_html=True)

# --- Header ---
logo_html = f'<img src="data:image/png;base64,{logo_b64}" alt="Mithril Capital" />' if logo_b64 else ""
st.markdown(f"""
<div class="app-header">
    {logo_html}
    <h1>Patrimônio <span>Futuro</span></h1>
    <div class="subtitle">Simule a evolução do seu patrimônio com aportes mensais e juros compostos</div>
    <div class="gold-line"></div>
</div>
""", unsafe_allow_html=True)

# --- Query params ---
qp = st.query_params
default_patrimonio = float(qp.get("p", 1_000_000))
default_aporte = float(qp.get("a", 5_000))
default_taxa = float(qp.get("t", 10))
default_variacao = float(qp.get("v", 2))
default_meta = float(qp.get("m", 0))
default_custo = float(qp.get("c", 0))

# --- Inputs ---
st.markdown('<div class="section-header">Parâmetros da Simulação</div>', unsafe_allow_html=True)

with st.container(border=True):
    col_input1, col_input2 = st.columns(2)

    with col_input1:
        patrimonio_atual = st.number_input(
            "Patrimônio atual (R$)", min_value=0.0, value=default_patrimonio,
            step=50_000.0, format="%.2f",
        )
        st.caption(f"R$ {patrimonio_atual:,.2f}".replace(",", "."))
        aporte_mensal = st.number_input(
            "Aporte mensal (R$)", min_value=0.0, value=default_aporte,
            step=500.0, format="%.2f",
        )
        st.caption(f"R$ {aporte_mensal:,.2f}".replace(",", "."))
        custo_vida = st.number_input(
            "Custo de vida mensal (R$, 0 = desativar)", min_value=0.0,
            value=default_custo, step=1_000.0, format="%.2f",
            help="Seu custo de vida mensal. Mostra quando os rendimentos superam esse valor.",
        )
        if custo_vida > 0:
            st.caption(f"R$ {custo_vida:,.2f}".replace(",", "."))

    with col_input2:
        taxa_anual = st.number_input(
            "Taxa de crescimento anual (%)", min_value=0.0, max_value=100.0,
            value=default_taxa, step=0.5, format="%.2f",
        )
        variacao_cenario = st.number_input(
            "Variação dos cenários (+/- %)", min_value=0.5, max_value=10.0,
            value=default_variacao, step=0.5, format="%.1f",
            help="Define a faixa dos cenários conservador e otimista.",
        )
        meta_patrimonio = st.number_input(
            "Meta de patrimônio (R$, 0 = sem meta)", min_value=0.0,
            value=default_meta, step=100_000.0, format="%.2f",
        )
        if meta_patrimonio > 0:
            st.caption(f"R$ {meta_patrimonio:,.2f}".replace(",", "."))


# --- Helper ---
def fmt(v):
    """Formata valor em R$ com separadores brasileiros."""
    return f"R$ {v:,.0f}".replace(",", ".")


# --- Cálculo dos 3 cenários ---
taxa_conservadora = max(taxa_anual - variacao_cenario, 0)
taxa_esperada = taxa_anual
taxa_otimista = taxa_anual + variacao_cenario
horizonte_meses = 20 * 12


def simular(taxa_anual_pct):
    taxa_m = (1 + taxa_anual_pct / 100) ** (1 / 12) - 1
    pat, aport, rend, rend_mensal = [], [], [], []
    p = patrimonio_atual
    total_ap = 0.0
    meta_mes = independencia_mes = None
    for mes in range(horizonte_meses + 1):
        pat.append(p)
        aport.append(patrimonio_atual + total_ap)
        rend.append(p - patrimonio_atual - total_ap)
        rm = p * taxa_m
        rend_mensal.append(rm)
        if meta_patrimonio > 0 and meta_mes is None and p >= meta_patrimonio:
            meta_mes = mes
        if custo_vida > 0 and independencia_mes is None and rm >= custo_vida:
            independencia_mes = mes
        if mes < horizonte_meses:
            p = p + rm + aporte_mensal
            total_ap += aporte_mensal
    return pat, aport, rend, rend_mensal, meta_mes, independencia_mes


pat_cons, aport_cons, rend_cons, rm_cons, meta_cons, ind_cons = simular(taxa_conservadora)
pat_esp, aport_esp, rend_esp, rm_esp, meta_esp, ind_esp = simular(taxa_esperada)
pat_otim, aport_otim, rend_otim, rm_otim, meta_otim, ind_otim = simular(taxa_otimista)

patrimonio = pat_esp
aportes_acumulados = aport_esp
rendimentos_acumulados = rend_esp
mes_meta_atingida = meta_esp
mes_independencia = ind_esp

marcos = [5, 10, 15, 20]
marcos_meses = [m * 12 for m in marcos]

# --- Métricas ---
st.markdown('<div class="section-header">Projeção por Período</div>', unsafe_allow_html=True)

cols = st.columns(len(marcos))
for i, (ano, mes_idx) in enumerate(zip(marcos, marcos_meses)):
    with cols[i]:
        valor = patrimonio[mes_idx]
        valor_cons = pat_cons[mes_idx]
        valor_otim = pat_otim[mes_idx]
        aportado = aportes_acumulados[mes_idx]
        rendimento = rendimentos_acumulados[mes_idx]

        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Em {ano} anos</div>
            <div class="metric-value">{fmt(valor)}</div>
            <div class="metric-range">{fmt(valor_cons)} — {fmt(valor_otim)}</div>
            <div class="metric-detail">
                Aportado: {fmt(aportado)}<br>
                Rendimentos: {fmt(rendimento)}
            </div>
        </div>
        """, unsafe_allow_html=True)

# --- Meta ---
if meta_patrimonio > 0:
    if mes_meta_atingida is not None:
        anos = mes_meta_atingida // 12
        meses_rest = mes_meta_atingida % 12
        tempo_str = f"{anos} anos" if meses_rest == 0 else f"{anos} anos e {meses_rest} meses"
        st.markdown(f"""
        <div class="status-card success">
            <div class="status-icon">&#9734;</div>
            <div class="status-content">
                <strong>Meta atingida</strong>
                <span>{fmt(meta_patrimonio)} alcançada em <strong>{tempo_str}</strong></span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="status-card warning">
            <div class="status-icon">&#9888;</div>
            <div class="status-content">
                <strong>Meta não atingida</strong>
                <span>{fmt(meta_patrimonio)} não é alcançada em 20 anos com os parâmetros atuais</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

# --- Independência ---
if custo_vida > 0:
    if mes_independencia is not None:
        anos_ind = mes_independencia // 12
        meses_ind = mes_independencia % 12
        tempo_ind = f"{anos_ind} anos" if meses_ind == 0 else f"{anos_ind} anos e {meses_ind} meses"
        rend_no_momento = rm_esp[mes_independencia]
        st.markdown(f"""
        <div class="status-card gold">
            <div class="status-icon">&#9733;</div>
            <div class="status-content">
                <strong>Independência financeira</strong>
                <span>Em <strong>{tempo_ind}</strong>, seus rendimentos mensais ({fmt(rend_no_momento)}) superam seu custo de vida ({fmt(custo_vida)})</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="status-card warning">
            <div class="status-icon">&#9888;</div>
            <div class="status-content">
                <strong>Independência financeira não atingida</strong>
                <span>Os rendimentos mensais não superam {fmt(custo_vida)}/mês em 20 anos</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

# --- Gráfico ---
st.markdown('<div class="section-header">Evolução do Patrimônio</div>', unsafe_allow_html=True)

meses_lista = list(range(horizonte_meses + 1))
anos_lista = [m / 12 for m in meses_lista]

fig = go.Figure()

# Faixa conservador-otimista
fig.add_trace(go.Scatter(
    x=anos_lista, y=pat_cons, name="Conservador", line=dict(width=0),
    showlegend=False, hoverinfo="skip",
))
fig.add_trace(go.Scatter(
    x=anos_lista, y=pat_otim,
    name=f"Faixa {taxa_conservadora:.1f}% — {taxa_otimista:.1f}%",
    fill="tonexty", fillcolor="rgba(191, 155, 48, 0.06)",
    line=dict(width=0), hoverinfo="skip",
))

# Capital investido
fig.add_trace(go.Scatter(
    x=anos_lista, y=aportes_acumulados, name="Capital investido",
    fill="tozeroy", fillcolor="rgba(139, 157, 175, 0.08)",
    line=dict(color=STEEL, width=1, dash="dot"),
    hovertemplate="Ano %{x:.1f}<br>Capital: R$ %{y:,.0f}<extra></extra>",
))

# Conservador
fig.add_trace(go.Scatter(
    x=anos_lista, y=pat_cons, name=f"Conservador ({taxa_conservadora:.1f}%)",
    line=dict(color="rgba(139,157,175,0.4)", width=1, dash="dot"),
    hovertemplate="Ano %{x:.1f}<br>Conservador: R$ %{y:,.0f}<extra></extra>",
))

# Esperado
fig.add_trace(go.Scatter(
    x=anos_lista, y=patrimonio, name=f"Esperado ({taxa_esperada:.1f}%)",
    line=dict(color=GOLD, width=3),
    hovertemplate="Ano %{x:.1f}<br>Esperado: R$ %{y:,.0f}<extra></extra>",
))

# Otimista
fig.add_trace(go.Scatter(
    x=anos_lista, y=pat_otim, name=f"Otimista ({taxa_otimista:.1f}%)",
    line=dict(color="rgba(212,180,76,0.5)", width=1, dash="dot"),
    hovertemplate="Ano %{x:.1f}<br>Otimista: R$ %{y:,.0f}<extra></extra>",
))

# Meta
if meta_patrimonio > 0:
    fig.add_hline(
        y=meta_patrimonio, line_dash="dash", line_color=GREEN, line_width=1.5,
        annotation_text=f"Meta: {fmt(meta_patrimonio)}",
        annotation_position="top left",
        annotation_font=dict(color=GREEN, size=11),
    )
    if mes_meta_atingida is not None:
        fig.add_trace(go.Scatter(
            x=[mes_meta_atingida / 12], y=[patrimonio[mes_meta_atingida]],
            mode="markers+text",
            marker=dict(size=10, color=GREEN, symbol="star"),
            text=[f"{mes_meta_atingida // 12}a {mes_meta_atingida % 12}m"],
            textposition="top center",
            textfont=dict(color=GREEN, size=10),
            name="Meta atingida",
            hovertemplate="Meta atingida<br>Ano %{x:.1f}<br>R$ %{y:,.0f}<extra></extra>",
        ))

# Independência
if custo_vida > 0 and mes_independencia is not None:
    fig.add_trace(go.Scatter(
        x=[mes_independencia / 12], y=[patrimonio[mes_independencia]],
        mode="markers+text",
        marker=dict(size=12, color=GOLD, symbol="star"),
        text=["Independência"], textposition="top center",
        textfont=dict(color=GOLD, size=10),
        name="Independência financeira",
        hovertemplate="Independência<br>Ano %{x:.1f}<br>R$ %{y:,.0f}<extra></extra>",
    ))

# Marcos
fig.add_trace(go.Scatter(
    x=[m / 12 for m in marcos_meses],
    y=[patrimonio[m] for m in marcos_meses],
    mode="markers+text",
    marker=dict(size=8, color=GOLD, symbol="diamond"),
    text=[f"{fmt(patrimonio[m])}" if patrimonio[m] < 1e6 else f"R$ {patrimonio[m]/1e6:.1f}M" for m in marcos_meses],
    textposition="top center",
    textfont=dict(color=GOLD_LIGHT, size=10, family="Outfit"),
    name="Marcos",
    hovertemplate="Ano %{x:.0f}<br>R$ %{y:,.0f}<extra></extra>",
))

fig.update_layout(
    xaxis_title="Anos", yaxis_title="Patrimônio (R$)",
    yaxis_tickformat=",.",
    hovermode="x unified",
    legend=dict(
        orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
        font=dict(size=11, color=STEEL, family="DM Sans"),
        bgcolor="rgba(0,0,0,0)",
    ),
    height=480,
    margin=dict(l=16, r=16, t=36, b=36),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans", color=STEEL),
    xaxis=dict(
        showgrid=False, linecolor="rgba(139,157,175,0.15)", linewidth=1,
        tickfont=dict(size=11, color="rgba(139,157,175,0.6)"),
        zeroline=False,
    ),
    yaxis=dict(
        gridcolor="rgba(139,157,175,0.07)", gridwidth=1,
        linecolor="rgba(139,157,175,0.15)", linewidth=1,
        tickfont=dict(size=11, color="rgba(139,157,175,0.6)"),
        zeroline=False,
    ),
)

st.plotly_chart(fig, use_container_width=True)

# --- Tabela ---
st.markdown('<div class="section-header">Detalhamento Anual</div>', unsafe_allow_html=True)

with st.expander("Ver tabela completa"):
    dados_tabela = []
    for ano in range(1, 21):
        m = ano * 12
        dados_tabela.append({
            "Ano": ano,
            "Conservador": fmt(pat_cons[m]),
            "Esperado": fmt(patrimonio[m]),
            "Otimista": fmt(pat_otim[m]),
            "Capital Investido": fmt(aportes_acumulados[m]),
            "Rendimentos": fmt(rendimentos_acumulados[m]),
        })
    df = pd.DataFrame(dados_tabela)
    st.dataframe(df, use_container_width=True, hide_index=True)

# --- Compartilhar ---
st.markdown('<div class="section-header">Compartilhar Simulação</div>', unsafe_allow_html=True)

params = urlencode({
    "p": patrimonio_atual, "a": aporte_mensal, "t": taxa_anual,
    "v": variacao_cenario, "m": meta_patrimonio, "c": custo_vida,
})
st.text_input("Link da simulação (copie e compartilhe)", value=f"?{params}")

# --- Relatórios ---
chart_html = fig.to_html(include_plotlyjs="cdn", full_html=False)

table_rows = ""
for ano in range(1, 21):
    m = ano * 12
    table_rows += f"""<tr>
        <td>{ano}</td><td>{fmt(pat_cons[m])}</td>
        <td><strong>{fmt(patrimonio[m])}</strong></td>
        <td>{fmt(pat_otim[m])}</td>
        <td>{fmt(aportes_acumulados[m])}</td>
        <td>{fmt(rendimentos_acumulados[m])}</td>
    </tr>"""

meta_html = ""
if meta_patrimonio > 0:
    if mes_meta_atingida is not None:
        a = mes_meta_atingida // 12
        mr = mes_meta_atingida % 12
        ts = f"{a} anos" if mr == 0 else f"{a} anos e {mr} meses"
        meta_html = f'<div class="card success">Meta atingida! {fmt(meta_patrimonio)} em <strong>{ts}</strong></div>'
    else:
        meta_html = f'<div class="card warning">Meta de {fmt(meta_patrimonio)} não atingida em 20 anos</div>'

independencia_html = ""
if custo_vida > 0:
    if mes_independencia is not None:
        ai = mes_independencia // 12
        mi = mes_independencia % 12
        ti = f"{ai} anos" if mi == 0 else f"{ai} anos e {mi} meses"
        ri = rm_esp[mes_independencia]
        independencia_html = f'<div class="card gold">Independência financeira em <strong>{ti}</strong> — rendimentos ({fmt(ri)}) superam custo de vida ({fmt(custo_vida)})</div>'
    else:
        independencia_html = f'<div class="card warning">Independência não atingida em 20 anos</div>'

report_html = f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="UTF-8">
<title>Patrimônio Futuro — Mithril Capital</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#E0E0E0;background:#0F1117;padding:2rem;max-width:1000px;margin:0 auto}}
.header{{text-align:center;margin-bottom:2rem}}
.header h1{{font-size:2rem;color:#fff}} .header h1 span{{color:#BF9B30}}
.header .date{{color:#8B9DAF;font-size:0.9rem;margin-top:0.5rem}}
.params{{display:grid;grid-template-columns:1fr 1fr;gap:0.75rem;margin-bottom:2rem}}
.param{{background:#1E222A;border:1px solid rgba(139,157,175,0.12);border-radius:10px;padding:0.75rem 1rem}}
.param .label{{font-size:0.75rem;color:#8B9DAF;text-transform:uppercase;letter-spacing:0.05em}}
.param .value{{font-size:1.05rem;font-weight:600;color:#E0E0E0;margin-top:0.1rem}}
.metrics{{display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;margin-bottom:1.5rem}}
.metric{{background:#1E222A;border:1px solid rgba(139,157,175,0.12);border-radius:14px;padding:1.25rem;text-align:center}}
.metric .mlabel{{font-size:0.75rem;color:#8B9DAF;text-transform:uppercase;letter-spacing:0.06em}}
.metric .mvalue{{font-size:1.4rem;font-weight:700;color:#BF9B30;margin:0.2rem 0}}
.metric .mrange{{font-size:0.7rem;color:rgba(139,157,175,0.5)}}
.metric .mdetail{{font-size:0.75rem;color:#8B9DAF;margin-top:0.3rem;line-height:1.5}}
.card{{background:#1E222A;border-radius:12px;padding:1rem 1.25rem;margin-bottom:1rem;border-left:3px solid #BF9B30}}
.card.success{{border-left-color:#34D399}} .card.warning{{border-left-color:#FBBF24}}
.section-title{{font-size:0.85rem;font-weight:600;color:#8B9DAF;text-transform:uppercase;letter-spacing:0.1em;margin:1.5rem 0 1rem;border-bottom:1px solid rgba(139,157,175,0.12);padding-bottom:0.4rem}}
table{{width:100%;border-collapse:collapse;font-size:0.82rem;margin-top:1rem}}
th{{background:#1A1D23;color:#8B9DAF;font-weight:600;text-align:left;padding:0.6rem;border-bottom:1px solid rgba(139,157,175,0.15)}}
td{{padding:0.5rem 0.6rem;border-bottom:1px solid rgba(139,157,175,0.06);color:#C0C0C0}}
.footer{{text-align:center;color:rgba(139,157,175,0.4);font-size:0.78rem;margin-top:2rem;padding-top:1rem;border-top:1px solid rgba(139,157,175,0.1)}}
@media print{{body{{background:#fff;color:#333}} .metric .mvalue{{color:#BF9B30}} th{{background:#f5f5f5;color:#666}} td{{color:#333}}}}
</style></head><body>
<div class="header"><h1>Patrimônio <span>Futuro</span></h1><div class="date">Mithril Capital — {date.today().strftime('%d/%m/%Y')}</div></div>
<div class="params">
<div class="param"><div class="label">Patrimônio atual</div><div class="value">{fmt(patrimonio_atual)}</div></div>
<div class="param"><div class="label">Aporte mensal</div><div class="value">{fmt(aporte_mensal)}</div></div>
<div class="param"><div class="label">Taxa esperada</div><div class="value">{taxa_anual:.1f}% a.a.</div></div>
<div class="param"><div class="label">Cenários</div><div class="value">{taxa_conservadora:.1f}% — {taxa_otimista:.1f}%</div></div>
{"" if meta_patrimonio==0 else f'<div class="param"><div class="label">Meta</div><div class="value">{fmt(meta_patrimonio)}</div></div>'}
{"" if custo_vida==0 else f'<div class="param"><div class="label">Custo de vida</div><div class="value">{fmt(custo_vida)}/mês</div></div>'}
</div>
<div class="section-title">Projeção por Período</div>
<div class="metrics">{"".join(f'<div class="metric"><div class="mlabel">Em {ano} anos</div><div class="mvalue">{fmt(patrimonio[m])}</div><div class="mrange">{fmt(pat_cons[m])} — {fmt(pat_otim[m])}</div><div class="mdetail">Aportado: {fmt(aportes_acumulados[m])}<br>Rendimentos: {fmt(rendimentos_acumulados[m])}</div></div>' for ano,m in zip(marcos,marcos_meses))}</div>
{meta_html}{independencia_html}
<div class="section-title">Evolução do Patrimônio</div>
<div>{chart_html}</div>
<div class="section-title">Detalhamento Anual</div>
<table><thead><tr><th>Ano</th><th>Conservador</th><th>Esperado</th><th>Otimista</th><th>Capital Inv.</th><th>Rendimentos</th></tr></thead><tbody>{table_rows}</tbody></table>
<div class="footer">Mithril Capital — Patrimônio Futuro</div>
</body></html>"""

col_dl1, col_dl2 = st.columns(2)

with col_dl1:
    st.download_button(
        label="Baixar relatório (HTML)",
        data=report_html,
        file_name=f"patrimonio-futuro-{date.today().isoformat()}.html",
        mime="text/html",
    )

with col_dl2:
    from fpdf import FPDF
    import tempfile, os

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    _font_dir = pathlib.Path(__file__).parent / "assets" / "fonts"
    pdf.add_font("Arial", "", str(_font_dir / "arial.ttf"), uni=True)
    pdf.add_font("Arial", "B", str(_font_dir / "arialbd.ttf"), uni=True)
    pdf.add_page()

    pdf.set_font("Arial", "B", 22)
    pdf.cell(0, 12, "Patrimônio Futuro", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_draw_color(191, 155, 48)
    pdf.set_line_width(0.8)
    pdf.line(85, pdf.get_y(), 125, pdf.get_y())
    pdf.ln(4)
    pdf.set_font("Arial", "", 10)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 6, f"Mithril Capital — {date.today().strftime('%d/%m/%Y')}", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(6)

    pdf.set_text_color(51, 51, 51)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Parâmetros", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(191, 155, 48)
    pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 40, pdf.get_y())
    pdf.ln(3)

    params_pdf = [
        ("Patrimônio atual", fmt(patrimonio_atual)),
        ("Aporte mensal", fmt(aporte_mensal)),
        ("Taxa esperada", f"{taxa_anual:.1f}% a.a."),
        ("Cenários", f"{taxa_conservadora:.1f}% - {taxa_otimista:.1f}%"),
    ]
    if meta_patrimonio > 0:
        params_pdf.append(("Meta", fmt(meta_patrimonio)))
    if custo_vida > 0:
        params_pdf.append(("Custo de vida", f"{fmt(custo_vida)}/mês"))

    col_w = 63
    for i, (label, value) in enumerate(params_pdf):
        col_idx = i % 3
        if col_idx == 0 and i > 0:
            pdf.ln(5)
        x = 10 + col_idx * col_w
        pdf.set_xy(x, pdf.get_y())
        pdf.set_text_color(136, 136, 136)
        pdf.set_font("Arial", "", 7)
        pdf.cell(col_w, 3.5, label.upper(), new_x="LEFT", new_y="NEXT")
        pdf.set_xy(x, pdf.get_y())
        pdf.set_text_color(51, 51, 51)
        pdf.set_font("Arial", "B", 9)
        pdf.cell(col_w, 4.5, value, new_x="LEFT", new_y="NEXT")

    pdf.ln(8)

    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(51, 51, 51)
    pdf.cell(0, 8, "Projeção por Período", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(191, 155, 48)
    pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 50, pdf.get_y())
    pdf.ln(3)

    y_met = pdf.get_y()
    box_w = 45
    for i, (ano, mes_idx) in enumerate(zip(marcos, marcos_meses)):
        x = 10 + i * box_w
        valor = patrimonio[mes_idx]
        aportado = aportes_acumulados[mes_idx]
        rendimento = rendimentos_acumulados[mes_idx]
        pdf.set_xy(x, y_met)
        pdf.set_text_color(136, 136, 136)
        pdf.set_font("Arial", "", 7)
        pdf.cell(box_w, 3.5, f"EM {ano} ANOS", new_x="LEFT", new_y="NEXT")
        pdf.set_xy(x, pdf.get_y())
        pdf.set_text_color(191, 155, 48)
        pdf.set_font("Arial", "B", 13)
        pdf.cell(box_w, 7, fmt(valor), new_x="LEFT", new_y="NEXT")
        pdf.set_xy(x, pdf.get_y())
        pdf.set_text_color(153, 153, 153)
        pdf.set_font("Arial", "", 7)
        pdf.cell(box_w, 3.5, f"{fmt(pat_cons[mes_idx])} - {fmt(pat_otim[mes_idx])}", new_x="LEFT", new_y="NEXT")
        pdf.set_xy(x, pdf.get_y())
        pdf.set_text_color(102, 102, 102)
        pdf.cell(box_w, 3.5, f"Aportado: {fmt(aportado)}", new_x="LEFT", new_y="NEXT")
        pdf.set_xy(x, pdf.get_y())
        pdf.cell(box_w, 3.5, f"Rendimentos: {fmt(rendimento)}", new_x="LEFT", new_y="NEXT")

    pdf.ln(8)
    pdf.set_text_color(51, 51, 51)
    pdf.set_font("Arial", "B", 10)
    if meta_patrimonio > 0:
        if mes_meta_atingida is not None:
            a = mes_meta_atingida // 12
            mr = mes_meta_atingida % 12
            ts = f"{a} anos" if mr == 0 else f"{a} anos e {mr} meses"
            pdf.cell(0, 6, f"Meta atingida! {fmt(meta_patrimonio)} em {ts}", new_x="LMARGIN", new_y="NEXT")
        else:
            pdf.cell(0, 6, f"Meta de {fmt(meta_patrimonio)} não atingida em 20 anos", new_x="LMARGIN", new_y="NEXT")
    if custo_vida > 0:
        if mes_independencia is not None:
            ai = mes_independencia // 12
            mi = mes_independencia % 12
            ti = f"{ai} anos" if mi == 0 else f"{ai} anos e {mi} meses"
            pdf.cell(0, 6, f"Independência financeira em {ti}", new_x="LMARGIN", new_y="NEXT")
        else:
            pdf.cell(0, 6, "Independência financeira não atingida em 20 anos", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(4)

    with tempfile.TemporaryDirectory() as tmpdir:
        img_path = os.path.join(tmpdir, "chart.png")
        fig.update_layout(paper_bgcolor="#FFFFFF", plot_bgcolor="#FAFAFA",
                          font=dict(color="#333"),
                          xaxis=dict(tickfont=dict(color="#666"), linecolor="#DDD", gridcolor="#EEE"),
                          yaxis=dict(tickfont=dict(color="#666"), linecolor="#DDD", gridcolor="#EEE"))
        fig.write_image(img_path, width=900, height=450, scale=2)

        pdf.set_font("Arial", "B", 12)
        pdf.set_text_color(51, 51, 51)
        pdf.cell(0, 8, "Evolução do Patrimônio", new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(191, 155, 48)
        pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 50, pdf.get_y())
        pdf.ln(2)
        pdf.image(img_path, x=10, w=190)

    pdf.add_page()
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(51, 51, 51)
    pdf.cell(0, 8, "Detalhamento Anual", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(191, 155, 48)
    pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 48, pdf.get_y())
    pdf.ln(3)

    headers_pdf = ["Ano", "Conserv.", "Esperado", "Otimista", "Capital Inv.", "Rendimentos"]
    col_widths = [14, 34, 34, 34, 36, 36]
    pdf.set_fill_color(245, 242, 235)
    pdf.set_text_color(102, 102, 102)
    pdf.set_font("Arial", "B", 8)
    for i, h in enumerate(headers_pdf):
        pdf.cell(col_widths[i], 6, h, border=0, fill=True)
    pdf.ln()

    pdf.set_font("Arial", "", 8)
    pdf.set_text_color(51, 51, 51)
    for ano in range(1, 21):
        m = ano * 12
        pdf.cell(col_widths[0], 5, str(ano), border=0)
        pdf.cell(col_widths[1], 5, fmt(pat_cons[m]), border=0)
        pdf.cell(col_widths[2], 5, fmt(patrimonio[m]), border=0)
        pdf.cell(col_widths[3], 5, fmt(pat_otim[m]), border=0)
        pdf.cell(col_widths[4], 5, fmt(aportes_acumulados[m]), border=0)
        pdf.cell(col_widths[5], 5, fmt(rendimentos_acumulados[m]), border=0)
        pdf.ln()

    pdf.ln(8)
    pdf.set_text_color(187, 187, 187)
    pdf.set_font("Arial", "", 8)
    pdf.cell(0, 5, "Mithril Capital — Patrimônio Futuro", align="C")

    pdf_buffer = BytesIO()
    pdf.output(pdf_buffer)

    st.download_button(
        label="Baixar relatório (PDF)",
        data=pdf_buffer.getvalue(),
        file_name=f"patrimonio-futuro-{date.today().isoformat()}.pdf",
        mime="application/pdf",
    )
