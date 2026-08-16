"""Folha `real | 3D` de um quadro-heroi.

E' a entrega e tambem a regua: a Lei 3 da noite diz que o 3D tem que GANHAR da
folha, nao so existir. Olhar o render sozinho e' como conferir traducao contra o
titulo em ingles -- so a comparacao lado a lado mostra o que falta.

Uso:
  python scripts/folha_heroi.py --real <foto.jpg> --render <render.png> \
      --saida out/heroi/Q1.jpg --titulo "Q1 - Portal" [--altura 900]
"""

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONTE = Path(__file__).resolve().parent.parent.parent / "fontes 2026" / "ArchivoNarrow-Bold.ttf"


def _fonte(px):
    try:
        return ImageFont.truetype(str(FONTE), px)
    except Exception:
        return ImageFont.load_default()


def montar(real, render, saida, titulo, altura=900, rotulos=("REAL", "3D")):
    a = Image.open(real).convert("RGB")
    b = Image.open(render).convert("RGB")

    # Mesma ALTURA nos dois, para a comparacao ser de forma e nao de escala
    a = a.resize((round(a.width * altura / a.height), altura), Image.LANCZOS)
    b = b.resize((round(b.width * altura / b.height), altura), Image.LANCZOS)

    faixa, borda = 54, 10
    L = a.width + b.width + borda * 3
    A = altura + faixa + borda * 2
    folha = Image.new("RGB", (L, A), (17, 17, 19))
    folha.paste(a, (borda, faixa + borda))
    folha.paste(b, (borda * 2 + a.width, faixa + borda))

    d = ImageDraw.Draw(folha)
    d.text((borda, 14), titulo, font=_fonte(30), fill=(238, 238, 234))
    for x, w, rot in ((borda, a.width, rotulos[0]),
                      (borda * 2 + a.width, b.width, rotulos[1])):
        cx = x + w // 2
        t = d.textlength(rot, font=_fonte(22))
        d.rectangle([cx - t / 2 - 12, faixa + borda + 10,
                     cx + t / 2 + 12, faixa + borda + 44], fill=(17, 17, 19))
        d.text((cx - t / 2, faixa + borda + 14), rot, font=_fonte(22),
               fill=(238, 238, 234))

    Path(saida).parent.mkdir(parents=True, exist_ok=True)
    folha.save(saida, quality=92)
    print(f"folha  {saida}  {folha.size[0]}x{folha.size[1]}")
    return saida


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--real", required=True)
    p.add_argument("--render", required=True)
    p.add_argument("--saida", required=True)
    p.add_argument("--titulo", default="")
    p.add_argument("--altura", type=int, default=900)
    p.add_argument("--rotulos", default="REAL,3D")
    a = p.parse_args()
    montar(a.real, a.render, a.saida, a.titulo, a.altura,
           tuple(a.rotulos.split(",")))


if __name__ == "__main__":
    main()
