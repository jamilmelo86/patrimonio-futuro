"""Reescrita editorial com IA (Claude Haiku).

Para cada artigo aprovado no filtro, a IA:
  1. Confirma se é mesmo uma boa notícia (classificação final);
  2. Escreve um TÍTULO e um RESUMO ORIGINAIS em português (reescritos, nunca
     copiados da fonte), de 2 a 4 parágrafos;
  3. Escolhe a categoria e sugere tags.

Se não houver ANTHROPIC_API_KEY (ou o SDK não estiver instalado), devolvemos um
rascunho-esqueleto SEM texto da fonte, para o humano escrever à mão — assim nunca
copiamos conteúdo de terceiros.
"""

from __future__ import annotations

import json
import os
import re

import fontes
from fontes import Artigo

CATEGORIAS_VALIDAS = [
    "ciencia", "solidariedade", "meio-ambiente", "saude",
    "animais", "superacao", "tecnologia", "mundo",
]

MODELO = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
# Confiança mínima para publicar (0 a 1). Publicação automática usa corte alto.
LIMIAR_CONFIANCA = float(os.getenv("LIMIAR_CONFIANCA", "0.7"))


PROMPT_SISTEMA = """Você é editor(a)-chefe de um portal brasileiro de NOTÍCIAS POSITIVAS.
Sua tarefa é transformar a referência de uma notícia em um resumo ORIGINAL em
português do Brasil, claro e otimista, SEM copiar frases da fonte.

As fontes são INTERNACIONAIS e vêm de vários países e idiomas (inglês, espanhol,
francês, alemão, italiano, holandês). O idioma original de cada notícia vem
indicado na referência. Portanto, TRADUZA e ADAPTE a história para o leitor
brasileiro: português natural e fluente (nunca deixe palavras no idioma original),
contexto quando o assunto for distante da realidade do Brasil, e conversão de
unidades/moeda quando ajudar (ex.: milhas → km, euros/dólares → aproximação em
reais só se fizer sentido). Se a referência estiver curta demais para traduzir com
segurança, VETE em vez de adivinhar.

IMPORTANTíSSIMO: o que você aprovar será PUBLICADO AUTOMATICAMENTE, SEM revisão
humana. Portanto, seja RIGOROSO. Na menor dúvida sobre veracidade, qualidade,
clareza ou relevância, VETE (eh_boa_noticia: false). É melhor deixar de publicar
do que publicar algo fraco, confuso ou duvidoso.

Regras:
- NUNCA copie trechos literais; reescreva com suas próprias palavras.
- Seja factual: não invente números, nomes ou fatos que não estejam na referência.
  Se a referência for curta/vaga demais para um resumo sólido e verificável, VETE
  (não preencha com invenção).
- Publique SOMENTE se for um FATO ou EVENTO jornalístico real e recente. Marque
  "eh_boa_noticia": false (vetar) se for: notícia trágica/negativa; opinião ou
  editorial; texto de autoajuda, motivacional, religioso ou filosófico; horóscopo;
  receita; lista/curiosidades genéricas ("X dicas", "X frases", "X coisas que...");
  publicidade ou divulgação de produto/curso/serviço; resenha; ou fofoca/entretenimento
  de celebridade sem um fato concreto e relevante.
- Evite temas sensíveis onde um erro seria grave (saúde/cura milagrosa, política
  partidária, religião) a menos que a referência seja clara, séria e bem embasada.
- Escolha a categoria que MELHOR descreve o fato central. Se a matéria não encaixar
  bem em nenhuma editoria, prefira vetar em vez de forçar uma categoria errada.
- ESCREVA UMA MATÉRIA APROFUNDADA E ORIGINAL, não um resumo. De 6 a 10 parágrafos
  (aproximadamente 600 a 1000 palavras), com esta estrutura:
    1. Abertura forte que apresenta o fato central e por que ele é uma boa notícia.
    2. O que aconteceu, com os fatos concretos (quem, o quê, onde, quando, números).
    3. Contexto e antecedentes: o pano de fundo que ajuda o leitor a entender a
       dimensão da história (como se chegou até aqui, o problema que ela resolve).
    4. POR QUE IMPORTA: o significado maior, o impacto nas pessoas e, quando fizer
       sentido, a relevância ou um paralelo para o leitor brasileiro.
    5. Falas, dados ou detalhes que enriquecem (sem copiar frases — reescreva).
    6. Fechamento que aponta o que vem a seguir ou a lição que fica.
- VALOR ORIGINAL (isto é essencial): não traduza nem parafraseie a matéria linha a
  linha. SINTETIZE e AGREGUE valor — explique termos, dê contexto que a fonte não
  deu, conecte com o quadro geral. O texto tem de oferecer algo que o leitor não
  teria lendo só a manchete: entendimento, contexto e clareza.
- Baseie CADA fato no material de referência fornecido. Nunca invente números,
  nomes, falas ou acontecimentos. Se o material for raso demais para uma matéria
  sólida e verificável de 600+ palavras, VETE (eh_boa_noticia: false) — é melhor
  não publicar do que encher com invenção ou repetição.
- Não inclua a fonte no corpo (o site já mostra o crédito com o link específico).
- Dê uma nota de CONFIANÇA de 0 a 1 (quão seguro você está de que é uma boa notícia
  real, relevante e bem escrita). Use < 0.7 quando tiver qualquer hesitação.
- Em "busca_imagem_en", dê 2 a 4 palavras EM INGLÊS para encontrar uma FOTO
  ilustrativa boa e genérica do tema (ex.: "sea turtle ocean", "mars rover rock",
  "solar panels field", "volunteers planting trees"). Evite nomes próprios.

Responda SOMENTE com um objeto JSON válido, sem texto ao redor, no formato:
{
  "eh_boa_noticia": true/false,
  "confianca": 0.0 a 1.0,
  "titulo": "título original em pt-BR",
  "resumo": "1 frase de chamada (máx 160 caracteres)",
  "corpo": "6 a 10 parágrafos (600-1000 palavras) separados por \\n\\n",
  "categoria": "um de: ciencia, solidariedade, meio-ambiente, saude, animais, superacao, tecnologia, mundo",
  "tags": ["palavra1", "palavra2"],
  "busca_imagem_en": "2-4 palavras em inglês para foto ilustrativa"
}"""


def _limpar_html(texto: str) -> str:
    return re.sub(r"<[^>]+>", " ", texto or "").strip()


def _fallback(artigo: Artigo) -> dict:
    """Rascunho-esqueleto quando não há IA disponível (sem texto da fonte)."""
    return {
        "eh_boa_noticia": True,
        "titulo": artigo.titulo,
        "resumo": "RASCUNHO — escreva a chamada aqui.",
        "corpo": (
            "> RASCUNHO SEM IA — escreva aqui um resumo ORIGINAL em português, "
            "com suas palavras, a partir da matéria da fonte (link abaixo). "
            "Não copie trechos.\n\n"
            "Depois, mude `draft: true` para `draft: false` para publicar."
        ),
        "categoria": "mundo",
        "tags": [t for t in artigo.tags_origem if t][:4],
        "_fallback": True,
    }


def reescrever(artigo: Artigo) -> dict | None:
    """Devolve o dicionário editorial, ou None se a IA classificar como não-positiva."""
    chave = os.getenv("ANTHROPIC_API_KEY")
    if not chave:
        return _fallback(artigo)

    try:
        import anthropic  # type: ignore
    except ImportError:
        print("[resumir] SDK anthropic não instalado — usando rascunho-esqueleto.")
        return _fallback(artigo)

    # Baixa o texto completo da matéria (material de referência para a IA escrever
    # uma peça mais profunda e sem inventar). Se falhar, usa só o trecho do RSS.
    try:
        texto_fonte = fontes.baixar_texto_fonte(artigo.url)
    except Exception:
        texto_fonte = ""

    referencia = (
        f"Título da fonte: {artigo.titulo}\n"
        f"Veículo: {artigo.fonte_nome}\n"
        f"Idioma original: {artigo.idioma}\n"
        f"Resumo/trecho da fonte: {_limpar_html(artigo.trecho)[:1500]}\n\n"
        f"Texto completo da matéria (referência para você reescrever com suas "
        f"palavras, NUNCA copiar):\n{texto_fonte or '(indisponível — use o trecho acima)'}"
    )

    try:
        cliente = anthropic.Anthropic(api_key=chave)
        resposta = cliente.messages.create(
            model=MODELO,
            max_tokens=4000,
            system=PROMPT_SISTEMA,
            messages=[{"role": "user", "content": referencia}],
        )
        bruto = resposta.content[0].text.strip()
    except Exception as exc:
        print(f"[resumir] erro na IA ({exc}) — usando rascunho-esqueleto.")
        return _fallback(artigo)

    dados = _extrair_json(bruto)
    if not dados:
        print(f"[resumir] JSON inválido para '{artigo.titulo[:50]}' — pulando.")
        return None

    if not dados.get("eh_boa_noticia", False):
        return None  # a IA vetou: não é boa notícia

    try:
        confianca = float(dados.get("confianca", 0))
    except (TypeError, ValueError):
        confianca = 0.0
    if confianca < LIMIAR_CONFIANCA:
        print(f"[resumir] confiança baixa ({confianca:.2f}) — vetado: {artigo.titulo[:50]}")
        return None

    if dados.get("categoria") not in CATEGORIAS_VALIDAS:
        dados["categoria"] = "mundo"
    return dados


def gerar_de_fonte(titulo: str, veiculo: str, idioma: str, trecho: str,
                   url: str) -> dict | None:
    """Gera uma matéria APROFUNDADA a partir da fonte (para o revisor aprofundar
    posts curtos). Baixa o texto da fonte; se não houver material suficiente,
    devolve None (não arrisca "inflar" texto sem base)."""
    chave = os.getenv("ANTHROPIC_API_KEY")
    if not chave:
        return None
    try:
        import anthropic  # type: ignore
    except ImportError:
        return None

    texto_fonte = fontes.baixar_texto_fonte(url)
    if len(texto_fonte) < 800:
        return None  # fonte indisponível/rasa — não dá para aprofundar com segurança

    referencia = (
        f"Título da fonte: {titulo}\n"
        f"Veículo: {veiculo}\n"
        f"Idioma original: {idioma or 'português'}\n"
        f"Resumo/trecho da fonte: {_limpar_html(trecho)[:1500]}\n\n"
        f"Texto completo da matéria (referência para você reescrever com suas "
        f"palavras, NUNCA copiar):\n{texto_fonte}"
    )
    try:
        cliente = anthropic.Anthropic(api_key=chave)
        resposta = cliente.messages.create(
            model=MODELO, max_tokens=4000, system=PROMPT_SISTEMA,
            messages=[{"role": "user", "content": referencia}],
        )
        dados = _extrair_json(resposta.content[0].text.strip())
    except Exception as exc:
        print(f"[resumir] erro ao aprofundar ({exc})")
        return None

    if not dados or not dados.get("eh_boa_noticia", False):
        return None
    if dados.get("categoria") not in CATEGORIAS_VALIDAS:
        dados["categoria"] = "mundo"
    return dados


def _extrair_json(texto: str) -> dict | None:
    # a IA às vezes embrulha em ```json ... ```
    m = re.search(r"\{.*\}", texto, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
