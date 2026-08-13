#!/usr/bin/env python3
"""
Baixa o relevo real do entorno do Parque de Exposicoes e grava um recorte em
data/, para o gerador da cena rodar depois sem rede.

Fonte: terrain tiles da AWS (s3.amazonaws.com/elevation-tiles-prod), formato
terrarium, dominio publico. E o unico provedor de elevacao que o proxy do
ambiente remoto libera -- OpenTopography, opentopodata e open-elevation estao
bloqueados. O dado de origem e da familia SRTM/NASADEM, ~30 m; o tile de z15
entrega 4,3 m por pixel, mas isso e reamostragem, nao resolucao real.

O que este dado resolve e o que nao resolve:

  RESOLVE  a profundidade geral do terreno -- o recinto cai cerca de 2 m a cada
           100 m, e tem 44 m entre o ponto mais alto e o mais baixo. A cena
           tinha 10 m estimados, chapados.
  NAO RESOLVE os patamares da arena. Um talude de 3,5 m em 15 m de extensao
           nao existe num dado de 30 m. Os patamares continuam vindo da planta,
           e as alturas continuam estimadas ate o cliente mandar um quadro de
           drone.

Uso:
    python3 scripts/fetch_dem.py
    python3 scripts/fetch_dem.py --lado 3000 --zoom 15
"""

import argparse
import io
import json
import math
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image

# Coordenada do recinto, R. Jorge Amado, Jardim Marcante, Dois Vizinhos - PR.
LAT, LON = -25.73144, -53.07627
ZOOM = 15
LADO = 2400.0    # m -- lado do recorte quadrado, com folga sobre os 808 m
URL = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"


def tile_fracionario(lat, lon, z):
    n = 2 ** z
    x = (lon + 180.0) / 360.0 * n
    la = math.radians(lat)
    y = (1.0 - math.log(math.tan(la) + 1 / math.cos(la)) / math.pi) / 2.0 * n
    return x, y


def metros_por_pixel(lat, z):
    """Tile de 256 px na projecao Web Mercator, corrigido pela latitude."""
    return 156543.03392 * math.cos(math.radians(lat)) / (2 ** z)


def baixar_tile(z, x, y):
    with urllib.request.urlopen(URL.format(z=z, x=x, y=y), timeout=60) as r:
        img = Image.open(io.BytesIO(r.read())).convert("RGB")
    a = np.asarray(img).astype(np.float64)
    # Terrarium: altura = R*256 + G + B/256 - 32768, em metros.
    return a[:, :, 0] * 256 + a[:, :, 1] + a[:, :, 2] / 256 - 32768


def montar(lat, lon, z, lado):
    fx, fy = tile_fracionario(lat, lon, z)
    tx, ty = int(fx), int(fy)
    mpp = metros_por_pixel(lat, z)
    raio_tiles = int(math.ceil(lado / 2 / (mpp * 256))) + 1

    faixas = []
    for dy in range(-raio_tiles, raio_tiles + 1):
        linha = [baixar_tile(z, tx + dx, ty + dy)
                 for dx in range(-raio_tiles, raio_tiles + 1)]
        faixas.append(np.hstack(linha))
    mosaico = np.vstack(faixas)

    # Centro do ponto pedido dentro do mosaico, em pixels.
    cx = (raio_tiles + (fx - tx)) * 256
    cy = (raio_tiles + (fy - ty)) * 256
    meia = lado / 2 / mpp
    x0, y0 = int(round(cx - meia)), int(round(cy - meia))
    x1, y1 = int(round(cx + meia)), int(round(cy + meia))
    return mosaico[y0:y1, x0:x1], mpp


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--lat", type=float, default=LAT)
    ap.add_argument("--lon", type=float, default=LON)
    ap.add_argument("--zoom", type=int, default=ZOOM)
    ap.add_argument("--lado", type=float, default=LADO,
                    help="lado do recorte quadrado, em metros")
    ap.add_argument("-o", "--out", default="data")
    args = ap.parse_args()

    altura, mpp = montar(args.lat, args.lon, args.zoom, args.lado)
    destino = Path(args.out)
    destino.mkdir(parents=True, exist_ok=True)
    arquivo = destino / "dem_recinto.npz"

    np.savez_compressed(
        arquivo,
        altura=altura.astype(np.float32),
        meta=json.dumps({
            "fonte": "AWS terrain tiles (terrarium), dominio publico",
            "dado_de_origem": "familia SRTM/NASADEM, ~30 m; z15 e reamostragem",
            "lat": args.lat, "lon": args.lon, "zoom": args.zoom,
            "metros_por_pixel": mpp, "lado_m": args.lado,
            "norte": "linha 0 = norte; coluna 0 = oeste",
        }),
    )

    plano = altura - altura.mean()
    ys, xs = np.mgrid[0:altura.shape[0], 0:altura.shape[1]]
    A = np.c_[xs.ravel() * mpp, ys.ravel() * mpp, np.ones(altura.size)]
    coef, *_ = np.linalg.lstsq(A, altura.ravel(), rcond=None)

    print(f"escrito: {arquivo}")
    print(f"  recorte ............. {altura.shape[1]} x {altura.shape[0]} px "
          f"({args.lado:.0f} x {args.lado:.0f} m)")
    print(f"  resolucao ........... {mpp:.2f} m/px (origem ~30 m)")
    print(f"  altitude ............ {altura.min():.0f} a {altura.max():.0f} m")
    print(f"  desnivel ............ {altura.max() - altura.min():.0f} m")
    print(f"  caimento medio ...... {math.hypot(coef[0], coef[1]) * 100:.1f} m "
          f"a cada 100 m")
    print(f"  desvio do plano ..... {np.std(plano):.1f} m")


if __name__ == "__main__":
    main()
