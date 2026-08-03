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

import requests

TIMEOUT = 20
PALAVRAS_ESPACO = {
    "mars", "marte", "nasa", "space", "espaço", "espaco", "planet", "planeta",
    "galaxy", "galáxia", "asteroid", "asteroide", "moon", "lua", "rover", "cosmos",
    "telescope", "telescópio", "estrela", "star", "nebula", "solar", "orbit",
}


def _https(url: str) -> str:
    return url.replace("http://", "https://", 1)


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
def _openverse(consulta: str) -> tuple[str | None, str | None]:
    try:
        r = requests.get(
            "https://api.openverse.org/v1/images/",
            params={"q": consulta, "page_size": 1, "license_type": "commercial", "mature": "false"},
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
def buscar_imagem(consulta: str, categoria: str = "") -> tuple[str | None, str | None]:
    """Devolve (url_https, credito) de uma imagem de licença livre, ou (None, None)."""
    consulta = (consulta or "").strip()
    if not consulta:
        return None, None

    termos = set(consulta.lower().split()) | {categoria.lower()}
    if termos & PALAVRAS_ESPACO:
        url, credito = _nasa(consulta)
        if url:
            return url, credito

    for fonte in (_pexels, _openverse):
        url, credito = fonte(consulta)
        if url:
            return url, credito

    return None, None  # nada relevante e livre — fica o placeholder da categoria
