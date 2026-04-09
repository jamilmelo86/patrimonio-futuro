"""Simulador de Imóvel na Planta — SPE / Seazone."""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import date
from io import BytesIO
from urllib.parse import urlencode
import base64, pathlib

st.set_page_config(
    page_title="Imóvel na Planta — Mithril Capital",
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
BLUE = "#60A5FA"

# --- Logo base64 ---
logo_path = pathlib.Path(__file__).parent.parent / "assets" / "logo_main.png"
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
.metric-card .metric-value.green {{
    background: linear-gradient(135deg, #6EE7B7, {GREEN});
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}}
.metric-card .metric-value.red {{
    background: linear-gradient(135deg, #FCA5A5, {RED});
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
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

/* === Status Cards === */
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
</style>
""", unsafe_allow_html=True)

# --- Header ---
logo_html = f'<img src="data:image/png;base64,{logo_b64}" alt="Mithril Capital" />' if logo_b64 else ""
st.markdown(f"""
<div class="app-header">
    {logo_html}
    <h1>Imóvel na <span>Planta</span></h1>
    <div class="subtitle">Simule o investimento completo: da compra na planta à geração de renda</div>
    <div class="gold-line"></div>
</div>
""", unsafe_allow_html=True)


def fmt(v):
    """Formata valor em R$ com separadores brasileiros."""
    return f"R$ {v:,.0f}".replace(",", ".")


# --- Query params ---
qp = st.query_params

# --- Inputs ---
st.markdown('<div class="section-header">Dados do Imóvel</div>', unsafe_allow_html=True)

with st.container(border=True):
    col1, col2 = st.columns(2)

    with col1:
        valor_imovel = st.number_input(
            "Valor do imóvel na planta (R$)",
            min_value=0.0, value=float(qp.get("vi", 500_000)), step=50_000.0, format="%.2f",
        )
        st.caption(fmt(valor_imovel))

        entrada = st.number_input(
            "Entrada (R$)",
            min_value=0.0, value=float(qp.get("e", 100_000)), step=10_000.0, format="%.2f",
        )
        st.caption(fmt(entrada))

        prazo_obra = st.number_input(
            "Prazo da obra (meses)",
            min_value=6, max_value=120, value=int(qp.get("po", 60)), step=6,
        )

    with col2:
        num_parcelas = st.number_input(
            "Parcelas mensais durante obra",
            min_value=0, max_value=120, value=int(qp.get("np", 48)), step=6,
        )

        valor_parcela = st.number_input(
            "Valor da parcela mensal (R$)",
            min_value=0.0, value=float(qp.get("vp", 2_000)), step=500.0, format="%.2f",
        )
        if valor_parcela > 0:
            st.caption(fmt(valor_parcela))

        valor_chaves = st.number_input(
            "Valor nas chaves (R$)",
            min_value=0.0, value=float(qp.get("vc", 0)), step=10_000.0, format="%.2f",
            help="Saldo restante pago na entrega das chaves.",
        )
        if valor_chaves > 0:
            st.caption(fmt(valor_chaves))

st.markdown('<div class="section-header">Valorização e Renda</div>', unsafe_allow_html=True)

with st.container(border=True):
    col3, col4 = st.columns(2)

    with col3:
        valorizacao_obra = st.number_input(
            "Valorização durante obra (% a.a.)",
            min_value=0.0, max_value=50.0, value=float(qp.get("vo", 8)), step=1.0, format="%.1f",
            help="Valorização anual estimada do imóvel durante a construção.",
        )

        valorizacao_pos = st.number_input(
            "Valorização pós-entrega (% a.a.)",
            min_value=0.0, max_value=30.0, value=float(qp.get("vpe", 4)), step=0.5, format="%.1f",
            help="Valorização anual estimada após entrega.",
        )

        horizonte_pos = st.number_input(
            "Horizonte pós-entrega (anos)",
            min_value=1, max_value=30, value=int(qp.get("hp", 10)), step=1,
            help="Quantos anos simular após a entrega do imóvel.",
        )

    with col4:
        receita_mensal = st.number_input(
            "Receita bruta mensal estimada (R$)",
            min_value=0.0, value=float(qp.get("rm", 4_000)), step=500.0, format="%.2f",
            help="Receita média mensal com aluguel (short stay ou longo prazo).",
        )
        if receita_mensal > 0:
            st.caption(fmt(receita_mensal))

        taxa_administracao = st.number_input(
            "Taxa de administração (%)",
            min_value=0.0, max_value=50.0, value=float(qp.get("ta", 20)), step=5.0, format="%.0f",
            help="Percentual da receita bruta retido pela administradora (ex: Seazone ~20%).",
        )

        custos_fixos = st.number_input(
            "Custos fixos mensais (R$)",
            min_value=0.0, value=float(qp.get("cf", 800)), step=100.0, format="%.2f",
            help="Condomínio, IPTU, seguro e outros custos mensais.",
        )
        if custos_fixos > 0:
            st.caption(fmt(custos_fixos))

st.markdown('<div class="section-header">Comparativo</div>', unsafe_allow_html=True)

with st.container(border=True):
    taxa_comparativa = st.number_input(
        "Taxa de referência para comparação (% a.a.)",
        min_value=0.0, max_value=30.0, value=float(qp.get("tc", 10)), step=0.5, format="%.1f",
        help="Se o mesmo dinheiro fosse investido no mercado financeiro, qual seria a taxa?",
    )

# --- Cálculos ---
horizonte_total = prazo_obra + horizonte_pos * 12

fluxo_caixa = []
fluxo_acumulado = []
valor_imovel_hist = []
patrimonio_liquido = []
investimento_alt = []

renda_liquida_mensal = receita_mensal * (1 - taxa_administracao / 100) - custos_fixos
total_investido = 0.0
acumulado = 0.0
alt_patrimonio = 0.0
taxa_alt_mensal = (1 + taxa_comparativa / 100) ** (1 / 12) - 1
taxa_val_obra_mensal = (1 + valorizacao_obra / 100) ** (1 / 12) - 1
taxa_val_pos_mensal = (1 + valorizacao_pos / 100) ** (1 / 12) - 1

payback_mes = None
valor_im = valor_imovel

for mes in range(horizonte_total + 1):
    if mes == 0:
        valor_im = valor_imovel
    elif mes <= prazo_obra:
        valor_im = valor_im * (1 + taxa_val_obra_mensal)
    else:
        valor_im = valor_im * (1 + taxa_val_pos_mensal)

    valor_imovel_hist.append(valor_im)

    fluxo_mes = 0.0

    if mes == 0:
        fluxo_mes = -entrada
    elif mes <= prazo_obra:
        if mes <= num_parcelas:
            fluxo_mes = -valor_parcela
        if mes == prazo_obra and valor_chaves > 0:
            fluxo_mes -= valor_chaves
    else:
        fluxo_mes = renda_liquida_mensal

    fluxo_caixa.append(fluxo_mes)
    acumulado += fluxo_mes
    fluxo_acumulado.append(acumulado)

    if fluxo_mes < 0:
        total_investido_mes = -fluxo_mes
    else:
        total_investido_mes = 0

    alt_patrimonio = alt_patrimonio * (1 + taxa_alt_mensal) + total_investido_mes
    investimento_alt.append(alt_patrimonio)

    pat_liq = valor_im + acumulado
    patrimonio_liquido.append(pat_liq)

    if payback_mes is None and mes > prazo_obra and acumulado >= 0:
        payback_mes = mes

total_desembolsado = -sum(f for f in fluxo_caixa if f < 0)
total_renda_recebida = sum(f for f in fluxo_caixa if f > 0)

valor_final_imovel = valor_imovel_hist[-1]
lucro_valorizacao = valor_final_imovel - valor_imovel

retorno_total = valor_final_imovel + total_renda_recebida - total_desembolsado
roi_pct = (retorno_total / total_desembolsado) * 100 if total_desembolsado > 0 else 0


def calcular_tir(fluxos, chute_min=-0.5, chute_max=2.0, iteracoes=200, tol=1e-7):
    """Calcula TIR mensal por bisection, retorna anualizada."""
    fluxos_tir = fluxos.copy()
    fluxos_tir[-1] += valor_final_imovel

    def vpn(taxa):
        return sum(f / (1 + taxa) ** i for i, f in enumerate(fluxos_tir))

    lo, hi = chute_min, chute_max
    for _ in range(iteracoes):
        mid = (lo + hi) / 2
        v = vpn(mid)
        if abs(v) < tol:
            break
        if v > 0:
            lo = mid
        else:
            hi = mid

    tir_mensal = (lo + hi) / 2
    tir_anual = (1 + tir_mensal) ** 12 - 1
    return tir_anual * 100


try:
    tir = calcular_tir(fluxo_caixa)
except Exception:
    tir = None

# --- Métricas principais ---
st.markdown('<div class="section-header">Resultado do Investimento</div>', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Total investido</div>
        <div class="metric-value">{fmt(total_desembolsado)}</div>
        <div class="metric-detail">
            Entrada: {fmt(entrada)}<br>
            Parcelas: {fmt(valor_parcela * num_parcelas)}<br>
            Chaves: {fmt(valor_chaves)}
        </div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Valor do imóvel final</div>
        <div class="metric-value">{fmt(valor_final_imovel)}</div>
        <div class="metric-detail">
            Compra: {fmt(valor_imovel)}<br>
            Valorização: {fmt(lucro_valorizacao)}<br>
            (+{lucro_valorizacao / valor_imovel * 100:.0f}%)
        </div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Renda acumulada</div>
        <div class="metric-value green">{fmt(total_renda_recebida)}</div>
        <div class="metric-detail">
            Renda líq./mês: {fmt(renda_liquida_mensal)}<br>
            Meses operando: {horizonte_pos * 12}
        </div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    tir_str = f"{tir:.1f}% a.a." if tir is not None else "N/A"
    tir_cls = "green" if tir is not None and tir > 0 else "red"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">TIR (IRR)</div>
        <div class="metric-value {tir_cls}">{tir_str}</div>
        <div class="metric-detail">
            ROI total: {roi_pct:.0f}%<br>
            Retorno líquido: {fmt(retorno_total)}
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- Payback ---
if payback_mes is not None:
    anos_pb = payback_mes // 12
    meses_pb = payback_mes % 12
    tempo_pb = f"{anos_pb} anos" if meses_pb == 0 else f"{anos_pb} anos e {meses_pb} meses"
    tempo_pos_entrega = payback_mes - prazo_obra
    anos_pe = tempo_pos_entrega // 12
    meses_pe = tempo_pos_entrega % 12
    tempo_pe_str = f"{anos_pe} anos" if meses_pe == 0 else f"{anos_pe} anos e {meses_pe} meses"
    st.markdown(f"""
    <div class="status-card gold">
        <div class="status-icon">&#9733;</div>
        <div class="status-content">
            <strong>Payback em {tempo_pb}</strong>
            <span>{tempo_pe_str} após a entrega — a renda acumulada cobre todo o valor investido</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div class="status-card warning">
        <div class="status-icon">&#9888;</div>
        <div class="status-content">
            <strong>Payback não atingido</strong>
            <span>A renda acumulada não cobre o investimento em {horizonte_pos} anos após a entrega</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- Comparativo ---
alt_final = investimento_alt[-1]
diferenca = patrimonio_liquido[-1] - alt_final
melhor = "Imóvel" if diferenca >= 0 else "Mercado financeiro"

if diferenca >= 0:
    st.markdown(f"""
    <div class="status-card success">
        <div class="status-icon">&#9734;</div>
        <div class="status-content">
            <strong>Comparativo: {melhor} vence</strong>
            <span>Imóvel (patrimônio líquido): <strong>{fmt(patrimonio_liquido[-1])}</strong> &nbsp;|&nbsp;
            Mercado ({taxa_comparativa:.1f}% a.a.): <strong>{fmt(alt_final)}</strong> &nbsp;|&nbsp;
            Diferença: <strong>{fmt(abs(diferenca))}</strong> a favor do imóvel</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div class="status-card warning">
        <div class="status-icon">&#9888;</div>
        <div class="status-content">
            <strong>Comparativo: {melhor} vence</strong>
            <span>Imóvel (patrimônio líquido): <strong>{fmt(patrimonio_liquido[-1])}</strong> &nbsp;|&nbsp;
            Mercado ({taxa_comparativa:.1f}% a.a.): <strong>{fmt(alt_final)}</strong> &nbsp;|&nbsp;
            Diferença: <strong>{fmt(abs(diferenca))}</strong> a favor do mercado</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- Gráfico: Fluxo de caixa acumulado ---
st.markdown('<div class="section-header">Fluxo de Caixa Acumulado</div>', unsafe_allow_html=True)

meses = list(range(horizonte_total + 1))
anos_x = [m / 12 for m in meses]

fig1 = go.Figure()

fig1.add_trace(go.Scatter(
    x=anos_x,
    y=fluxo_acumulado,
    name="Fluxo acumulado",
    fill="tozeroy",
    fillcolor="rgba(191, 155, 48, 0.08)",
    line=dict(color=GOLD, width=2),
    hovertemplate="Ano %{x:.1f}<br>Acumulado: R$ %{y:,.0f}<extra></extra>",
))

fig1.add_hline(y=0, line_color="rgba(139,157,175,0.2)", line_width=1)

fig1.add_vline(
    x=prazo_obra / 12, line_dash="dash", line_color="rgba(139,157,175,0.3)", line_width=1,
    annotation_text="Entrega", annotation_position="top",
    annotation_font=dict(color=STEEL, size=11),
)

if payback_mes is not None:
    fig1.add_trace(go.Scatter(
        x=[payback_mes / 12],
        y=[0],
        mode="markers+text",
        marker=dict(size=12, color=GREEN, symbol="star"),
        text=["Payback"],
        textposition="top center",
        textfont=dict(color=GREEN, size=11),
        name="Payback",
        hovertemplate="Payback<br>Ano %{x:.1f}<extra></extra>",
    ))

fig1.update_layout(
    xaxis_title="Anos",
    yaxis_title="Fluxo Acumulado (R$)",
    yaxis_tickformat=",.",
    hovermode="x unified",
    legend=dict(
        orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
        font=dict(size=11, color=STEEL, family="DM Sans"),
        bgcolor="rgba(0,0,0,0)",
    ),
    height=420,
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

st.plotly_chart(fig1, use_container_width=True)

# --- Gráfico: Patrimônio líquido vs alternativa ---
st.markdown('<div class="section-header">Patrimônio: Imóvel vs Mercado Financeiro</div>', unsafe_allow_html=True)

fig2 = go.Figure()

fig2.add_trace(go.Scatter(
    x=anos_x,
    y=patrimonio_liquido,
    name="Imóvel (valor + renda)",
    line=dict(color=GOLD, width=3),
    hovertemplate="Ano %{x:.1f}<br>Imóvel: R$ %{y:,.0f}<extra></extra>",
))

fig2.add_trace(go.Scatter(
    x=anos_x,
    y=investimento_alt,
    name=f"Mercado ({taxa_comparativa:.1f}% a.a.)",
    line=dict(color=BLUE, width=2, dash="dash"),
    hovertemplate="Ano %{x:.1f}<br>Mercado: R$ %{y:,.0f}<extra></extra>",
))

fig2.add_trace(go.Scatter(
    x=anos_x,
    y=valor_imovel_hist,
    name="Valor do imóvel",
    line=dict(color="rgba(191,155,48,0.4)", width=1, dash="dot"),
    hovertemplate="Ano %{x:.1f}<br>Imóvel: R$ %{y:,.0f}<extra></extra>",
))

fig2.add_vline(
    x=prazo_obra / 12, line_dash="dash", line_color="rgba(139,157,175,0.3)", line_width=1,
    annotation_text="Entrega", annotation_position="top",
    annotation_font=dict(color=STEEL, size=11),
)

fig2.update_layout(
    xaxis_title="Anos",
    yaxis_title="Patrimônio (R$)",
    yaxis_tickformat=",.",
    hovermode="x unified",
    legend=dict(
        orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
        font=dict(size=11, color=STEEL, family="DM Sans"),
        bgcolor="rgba(0,0,0,0)",
    ),
    height=460,
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

st.plotly_chart(fig2, use_container_width=True)

# --- Tabela detalhada ---
st.markdown('<div class="section-header">Detalhamento Anual</div>', unsafe_allow_html=True)

with st.expander("Ver tabela completa"):
    dados = []
    for ano in range(1, (horizonte_total // 12) + 1):
        m = ano * 12
        if m > horizonte_total:
            break
        fase = "Obra" if m <= prazo_obra else "Operação"
        dados.append({
            "Ano": ano,
            "Fase": fase,
            "Valor Imóvel": fmt(valor_imovel_hist[m]),
            "Fluxo Acumulado": fmt(fluxo_acumulado[m]),
            "Patrimônio Líquido": fmt(patrimonio_liquido[m]),
            "Alternativa Mercado": fmt(investimento_alt[m]),
        })

    df = pd.DataFrame(dados)
    st.dataframe(df, use_container_width=True, hide_index=True)

# --- Compartilhar ---
st.markdown('<div class="section-header">Compartilhar Simulação</div>', unsafe_allow_html=True)

params = urlencode({
    "vi": valor_imovel, "e": entrada, "po": prazo_obra,
    "np": num_parcelas, "vp": valor_parcela, "vc": valor_chaves,
    "vo": valorizacao_obra, "vpe": valorizacao_pos, "hp": horizonte_pos,
    "rm": receita_mensal, "ta": taxa_administracao, "cf": custos_fixos,
    "tc": taxa_comparativa,
})
st.text_input("Link da simulação (copie e compartilhe)", value=f"?{params}")

# --- Relatórios ---
chart1_html = fig1.to_html(include_plotlyjs="cdn", full_html=False)
chart2_html = fig2.to_html(include_plotlyjs="cdn", full_html=False)

table_rows = ""
for d in dados:
    table_rows += f"<tr><td>{d['Ano']}</td><td>{d['Fase']}</td><td>{d['Valor Imóvel']}</td><td>{d['Fluxo Acumulado']}</td><td>{d['Patrimônio Líquido']}</td><td>{d['Alternativa Mercado']}</td></tr>"

payback_html = ""
if payback_mes is not None:
    payback_html = f'<div class="card gold">Payback em <strong>{tempo_pb}</strong> ({tempo_pe_str} após entrega) — renda acumulada cobre o investimento</div>'
else:
    payback_html = f'<div class="card warning">Payback não atingido em {horizonte_pos} anos após entrega</div>'

comp_html = f"""<div class="card {'success' if diferenca >= 0 else 'warning'}">
    <strong>Comparativo: {melhor} vence</strong><br>
    Imóvel: {fmt(patrimonio_liquido[-1])} | Mercado ({taxa_comparativa:.1f}%): {fmt(alt_final)} | Diferença: {fmt(abs(diferenca))}
</div>"""

report_html = f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="UTF-8">
<title>Imóvel na Planta — Mithril Capital</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#E0E0E0;background:#0F1117;padding:2rem;max-width:1000px;margin:0 auto}}
.header{{text-align:center;margin-bottom:2rem}}
.header h1{{font-size:2rem;color:#fff}} .header h1 span{{color:#BF9B30}}
.header .date{{color:#8B9DAF;font-size:0.9rem;margin-top:0.5rem}}
.params{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:0.75rem;margin-bottom:2rem}}
.param{{background:#1E222A;border:1px solid rgba(139,157,175,0.12);border-radius:10px;padding:0.75rem 1rem}}
.param .label{{font-size:0.75rem;color:#8B9DAF;text-transform:uppercase;letter-spacing:0.05em}}
.param .value{{font-size:1.05rem;font-weight:600;color:#E0E0E0;margin-top:0.1rem}}
.metrics{{display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;margin-bottom:1.5rem}}
.metric{{background:#1E222A;border:1px solid rgba(139,157,175,0.12);border-radius:14px;padding:1.25rem;text-align:center}}
.metric .mlabel{{font-size:0.75rem;color:#8B9DAF;text-transform:uppercase;letter-spacing:0.06em}}
.metric .mvalue{{font-size:1.4rem;font-weight:700;color:#BF9B30;margin:0.2rem 0}}
.metric .mvalue.green{{color:#34D399}}
.metric .mdetail{{font-size:0.75rem;color:#8B9DAF;margin-top:0.3rem;line-height:1.5}}
.card{{background:#1E222A;border-radius:12px;padding:1rem 1.25rem;margin-bottom:1rem;border-left:3px solid #BF9B30}}
.card.gold{{border-left-color:#BF9B30}} .card.success{{border-left-color:#34D399}} .card.warning{{border-left-color:#FBBF24}}
.section-title{{font-size:0.85rem;font-weight:600;color:#8B9DAF;text-transform:uppercase;letter-spacing:0.1em;margin:1.5rem 0 1rem;border-bottom:1px solid rgba(139,157,175,0.12);padding-bottom:0.4rem}}
table{{width:100%;border-collapse:collapse;font-size:0.82rem;margin-top:1rem}}
th{{background:#1A1D23;color:#8B9DAF;font-weight:600;text-align:left;padding:0.6rem;border-bottom:1px solid rgba(139,157,175,0.15)}}
td{{padding:0.5rem 0.6rem;border-bottom:1px solid rgba(139,157,175,0.06);color:#C0C0C0}}
.footer{{text-align:center;color:rgba(139,157,175,0.4);font-size:0.78rem;margin-top:2rem;padding-top:1rem;border-top:1px solid rgba(139,157,175,0.1)}}
@media print{{body{{background:#fff;color:#333}} .metric .mvalue{{color:#BF9B30}} th{{background:#f5f5f5;color:#666}} td{{color:#333}}}}
</style></head><body>
<div class="header"><h1>Imóvel na <span>Planta</span></h1><div class="date">Mithril Capital — {date.today().strftime('%d/%m/%Y')}</div></div>
<div class="params">
<div class="param"><div class="label">Valor na planta</div><div class="value">{fmt(valor_imovel)}</div></div>
<div class="param"><div class="label">Entrada</div><div class="value">{fmt(entrada)}</div></div>
<div class="param"><div class="label">Parcelas</div><div class="value">{num_parcelas}x {fmt(valor_parcela)}</div></div>
<div class="param"><div class="label">Chaves</div><div class="value">{fmt(valor_chaves)}</div></div>
<div class="param"><div class="label">Prazo obra</div><div class="value">{prazo_obra} meses</div></div>
<div class="param"><div class="label">Valorização obra</div><div class="value">{valorizacao_obra:.1f}% a.a.</div></div>
<div class="param"><div class="label">Receita mensal</div><div class="value">{fmt(receita_mensal)}</div></div>
<div class="param"><div class="label">Administração</div><div class="value">{taxa_administracao:.0f}%</div></div>
<div class="param"><div class="label">Custos fixos</div><div class="value">{fmt(custos_fixos)}/mês</div></div>
</div>
<div class="section-title">Resultado</div>
<div class="metrics">
<div class="metric"><div class="mlabel">Total investido</div><div class="mvalue">{fmt(total_desembolsado)}</div><div class="mdetail">Entrada + Parcelas + Chaves</div></div>
<div class="metric"><div class="mlabel">Valor imóvel final</div><div class="mvalue">{fmt(valor_final_imovel)}</div><div class="mdetail">+{lucro_valorizacao / valor_imovel * 100:.0f}% valorização</div></div>
<div class="metric"><div class="mlabel">Renda acumulada</div><div class="mvalue green">{fmt(total_renda_recebida)}</div><div class="mdetail">{fmt(renda_liquida_mensal)}/mês x {horizonte_pos * 12} meses</div></div>
<div class="metric"><div class="mlabel">TIR</div><div class="mvalue green">{f"{tir:.1f}% a.a." if tir else "N/A"}</div><div class="mdetail">ROI: {roi_pct:.0f}%</div></div>
</div>
{payback_html}
{comp_html}
<div class="section-title">Fluxo de Caixa Acumulado</div>
<div class="chart">{chart1_html}</div>
<div class="section-title">Patrimônio: Imóvel vs Mercado</div>
<div class="chart">{chart2_html}</div>
<div class="section-title">Detalhamento Anual</div>
<table><thead><tr><th>Ano</th><th>Fase</th><th>Valor Imóvel</th><th>Fluxo Acum.</th><th>Patrim. Líquido</th><th>Alternativa</th></tr></thead><tbody>{table_rows}</tbody></table>
<div class="footer">Mithril Capital — Imóvel na Planta</div>
</body></html>"""

# --- Botões de download ---
col_dl1, col_dl2 = st.columns(2)

with col_dl1:
    st.download_button(
        label="Baixar relatório (HTML)",
        data=report_html,
        file_name=f"imovel-planta-{date.today().isoformat()}.html",
        mime="text/html",
    )

with col_dl2:
    from fpdf import FPDF
    import tempfile, os

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    _font_dir = pathlib.Path(__file__).parent.parent / "assets" / "fonts"
    pdf.add_font("Arial", "", str(_font_dir / "arial.ttf"), uni=True)
    pdf.add_font("Arial", "B", str(_font_dir / "arialbd.ttf"), uni=True)
    pdf.add_page()

    # Header
    pdf.set_font("Arial", "B", 22)
    pdf.cell(0, 12, "Imóvel na Planta", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_draw_color(191, 155, 48)
    pdf.set_line_width(0.8)
    pdf.line(85, pdf.get_y(), 125, pdf.get_y())
    pdf.ln(4)
    pdf.set_font("Arial", "", 10)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 6, f"Mithril Capital — {date.today().strftime('%d/%m/%Y')}", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(6)

    # Parâmetros
    pdf.set_text_color(51, 51, 51)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Parâmetros", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(191, 155, 48)
    pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 40, pdf.get_y())
    pdf.ln(3)

    pdf.set_font("Arial", "", 9)
    params_list = [
        ("Valor na planta", fmt(valor_imovel)),
        ("Entrada", fmt(entrada)),
        ("Parcelas", f"{num_parcelas}x {fmt(valor_parcela)}"),
        ("Chaves", fmt(valor_chaves)),
        ("Prazo obra", f"{prazo_obra} meses"),
        ("Valorização obra", f"{valorizacao_obra:.1f}% a.a."),
        ("Valorização pós", f"{valorizacao_pos:.1f}% a.a."),
        ("Receita mensal", fmt(receita_mensal)),
        ("Administração", f"{taxa_administracao:.0f}%"),
        ("Custos fixos", f"{fmt(custos_fixos)}/mês"),
        ("Horizonte pós-entrega", f"{horizonte_pos} anos"),
        ("Taxa comparativa", f"{taxa_comparativa:.1f}% a.a."),
    ]

    col_w = 63
    for i, (label, value) in enumerate(params_list):
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

    # Resultados
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(51, 51, 51)
    pdf.cell(0, 8, "Resultado", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(191, 155, 48)
    pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 30, pdf.get_y())
    pdf.ln(3)

    results = [
        ("Total investido", fmt(total_desembolsado)),
        ("Valor imóvel final", fmt(valor_final_imovel)),
        ("Renda acumulada", fmt(total_renda_recebida)),
        ("TIR", f"{tir:.1f}% a.a." if tir else "N/A"),
    ]

    y_res = pdf.get_y()
    box_w = 45
    for i, (label, value) in enumerate(results):
        x = 10 + i * box_w
        pdf.set_xy(x, y_res)
        pdf.set_text_color(136, 136, 136)
        pdf.set_font("Arial", "", 7)
        pdf.cell(box_w, 3.5, label.upper(), new_x="LEFT", new_y="NEXT")
        pdf.set_xy(x, pdf.get_y())
        pdf.set_text_color(191, 155, 48)
        pdf.set_font("Arial", "B", 13)
        pdf.cell(box_w, 7, value, new_x="LEFT", new_y="NEXT")
        pdf.set_xy(x, pdf.get_y())
        pdf.set_text_color(102, 102, 102)
        pdf.set_font("Arial", "", 8)
        if i == 0:
            pdf.cell(box_w, 4, f"Entrada + Parcelas + Chaves")
        elif i == 1:
            pdf.cell(box_w, 4, f"+{lucro_valorizacao / valor_imovel * 100:.0f}% valorização")
        elif i == 2:
            pdf.cell(box_w, 4, f"{fmt(renda_liquida_mensal)}/mês x {horizonte_pos * 12} meses")
        elif i == 3:
            pdf.cell(box_w, 4, f"ROI total: {roi_pct:.0f}%")

    pdf.ln(12)

    # Payback
    pdf.set_text_color(51, 51, 51)
    pdf.set_font("Arial", "B", 10)
    if payback_mes is not None:
        pdf.cell(0, 6, f"Payback em {tempo_pb} ({tempo_pe_str} após entrega)", new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.cell(0, 6, f"Payback não atingido em {horizonte_pos} anos após entrega", new_x="LMARGIN", new_y="NEXT")

    # Comparativo
    pdf.set_font("Arial", "", 9)
    pdf.cell(0, 5, f"Comparativo: {melhor} vence | Imóvel: {fmt(patrimonio_liquido[-1])} | Mercado: {fmt(alt_final)} | Diferença: {fmt(abs(diferenca))}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    # Gráficos como imagens
    with tempfile.TemporaryDirectory() as tmpdir:
        img1_path = os.path.join(tmpdir, "chart1.png")
        img2_path = os.path.join(tmpdir, "chart2.png")

        fig1.update_layout(
            paper_bgcolor="#FFFFFF", plot_bgcolor="#FAFAFA",
            font=dict(color="#333"),
            xaxis=dict(tickfont=dict(color="#666"), linecolor="#DDD", gridcolor="#EEE"),
            yaxis=dict(tickfont=dict(color="#666"), linecolor="#DDD", gridcolor="#EEE"),
        )
        fig2.update_layout(
            paper_bgcolor="#FFFFFF", plot_bgcolor="#FAFAFA",
            font=dict(color="#333"),
            xaxis=dict(tickfont=dict(color="#666"), linecolor="#DDD", gridcolor="#EEE"),
            yaxis=dict(tickfont=dict(color="#666"), linecolor="#DDD", gridcolor="#EEE"),
        )

        fig1.write_image(img1_path, width=900, height=380, scale=2)
        fig2.write_image(img2_path, width=900, height=400, scale=2)

        pdf.set_font("Arial", "B", 12)
        pdf.set_text_color(51, 51, 51)
        pdf.cell(0, 8, "Fluxo de Caixa Acumulado", new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(191, 155, 48)
        pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 55, pdf.get_y())
        pdf.ln(2)
        pdf.image(img1_path, x=10, w=190)
        pdf.ln(4)

        pdf.add_page()
        pdf.set_font("Arial", "B", 12)
        pdf.set_text_color(51, 51, 51)
        pdf.cell(0, 8, "Patrimônio: Imóvel vs Mercado Financeiro", new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(191, 155, 48)
        pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 75, pdf.get_y())
        pdf.ln(2)
        pdf.image(img2_path, x=10, w=190)
        pdf.ln(6)

    # Tabela
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Detalhamento Anual", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(191, 155, 48)
    pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 48, pdf.get_y())
    pdf.ln(3)

    headers = ["Ano", "Fase", "Valor Imóvel", "Fluxo Acum.", "Patrim. Líq.", "Alternativa"]
    col_widths = [15, 22, 38, 38, 38, 38]

    pdf.set_fill_color(245, 242, 235)
    pdf.set_text_color(102, 102, 102)
    pdf.set_font("Arial", "B", 8)
    for i, h in enumerate(headers):
        pdf.cell(col_widths[i], 6, h, border=0, fill=True)
    pdf.ln()

    pdf.set_font("Arial", "", 8)
    pdf.set_text_color(51, 51, 51)
    for d in dados:
        pdf.cell(col_widths[0], 5, str(d["Ano"]), border=0)
        pdf.cell(col_widths[1], 5, d["Fase"], border=0)
        pdf.cell(col_widths[2], 5, d["Valor Imóvel"], border=0)
        pdf.cell(col_widths[3], 5, d["Fluxo Acumulado"], border=0)
        pdf.cell(col_widths[4], 5, d["Patrimônio Líquido"], border=0)
        pdf.cell(col_widths[5], 5, d["Alternativa Mercado"], border=0)
        pdf.ln()

    # Footer
    pdf.ln(8)
    pdf.set_text_color(187, 187, 187)
    pdf.set_font("Arial", "", 8)
    pdf.cell(0, 5, "Mithril Capital — Imóvel na Planta", align="C")

    pdf_buffer = BytesIO()
    pdf.output(pdf_buffer)

    st.download_button(
        label="Baixar relatório (PDF)",
        data=pdf_buffer.getvalue(),
        file_name=f"imovel-planta-{date.today().isoformat()}.pdf",
        mime="application/pdf",
    )
