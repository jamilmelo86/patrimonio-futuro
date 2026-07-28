"""Orquestrador do pipeline: coleta -> filtra -> reescreve com IA -> grava rascunhos.

Gera arquivos Markdown com `draft: true` em site/src/content/posts/. NADA é
publicado automaticamente: o humano revisa e muda para `draft: false`.

Uso:
    python gerar_rascunhos.py            # roda o pipeline completo
    MAX_DRAFTS=5 python gerar_rascunhos.py

Variáveis de ambiente (todas opcionais; veja .env.example):
    ANTHROPIC_API_KEY   -> ativa a reescrita por IA (sem ela, gera esqueletos)
    GUARDIAN_API_KEY    -> ativa a fonte The Guardian
    NEWSDATA_API_KEY    -> ativa a fonte NewsData.io
    MAX_DRAFTS          -> máximo de rascunhos por execução (padrão 8)
    CONTENT_DIR         -> destino dos .md (padrão ../site/src/content/posts)
"""

from __future__ import annotations

import os
import re
import unicodedata
from datetime import date, datetime
from pathlib import Path

import fontes
import resumir
from filtro import (
    carregar_ja_vistos,
    filtrar_novos,
    salvar_ja_vistos,
    titulos_ja_publicados,
    urls_ja_publicadas,
)

RAIZ = Path(__file__).resolve().parent
CONTENT_DIR = Path(os.getenv("CONTENT_DIR", RAIZ.parent / "site" / "src" / "content" / "posts"))
LEDGER = RAIZ / "_estado" / "ja_vistos.json"
MAX_DRAFTS = int(os.getenv("MAX_DRAFTS", "8"))
# Máximo de rascunhos por editoria numa mesma execução (mantém o dia variado).
MAX_POR_CATEGORIA = int(os.getenv("MAX_POR_CATEGORIA", "3"))

# Por padrão NÃO reaproveitamos a imagem da fonte: evita questão de direitos
# autorais e URLs inválidas (ex.: embed de vídeo). Fica o placeholder colorido da
# categoria, e você adiciona uma imagem de licença livre na revisão pelo /admin.
# Para religar (por sua conta e risco de direitos), defina USAR_IMAGEM_FONTE=1.
USAR_IMAGEM_FONTE = os.getenv("USAR_IMAGEM_FONTE", "") not in ("", "0", "false", "False")


def _img_valida(url: str | None) -> bool:
    """Aceita só URLs que aparentam ser imagens de verdade."""
    if not url:
        return False
    u = url.lower().split("?")[0]
    return u.startswith("http") and u.endswith((".jpg", ".jpeg", ".png", ".webp", ".gif"))


def slugify(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    texto = re.sub(r"[^a-zA-Z0-9\s-]", "", texto).strip().lower()
    texto = re.sub(r"[\s_-]+", "-", texto)
    return texto[:70].strip("-") or "noticia"


def _yaml_str(valor: str) -> str:
    """Serializa string com segurança para o frontmatter YAML."""
    return '"' + valor.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").strip() + '"'


def montar_markdown(dados: dict, artigo: fontes.Artigo) -> str:
    dia = (artigo.publicado or datetime.now()).date() if isinstance(artigo.publicado, datetime) else date.today()
    tags = dados.get("tags") or []
    tags_yaml = "[" + ", ".join(_yaml_str(str(t)) for t in tags if t) + "]"

    linhas = [
        "---",
        f"titulo: {_yaml_str(dados['titulo'])}",
        f"resumo: {_yaml_str(dados['resumo'])}",
        f"categoria: {_yaml_str(dados['categoria'])}",
        f"data: {dia.isoformat()}",
        f"fonteNome: {_yaml_str(artigo.fonte_nome)}",
        f"fonteUrl: {_yaml_str(artigo.url)}",
    ]
    if USAR_IMAGEM_FONTE and _img_valida(artigo.imagem):
        linhas.append(f"imagem: {_yaml_str(artigo.imagem)}")
        linhas.append(f"creditoImagem: {_yaml_str('Imagem: ' + artigo.fonte_nome)}")
    linhas.append(f"tags: {tags_yaml}")
    linhas.append("draft: true")
    linhas.append("---")
    linhas.append("")
    linhas.append(dados["corpo"].strip())
    linhas.append("")
    return "\n".join(linhas)


def gravar_rascunho(dados: dict, artigo: fontes.Artigo) -> Path:
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    base = slugify(dados["titulo"])
    caminho = CONTENT_DIR / f"{base}.md"
    n = 2
    while caminho.exists():
        caminho = CONTENT_DIR / f"{base}-{n}.md"
        n += 1
    caminho.write_text(montar_markdown(dados, artigo), encoding="utf-8")
    return caminho


def main() -> None:
    print(f"[pipeline] destino: {CONTENT_DIR}")
    ja_vistos = carregar_ja_vistos(LEDGER)
    publicados = urls_ja_publicadas(CONTENT_DIR)
    titulos_pub = titulos_ja_publicados(CONTENT_DIR)

    brutos = fontes.coletar_tudo()
    print(f"[pipeline] {len(brutos)} artigos coletados no total")

    candidatos = filtrar_novos(brutos, ja_vistos, publicados, titulos_pub)
    print(f"[pipeline] {len(candidatos)} candidatos após filtro (positividade, dedup de URL e título)")

    criados = 0
    tentativas = 0
    limite_tentativas = MAX_DRAFTS * 3  # não gastar IA à toa
    por_categoria: dict[str, int] = {}

    for artigo in candidatos:
        if criados >= MAX_DRAFTS or tentativas >= limite_tentativas:
            break
        tentativas += 1
        chave = artigo.url.split("?")[0].rstrip("/").lower()

        dados = resumir.reescrever(artigo)
        if dados is None:
            ja_vistos.add(chave)  # vetado pela IA: não reprocessar
            print(f"[pipeline]  ✗ vetado (não é boa notícia): {artigo.titulo[:60]}")
            continue

        cat = dados.get("categoria", "mundo")
        if por_categoria.get(cat, 0) >= MAX_POR_CATEGORIA:
            # editoria já cheia nesta execução — adia para a próxima (não marca visto)
            print(f"[pipeline]  ↷ adiado (editoria '{cat}' cheia): {artigo.titulo[:50]}")
            continue

        ja_vistos.add(chave)
        caminho = gravar_rascunho(dados, artigo)
        por_categoria[cat] = por_categoria.get(cat, 0) + 1
        criados += 1
        marca = " (esqueleto)" if dados.get("_fallback") else ""
        print(f"[pipeline]  ✓ rascunho{marca} [{cat}]: {caminho.name}")

    salvar_ja_vistos(LEDGER, ja_vistos)
    resumo_cat = ", ".join(f"{k}:{v}" for k, v in sorted(por_categoria.items())) or "nenhuma"
    print(f"[pipeline] concluído: {criados} rascunho(s) por editoria ({resumo_cat}). Revise antes de publicar!")


if __name__ == "__main__":
    main()
