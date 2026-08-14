#!/usr/bin/env python3
"""Tira a cor-base de cada material do footage do proprio recinto.

Ate 14/08 as cores da cena eram chapadas e escolhidas por mim -- e o `CLAUDE.md`
proibe design system default: cor de material tem que descer de alguma coisa.
Aqui ela desce do que a camera do cliente viu.

**O problema que este script resolve, e o motivo do metodo ser esse:** quadro de
video nao entrega albedo, entrega cor ILUMINADA. Amostrar o pixel e chamar de
cor-base cozinha o sol de novembro dentro do material, e depois o HDRI ilumina
o sol que ja esta pintado. Duas saidas honestas existem: carta de cor no set
(nao ha) ou uma REFERENCIA CONHECIDA dentro do mesmo quadro.

O metodo, entao:

1. **Um quadro so, e de golden hour.** Todas as classes saem do mesmo frame --
   `DJI_20251129182345_0168_D` 00:00:52, o mesmo horario do filme. Misturar
   quadros e misturar iluminantes, e ai a comparacao entre classes nao vale.
2. **A lona branca de tenda e a ancora.** Lona de tenda de feira tem albedo
   conhecido, ~0,75. O que se mede nela e o ILUMINANTE; dividir as outras
   classes por ele derruba o sol e sobra a cor propria.
3. **Mediana, nao media.** Recorte de quadro real tem gente, cabo e sombra
   dentro; a mediana ignora isso, a media nao.
4. **Trabalho em LINEAR.** O JPEG e sRGB com gama; medir e dividir em sRGB da
   numero errado. Converte-se antes, volta-se depois.

O que sai daqui e `data/materiais-medidos.json`, com o recorte de cada amostra
escrito, para qualquer um conferir de onde veio cada cor.

Roda no venv (cv2 + numpy).

Uso:
    .venv/Scripts/python.exe scripts/medir_materiais.py
    .venv/Scripts/python.exe scripts/medir_materiais.py --debug out/amostras.png
"""

import argparse
import json
from pathlib import Path

import cv2
import numpy as np

RAIZ = Path(__file__).resolve().parent.parent

QUADRO = Path(r"E:\Projetos todos\Mapa - agroshow\Brutos Expo\_triagem"
              r"\provas-materiais\telha-metalica"
              r"\telha-metalica__DJI_20251129182345_0168_D__00m52_000s.jpg")

ALBEDO_DA_LONA = 0.75
"""Lona branca de tenda: refletancia difusa de ~0,75.

Nao e chute e nao e medida minha: e a faixa de mercado para PVC branco de
cobertura (0,70-0,80 novo, cai com sujeira). O valor exato importa menos do que
parece -- ele fixa a ESCALA de todas as classes de uma vez, entao um erro aqui
clareia ou escurece a cena inteira por igual, que e coisa que se corrige com
exposicao. O que o metodo protege e a RELACAO entre os materiais, e essa e
medida."""

# Recortes declarados, em pixel do quadro original (3840x2160). Escolhidos
# olhando o quadro, cada um dentro de uma superficie so e ao sol.
AMOSTRAS = {
    "lona": {
        "caixa": (1440, 770, 1960, 850),
        "onde": ("agua do telhado do pavilhao de tendas ao centro-alto, a que "
                 "esta VIRADA PARA O SOL. A primeira tentativa amostrou a agua "
                 "virada para o ceu e o iluminante saiu azul (R/B 0,63), o que "
                 "deixou a grama marrom -- superficie de ancora tem que estar "
                 "iluminada como as que se quer medir"),
        "material": "MAT_LONA",
    },
    "telha": {
        "caixa": (120, 830, 500, 960),
        "onde": "telhado metalico do galpao a esquerda, com o sol rasante nas ondas",
        "material": "MAT_TELHA",
    },
    "grama_pisada": {
        "caixa": (1240, 1300, 1520, 1380),
        "onde": ("gramado junto a alameda, ao sol -- e a grama PISADA de fim de "
                 "evento. Nao serve de cor geral do recinto: usada em 170.000 m² "
                 "chapados, ela deixou a cena com cara de deserto no render de "
                 "prova. Fica como a cor do desgaste, para a textura da Rodada 2"),
        "material": None,
    },
    "grama": {
        "caixa": (1660, 1380, 1960, 1480),
        "onde": ("faixa de gramado preservado entre a alameda e o bosque, ao sol "
                 "-- e a grama SA, e e ela que cobre a maior parte do recinto"),
        "material": "MAT_TERRENO",
    },
    "terra": {
        "caixa": (1520, 1120, 2000, 1170),
        "onde": "alameda de chao batido entre os pavilhoes de tenda",
        "material": "MAT_ARENA",
    },
    "brita": {
        "caixa": (200, 1800, 600, 1920),
        "onde": "piso solto da area de maquinas, ao pe das tendas",
        "material": "MAT_SAIBRO",
    },
    "arvore": {
        "caixa": (3000, 1240, 3300, 1320),
        "onde": ("massa fechada de copa no LADO DIREITO do quadro, longe do sol. "
                 "Duas tentativas antes falharam e as duas pelo mesmo motivo: "
                 "recorte largo pegava vao de ceu entre as copas, e recorte perto "
                 "do sol pegava o veu do flare -- os dois devolviam copa mais "
                 "clara que o gramado, o que nao existe"),
        "material": "MAT_COPA",
    },
    "campo": {
        "caixa": (2100, 500, 2500, 580),
        "onde": ("lavoura verde ao fundo, no alto do quadro. NAO entra em "
                 "material nenhum: e o CONTROLE do metodo. Qualquer um olha e "
                 "diz que e verde; se a inversao devolver isto oliva, quem "
                 "esta errado e a inversao, nao a grama"),
        "material": None,
    },
}


def srgb_para_linear(c):
    c = np.asarray(c, dtype=np.float64) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def linear_para_srgb(c):
    c = np.clip(np.asarray(c, dtype=np.float64), 0.0, 1.0)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def amostrar(img, caixa):
    x0, y0, x1, y1 = caixa
    r = img[y0:y1, x0:x1]
    if r.size == 0:
        return None
    bgr = np.median(r.reshape(-1, 3), axis=0)
    rgb = bgr[::-1]
    return srgb_para_linear(rgb), rgb


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--quadro", default=str(QUADRO))
    ap.add_argument("--saida", default="data/materiais-medidos.json")
    ap.add_argument("--debug")
    args = ap.parse_args()

    caminho = Path(args.quadro)
    if not caminho.exists():
        raise SystemExit(f"quadro nao encontrado: {caminho}\n"
                         "O footage nao esta no repositorio de proposito "
                         "(material de cliente, origin publico). Ver ESTADO.md.")

    # cv2.imread nao abre caminho com acento no Windows -- armadilha 9
    img = cv2.imdecode(np.fromfile(str(caminho), dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise SystemExit(f"nao consegui decodificar {caminho}")
    print(f"quadro {img.shape[1]}x{img.shape[0]}  {caminho.name}\n")

    bruto = {}
    for nome, a in AMOSTRAS.items():
        r = amostrar(img, a["caixa"])
        if r is None:
            raise SystemExit(f"recorte vazio em {nome}")
        bruto[nome] = r

    lin_lona = bruto["lona"][0]
    # o iluminante e o que a lona devolve dividido pelo que ela deveria devolver
    iluminante = lin_lona / ALBEDO_DA_LONA
    print(f"iluminante medido na lona (linear RGB): "
          f"{iluminante[0]:.3f} {iluminante[1]:.3f} {iluminante[2]:.3f}")
    print(f"  -> luz {'quente' if iluminante[0] > iluminante[2] else 'fria'}: "
          f"R/B = {iluminante[0] / max(iluminante[2], 1e-6):.2f}\n")

    itens = {}
    print(f"{'classe':10s} {'sRGB no quadro':>18s} {'albedo linear':>22s}  {'hex':>8s}")
    for nome, a in AMOSTRAS.items():
        lin, srgb_bruto = bruto[nome]
        albedo = np.clip(lin / iluminante, 0.0, 1.0)
        srgb_out = linear_para_srgb(albedo)
        hexa = "#" + "".join(f"{int(round(v * 255)):02x}" for v in srgb_out)
        print(f"{nome:10s} "
              f"{int(srgb_bruto[0]):4d},{int(srgb_bruto[1]):4d},{int(srgb_bruto[2]):4d}   "
              f"{albedo[0]:6.3f} {albedo[1]:6.3f} {albedo[2]:6.3f}  {hexa}")
        itens[nome] = {
            "material": a["material"],
            "onde": a["onde"],
            "caixa_px": list(a["caixa"]),
            "srgb_no_quadro": [int(v) for v in srgb_bruto],
            "albedo_linear": [round(float(v), 4) for v in albedo],
            "hex_aproximado": hexa,
        }

    alvo = RAIZ / args.saida
    alvo.write_text(json.dumps({
        "o_que_e": ("Cor-base por classe, tirada do footage do proprio recinto e "
                    "corrigida do iluminante. NAO e medida de laboratorio: e a "
                    "melhor leitura possivel de um quadro de video sem carta de cor."),
        "quadro": caminho.name,
        "quadro_completo": str(caminho),
        "por_que_este_quadro": ("golden hour, a mesma luz do filme, e tem telha, "
                                "lona, grama, terra e arvore no MESMO quadro -- "
                                "entao as classes sao comparaveis entre si."),
        "ancora": {"classe": "lona", "albedo_assumido": ALBEDO_DA_LONA,
                   "por_que": "lona de PVC branco de tenda tem refletancia de mercado 0,70-0,80"},
        "iluminante_linear_rgb": [round(float(v), 4) for v in iluminante],
        "itens": itens,
    }, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\ngravado: {alvo}")

    if args.debug:
        vis = img.copy()
        for nome, a in AMOSTRAS.items():
            x0, y0, x1, y1 = a["caixa"]
            cv2.rectangle(vis, (x0, y0), (x1, y1), (0, 0, 255), 6)
            cv2.putText(vis, nome, (x0 + 8, y0 + 46), cv2.FONT_HERSHEY_SIMPLEX,
                        1.6, (0, 0, 255), 4)
        p = RAIZ / args.debug
        p.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(p), cv2.resize(vis, None, fx=0.5, fy=0.5))
        print(f"debug: {p}")


if __name__ == "__main__":
    main()
