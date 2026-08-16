"""Folha das horas de golden hour, lado a lado, para o LOOK LOCK.

Existe porque a pergunta da hora **nao e' deste ou daquele quadro: e' do filme
inteiro** (D084). O parque e' todo chao horizontal, e com o sol a 10,1 graus do
contrato todo chao recebe `sin(10,1) = 0,17` do sol direto e o resto vem do ceu
azul. Isso decide a cor da grama, a cor do saibro e -- no Q3, que e' interior
coberto -- decide se o fundo do pavilhao e' um lugar ou um tunel preto.

O `folha_heroi.py` compara REAL contra 3D. Este compara **o mesmo 3D contra ele
mesmo em horas diferentes**, que e' outra pergunta: la se mede acerto, aqui se
escolhe. E escolha e' do Natan -- este script so poe as opcoes na mesma altura,
para o olho nao ser enganado por escala.

Uso:
  python scripts/folha_horas.py --saida out/heroi/Q3-hora.jpg \\
      --titulo "Q3 - a hora do LOOK LOCK" --altura 460 \\
      F:/heroi/Q3/hora-1815.png=18:15 (contrato) \\
      F:/heroi/Q3/hora-1730.png=17:30 \\
      F:/heroi/Q3/hora-1700.png=17:00
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


def montar(itens, saida, titulo="", altura=460):
    """`itens` e' uma lista de (caminho, rotulo)."""
    imgs = []
    for caminho, rotulo in itens:
        im = Image.open(caminho).convert("RGB")
        # MESMA ALTURA nos tres: comparacao de luz nao pode virar comparacao
        # de tamanho. E' a mesma regra do folha_heroi.py.
        im = im.resize((round(im.width * altura / im.height), altura),
                       Image.LANCZOS)
        imgs.append((im, rotulo))

    faixa, borda = 54, 10
    L = sum(im.width for im, _ in imgs) + borda * (len(imgs) + 1)
    A = altura + faixa + borda * 2
    folha = Image.new("RGB", (L, A), (17, 17, 19))
    d = ImageDraw.Draw(folha)
    d.text((borda, 14), titulo, font=_fonte(30), fill=(238, 238, 234))

    x = borda
    for im, rotulo in imgs:
        folha.paste(im, (x, faixa + borda))
        cx = x + im.width // 2
        t = d.textlength(rotulo, font=_fonte(22))
        d.rectangle([cx - t / 2 - 12, faixa + borda + 10,
                     cx + t / 2 + 12, faixa + borda + 44], fill=(17, 17, 19))
        d.text((cx - t / 2, faixa + borda + 14), rotulo, font=_fonte(22),
               fill=(238, 238, 234))
        x += im.width + borda

    Path(saida).parent.mkdir(parents=True, exist_ok=True)
    folha.save(saida, quality=92)
    print(f"folha  {saida}  {folha.size[0]}x{folha.size[1]}  {len(imgs)} horas")
    return saida


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--saida", required=True)
    p.add_argument("--titulo", default="")
    p.add_argument("--altura", type=int, default=460)
    p.add_argument("itens", nargs="+",
                   help="caminho=rotulo, na ordem em que entram na folha")
    a = p.parse_args()

    itens = []
    for bruto in a.itens:
        caminho, _, rotulo = bruto.partition("=")
        if not Path(caminho).exists():
            raise SystemExit(f"ABORTA: nao existe -- {caminho}")
        itens.append((caminho, rotulo or Path(caminho).stem))
    montar(itens, a.saida, a.titulo, a.altura)


if __name__ == "__main__":
    main()
