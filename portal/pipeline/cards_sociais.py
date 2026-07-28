"""Gera um card 1080x1080 (Instagram/feed) a partir de um post publicado.

Uso:
    python cards_sociais.py <slug>        # ex.: exemplo-resgate-animais
    python cards_sociais.py --todos       # gera cards de todos os posts publicados

Os cards saem em pipeline/_cards/. Publicação nas redes é manual (por enquanto):
link na bio -> site.
"""

from __future__ import annotations

import re
import sys
import textwrap
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Instale o Pillow:  pip install pillow")
    sys.exit(1)

RAIZ = Path(__file__).resolve().parent
CONTENT_DIR = RAIZ.parent / "site" / "src" / "content" / "posts"
SAIDA = RAIZ / "_cards"
MARCA = "O Lado Bom"
SITE_URL = "oladobom.com.br"
ARROBA = "@oladobom"

# slug -> (nome, emoji) para o rótulo de categoria no card
CATEGORIAS = {
    "ciencia": ("Ciência", "🔬"),
    "solidariedade": ("Solidariedade", "🤝"),
    "meio-ambiente": ("Meio Ambiente", "🌱"),
    "saude": ("Saúde", "❤️"),
    "animais": ("Animais", "🐾"),
    "superacao": ("Superação", "⭐"),
    "tecnologia": ("Tecnologia do Bem", "💡"),
    "mundo": ("Mundo", "🌍"),
}

AMARELO = (245, 180, 0)
AMARELO_CLARO = (255, 246, 218)
VERDE_CLARO = (234, 250, 240)
TINTA = (31, 36, 48)
TINTA_SUAVE = (85, 96, 122)
VERDE = (21, 112, 72)


def _fonte(tamanho: int, negrito: bool = False):
    candidatos = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if negrito
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if negrito
        else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for c in candidatos:
        if Path(c).exists():
            return ImageFont.truetype(c, tamanho)
    return ImageFont.load_default()


def _ler_frontmatter(md: Path) -> dict:
    texto = md.read_text(encoding="utf-8")
    m = re.search(r"^---\n(.*?)\n---", texto, re.DOTALL)
    campos: dict[str, str] = {}
    if m:
        for linha in m.group(1).splitlines():
            if ":" in linha:
                chave, _, valor = linha.partition(":")
                campos[chave.strip()] = valor.strip().strip('"')
    return campos


def gerar_card(md: Path) -> Path | None:
    dados = _ler_frontmatter(md)
    if dados.get("draft", "false") == "true":
        return None  # não gera card para rascunho

    titulo = dados.get("titulo", md.stem)
    fonte_nome = dados.get("fonteNome", "")
    cat_nome, _cat_emoji = CATEGORIAS.get(dados.get("categoria", ""), ("Boa notícia", ""))

    img = Image.new("RGB", (1080, 1080), AMARELO_CLARO)
    d = ImageDraw.Draw(img)

    # faixa superior verde-clara + sol + marca
    d.rectangle([0, 0, 1080, 190], fill=VERDE_CLARO)
    d.ellipse([70, 74, 146, 150], fill=AMARELO)
    d.text((172, 92), MARCA, font=_fonte(52, negrito=True), fill=TINTA)
    d.text((174, 148), ARROBA, font=_fonte(26), fill=VERDE)

    # rótulo da categoria (uppercase, dourado)
    d.text((80, 250), cat_nome.upper(), font=_fonte(30, negrito=True), fill=(180, 132, 0))

    # título centralizado verticalmente na área de conteúdo
    fonte_titulo = _fonte(64, negrito=True)
    linhas = textwrap.wrap(titulo, width=24)[:6]
    bloco_altura = len(linhas) * 82
    y = 320 + max(0, (520 - bloco_altura) // 2)
    for linha in linhas:
        d.text((80, y), linha, font=fonte_titulo, fill=TINTA)
        y += 82

    # rodapé verde: fonte à esquerda, site à direita
    d.rectangle([0, 980, 1080, 1080], fill=VERDE)
    credito = f"Fonte: {fonte_nome}" if fonte_nome else "Boa notícia do dia"
    d.text((80, 1014), credito, font=_fonte(30), fill=(255, 255, 255))
    url_font = _fonte(30, negrito=True)
    largura_url = d.textlength(SITE_URL, font=url_font)
    d.text((1000 - largura_url, 1014), SITE_URL, font=url_font, fill=(255, 255, 255))

    SAIDA.mkdir(parents=True, exist_ok=True)
    destino = SAIDA / f"{md.stem}.png"
    img.save(destino, "PNG")
    return destino


def main() -> None:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return

    if args[0] == "--todos":
        alvos = sorted(CONTENT_DIR.glob("*.md"))
    else:
        alvos = [CONTENT_DIR / f"{args[0]}.md"]

    for md in alvos:
        if not md.exists():
            print(f"[cards] não encontrado: {md.name}")
            continue
        destino = gerar_card(md)
        if destino:
            print(f"[cards] ✓ {destino}")
        else:
            print(f"[cards] pulado (rascunho): {md.name}")


if __name__ == "__main__":
    main()
