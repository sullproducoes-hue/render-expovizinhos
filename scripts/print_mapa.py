#!/usr/bin/env python3
"""
Desenha o que o auditor leu por cima da propria planta, para conferencia humana.

Existe porque o auditor devolve 142 coordenadas e ninguem confere coordenada
lendo JSON. Aqui elas viram marcador numerado sobre o mapa, com a lista ao lado.
O Natan olha, e o que estiver no lugar errado ele diz pelo numero.

Tres saidas, e cada uma responde a uma pergunta diferente:

    --roteiro   so a camada vermelha, 21 lugares. "os lugares do video estao
                onde eu penso que estao?"
    --tudo      as 142. "faltou algum nome?"
    --vias      so as vias e o entorno. "a estrada esta passando onde deve?"

Uso:
    python scripts/print_mapa.py --roteiro -o docs/
    python scripts/print_mapa.py --tudo --dpi 200
"""

import argparse
import json
import sys
from pathlib import Path

import pymupdf
from PIL import Image, ImageDraw, ImageFont

FONTES = [
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]

COR_ROTEIRO = (220, 30, 30)
COR_PLANTA = (20, 80, 200)
COR_VIA = (200, 120, 0)
BRANCO = (255, 255, 255)
PRETO = (25, 25, 25)

# Rotulos da planta que descrevem via ou entorno, e nao um lugar do recinto.
VIAS = {
    "PR 473", "AV. VER. DORVALINO TOSI", "AVENIDA JOSÉ MARCANTE",
    "AVENIDA VINICIUS DE MORAIS", "RUA JORGE AMADO", "CARROS DE APLICATIVO",
    "CRUZEIRO DO IGUAÇU", "DOIS VIZINHOS", "ESTACIONAMENTO", "PORTARIA",
    "PORTAL", "Trilha",
}


def fonte(tamanho):
    for caminho in FONTES:
        if Path(caminho).exists():
            return ImageFont.truetype(caminho, tamanho)
    return ImageFont.load_default()


def escolher(locais, modo):
    if modo == "roteiro":
        return [lo for lo in locais if lo["camada"] == "roteiro"]
    if modo == "vias":
        return [lo for lo in locais if lo["nome"] in VIAS]
    return locais


def desenhar(dados, pdf_path, modo, dpi, destino):
    page = pymupdf.open(pdf_path)[0]
    pix = page.get_pixmap(dpi=dpi)
    mapa = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

    # pontos de PDF -> pixels da imagem renderizada
    escala_px = pix.width / dados["prancha"]["largura_pt"]

    alvos = escolher(dados["locais"], modo)
    alvos.sort(key=lambda lo: (lo["y_pt"], lo["x_pt"]))

    # Faixa branca a direita para a lista. Sem ela os nomes cobrem o desenho.
    largura_lista = int(pix.width * 0.26)
    tela = Image.new("RGB", (pix.width + largura_lista, pix.height), BRANCO)
    tela.paste(mapa, (0, 0))
    d = ImageDraw.Draw(tela)

    raio = max(9, int(pix.width / 220))
    f_num = fonte(int(raio * 1.5))
    f_lista = fonte(max(13, int(pix.width / 190)))
    f_titulo = fonte(max(18, int(pix.width / 120)))

    for i, lo in enumerate(alvos, 1):
        cor = COR_ROTEIRO if lo["camada"] == "roteiro" else (
            COR_VIA if lo["nome"] in VIAS else COR_PLANTA)
        cx = lo["x_pt"] * escala_px
        cy = lo["y_pt"] * escala_px
        d.ellipse([cx - raio, cy - raio, cx + raio, cy + raio],
                  fill=cor, outline=BRANCO, width=max(2, raio // 4))
        d.text((cx, cy), str(i), font=f_num, fill=BRANCO, anchor="mm")

    x0 = pix.width + int(largura_lista * 0.05)
    y = int(pix.height * 0.02)
    titulo = {"roteiro": "Camada do roteiro do cliente",
              "vias": "Vias, portões e entorno",
              "tudo": "Todos os rótulos lidos da planta"}[modo]
    d.text((x0, y), titulo, font=f_titulo, fill=PRETO)
    y += int(f_titulo.size * 2.0)
    d.text((x0, y), f"{len(alvos)} de {len(dados['locais'])} rótulos  ·  "
                    f"{dados['fonte']}", font=f_lista, fill=(110, 110, 110))
    y += int(f_lista.size * 2.2)

    passo = int(f_lista.size * 1.55)
    for i, lo in enumerate(alvos, 1):
        if y > pix.height - passo:
            d.text((x0, y), f"... e mais {len(alvos) - i + 1}",
                   font=f_lista, fill=(110, 110, 110))
            break
        cor = COR_ROTEIRO if lo["camada"] == "roteiro" else (
            COR_VIA if lo["nome"] in VIAS else COR_PLANTA)
        d.ellipse([x0, y + 3, x0 + f_lista.size * 0.7, y + 3 + f_lista.size * 0.7],
                  fill=cor)
        nome = lo["nome"]
        if lo.get("descricao"):
            nome += f"  ({lo['descricao']})"
        if len(nome) > 44:
            nome = nome[:41] + "..."
        d.text((x0 + f_lista.size * 1.1, y), f"{i}. {nome}",
               font=f_lista, fill=PRETO)
        y += passo

    tela.save(destino, quality=94)
    return destino, len(alvos)


def desenhar_tracado(dados, vias, pdf_path, dpi, destino):
    """A polilinha lida do bitmap por cima da planta, para o Natan conferir."""
    page = pymupdf.open(pdf_path)[0]
    pix = page.get_pixmap(dpi=dpi)
    mapa = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    escala_px = pix.width / dados["prancha"]["largura_pt"]

    d = ImageDraw.Draw(mapa)
    f_id = fonte(max(20, int(pix.width / 130)))
    reais = [v for v in vias if v["e_via"]]

    for v in reais:
        pts = [(x * escala_px, y * escala_px) for x, y in v["pontos_pt"]]
        # Laranja: via com nome na planta. Azul: traco de dentro do recinto,
        # onde o desenho nao diz se e corredor ou borda de talude.
        cor = COR_VIA if v.get("tipo") == "perimetro" else COR_PLANTA
        d.line(pts, fill=cor, width=max(4, int(pix.width / 700)), joint="curve")
        d.text(pts[0], v["id"], font=f_id, fill=cor,
               stroke_width=4, stroke_fill=BRANCO)

    mapa.save(destino, quality=94)
    return destino, len(reais)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--locais", default="data/locais.json")
    ap.add_argument("--vias-json", default="data/vias.json")
    ap.add_argument("--pdf", default="reference/Mapa_AGROSHOW26.pdf")
    ap.add_argument("-o", "--out", default="docs")
    ap.add_argument("--dpi", type=int, default=170)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--roteiro", action="store_const", const="roteiro",
                   dest="modo")
    g.add_argument("--tudo", action="store_const", const="tudo", dest="modo")
    g.add_argument("--vias", action="store_const", const="vias", dest="modo")
    g.add_argument("--tracado", action="store_const", const="tracado", dest="modo")
    ap.set_defaults(modo="roteiro")
    args = ap.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")
    dados = json.loads(Path(args.locais).read_text(encoding="utf-8"))
    saida = Path(args.out) / f"conferencia-{args.modo}.jpg"
    saida.parent.mkdir(parents=True, exist_ok=True)

    if args.modo == "tracado":
        vias = json.loads(Path(args.vias_json).read_text(encoding="utf-8"))["vias"]
        destino, n = desenhar_tracado(dados, vias, args.pdf, args.dpi, saida)
        print(f"escrito: {destino}  ({n} vias traçadas)")
        return

    destino, n = desenhar(dados, args.pdf, args.modo, args.dpi, saida)
    print(f"escrito: {destino}  ({n} marcadores)")


if __name__ == "__main__":
    main()
