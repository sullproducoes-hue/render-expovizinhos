#!/usr/bin/env python3
"""Mede quanto do TELHADO esta no teto da escala, quadro a quadro.

    .venv/Scripts/python.exe scripts/varrer_estouro.py
    .venv/Scripts/python.exe scripts/varrer_estouro.py --videos "1 (2)" "1 (3)"

Existe porque eu passei tres rodadas cacando caixa de amostra no telhado e
recebendo `2,22%`, `0,87%`, `4,78%` de pixel no teto -- mexendo na caixa e
tentando de novo. Isso e ajustar parametro ate o numero ficar bonito, que a
**armadilha 16** deste projeto proibe em uma linha: *"parametro que muda a
resposta nao e medida"*.

O certo era parar de cacar e medir o problema. E o problema tem numero:

**Num nadir de parque, os 3% de pixel mais claros do quadro SAO o telhado** --
nao ha outra superficie grande e clara ali. Entao a conta e direta: que fracao
deles esta em 65000/65535 ou acima.

A resposta, nos quatro nadires de 13/08: **30% a 40%**. O drone expos para o
chao, e a chapa metalica -- que e a coisa mais clara do parque -- saturou. Em
dia encoberto, sem disco solar em lugar nenhum.

**Isso mata a hipotese que eu tinha vendido**: eu disse que a medicao de 14/08
estourou por reflexo especular do sol, e que num dia encoberto daria para medir.
Da nao. O estouro nao e so do sol: e de exposicao, e acontece com ceu fechado
tambem. Enquanto o material que existe for este, `MAT_TELHA` nao se mede.

O que **fecharia**, e e barato quando alguem estiver la: um quadro exposto para
o TELHADO, nem que o chao va a preto. Meia parada de diafragma resolve, e o
material de medicao nao precisa ser bonito.
"""

import argparse
import json
from pathlib import Path

import cv2
import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
LINEAR = Path(r"E:\Projetos todos\Mapa - agroshow\Brutos Expo"
              r"\agroshow extrator somente\extracao\linear")

TETO = 65000
"""Valor a partir do qual o pixel conta como saturado, em 16 bits (0-65535)."""

PERCENTIL_CLARO = 97
"""Os `100 - P`% mais claros do quadro. Num nadir de parque isso e o telhado.

Nao e limiar de gosto: e a fracao de area que telhado ocupa nestes quadros. Subir
para 99 mede so o brilho especular; descer para 90 comeca a pegar terra clara."""


def varrer(png):
    b = cv2.imdecode(np.fromfile(str(png), dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    if b is None or b.dtype != np.uint16:
        return None
    lin = b.astype(np.float64) / 65535.0
    lum = 0.2126 * lin[:, :, 2] + 0.7152 * lin[:, :, 1] + 0.0722 * lin[:, :, 0]
    claros = lum > np.percentile(lum, PERCENTIL_CLARO)
    estourado = (b >= TETO).any(axis=2)
    return {
        "estouro_no_quadro": float(estourado.mean()),
        "estouro_nos_claros": float(estourado[claros].mean()) if claros.any() else 0.0,
        "luminancia_p97": float(np.percentile(lum, PERCENTIL_CLARO)),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--videos", nargs="*", default=["1 (2)", "1 (3)"])
    ap.add_argument("--saida", default="data/estouro-telhado.json")
    args = ap.parse_args()

    print("=" * 72)
    print("VARREDURA DE ESTOURO NO TELHADO -- os 3% mais claros de cada quadro")
    print("=" * 72)
    print(f"  {'quadro':22s} {'no quadro':>10s} {'nos claros':>12s}")

    itens, piores = {}, []
    for v in args.videos:
        pasta = LINEAR / v
        if not pasta.is_dir():
            print(f"  {v}: sem extracao linear")
            continue
        for png in sorted(pasta.glob("*.png")):
            r = varrer(png)
            if r is None:
                continue
            itens[png.stem] = r
            print(f"  {png.stem:22s} {r['estouro_no_quadro']*100:9.2f}% "
                  f"{r['estouro_nos_claros']*100:11.1f}%")
            piores.append(r["estouro_nos_claros"])

    if not itens:
        raise SystemExit("nenhum quadro varrido")

    melhor = min(itens.items(), key=lambda kv: kv[1]["estouro_nos_claros"])
    print(f"\n  melhor quadro: {melhor[0]} com "
          f"{melhor[1]['estouro_nos_claros']*100:.1f}% dos claros no teto")
    print(f"  mediana entre {len(piores)} quadros: "
          f"{np.median(piores)*100:.1f}%")
    print("\n  VEREDITO: a telha NAO se mede neste material. O drone expos para o")
    print("  chao e a chapa saturou -- em dia encoberto, sem disco solar em lugar")
    print("  nenhum. Nao e reflexo do sol, e exposicao.")

    alvo = RAIZ / args.saida
    alvo.write_text(json.dumps({
        "_procedencia": "registro — varredura de saturacao no telhado, 15/08/2026",
        "_por_que": ("tres tentativas de medir MAT_TELHA devolveram caixas com 2,2%, "
                     "0,9% e 4,8% de pixel no teto. Em vez de mexer na caixa ate o "
                     "numero passar (armadilha 16), mediu-se o problema."),
        "teto_16_bits": TETO,
        "percentil_claro": PERCENTIL_CLARO,
        "melhor_quadro": melhor[0],
        "melhor_estouro_nos_claros": round(melhor[1]["estouro_nos_claros"], 4),
        "mediana_estouro_nos_claros": round(float(np.median(piores)), 4),
        "veredito": "MAT_TELHA nao e medivel neste footage",
        "o_que_fecharia": ("um quadro exposto para o TELHADO, nem que o chao va a "
                           "preto. Meia parada de diafragma. Material de medicao "
                           "nao precisa ser bonito."),
        "quadros": itens,
    }, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\ngravado: {alvo}")
    print("=" * 72)


if __name__ == "__main__":
    main()
