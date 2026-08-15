#!/usr/bin/env python3
"""Projeta as 42 vias da planta sobre o aereo nadir de 13/08, para conferir.

    .venv/Scripts/python.exe scripts/sobrepor_aereo.py
    .venv/Scripts/python.exe scripts/sobrepor_aereo.py --escala 5.5 6.0 6.4

`data/vias.json` carrega o aviso desde que foi gerado: *"TRACADO LIDO DE BITMAP,
NAO CONFERIDO. Nada daqui vira geometria antes de conferido_pelo_natan: true"*.
As 42 continuam com `false`. O video `1 (2)` e nadir de drone, e mostra o
tracado real -- entao da para conferir por medicao em vez de perguntar.

## A transformacao, e de onde sai cada parte

Nadir, entao mundo -> imagem e uma SEMELHANCA (escala, rotacao, translacao), sem
perspectiva de primeira ordem:

    p_img = C_img + s * R(delta) * (p_mundo - C_mundo)

- **C_mundo** = centro da arena, `(-74,7 / -3,2)` m, marcado pelo Natan na
  planta em 14/08. E o unico ponto do recinto com posicao confirmada por ele.
- **C_img** = centro dos arcos concentricos no quadro.
- **delta** = rotacao, do eixo dos pavilhoes: rumo de mapa 108 graus (medido no
  footprint em 14/08) contra a direcao do mesmo galpao na imagem.
- **s** = escala, em px/m. **E a parte fraca**, e por isso ela e parametro: sai
  do raio do patamar mais externo, e qual arco visivel corresponde a qual
  patamar e leitura, nao medida. Por isso o script desenha varias escalas.

## O que este script NAO faz

Nao decide nada. Ele produz a folha para OLHAR. Via da planta que cair em cima
de via na foto confere; via que cair no mato nao confere. E `conferido_pelo_natan`
continua sendo dele -- o nome do campo diz de quem e.
"""

import argparse
import json
import math
from pathlib import Path

import cv2
import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
LINEAR = Path(r"E:\Projetos todos\Mapa - agroshow\Brutos Expo"
              r"\agroshow extrator somente\extracao\linear")

QUADRO = "1 (2)__0076s"
C_IMG = (1780.0, 1150.0)
"""Centro dos arcos concentricos, em px do quadro original.

Primeira leitura foi (1820, 1600), tirada da folha reduzida a 25%. A propria
sobreposicao mostrou o erro: os aneis do modelo pousaram 470 px abaixo dos
terracos da foto. **Este e o ponto de ajuste, e ele e honesto porque o que
VALIDA a transformacao nao entra nela:** o centro, a escala e a rotacao saem da
arena e dos pavilhoes; quem confere sao as 42 VIAS, que nao foram usadas em
nada disso. Via que pousa em cima de estrada visivel confere."""
PAVILHAO_A = (1760.0, 140.0)
PAVILHAO_B = (2800.0, 820.0)
RUMO_PAVILHOES = 108.0        # rumo de mapa, medido no footprint em 14/08


def lin2srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def delta_rotacao():
    """Angulo entre o mundo e a imagem, tirado do eixo dos pavilhoes.

    Convencao do mundo: x = leste do mapa, y = norte do mapa; rumo de mapa
    R relaciona-se com o angulo matematico phi por `R = 90 - phi`.
    Na imagem, y aponta para BAIXO, entao o angulo matematico e
    `atan2(-dy, dx)`."""
    phi_mundo = math.radians(90.0 - RUMO_PAVILHOES)
    dx = PAVILHAO_B[0] - PAVILHAO_A[0]
    dy = PAVILHAO_B[1] - PAVILHAO_A[1]
    psi_img = math.atan2(-dy, dx)
    return psi_img - phi_mundo


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--escala", type=float, nargs="*", default=[5.0, 5.87, 6.8],
                    help="px por metro. Varias -> varias folhas")
    args = ap.parse_args()

    png = LINEAR / QUADRO.split("__")[0] / f"{QUADRO}.png"
    bruto = cv2.imdecode(np.fromfile(str(png), dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    base = (lin2srgb(bruto.astype(np.float64) / 65535.0) * 255).astype(np.uint8)

    vias = [v for v in json.loads((RAIZ / "data" / "vias.json")
                                  .read_text(encoding="utf-8"))["vias"] if v["e_via"]]
    bacia = json.loads((RAIZ / "data" / "bacia.json").read_text(encoding="utf-8"))
    cx, cy = bacia["a_medicao"]["centro_da_arena_m"]

    d = delta_rotacao()
    print(f"quadro   : {QUADRO}")
    print(f"rotacao  : {math.degrees(d):+.1f} graus (mundo -> imagem), do eixo dos pavilhoes")
    print(f"centro   : mundo ({cx}, {cy}) m  ->  imagem {C_IMG} px")
    print(f"vias     : {len(vias)} com e_via=true\n")

    cos_d, sin_d = math.cos(d), math.sin(d)

    for s in args.escala:
        vis = base.copy()

        def proj(p):
            X, Y = p[0] - cx, p[1] - cy
            xi = X * cos_d - Y * sin_d
            yi = X * sin_d + Y * cos_d
            return (int(round(C_IMG[0] + s * xi)),
                    int(round(C_IMG[1] - s * yi)))    # y da imagem cresce p/ baixo

        # aneis do modelo da bacia, para casar com os arcos visiveis
        for r, rot in [(45, 1), (62, 0), (78, 1), (95, 0), (125, 1), (150, 0)]:
            pts = np.array([proj((cx + r * math.cos(math.radians(a)),
                                  cy + r * math.sin(math.radians(a))))
                            for a in range(0, 361, 3)], np.int32)
            cv2.polylines(vis, [pts], False, (0, 200, 255) if rot else (0, 120, 255), 3)

        dentro = 0
        for v in vias:
            pts = np.array([proj(p) for p in v["pontos_m"]], np.int32)
            if ((pts[:, 0] >= 0) & (pts[:, 0] < vis.shape[1]) &
                    (pts[:, 1] >= 0) & (pts[:, 1] < vis.shape[0])).any():
                dentro += 1
            cv2.polylines(vis, [pts], False, (60, 255, 60), 5)
            cv2.putText(vis, v["id"], tuple(pts[0]), cv2.FONT_HERSHEY_SIMPLEX,
                        1.2, (60, 255, 60), 3)

        cv2.circle(vis, (int(C_IMG[0]), int(C_IMG[1])), 18, (255, 0, 255), -1)
        cv2.putText(vis, f"escala {s:.2f} px/m   {dentro}/{len(vias)} vias caem no quadro",
                    (40, 90), cv2.FONT_HERSHEY_SIMPLEX, 2.2, (255, 0, 255), 5)

        out = RAIZ / "out" / "aereo" / f"vias-escala-{s:.2f}.jpg"
        out.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(out), cv2.resize(vis, None, fx=0.35, fy=0.35),
                    [cv2.IMWRITE_JPEG_QUALITY, 92])
        print(f"  {s:5.2f} px/m -> {dentro}/{len(vias)} vias no quadro   {out.relative_to(RAIZ)}")

    print("\nAmarelo/laranja = aneis do modelo da bacia. Verde = vias da planta.")
    print("Se os aneis casarem com os arcos da foto, a escala esta certa.")


if __name__ == "__main__":
    main()
