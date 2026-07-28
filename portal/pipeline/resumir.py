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

from fontes import Artigo

CATEGORIAS_VALIDAS = [
    "ciencia", "solidariedade", "meio-ambiente", "saude",
    "animais", "superacao", "tecnologia", "mundo",
]

MODELO = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")


PROMPT_SISTEMA = """Você é editor(a) de um portal brasileiro de NOTÍCIAS POSITIVAS.
Sua tarefa é transformar a referência de uma notícia em um resumo ORIGINAL em
português do Brasil, claro e otimista, SEM copiar frases da fonte.

Regras:
- NUNCA copie trechos literais; reescreva com suas próprias palavras.
- Seja factual: não invente números, nomes ou fatos que não estejam na referência.
- Publique SOMENTE se for um FATO ou EVENTO jornalístico real e recente. Marque
  "eh_boa_noticia": false (vetar) se for: notícia trágica/negativa; opinião ou
  editorial; texto de autoajuda, motivacional, religioso ou filosófico; horóscopo;
  receita; lista/curiosidades genéricas ("X dicas", "X frases", "X coisas que...");
  publicidade ou divulgação de produto/curso/serviço; resenha; ou fofoca/entretenimento
  de celebridade sem um fato concreto e relevante.
- Escolha a categoria que MELHOR descreve o fato central. Se a matéria não encaixar
  bem em nenhuma editoria, prefira vetar em vez de forçar uma categoria errada.
- O corpo deve ter de 4 a 6 parágrafos (aproximadamente 250 a 380 palavras),
  explicando o que aconteceu, o contexto, por que importa e o impacto. Nada de
  resumo raso: desenvolva a história com clareza.
- Não inclua a fonte no corpo (o site já mostra o crédito com o link específico).

Responda SOMENTE com um objeto JSON válido, sem texto ao redor, no formato:
{
  "eh_boa_noticia": true/false,
  "titulo": "título original em pt-BR",
  "resumo": "1 frase de chamada (máx 160 caracteres)",
  "corpo": "4 a 6 parágrafos (250-380 palavras) separados por \\n\\n",
  "categoria": "um de: ciencia, solidariedade, meio-ambiente, saude, animais, superacao, tecnologia, mundo",
  "tags": ["palavra1", "palavra2"]
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

    referencia = (
        f"Título da fonte: {artigo.titulo}\n"
        f"Veículo: {artigo.fonte_nome}\n"
        f"Idioma original: {artigo.idioma}\n"
        f"Resumo/trecho da fonte: {_limpar_html(artigo.trecho)[:1500]}"
    )

    try:
        cliente = anthropic.Anthropic(api_key=chave)
        resposta = cliente.messages.create(
            model=MODELO,
            max_tokens=2000,
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
