"""Filtro de positividade + deduplicação.

1. Heurística barata (léxico PT/EN) descarta o óbvio e ordena por "quão positivo".
2. A confirmação fina de "é mesmo uma boa notícia?" é feita pela IA em resumir.py.
3. Deduplicação evita reprocessar URLs já vistas ou já publicadas.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from fontes import Artigo

# Termos que indicam boa notícia (PT + EN).
POSITIVAS = {
    "cura", "curou", "salv", "resgat", "doaç", "doou", "adoç", "adotad", "record",
    "conquist", "premiad", "prêmio", "premio", "descobert", "avanç", "solidar",
    "recuper", "reflorest", "voluntári", "esperança", "inspir", "supera", "vitória",
    "gratuito", "ajuda", "sucesso", "aprovad", "inédit", "histórico", "emocion",
    "reduç", "melhora", "cresce", "recuperou", "renov",
    # inglês
    "rescue", "cure", "cured", "record", "breakthrough", "restor", "donate",
    "volunteer", "hope", "inspir", "success", "recover", "award", "wildlife",
    "reforest", "kindness", "hero", "saved", "milestone",
}

# Termos que quase sempre indicam notícia ruim — descartam o item.
NEGATIVAS = {
    "morte", "morto", "morre", "assassin", "homicíd", "estupro", "feminicíd",
    "tragéd", "acidente", "tiroteio", "atentad", "guerra", "massacre", "abuso",
    "tortura", "sequestr", "roubo", "assalto", "golpe", "fraude", "corrupç",
    "incênd", "enchente que matou", "desastre", "óbito", "chacina", "facção",
    # inglês
    "death", "dead", "kill", "murder", "rape", "war", "attack", "shooting",
    "disaster", "scandal", "fraud", "abuse",
}


def pontuar(artigo: Artigo) -> int:
    texto = f"{artigo.titulo} {artigo.trecho}".lower()
    texto = re.sub(r"<[^>]+>", " ", texto)  # tira HTML do resumo do RSS
    positivo = sum(1 for termo in POSITIVAS if termo in texto)
    negativo = sum(1 for termo in NEGATIVAS if termo in texto)
    return positivo - 2 * negativo  # notícia ruim pesa o dobro


def provavelmente_positiva(artigo: Artigo) -> bool:
    """Corte grosseiro: descarta o claramente negativo; deixa o resto para a IA."""
    return pontuar(artigo) >= 0 and not _tem_negativa_forte(artigo)


def _tem_negativa_forte(artigo: Artigo) -> bool:
    titulo = artigo.titulo.lower()
    return any(t in titulo for t in ("morte", "morto", "morre", "assassin", "estupro", "guerra"))


# --------------------------------------------------------------------------
# Deduplicação
# --------------------------------------------------------------------------
def _normalizar_url(url: str) -> str:
    return url.split("?")[0].rstrip("/").lower()


def carregar_ja_vistos(caminho_ledger: Path) -> set[str]:
    """URLs já processadas em execuções anteriores."""
    if caminho_ledger.exists():
        try:
            return set(json.loads(caminho_ledger.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            return set()
    return set()


def salvar_ja_vistos(caminho_ledger: Path, urls: set[str]) -> None:
    caminho_ledger.parent.mkdir(parents=True, exist_ok=True)
    caminho_ledger.write_text(
        json.dumps(sorted(urls), ensure_ascii=False, indent=0), encoding="utf-8"
    )


def urls_ja_publicadas(dir_posts: Path) -> set[str]:
    """Lê fonteUrl de todos os .md existentes para não republicar a mesma fonte."""
    vistos: set[str] = set()
    if not dir_posts.exists():
        return vistos
    for md in dir_posts.glob("*.md"):
        try:
            texto = md.read_text(encoding="utf-8")
        except OSError:
            continue
        m = re.search(r'fonteUrl:\s*"?([^"\n]+)"?', texto)
        if m:
            vistos.add(_normalizar_url(m.group(1).strip()))
    return vistos


_STOPWORDS = {
    "a", "o", "de", "da", "do", "e", "em", "para", "com", "que", "no", "na",
    "os", "as", "um", "uma", "por", "dos", "das", "ao", "à", "se", "the", "of",
}


def _tokens_titulo(texto: str) -> set[str]:
    texto = re.sub(r"<[^>]+>", " ", texto or "").lower()
    texto = re.sub(r"[^0-9a-zà-ÿ ]", " ", texto)
    return {t for t in texto.split() if len(t) > 2 and t not in _STOPWORDS}


def titulos_ja_publicados(dir_posts: Path) -> list[set[str]]:
    """Conjuntos de palavras dos títulos já existentes (para evitar repetição)."""
    saida: list[set[str]] = []
    if not dir_posts.exists():
        return saida
    for md in dir_posts.glob("*.md"):
        try:
            texto = md.read_text(encoding="utf-8")
        except OSError:
            continue
        m = re.search(r'titulo:\s*"?([^"\n]+)"?', texto)
        if m:
            saida.append(_tokens_titulo(m.group(1)))
    return saida


def _titulo_repetido(titulo: str, publicados: list[set[str]], limiar: float = 0.6) -> bool:
    t = _tokens_titulo(titulo)
    if not t:
        return False
    return any(p and len(t & p) / len(t) >= limiar for p in publicados)


def filtrar_novos(
    artigos: list[Artigo],
    ja_vistos: set[str],
    publicados: set[str],
    titulos_pub: list[set[str]] | None = None,
) -> list[Artigo]:
    """Remove duplicados (URL no ledger/publicados, título parecido com algo já
    publicado) e artigos claramente negativos, devolvendo os candidatos ordenados
    do mais positivo para o menos."""
    novos: list[Artigo] = []
    vistos_agora: set[str] = set()
    for a in artigos:
        chave = _normalizar_url(a.url)
        if chave in ja_vistos or chave in publicados or chave in vistos_agora:
            continue
        if titulos_pub and _titulo_repetido(a.titulo, titulos_pub):
            continue
        if not provavelmente_positiva(a):
            continue
        vistos_agora.add(chave)
        novos.append(a)
    novos.sort(key=pontuar, reverse=True)
    return novos
