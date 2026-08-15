#!/usr/bin/env python3
"""Confere o mapa 3D comprado no maps3d.io contra o que a cena ja tem.

    .venv/Scripts/python.exe scripts/conferir_mapa_comprado.py

O Natan comprou em 15/08 um mapa 3D de Dois Vizinhos e perguntou se ajuda. Este
script responde com numero em vez de opiniao: le o OBJ, projeta as vias de
OpenStreetMap no mundo da cena e desenha por cima das 42 vias que sairam do
bitmap da planta.

## O que o mapa comprado E

Nao e fotogrametria. E construcao procedural a partir de tres fontes, e o
`metadata.json` diz cada uma:

- **relevo**: elevacao em canvas de 52x37 sobre 1973x1419 m -> **38 m por
  amostra**. O projeto ja tem SRTM de 30 m ate 12 km, conferido em +-5 m contra
  segunda fonte. **O comprado e mais grosso e cobre 6x menos.**
- **imagem de chao**: Satlas super-resolvida, zoom 15 -> 4,3 m/px. Melhor
  resolucao que o WorldCover de 10 m, mas e IMAGEM com luz assada dentro, e a
  doutrina daqui e cor MEDIDA com de-lighting, nao foto colada.
- **predios**: 1.351 caixas de OSM, **uma cor chapada** (0,945/0,925/0,882) e
  altura inventada entre 6 e 10 m (`minHeight: 6, maxHeight: 10`,
  `heightRandomnessPercent: 0`, `detailed: false`).
- **vias**: 185 segmentos de OSM, e **e aqui que pode ter valor** -- fonte
  vetorial, georreferenciada e INDEPENDENTE do Hough sobre bitmap.

## A licenca esta limpa, e isso importa

`README.txt`: *"Voce pode usa-lo para qualquer finalidade, desde que adicione a
atribuicao correta"* -- Satlas (Allen Institute for AI) e, para os dados
topograficos, `(c) OpenStreetMap contributors`. Uso comercial liberado com
credito, como o ESA WorldCover que ja esta no `assets/MANIFESTO.md`. **Isto e
entrega de cliente, entao a linha de credito nao pode sumir.**

## A ressalva do alinhamento, e ela e honesta

O mundo da cena tem origem no **centro da prancha** (`dados["_origem"]`), que e
um ponto de DESENHO, nao geografico -- nao ha lat/lon guardado para ele. Entao
para sobrepor eu preciso assumir que o centro usado no download do DEM
(`data/relevo-entorno.json`, -25,73144 / -53,07627) e a origem do mundo.

**Isso e suposicao, e o proprio desenho a testa:** se as vias de OSM cairem em
cima das vias da planta, a suposicao vale; se cairem deslocadas, nao vale e o
mapa nao serve para conferir nada sem uma ancora de verdade.
"""

import json
import math
from pathlib import Path

import cv2
import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
COMPRADO = Path(r"E:\Projetos todos\Mapa - agroshow\Mapa 3d comprado"
                r"\maps3d-obj-2026-08-15_12-10-14")
OBJ = COMPRADO / "maps3d-2026-08-15_12-10-14.obj"

NORTE_DO_MAPA = 11.5
"""Quanto o norte verdadeiro esta girado em relacao ao +Y do mundo da cena.

`data/luz.json`, medido na rosa dos ventos da prancha. O OSM esta em norte
VERDADEIRO; o mundo da cena esta no norte do MAPA. Sem esta rotacao a
sobreposicao sai torta em 11,5 graus e alguem chamaria isso de erro do OSM."""

LADOS_VIA = ("roadGroup_local_flat", "roadGroup_service_flat",
             "roadGroup_collector_flat")


def wgs84_para_3857(lon, lat):
    R = 6378137.0
    return (R * math.radians(lon),
            R * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)))


def ler_obj(caminho, materiais):
    """Devolve {material: array Nx3} com os vertices usados por cada material."""
    verts, grupos, atual = [], {}, None
    for linha in caminho.read_text(errors="ignore").split("\n"):
        if linha.startswith("v "):
            p = linha.split()
            verts.append((float(p[1]), float(p[2]), float(p[3])))
        elif linha.startswith("usemtl "):
            atual = linha[7:].strip()
        elif linha.startswith("f ") and atual in materiais:
            for t in linha.split()[1:]:
                i = int(t.split("/")[0])
                grupos.setdefault(atual, []).append(i - 1 if i > 0 else len(verts) + i)
    V = np.array(verts)
    return {m: V[np.unique(idx)] for m, idx in grupos.items()}


def main():
    meta = json.loads((COMPRADO / "metadata.json").read_text(encoding="utf-8"))
    rel = json.loads((RAIZ / "data" / "relevo-entorno.json").read_text(encoding="utf-8"))
    vias = json.loads((RAIZ / "data" / "vias.json").read_text(encoding="utf-8"))
    bacia = json.loads((RAIZ / "data" / "bacia.json").read_text(encoding="utf-8"))
    cxa, cya = bacia["a_medicao"]["centro_da_arena_m"]

    lat, lon = rel["centro"]["lat"], rel["centro"]["lon"]
    sx, sy = wgs84_para_3857(lon, lat)
    ox, oy = meta["sceneOrigin"]
    k = math.cos(math.radians(lat))          # mercator -> metros reais
    dx, dy = (sx - ox) * k, (sy - oy) * k    # sitio no espaco do modelo

    print("=" * 74)
    print("MAPA 3D COMPRADO -- confere contra o que a cena ja tem")
    print("=" * 74)
    print(f"  cobertura   : {meta['modelDimensionsInMeters']['width']:.0f} x "
          f"{meta['modelDimensionsInMeters']['length']:.0f} m")
    print(f"  elevacao    : {meta['modelDimensionsInMeters']['width']/meta['elevationCanvas']['width']:.1f} m por amostra"
          "   (o projeto ja tem SRTM de 30 m ate 12 km)")
    print(f"  textura     : zoom {meta['resolution']['texture']['zoom']} -> "
          f"{156543.03*k/2**meta['resolution']['texture']['zoom']:.2f} m/px")
    print(f"  sitio no modelo: x={dx:+.1f}  z={-dy:+.1f} m\n")

    grupos = ler_obj(OBJ, set(LADOS_VIA))
    if not grupos:
        raise SystemExit("nenhuma via encontrada no OBJ")

    # modelo (x, z) -> local com norte VERDADEIRO (E, N) -> mundo da cena
    c, s = math.cos(math.radians(NORTE_DO_MAPA)), math.sin(math.radians(NORTE_DO_MAPA))
    pontos = {}
    for mat, P in grupos.items():
        E = P[:, 0] - dx
        N = -(P[:, 2] + dy)
        pontos[mat] = np.stack([E * c - N * s, N * c + E * s], axis=1)
        print(f"  {mat:26s} {len(P):6d} vertices")

    # --- folha de prova
    ESC, R = 1.6, 420.0                       # px por metro, raio da folha
    lado = int(2 * R * ESC)
    img = np.full((lado, lado, 3), 22, np.uint8)

    def px(p):
        return (int(lado / 2 + p[0] * ESC), int(lado / 2 - p[1] * ESC))

    for r in (45, 62, 78, 95, 125, 150):      # aneis da bacia, so de referencia
        cv2.circle(img, px((cxa, cya)), int(r * ESC), (55, 55, 55), 1)

    n_osm = 0
    for mat, P in pontos.items():
        for p in P:
            if abs(p[0]) < R and abs(p[1]) < R:
                cv2.circle(img, px(p), 2, (70, 200, 255), -1)
                n_osm += 1

    reais = [v for v in vias["vias"] if v["e_via"]]
    cores = {"estrada": (90, 255, 90), "curva_de_nivel": (90, 90, 255),
             "indeterminado": (150, 150, 150)}
    for v in reais:
        cor = cores.get(v.get("classe_geometrica"), (200, 200, 200))
        pts = np.array([px(p) for p in v["pontos_m"]], np.int32)
        cv2.polylines(img, [pts], False, cor, 2)

    cv2.circle(img, px((cxa, cya)), 6, (255, 0, 255), -1)
    for i, (txt, cor) in enumerate([
            ("amarelo = vias do OSM (mapa comprado)", (70, 200, 255)),
            ("verde   = classificadas ESTRADA pela planta", (90, 255, 90)),
            ("azul    = classificadas CURVA DE NIVEL", (90, 90, 255)),
            ("magenta = centro da arena", (255, 0, 255))]):
        cv2.putText(img, txt, (16, 28 + i * 26), cv2.FONT_HERSHEY_SIMPLEX,
                    0.6, cor, 1, cv2.LINE_AA)

    saida = RAIZ / "out" / "mapa-comprado" / "vias-osm-x-planta.png"
    saida.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(saida), img)
    print(f"\n  {n_osm} vertices de via do OSM dentro de {R:.0f} m do centro")
    print(f"  folha: {saida.relative_to(RAIZ)}")
    print("\n  Se o amarelo cair em cima do verde, a suposicao de origem vale e o")
    print("  OSM serve de segunda fonte para a pendencia 9. Se cair deslocado,")
    print("  o mapa nao confere nada sem uma ancora de verdade.")
    print("=" * 74)


if __name__ == "__main__":
    main()
