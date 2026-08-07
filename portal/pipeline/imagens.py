"""Busca de imagens de LICENÇA LIVRE (sem ferir direitos autorais).

Cascata de fontes, todas com uso comercial permitido:
  1. NASA Images  — domínio público (para espaço/astronomia). Sem chave.
  2. Pexels       — uso comercial liberado. Requer PEXELS_API_KEY (grátis).
  3. Openverse    — imagens Creative Commons (filtro comercial). Sem chave.

Sempre devolve (url_https, credito). Se nada for encontrado, (None, None) e o site
mostra o placeholder colorido da categoria.
"""

from __future__ import annotations

import os
import re
from urllib.parse import urlparse

import requests

TIMEOUT = 20

# Domínios OFICIAIS / de licença amigável — deles podemos usar a foto real que a
# própria fonte publicou (a "foto citada na notícia").
MARCAS_OFICIAIS = (
    ".gov", ".edu", ".int", ".ac.", "iucn.org", "paho.org", "who.",
    "unicef.org", "fao.org", "wmo.int", "nasa.gov", "europa.eu", "noaa.gov",
    "unicamp.br", "usp.br", "fiocruz.br", "embrapa.br", "butantan",
)
PALAVRAS_ESPACO = {
    "mars", "marte", "nasa", "space", "espaço", "espaco", "planet", "planeta",
    "galaxy", "galáxia", "asteroid", "asteroide", "moon", "lua", "rover", "cosmos",
    "telescope", "telescópio", "estrela", "star", "nebula", "solar", "orbit",
}

# Consulta genérica (em inglês) por editoria — usada quando a busca específica
# não encontra nada, antes do último recurso.
GENERICOS_CATEGORIA = {
    "ciencia": "laboratory science research",
    "solidariedade": "volunteers helping community",
    "meio-ambiente": "nature forest landscape",
    "saude": "health medicine hospital",
    "animais": "wildlife animals nature",
    "superacao": "athlete achievement celebration",
    "tecnologia": "technology innovation circuit",
    "mundo": "world people community",
}

# ÚLTIMO RECURSO garantido: toda editoria tem uma imagem de licença livre já
# verificada. Assim NENHUMA notícia fica sem imagem, mesmo se as buscas online
# falharem (ex.: limite de taxa). Todas de domínio público ou Creative Commons.
FALLBACK_CATEGORIA = {
    "ciencia": ("https://images-assets.nasa.gov/image/KSC-20170719-PH_SWW01_0001/KSC-20170719-PH_SWW01_0001~small.jpg", "Imagem: NASA (domínio público)"),
    "solidariedade": ("https://live.staticflickr.com/7709/16828647513_753ccddf70_b.jpg", "Foto: DFID - UK Department for International Development (BY) via Openverse"),
    "meio-ambiente": ("https://live.staticflickr.com/2664/3825008839_2f54a6ea15_b.jpg", "Foto: davidgsteadman (PDM) via Openverse"),
    "saude": ("https://live.staticflickr.com/7076/26383067663_2e81a945ef_b.jpg", "Foto: Ministry of Defense of Ukraine (BY-SA) via Openverse"),
    "animais": ("https://live.staticflickr.com/394/20155235429_4feeddb06d.jpg", "Foto: Frontierofficial (BY) via Openverse"),
    "superacao": ("https://live.staticflickr.com/4828/30881190687_f2cd0ea29c_b.jpg", "Foto: jurvetson (BY) via Openverse"),
    "tecnologia": ("https://live.staticflickr.com/71/202290560_fb40def5b7_b.jpg", "Foto: scottbb (BY-SA) via Openverse"),
    "mundo": ("https://live.staticflickr.com/6098/6376560841_23a50bd4b9_b.jpg", "Foto: Kevin M. Gill (BY) via Openverse"),
}
FALLBACK_PADRAO = FALLBACK_CATEGORIA["mundo"]


def _https(url: str) -> str:
    return url.replace("http://", "https://", 1)


# --------------------------------------------------------------------------
# Foto REAL citada na notícia — só de fontes OFICIAIS / domínio público
# --------------------------------------------------------------------------
def _dominio_oficial(url: str) -> bool:
    """True se o domínio da fonte for oficial/público (podemos usar a foto real)."""
    try:
        host = (urlparse(url).hostname or "").lower()
    except Exception:
        return False
    if not host:
        return False
    return any(marca in host for marca in MARCAS_OFICIAIS)


_RE_META = re.compile(
    r'<meta[^>]+(?:property|name)=["\'](?:og:image(?::url)?|twitter:image(?::src)?)["\']'
    r'[^>]+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
_RE_META_REV = re.compile(
    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)='
    r'["\'](?:og:image(?::url)?|twitter:image(?::src)?)["\']',
    re.IGNORECASE,
)


def _og_image(pagina_url: str) -> str | None:
    """Extrai a URL da imagem principal (og:image / twitter:image) de uma página."""
    try:
        r = requests.get(
            pagina_url,
            timeout=TIMEOUT,
            headers={"User-Agent": "Mozilla/5.0 (compatible; OLadoBom/1.0)"},
        )
        if r.status_code != 200:
            return None
        html = r.text[:200_000]
    except Exception:
        return None

    m = _RE_META.search(html) or _RE_META_REV.search(html)
    if not m:
        return None
    img = m.group(1).strip()
    if not img:
        return None
    # descarta logos / ícones / placeholders (não são a "foto da notícia")
    baixo = img.lower()
    if baixo.endswith(".svg") or any(
        marca in baixo for marca in ("logo", "favicon", "sprite", "/icons/", "icon-", "placeholder")
    ):
        return None
    if img.startswith("//"):
        img = "https:" + img
    elif img.startswith("/"):
        p = urlparse(pagina_url)
        img = f"{p.scheme}://{p.netloc}{img}"
    img = _https(img)
    if not img.lower().startswith("https://"):
        return None
    # confirma que a imagem realmente carrega
    try:
        h = requests.head(img, timeout=TIMEOUT, allow_redirects=True,
                          headers={"User-Agent": "Mozilla/5.0 (compatible; OLadoBom/1.0)"})
        tipo = h.headers.get("Content-Type", "")
        if h.status_code == 200 and tipo.startswith("image"):
            return img
        # alguns servidores não respondem HEAD — tenta GET leve
        g = requests.get(img, timeout=TIMEOUT, stream=True,
                         headers={"User-Agent": "Mozilla/5.0 (compatible; OLadoBom/1.0)"})
        if g.status_code == 200 and g.headers.get("Content-Type", "").startswith("image"):
            return img
    except Exception:
        return None
    return None


def imagem_da_fonte(fonte_url: str | None, fonte_nome: str | None) -> tuple[str | None, str | None]:
    """A foto real citada na notícia — apenas quando a fonte é oficial/domínio público."""
    if not fonte_url or not _dominio_oficial(fonte_url):
        return None, None
    img = _og_image(fonte_url)
    if not img:
        return None, None
    nome = (fonte_nome or "").strip() or "fonte oficial"
    return img, f"Foto: {nome} (site oficial)"


# --------------------------------------------------------------------------
# NASA — domínio público
# --------------------------------------------------------------------------
def _nasa(consulta: str) -> tuple[str | None, str | None]:
    try:
        r = requests.get(
            "https://images-api.nasa.gov/search",
            params={"q": consulta, "media_type": "image"},
            timeout=TIMEOUT,
        )
        itens = r.json().get("collection", {}).get("items", [])
    except Exception:
        return None, None

    for it in itens[:5]:
        dados = (it.get("data") or [{}])[0]
        nasa_id = dados.get("nasa_id")
        if not nasa_id:
            continue
        try:
            a = requests.get(f"https://images-api.nasa.gov/asset/{nasa_id}", timeout=TIMEOUT)
            hrefs = [x.get("href", "") for x in a.json().get("collection", {}).get("items", [])]
        except Exception:
            continue
        jpgs = [h for h in hrefs if h.lower().endswith(".jpg")]
        # prefere ~small (leve); senão ~orig
        escolha = next((h for h in jpgs if "~small" in h), None) or next((h for h in jpgs if "~orig" in h), None)
        if escolha:
            return _https(escolha), "Imagem: NASA/JPL-Caltech (domínio público)"
    return None, None


# --------------------------------------------------------------------------
# Pexels — uso comercial liberado (grátis, requer chave)
# --------------------------------------------------------------------------
def _pexels(consulta: str) -> tuple[str | None, str | None]:
    chave = os.getenv("PEXELS_API_KEY")
    if not chave:
        return None, None
    try:
        r = requests.get(
            "https://api.pexels.com/v1/search",
            params={"query": consulta, "per_page": 1, "orientation": "landscape"},
            headers={"Authorization": chave},
            timeout=TIMEOUT,
        )
        fotos = r.json().get("photos", [])
    except Exception:
        return None, None
    if not fotos:
        return None, None
    foto = fotos[0]
    url = (foto.get("src") or {}).get("large") or (foto.get("src") or {}).get("original")
    autor = foto.get("photographer", "Pexels")
    if url:
        return _https(url), f"Foto: {autor} / Pexels"
    return None, None


# --------------------------------------------------------------------------
# Openverse — Creative Commons (sem chave; filtro de uso comercial)
# --------------------------------------------------------------------------
def _openverse(consulta: str, pagina: int = 1) -> tuple[str | None, str | None]:
    try:
        r = requests.get(
            "https://api.openverse.org/v1/images/",
            params={"q": consulta, "page_size": 1, "page": pagina,
                    "license_type": "commercial", "mature": "false"},
            headers={"User-Agent": "OLadoBom/1.0 (portal de boas noticias)"},
            timeout=TIMEOUT,
        )
        res = r.json().get("results", [])
    except Exception:
        return None, None
    if not res:
        return None, None
    img = res[0]
    url = img.get("url")
    autor = img.get("creator") or "autor desconhecido"
    lic = (img.get("license") or "CC").upper()
    if url and url.startswith("https"):
        return url, f"Foto: {autor} ({lic}) via Openverse"
    return None, None


# --------------------------------------------------------------------------
def buscar_imagem(
    consulta: str,
    categoria: str = "",
    fonte_url: str | None = None,
    fonte_nome: str | None = None,
) -> tuple[str | None, str | None]:
    """Devolve (url_https, credito) de uma imagem sem ferir direitos autorais.

    NUNCA devolve (None, None): toda notícia recebe uma imagem. Ordem:
      1. A foto REAL citada na notícia — só quando a fonte é oficial/domínio
         público (ex.: NASA, OMS, IUCN, .gov, universidades). É a foto certa
         para notícias que descrevem uma imagem específica.
      2. NASA Images (domínio público) para temas de espaço/astronomia.
      3. Pexels / Openverse com a consulta específica da notícia.
      4. Pexels / Openverse com uma consulta genérica da editoria.
      5. Último recurso garantido: imagem fixa de licença livre da editoria.
    """
    cat = (categoria or "").strip().lower()

    # 1. foto real da fonte oficial (a "foto citada na notícia")
    url, credito = imagem_da_fonte(fonte_url, fonte_nome)
    if url:
        return url, credito

    consulta = (consulta or "").strip()
    if consulta:
        termos = set(consulta.lower().split()) | {cat}
        if termos & PALAVRAS_ESPACO:
            url, credito = _nasa(consulta)
            if url:
                return url, credito
        for fonte in (_pexels, _openverse):
            url, credito = fonte(consulta)
            if url:
                return url, credito

    # 4. consulta genérica da editoria (quando a específica não achou nada).
    #    Varia a página pelo hash do texto para posts da mesma editoria não
    #    ficarem todos com a MESMA imagem genérica.
    generico = GENERICOS_CATEGORIA.get(cat)
    if generico:
        pagina = 1 + (abs(hash(consulta or cat)) % 8)
        url, credito = _pexels(generico)
        if url:
            return url, credito
        url, credito = _openverse(generico, pagina=pagina)
        if url:
            return url, credito

    # 5. último recurso: imagem fixa da editoria (garante que sempre há imagem)
    return FALLBACK_CATEGORIA.get(cat, FALLBACK_PADRAO)
