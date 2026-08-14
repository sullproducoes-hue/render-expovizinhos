#!/usr/bin/env python3
"""Acha o disco solar dentro de um HDRI, por pixel.

Roda **dentro do Blender** -- ele le .hdr nativo e traz numpy junto. O venv tem
cv2, mas o Blender nao ve o venv, e o caminho curto e usar o proprio.

Por que medir em vez de ler o metadado: o `date_taken` da API do Poly Haven vem
do EXIF e o fuso e ambiguo. O pixel nao mente.

O que sai daqui alimenta a rotacao do ceu:

    rotacao_do_ceu = azimute_alvo (sol.py, NOAA) - azimute_medido (aqui)

Uso:
    blender --background --python scripts/medir_hdri.py -- assets/hdri/*.hdr
"""

import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np

RAIZ = Path(__file__).resolve().parent.parent


def _direcao_do_pixel(u, v):
    """Inversa exata do `direction_to_equirectangular` do Cycles.

    u,v em [0,1), com v=0 na BASE da imagem -- que e como `pixels.foreach_get`
    entrega, entao nao se inverte nada aqui.

    Devolve (elevacao_graus, azimute_graus) no compasso do projeto:
    0 = norte (+Y), 90 = leste (+X), horario.
    """
    phi = (u - 0.5) * 2.0 * math.pi
    theta = (v - 0.5) * math.pi
    # Cycles: u = -atan2(y, x)/(2pi) + 0.5  ->  atan2(y, x) = -phi
    r = math.cos(theta)
    x = r * math.cos(phi)
    y = -r * math.sin(phi)
    return math.degrees(theta), math.degrees(math.atan2(x, y)) % 360.0


def _borrar(a, k=3):
    """Media movel separavel. Evita cair num pixel quente solto (hot pixel de
    sensor ou estrela), que e o modo classico de errar o sol por 40 graus."""
    pad = k // 2
    b = np.pad(a, pad, mode="edge")
    saida = np.zeros_like(a)
    for i in range(k):
        for j in range(k):
            saida += b[i:i + a.shape[0], j:j + a.shape[1]]
    return saida / (k * k)


def medir(caminho):
    img = bpy.data.images.load(str(caminho), check_existing=False)
    w, h = img.size
    buf = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(buf)
    px = buf.reshape(h, w, 4)[:, :, :3]

    lum = px @ np.float32([0.2126, 0.7152, 0.0722])
    suave = _borrar(lum, 3)

    py, pxx = divmod(int(np.argmax(suave)), w)
    u = (pxx + 0.5) / w
    v = (py + 0.5) / h
    elev, azim = _direcao_do_pixel(u, v)

    # Cor e potencia do disco: tudo acima de metade do pico, na vizinhanca.
    pico = float(suave[py, pxx])
    raio = max(4, w // 200)
    y0, y1 = max(0, py - raio), min(h, py + raio + 1)
    x0, x1 = max(0, pxx - raio), min(w, pxx + raio + 1)
    janela = px[y0:y1, x0:x1]
    lj = suave[y0:y1, x0:x1]
    disco = janela[lj > pico * 0.5]
    cor = disco.mean(axis=0) if len(disco) else px[py, pxx]
    cor = (cor / max(float(cor.max()), 1e-6)).tolist()   # normaliza em R=1

    # Irradiancia implicita do disco: soma de L * angulo solido. E o ponto de
    # partida honesto para a energia da SUN, em vez de um "3.0" sem procedencia.
    theta = (np.arange(h) + 0.5) / h * math.pi - math.pi / 2.0
    d_omega = (2.0 * math.pi / w) * (math.pi / h) * np.cos(theta)
    mascara = suave > pico * 0.5
    irrad = float((lum * mascara * d_omega[:, None]).sum())

    # Media do ceu inteiro, para saber quanto do total vem do disco
    total = float((lum * d_omega[:, None]).sum())

    bpy.data.images.remove(img)
    return {
        "arquivo": str(Path(caminho).relative_to(RAIZ)).replace("\\", "/"),
        "resolucao": [w, h],
        "pixel_do_sol": [int(pxx), int(py)],
        "elevacao_deg": round(elev, 2),
        "azimute_deg": round(azim, 2),
        "cor_do_disco": [round(c, 4) for c in cor],
        "luminancia_pico": round(pico, 1),
        "irradiancia_do_disco": round(irrad, 3),
        "irradiancia_total": round(total, 3),
        "fracao_do_disco": round(irrad / total, 4) if total else None,
        "medido_por": "scripts/medir_hdri.py",
    }


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    alvos = [Path(a) for a in argv]
    if not alvos:
        alvos = sorted((RAIZ / "assets" / "hdri").glob("*.hdr"))
    if not alvos:
        raise SystemExit("nenhum .hdr -- rode scripts/assets.py --hdri <slug>")

    saida = []
    for caminho in alvos:
        d = medir(caminho)
        saida.append(d)
        print(f"\n{caminho.name}")
        print(f"  {d['resolucao'][0]}x{d['resolucao'][1]}  "
              f"pixel do sol {d['pixel_do_sol']}")
        print(f"  elevacao {d['elevacao_deg']:6.2f} graus   "
              f"azimute {d['azimute_deg']:6.2f} graus")
        print(f"  cor do disco {[round(c, 3) for c in d['cor_do_disco']]}")
        print(f"  disco = {d['fracao_do_disco'] * 100:.1f}% da irradiancia do ceu")
        # A prova honesta: golden hour tem que dar poucos graus de elevacao.
        if d["elevacao_deg"] > 25.0:
            print(f"  ATENCAO: {d['elevacao_deg']:.1f} graus nao e golden hour. "
                  f"Ou o HDRI nao e de fim de tarde, ou o metodo esta errado.")

    alvo = RAIZ / "data" / "hdri-medido.json"
    alvo.parent.mkdir(parents=True, exist_ok=True)
    alvo.write_text(json.dumps({"itens": saida}, indent=1, ensure_ascii=False),
                    encoding="utf-8")
    print(f"\ngravado: {alvo}")


if __name__ == "__main__":
    main()
