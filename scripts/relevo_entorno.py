#!/usr/bin/env python3
"""Relevo real do entorno de Dois Vizinhos, para o horizonte deixar de ser reta.

O problema, registrado como pendencia 11: o entorno e um disco CHAPADO e o
horizonte sai numa linha de regua. Com o sol a 10 graus e a camera baixa isso
le como CG na hora, por melhor que esteja a luz -- e ha prova em imagem do
contrario no proprio footage (`DJI_20251129182345_0168_D` 00:00:52 mostra o
morro atras do recinto e a lavoura subindo em socalco).

**Fonte: AWS Terrain Tiles**, dominio publico, sem chave e sem cadastro --
`s3.amazonaws.com/elevation-tiles-prod/terrarium`. Sobre o Brasil o dado e
SRTM. Foi escolhida contra as outras duas justamente por nao pedir conta:
OpenTopography exige cadastro e chave de API, e criar conta nao e coisa que se
faz sozinho; o TOPODATA/INPE e otimo e livre, mas entrega zip por folha de 1
grau, o que e bem mais peso para o mesmo resultado a 30 m.

**O que este dado NAO serve para fazer, e ja esta medido:** os patamares do
recinto. 30 m de resolucao dao 27 pixels no recinto inteiro e os taludes somem
(ver ESTADO.md, "DEM global nao serve para o recinto"). A bacia continua vindo
da planta. Aqui e SO o que esta longe.

Terrarium codifica a altura no pixel: `h = (R*256 + G + B/256) - 32768`, em
metros. E um formato de 24 bits -- nao e escala de cinza, e ler como cinza
devolve serra dentada.

Uso:
    python scripts/relevo_entorno.py                  # 24 km de lado, z12
    python scripts/relevo_entorno.py --raio 8000 --zoom 13
"""

import argparse
import json
import math
import sys
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SAIDA_GRID = RAIZ / "assets" / "relevo" / "entorno_alturas.npy"
SAIDA_META = RAIZ / "data" / "relevo-entorno.json"

# Local: R. Jorge Amado, Jardim Marcante, Dois Vizinhos - PR (ESTADO.md)
LAT, LON = -25.73144, -53.07627

BASE = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium"
CABECALHO = {"User-Agent": "render-expovizinhos/1.0 (contato via github)"}


def _tile(lat, lon, z):
    """lat/lon -> indice de tile do slippy map (float, para saber o subpixel)."""
    n = 2.0 ** z
    x = (lon + 180.0) / 360.0 * n
    rad = math.radians(lat)
    y = (1.0 - math.asinh(math.tan(rad)) / math.pi) / 2.0 * n
    return x, y


def _metros_por_pixel(lat, z):
    """Web Mercator: o pixel encolhe com o cosseno da latitude."""
    return 40075016.686 / (256 * 2.0 ** z) * math.cos(math.radians(lat))


def baixar(raio_m, zoom):
    import numpy as np
    from PIL import Image
    import io

    mpp = _metros_por_pixel(LAT, zoom)
    # quantos pixels de cada lado do centro
    meia = int(math.ceil(raio_m / mpp))
    cx, cy = _tile(LAT, LON, zoom)
    px_c, py_c = cx * 256.0, cy * 256.0

    x0, x1 = int(math.floor((px_c - meia) / 256)), int(math.floor((px_c + meia) / 256))
    y0, y1 = int(math.floor((py_c - meia) / 256)), int(math.floor((py_c + meia) / 256))
    n_tiles = (x1 - x0 + 1) * (y1 - y0 + 1)
    print(f"zoom {zoom}: {mpp:.1f} m/pixel, raio {raio_m} m -> {meia} px de cada lado")
    print(f"{n_tiles} tiles ({x1-x0+1} x {y1-y0+1})")

    mosaico = np.zeros(((y1 - y0 + 1) * 256, (x1 - x0 + 1) * 256), dtype=np.float32)
    for ty in range(y0, y1 + 1):
        for tx in range(x0, x1 + 1):
            url = f"{BASE}/{zoom}/{tx}/{ty}.png"
            req = urllib.request.Request(url, headers=CABECALHO)
            with urllib.request.urlopen(req, timeout=60) as r:
                bruto = r.read()
            rgb = np.asarray(Image.open(io.BytesIO(bruto)).convert("RGB"),
                             dtype=np.float32)
            # Terrarium: 24 bits em R,G,B -- NAO e escala de cinza
            h = rgb[..., 0] * 256.0 + rgb[..., 1] + rgb[..., 2] / 256.0 - 32768.0
            iy, ix = (ty - y0) * 256, (tx - x0) * 256
            mosaico[iy:iy + 256, ix:ix + 256] = h
        print(f"  linha {ty - y0 + 1}/{y1 - y0 + 1}")

    # recorta o quadrado centrado no sitio
    ox, oy = px_c - x0 * 256, py_c - y0 * 256
    i0, i1 = int(round(oy - meia)), int(round(oy + meia))
    j0, j1 = int(round(ox - meia)), int(round(ox + meia))
    recorte = mosaico[i0:i1 + 1, j0:j1 + 1]
    return recorte, mpp


def preparar(raio_m, zoom):
    import numpy as np

    bruto, mpp = baixar(raio_m, zoom)
    n = bruto.shape[0]
    meio = n // 2
    z_sitio = float(bruto[meio, meio])

    # A cena tem o platao do recinto em z = 10 m (PATAMARES). O DEM vem em
    # altitude absoluta, entao o que interessa e o DESNIVEL em relacao ao
    # sitio -- somado a 10 devolve tudo no referencial da cena.
    rel = bruto - z_sitio

    # O recinto tem geometria propria e MEDIDA: o relevo de 30 m nao pode
    # levantar nem afundar nada la dentro. A prancha vai a ~485 x 273 m do
    # centro; o amortecimento comeca em 600 m (zero) e chega inteiro em 1500 m.
    ys, xs = np.mgrid[0:n, 0:n]
    dist = np.hypot(xs - meio, ys - meio) * mpp
    peso = np.clip((dist - 600.0) / 900.0, 0.0, 1.0)
    # suaviza a borda do amortecimento: rampa reta deixa um anel visivel
    peso = peso * peso * (3.0 - 2.0 * peso)
    rel = rel * peso

    SAIDA_GRID.parent.mkdir(parents=True, exist_ok=True)
    np.save(SAIDA_GRID, rel.astype(np.float32))

    meta = {
        "o_que_e": "Desnivel do entorno em relacao ao sitio, em metros, ja "
                   "amortecido para nao tocar no recinto. Some 10 m (o platao) "
                   "para ter a cota na cena.",
        "fonte": "AWS Terrain Tiles (terrarium), dominio publico; sobre o "
                 "Brasil o dado e SRTM",
        "url": f"{BASE}/{{z}}/{{x}}/{{y}}.png",
        "licenca": "dominio publico (SRTM) — sem chave, sem cadastro",
        "nao_serve_para": "os patamares do recinto. 30 m de resolucao dao ~27 "
                          "pixels no recinto inteiro e os taludes somem. A "
                          "bacia continua vindo da planta.",
        "centro": {"lat": LAT, "lon": LON},
        "altitude_do_sitio_m": round(z_sitio, 1),
        "zoom": zoom,
        "metros_por_pixel": round(mpp, 2),
        "lado_px": int(n),
        "lado_m": round(n * mpp, 1),
        "amortecimento": {"comeca_m": 600.0, "inteiro_m": 1500.0,
                          "por_que": "o recinto tem geometria medida e o DEM "
                                     "de 30 m nao pode mexer nela"},
        "desnivel_m": {
            "min": round(float(rel.min()), 1),
            "max": round(float(rel.max()), 1),
            "p05": round(float(np.percentile(rel, 5)), 1),
            "p95": round(float(np.percentile(rel, 95)), 1),
        },
        "grid": str(SAIDA_GRID.relative_to(RAIZ)).replace("\\", "/"),
    }
    SAIDA_META.write_text(json.dumps(meta, indent=1, ensure_ascii=False),
                          encoding="utf-8")

    print(f"\naltitude do sitio: {z_sitio:.0f} m")
    print(f"desnivel do entorno: {rel.min():+.0f} a {rel.max():+.0f} m "
          f"(p05 {np.percentile(rel,5):+.0f}, p95 {np.percentile(rel,95):+.0f})")
    print(f"lado: {n * mpp / 1000:.1f} km em {n} px")
    print(f"gravado: {SAIDA_GRID.relative_to(RAIZ)}")
    print(f"         {SAIDA_META.relative_to(RAIZ)}")
    return meta


# --------------------------------------------------------------------------
# Leitura (roda dentro do Blender tambem: so numpy)

def carregar():
    """Devolve (grid, metros_por_pixel, lado_m) ou None se nao foi baixado."""
    if not (SAIDA_GRID.exists() and SAIDA_META.exists()):
        return None
    import numpy as np
    meta = json.loads(SAIDA_META.read_text(encoding="utf-8"))
    return np.load(SAIDA_GRID), meta["metros_por_pixel"], meta["lado_m"]


def altura(grid, mpp, x, y):
    """Desnivel em (x, y) metros do centro da arena, por interpolacao bilinear.

    Vizinho mais proximo deixaria degrau de 34 m visivel na silhueta do morro,
    que e exatamente o que se quer consertar.
    """
    n = grid.shape[0]
    meio = (n - 1) / 2.0
    fx, fy = meio + x / mpp, meio + y / mpp
    if not (0 <= fx <= n - 1 and 0 <= fy <= n - 1):
        return 0.0
    j0, i0 = int(fx), int(fy)
    j1, i1 = min(j0 + 1, n - 1), min(i0 + 1, n - 1)
    tx, ty = fx - j0, fy - i0
    return float(
        grid[i0, j0] * (1 - tx) * (1 - ty) + grid[i0, j1] * tx * (1 - ty)
        + grid[i1, j0] * (1 - tx) * ty + grid[i1, j1] * tx * ty)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raio", type=float, default=12000.0,
                    help="metros do centro ate a borda (padrao 12000: a 48 m "
                         "de camera o horizonte real esta a ~25 km)")
    ap.add_argument("--zoom", type=int, default=12,
                    help="zoom do tile. 12 da ~34 m/px, que e a propria "
                         "resolucao do SRTM: pedir mais so interpola")
    args = ap.parse_args()
    preparar(args.raio, args.zoom)
    return 0


if __name__ == "__main__":
    sys.exit(main())
