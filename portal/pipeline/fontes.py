"""Coleta de notícias candidatas a partir de RSS e de APIs (uso comercial OK).

Todas as fontes são normalizadas para o mesmo formato (`Artigo`). Nada aqui
publica nada — apenas devolve candidatas para o filtro e o resumo.
"""

from __future__ import annotations

import os
import re
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
    idioma: str = "português"  # idioma original (ex.: inglês, espanhol, francês)
    imagem: str | None = None
    tags_origem: list[str] = field(default_factory=list)
    pais: str = ""            # país de origem da fonte (só para variar/registrar)


# --------------------------------------------------------------------------
# Fontes RSS (gratuitas) — Brasil + internacionais de boas notícias
# --------------------------------------------------------------------------
# Fontes INTERNACIONAIS de vários países e idiomas. O robô traduz e adapta cada
# notícia para o português do Brasil. Misturamos portais dedicados a boas notícias
# com grandes jornais (destes, o filtro + a IA selecionam só o que é positivo).
# O coletor ALTERNA as fontes (round-robin), para o site nunca ficar dominado por
# um único portal ou país.
FEEDS_RSS: list[dict] = [
    # --- Inglês -----------------------------------------------------------
    {"nome": "Positive News", "url": "https://www.positive.news/feed/", "idioma": "inglês", "pais": "Reino Unido"},
    {"nome": "Good News Network", "url": "https://www.goodnewsnetwork.org/feed/", "idioma": "inglês", "pais": "EUA"},
    {"nome": "Reasons to be Cheerful", "url": "https://reasonstobecheerful.world/feed/", "idioma": "inglês", "pais": "EUA"},
    {"nome": "Optimist Daily", "url": "https://www.optimistdaily.com/feed/", "idioma": "inglês", "pais": "EUA"},
    # --- Espanhol ---------------------------------------------------------
    {"nome": "Noticias Positivas", "url": "https://www.noticiaspositivas.org/feed/", "idioma": "espanhol", "pais": "Argentina"},
    {"nome": "La Vanguardia", "url": "https://www.lavanguardia.com/rss/home.xml", "idioma": "espanhol", "pais": "Espanha"},
    {"nome": "El País", "url": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada", "idioma": "espanhol", "pais": "Espanha"},
    # --- Francês ----------------------------------------------------------
    {"nome": "Positivr", "url": "https://positivr.fr/feed/", "idioma": "francês", "pais": "França"},
    {"nome": "Le Monde", "url": "https://www.lemonde.fr/rss/une.xml", "idioma": "francês", "pais": "França"},
    # --- Alemão -----------------------------------------------------------
    {"nome": "Good News", "url": "https://www.goodnews.eu/feed/", "idioma": "alemão", "pais": "Alemanha"},
    {"nome": "Tagesschau", "url": "https://www.tagesschau.de/index~rss2.xml", "idioma": "alemão", "pais": "Alemanha"},
    # --- Italiano ---------------------------------------------------------
    {"nome": "ANSA", "url": "https://www.ansa.it/sito/ansait_rss.xml", "idioma": "italiano", "pais": "Itália"},
    {"nome": "Rai News", "url": "https://www.rainews.it/rss/tutti", "idioma": "italiano", "pais": "Itália"},
    # --- Holandês ---------------------------------------------------------
    {"nome": "NOS", "url": "https://feeds.nos.nl/nosnieuwsalgemeen", "idioma": "holandês", "pais": "Holanda"},
]

# Não trazer notícia velha (dias). Ajustável via MAX_IDADE_DIAS.
MAX_IDADE_DIAS = int(os.getenv("MAX_IDADE_DIAS", "45"))

# Timeout de rede para baixar cada feed. IMPORTANTE: o feedparser.parse(url) NÃO
# tem timeout próprio — se um servidor de RSS travar, ele bloqueia para sempre e
# derruba a execução. Por isso baixamos o feed com requests (com timeout) e só
# então entregamos os bytes ao feedparser.
FEED_TIMEOUT = int(os.getenv("FEED_TIMEOUT", "15"))
_UA = {"User-Agent": "Mozilla/5.0 (compatible; OLadoBom/1.0; +https://oladobom.com.br)"}


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
            resp = requests.get(feed["url"], timeout=FEED_TIMEOUT, headers=_UA)
            resp.raise_for_status()
            data = feedparser.parse(resp.content)
        except Exception as exc:  # feed lento/fora do ar não pode travar o pipeline
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
                    idioma=feed.get("idioma", "português"),
                    imagem=_imagem_do_entry(entry),
                    tags_origem=[t.get("term", "") for t in getattr(entry, "tags", []) or []],
                    pais=feed.get("pais", ""),
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
                idioma="inglês",
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
                "language": "en",
                "q": "breakthrough OR rescued OR record OR restored OR donated OR milestone OR cure",
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
                idioma="inglês",
                imagem=r.get("image_url"),
            )
        )
    print(f"[fontes] NewsData: {len(artigos)} itens")
    return artigos


def baixar_texto_fonte(url: str, limite_chars: int = 7000) -> str:
    """Baixa a matéria da fonte e extrai o texto principal (parágrafos).

    Serve como MATERIAL DE REFERÊNCIA para a IA escrever uma matéria própria,
    mais profunda e sem inventar fatos. Não é publicado — só alimenta o modelo.
    Devolve "" se não conseguir (a IA usa então só o trecho do RSS)."""
    if not url:
        return ""
    try:
        r = requests.get(url, timeout=20, headers=_UA)
        if r.status_code != 200 or "text/html" not in r.headers.get("Content-Type", ""):
            return ""
        html = r.text
    except Exception:
        return ""

    # remove blocos que não são conteúdo
    html = re.sub(r"(?is)<(script|style|nav|header|footer|aside|form)[^>]*>.*?</\1>", " ", html)
    # extrai parágrafos
    paras = re.findall(r"(?is)<p[^>]*>(.*?)</p>", html)
    limpos = []
    for p in paras:
        txt = re.sub(r"(?is)<[^>]+>", " ", p)  # tira tags internas
        txt = re.sub(r"\s+", " ", txt).strip()
        txt = (txt.replace("&nbsp;", " ").replace("&amp;", "&")
                  .replace("&#8217;", "'").replace("&#8216;", "'")
                  .replace("&quot;", '"').replace("&#8220;", '"').replace("&#8221;", '"'))
        if len(txt) >= 60:  # ignora legendas/menus curtos
            limpos.append(txt)
    texto = "\n\n".join(limpos)
    return texto[:limite_chars]


def coletar_tudo() -> list[Artigo]:
    """Junta todas as fontes disponíveis (as que exigem chave são opcionais)."""
    artigos = coletar_rss() + coletar_guardian() + coletar_newsdata()
    # remove itens sem título ou sem URL
    return [a for a in artigos if a.titulo and a.url]
