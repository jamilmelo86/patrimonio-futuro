"""Robô revisor — roda a cada 2 dias.

Relê as notícias PUBLICADAS e usa a IA (Claude Haiku) como editor(a)-chefe para:
  - corrigir erros de português, clareza e formatação;
  - corrigir categoria errada;
  - DESPUBLICAR (voltar a draft:true) o que estiver fraco, confuso, duvidoso, fora
    do tom ou que não seja uma notícia de fato.

Princípio de segurança: NÃO inventa fatos. Se suspeitar de um problema factual que
não dá para corrigir com segurança, o revisor DESPUBLICA em vez de "consertar"
chutando. (Ele não acessa a fonte; avalia texto, coerência e qualidade.)

Guarda um registro (_estado/revisados.json) do hash de cada post já revisado, para
revisar só o que é novo ou mudou. Limite por execução via MAX_REVISAR.

Uso:
    python revisar.py
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
CONTENT_DIR = Path(os.getenv("CONTENT_DIR", RAIZ.parent / "site" / "src" / "content" / "posts"))
LEDGER = RAIZ / "_estado" / "revisados.json"
MAX_REVISAR = int(os.getenv("MAX_REVISAR", "12"))
MODELO = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

CATEGORIAS_VALIDAS = [
    "ciencia", "solidariedade", "meio-ambiente", "saude",
    "animais", "superacao", "tecnologia", "mundo",
]

PROMPT_SISTEMA = """Você é revisor(a)-chefe de um portal brasileiro de NOTÍCIAS POSITIVAS.
Recebe uma notícia JÁ PUBLICADA (título, chamada, categoria, texto e fonte) e faz
o controle de qualidade final, com rigor de editor(a) experiente.

Avalie:
- Português: gramática, ortografia, pontuação, concordância.
- Clareza e fluidez; parágrafos bem formados (4 a 6 parágrafos).
- Se o título e a chamada combinam com o texto e não são sensacionalistas.
- Se a categoria está correta (senão, corrija).
- Se é mesmo uma BOA NOTÍCIA séria e de interesse — NÃO pode ser opinião, autoajuda,
  motivacional, religioso, horóscopo, receita, lista genérica, propaganda ou fofoca.
- Coerência interna: sem contradições, frases sem sentido ou trechos truncados.

Regras:
- NÃO invente fatos novos nem números; só melhore a forma do que já existe.
- Se houver suspeita de erro factual/exagero que você NÃO pode corrigir com segurança
  (ex.: "cura milagrosa", número improvável), escolha "despublicar".
- Se já estiver bom, escolha "manter" (seja conservador; não reescreva à toa).

Responda SOMENTE com um objeto JSON válido, sem texto ao redor:
{
  "acao": "manter" | "corrigir" | "despublicar",
  "motivo": "explicação curta",
  "titulo": "título revisado (se corrigir)",
  "resumo": "chamada revisada (máx 160 caracteres)",
  "corpo": "texto revisado em 4 a 6 parágrafos separados por \\n\\n",
  "categoria": "um de: ciencia, solidariedade, meio-ambiente, saude, animais, superacao, tecnologia, mundo",
  "tags": ["palavra1", "palavra2"]
}"""


# --------------------------------------------------------------------------
# Leitura / escrita do arquivo Markdown (preservando o frontmatter)
# --------------------------------------------------------------------------
def _yaml_str(valor: str) -> str:
    return '"' + valor.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").strip() + '"'


def ler_post(md: Path) -> tuple[dict[str, str], str] | None:
    """Devolve (frontmatter como dict ordenado de chave->valor bruto, corpo)."""
    texto = md.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", texto, re.DOTALL)
    if not m:
        return None
    campos: dict[str, str] = {}
    for linha in m.group(1).splitlines():
        if ":" in linha and not linha.startswith(" "):
            chave, _, valor = linha.partition(":")
            campos[chave.strip()] = valor.strip()
    return campos, m.group(2).strip()


def escrever_post(md: Path, campos: dict[str, str], corpo: str) -> None:
    linhas = ["---"]
    for chave, valor in campos.items():
        linhas.append(f"{chave}: {valor}")
    linhas.append("---")
    linhas.append("")
    linhas.append(corpo.strip())
    linhas.append("")
    md.write_text("\n".join(linhas), encoding="utf-8")


def _valor_str(campos: dict[str, str], chave: str) -> str:
    """Valor de um campo de texto sem as aspas do YAML."""
    return campos.get(chave, "").strip().strip('"')


def _hash(*partes: str) -> str:
    return hashlib.sha1("||".join(partes).encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------
# Revisão por IA
# --------------------------------------------------------------------------
def _extrair_json(texto: str) -> dict | None:
    m = re.search(r"\{.*\}", texto, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


def revisar_ia(campos: dict[str, str], corpo: str) -> dict | None:
    chave = os.getenv("ANTHROPIC_API_KEY")
    if not chave:
        return None
    try:
        import anthropic  # type: ignore
    except ImportError:
        return None

    referencia = (
        f"TÍTULO: {_valor_str(campos, 'titulo')}\n"
        f"CHAMADA: {_valor_str(campos, 'resumo')}\n"
        f"CATEGORIA: {_valor_str(campos, 'categoria')}\n"
        f"FONTE: {_valor_str(campos, 'fonteNome')}\n\n"
        f"TEXTO:\n{corpo}"
    )
    try:
        cliente = anthropic.Anthropic(api_key=chave)
        resp = cliente.messages.create(
            model=MODELO,
            max_tokens=2000,
            system=PROMPT_SISTEMA,
            messages=[{"role": "user", "content": referencia}],
        )
        return _extrair_json(resp.content[0].text.strip())
    except Exception as exc:
        print(f"[revisor] erro na IA: {exc}")
        return None


def _aplicar_correcao(campos: dict[str, str], dados: dict) -> tuple[dict[str, str], str]:
    if dados.get("titulo"):
        campos["titulo"] = _yaml_str(dados["titulo"])
    if dados.get("resumo"):
        campos["resumo"] = _yaml_str(dados["resumo"])
    if dados.get("categoria") in CATEGORIAS_VALIDAS:
        campos["categoria"] = _yaml_str(dados["categoria"])
    if isinstance(dados.get("tags"), list) and dados["tags"]:
        campos["tags"] = "[" + ", ".join(_yaml_str(str(t)) for t in dados["tags"] if t) + "]"
    corpo = dados.get("corpo") or ""
    return campos, corpo


# --------------------------------------------------------------------------
def main() -> None:
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("[revisor] sem ANTHROPIC_API_KEY — nada a fazer.")
        return

    ledger: dict[str, str] = {}
    if LEDGER.exists():
        try:
            ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            ledger = {}

    posts = sorted(CONTENT_DIR.glob("*.md"))
    revisados = mantidos = corrigidos = despublicados = 0

    for md in posts:
        if revisados >= MAX_REVISAR:
            break
        lido = ler_post(md)
        if not lido:
            continue
        campos, corpo = lido
        if campos.get("draft", "false").strip().strip('"') == "true":
            continue  # só revisa o que está publicado

        assinatura = _hash(_valor_str(campos, "titulo"), corpo)
        if ledger.get(md.name) == assinatura:
            continue  # já revisado e sem mudança

        dados = revisar_ia(campos, corpo)
        revisados += 1
        if not dados:
            ledger[md.name] = assinatura
            continue

        acao = dados.get("acao", "manter")
        if acao == "despublicar":
            campos["draft"] = "true"
            escrever_post(md, campos, corpo)
            despublicados += 1
            print(f"[revisor]  ⊘ despublicado: {md.name} — {dados.get('motivo', '')[:80]}")
        elif acao == "corrigir":
            campos, novo_corpo = _aplicar_correcao(campos, dados)
            escrever_post(md, campos, novo_corpo or corpo)
            corrigidos += 1
            print(f"[revisor]  ✎ corrigido: {md.name} — {dados.get('motivo', '')[:80]}")
        else:
            mantidos += 1

        # recalcula a assinatura após possível alteração
        lido2 = ler_post(md)
        if lido2:
            c2, corpo2 = lido2
            ledger[md.name] = _hash(_valor_str(c2, "titulo"), corpo2)

    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(json.dumps(ledger, ensure_ascii=False, indent=0), encoding="utf-8")
    print(
        f"[revisor] concluído: {revisados} revisados "
        f"({mantidos} mantidos, {corrigidos} corrigidos, {despublicados} despublicados)."
    )


if __name__ == "__main__":
    main()
