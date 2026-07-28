"""Coleta de notícias candidatas a partir de RSS e de APIs (uso comercial OK).

Todas as fontes são normalizadas para o mesmo formato (`Artigo`). Nada aqui
publica nada — apenas devolve candidatas para o filtro e o resumo.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone

import requests

try:
    import feedparser  # type: ignore
except ImportError:  # pragma: no cover
    feedparser = None


# --------------------------------------------------------------------------
# Modelo normalizado
# --------------------------------------------------------------------------
@dataclass
class Artigo:
    titulo: str
    url: str
    fonte_nome: str
    trecho: str = ""          # resumo/excerto vindo da fonte (só p/ referência)
    publicado: datetime | None = None
    idioma: str = "pt"        # "pt" ou "en"
    imagem: str | None = None
    tags_origem: list[str] = field(default_factory=list)


# --------------------------------------------------------------------------
# Fontes RSS (gratuitas) — Brasil + internacionais de boas notícias
# --------------------------------------------------------------------------
FEEDS_RSS: list[dict] = [
    {"nome": "Só Notícia Boa", "url": "https://www.sonoticiaboa.com.br/feed/", "idioma": "pt"},
    {"nome": "Razões para Acreditar", "url": "https://razoesparaacreditar.com/feed/", "idioma": "pt"},
    {"nome": "Catraca Livre", "url": "https://catracalivre.com.br/feed/", "idioma": "pt"},
    {"nome": "Hypeness", "url": "https://www.hypeness.com.br/feed/", "idioma": "pt"},
    {"nome": "CicloVivo", "url": "https://ciclovivo.com.br/feed/", "idioma": "pt"},
    {"nome": "Positive News", "url": "https://www.positive.news/feed/", "idioma": "en"},
    {"nome": "Good News Network", "url": "https://www.goodnewsnetwork.org/feed/", "idioma": "en"},
]

# Não trazer notícia velha (dias). Ajustável via MAX_IDADE_DIAS.
MAX_IDADE_DIAS = int(os.getenv("MAX_IDADE_DIAS", "45"))


def _muito_antigo(pub: datetime) -> bool:
    try:
        return (datetime.now(timezone.utc) - pub).days > MAX_IDADE_DIAS
    except (TypeError, ValueError):
        return False


def _parse_data(entry) -> datetime | None:
    for campo in ("published_parsed", "updated_parsed"):
        valor = getattr(entry, campo, None)
        if valor:
            try:
                return datetime(*valor[:6], tzinfo=timezone.utc)
            except (TypeError, ValueError):
                pass
    return None


def _imagem_do_entry(entry) -> str | None:
    # media:content / media:thumbnail / enclosure
    for attr in ("media_content", "media_thumbnail"):
        val = getattr(entry, attr, None)
        if val and isinstance(val, list) and val and val[0].get("url"):
            return val[0]["url"]
    for link in getattr(entry, "links", []) or []:
        if link.get("rel") == "enclosure" and str(link.get("type", "")).startswith("image"):
            return link.get("href")
    return None


def coletar_rss(limite_por_feed: int = 15) -> list[Artigo]:
    """Lê todos os feeds RSS configurados e devolve os artigos normalizados."""
    if feedparser is None:
        print("[fontes] feedparser não instalado — pulando RSS.")
        return []

    artigos: list[Artigo] = []
    for feed in FEEDS_RSS:
        try:
            data = feedparser.parse(feed["url"])
        except Exception as exc:  # rede instável não deve derrubar o pipeline
            print(f"[fontes] erro ao ler {feed['nome']}: {exc}")
            continue
        for entry in data.entries[:limite_por_feed]:
            pub = _parse_data(entry)
            if pub and _muito_antigo(pub):
                continue  # notícia velha demais
            resumo = getattr(entry, "summary", "") or ""
            artigos.append(
                Artigo(
                    titulo=getattr(entry, "title", "").strip(),
                    url=getattr(entry, "link", "").strip(),
                    fonte_nome=feed["nome"],
                    trecho=resumo,
                    publicado=pub,
                    idioma=feed["idioma"],
                    imagem=_imagem_do_entry(entry),
                    tags_origem=[t.get("term", "") for t in getattr(entry, "tags", []) or []],
                )
            )
        print(f"[fontes] {feed['nome']}: {len(data.entries[:limite_por_feed])} itens")
    return artigos


# --------------------------------------------------------------------------
# The Guardian — "The Upside" (boas notícias). Grátis, uso comercial liberado.
# Requer GUARDIAN_API_KEY (https://open-platform.theguardian.com/).
# --------------------------------------------------------------------------
def coletar_guardian(limite: int = 20) -> list[Artigo]:
    chave = os.getenv("GUARDIAN_API_KEY")
    if not chave:
        return []
    try:
        resp = requests.get(
            "https://content.guardianapis.com/search",
            params={
                "tag": "world/series/the-upside",
                "show-fields": "trailText,thumbnail",
                "page-size": limite,
                "order-by": "newest",
                "api-key": chave,
            },
            timeout=20,
        )
        resp.raise_for_status()
        resultados = resp.json().get("response", {}).get("results", [])
    except Exception as exc:
        print(f"[fontes] Guardian indisponível: {exc}")
        return []

    artigos = []
    for r in resultados:
        campos = r.get("fields", {})
        artigos.append(
            Artigo(
                titulo=r.get("webTitle", "").strip(),
                url=r.get("webUrl", ""),
                fonte_nome="The Guardian (The Upside)",
                trecho=campos.get("trailText", ""),
                publicado=None,
                idioma="en",
                imagem=campos.get("thumbnail"),
            )
        )
    print(f"[fontes] The Guardian: {len(artigos)} itens")
    return artigos


# --------------------------------------------------------------------------
# NewsData.io — free tier com uso comercial. Requer NEWSDATA_API_KEY.
# --------------------------------------------------------------------------
def coletar_newsdata(limite: int = 10) -> list[Artigo]:
    chave = os.getenv("NEWSDATA_API_KEY")
    if not chave:
        return []
    try:
        resp = requests.get(
            "https://newsdata.io/api/1/news",
            params={
                "apikey": chave,
                "language": "pt",
                "q": "solidariedade OR doação OR resgate OR conquista OR descoberta OR premiado",
                "country": "br",
            },
            timeout=20,
        )
        resp.raise_for_status()
        resultados = resp.json().get("results", []) or []
    except Exception as exc:
        print(f"[fontes] NewsData indisponível: {exc}")
        return []

    artigos = []
    for r in resultados[:limite]:
        artigos.append(
            Artigo(
                titulo=(r.get("title") or "").strip(),
                url=r.get("link", ""),
                fonte_nome=r.get("source_id", "NewsData"),
                trecho=r.get("description") or "",
                idioma="pt",
                imagem=r.get("image_url"),
            )
        )
    print(f"[fontes] NewsData: {len(artigos)} itens")
    return artigos


def coletar_tudo() -> list[Artigo]:
    """Junta todas as fontes disponíveis (as que exigem chave são opcionais)."""
    artigos = coletar_rss() + coletar_guardian() + coletar_newsdata()
    # remove itens sem título ou sem URL
    return [a for a in artigos if a.titulo and a.url]
