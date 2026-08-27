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

import yaml

import imagens
import resumir

RAIZ = Path(__file__).resolve().parent
CONTENT_DIR = Path(os.getenv("CONTENT_DIR", RAIZ.parent / "site" / "src" / "content" / "posts"))
LEDGER = RAIZ / "_estado" / "revisados.json"
# Conta tentativas de aprofundar cada post (desiste após MAX_TENTATIVAS falhas —
# fonte provavelmente morta/paywall — para não travar a fila todo dia).
TENTATIVAS_LEDGER = RAIZ / "_estado" / "aprofundar_tentativas.json"
MAX_TENTATIVAS = 3
MAX_REVISAR = int(os.getenv("MAX_REVISAR", "12"))
# Abaixo disto (palavras no corpo), o revisor tenta APROFUNDAR a matéria.
LIMIAR_APROFUNDAR = int(os.getenv("LIMIAR_APROFUNDAR", "450"))


def _palavras(texto: str) -> int:
    return len(re.findall(r"\w+", texto or ""))
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
  "tags": ["palavra1", "palavra2"],
  "busca_imagem_en": "2-4 palavras em inglês para uma foto ilustrativa do tema (sem nomes próprios)"
}"""


# --------------------------------------------------------------------------
# Leitura / escrita do arquivo Markdown (preservando o frontmatter)
# --------------------------------------------------------------------------
def ler_post(md: Path) -> tuple[dict, str] | None:
    """Devolve (frontmatter como dict, corpo). Usa PyYAML — lida com YAML de
    várias linhas (títulos longos, listas de tags em bloco) sem quebrar."""
    texto = md.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", texto, re.DOTALL)
    if not m:
        return None
    try:
        campos = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return None
    if not isinstance(campos, dict):
        return None
    return campos, m.group(2).strip()


def escrever_post(md: Path, campos: dict, corpo: str) -> None:
    fm = yaml.safe_dump(
        campos, allow_unicode=True, sort_keys=False, default_flow_style=False, width=4096
    ).strip()
    md.write_text(f"---\n{fm}\n---\n\n{corpo.strip()}\n", encoding="utf-8")


def _valor_str(campos: dict, chave: str) -> str:
    """Valor de um campo como texto simples."""
    v = campos.get(chave, "")
    return str(v) if v is not None else ""


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
        campos["titulo"] = dados["titulo"]
    if dados.get("resumo"):
        campos["resumo"] = dados["resumo"]
    if dados.get("categoria") in CATEGORIAS_VALIDAS:
        campos["categoria"] = dados["categoria"]
    if isinstance(dados.get("tags"), list) and dados["tags"]:
        campos["tags"] = [str(t) for t in dados["tags"] if t]
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

    tentativas: dict[str, int] = {}
    if TENTATIVAS_LEDGER.exists():
        try:
            tentativas = json.loads(TENTATIVAS_LEDGER.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            tentativas = {}

    # Processa as matérias MAIS CURTAS primeiro: assim o orçamento diário de
    # revisão é gasto aprofundando o acervo fino, não relendo o que já está bom.
    def _tamanho(md: Path) -> int:
        try:
            txt = md.read_text(encoding="utf-8")
            corpo = txt.split("---", 2)[2] if txt.startswith("---") else txt
            return len(re.findall(r"\w+", corpo))
        except Exception:
            return 10_000
    posts = sorted(CONTENT_DIR.glob("*.md"), key=_tamanho)
    revisados = mantidos = corrigidos = despublicados = imagens_add = aprofundados = 0

    for md in posts:
        if revisados >= MAX_REVISAR:
            break
        lido = ler_post(md)
        if not lido:
            continue
        campos, corpo = lido
        if campos.get("draft") is True:
            continue  # só revisa o que está publicado

        # Rede de segurança determinística: esqueleto sem IA jamais fica no ar.
        # (título não traduzido, resumo/corpo placeholder). Despublica na hora,
        # sem gastar chamada de IA.
        if "RASCUNHO" in corpo or "RASCUNHO" in _valor_str(campos, "resumo"):
            campos["draft"] = True
            escrever_post(md, campos, corpo)
            despublicados += 1
            print(f"[revisor]  ⊘ despublicado (esqueleto sem IA): {md.name}")
            continue

        assinatura = _hash(_valor_str(campos, "titulo"), corpo)
        # Uma matéria ainda curta que TEM fonte e não esgotou as tentativas de
        # aprofundamento deve ser reprocessada mesmo já estando no ledger — senão
        # ela ficaria presa curta para sempre depois de uma revisão comum antiga.
        pode_aprofundar = (
            _palavras(corpo) < LIMIAR_APROFUNDAR
            and _valor_str(campos, "fonteUrl")
            and tentativas.get(md.name, 0) < MAX_TENTATIVAS
        )
        if ledger.get(md.name) == assinatura and not pode_aprofundar:
            continue  # já revisado, sem mudança e sem como aprofundar

        # APROFUNDAR matérias curtas: reescreve como peça densa (600-1000 palavras)
        # a partir do texto da fonte. Só quando há material suficiente na fonte —
        # nunca "infla" texto sem base. É o que eleva o valor do conteúdo (AdSense).
        if _palavras(corpo) < LIMIAR_APROFUNDAR and _valor_str(campos, "fonteUrl"):
            revisados += 1
            fundo = resumir.gerar_de_fonte(
                _valor_str(campos, "titulo"), _valor_str(campos, "fonteNome"),
                _valor_str(campos, "idioma") or "português",
                _valor_str(campos, "resumo"), _valor_str(campos, "fonteUrl"),
            )
            if fundo and _palavras(fundo.get("corpo", "")) > _palavras(corpo) + 100:
                campos, corpo_final = _aplicar_correcao(campos, fundo)
                if "imagem" not in campos:
                    u, cr = imagens.buscar_imagem(
                        fundo.get("busca_imagem_en") or _valor_str(campos, "titulo"),
                        _valor_str(campos, "categoria"),
                        fonte_url=_valor_str(campos, "fonteUrl"),
                        fonte_nome=_valor_str(campos, "fonteNome"))
                    if u:
                        campos["imagem"], campos["creditoImagem"] = u, cr
                escrever_post(md, campos, corpo_final)
                ledger[md.name] = _hash(_valor_str(campos, "titulo"), corpo_final)
                tentativas.pop(md.name, None)
                aprofundados += 1
                print(f"[revisor]  ⤢ aprofundado ({_palavras(corpo)}→{_palavras(corpo_final)} pal.): {md.name}")
                continue
            # falhou (fonte rasa/indisponível): conta a tentativa e tenta de novo
            # noutro dia; só desiste (segue p/ revisão normal) após MAX_TENTATIVAS.
            tentativas[md.name] = tentativas.get(md.name, 0) + 1
            if tentativas[md.name] < MAX_TENTATIVAS:
                continue
            # Esgotou as tentativas e o texto segue muito curto (< 300 palavras):
            # a fonte não está acessível e não há como aprofundar. Tira do ar —
            # é o tipo de conteúdo fraco que derruba a avaliação do AdSense.
            if _palavras(corpo) < 300:
                campos["draft"] = True
                escrever_post(md, campos, corpo)
                ledger[md.name] = _hash(_valor_str(campos, "titulo"), corpo)
                despublicados += 1
                print(f"[revisor]  ⊘ despublicado (curto e sem fonte p/ aprofundar): {md.name}")
                continue

        dados = revisar_ia(campos, corpo)
        revisados += 1
        if not dados:
            ledger[md.name] = assinatura
            continue

        acao = dados.get("acao", "manter")
        corpo_final = corpo
        mudou = False

        if acao == "despublicar":
            campos["draft"] = True
            despublicados += 1
            mudou = True
            print(f"[revisor]  ⊘ despublicado: {md.name} — {dados.get('motivo', '')[:80]}")
        elif acao == "corrigir":
            campos, novo_corpo = _aplicar_correcao(campos, dados)
            corpo_final = novo_corpo or corpo
            corrigidos += 1
            mudou = True
            print(f"[revisor]  ✎ corrigido: {md.name} — {dados.get('motivo', '')[:80]}")
        else:
            mantidos += 1

        # Backfill de imagem de licença livre, se ainda não houver (e não despublicado)
        if acao != "despublicar" and "imagem" not in campos:
            consulta = dados.get("busca_imagem_en") or _valor_str(campos, "titulo")
            url, credito = imagens.buscar_imagem(
                consulta, _valor_str(campos, "categoria"),
                fonte_url=_valor_str(campos, "fonteUrl"),
                fonte_nome=_valor_str(campos, "fonteNome"),
            )
            if url:
                campos["imagem"] = url
                campos["creditoImagem"] = credito
                mudou = True
                imagens_add += 1
                print(f"[revisor]  🖼 imagem adicionada: {md.name}")

        if mudou:
            escrever_post(md, campos, corpo_final)

        lido2 = ler_post(md)
        if lido2:
            c2, corpo2 = lido2
            ledger[md.name] = _hash(_valor_str(c2, "titulo"), corpo2)

    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(json.dumps(ledger, ensure_ascii=False, indent=0), encoding="utf-8")
    TENTATIVAS_LEDGER.write_text(json.dumps(tentativas, ensure_ascii=False, indent=0), encoding="utf-8")
    print(
        f"[revisor] concluído: {revisados} revisados "
        f"({aprofundados} aprofundados, {mantidos} mantidos, {corrigidos} corrigidos, "
        f"{despublicados} despublicados, {imagens_add} imagens adicionadas)."
    )


if __name__ == "__main__":
    main()
