#!/usr/bin/env python3
"""Poe as posicoes da CENA por cima do MAPA OFICIAL do AGROSHOW.

Pedido do Natan em 15/08, olhando a cena aberta no Blender: *"as posicoes nao
estao corretas, tem coisa torta -- compara com o mapa do agroshow para
reposicionar. Antes de fazer quero ver a imagem sobreposta para conferir."*

Isto é a CONFERÊNCIA, não o conserto. Não move nada: mede e desenha.

Diferença para o `sobrepor.py`, que já existia: aquele compara a cena com o
SATÉLITE do Google e ancora na arena. Este compara com a PLANTA do evento, que
é a fonte de onde as posições saíram — então qualquer desvio aqui é erro de
transporte planta -> cena, não erro de georreferenciamento.

Método: a conversão planta -> mundo em `terreno.para_mundo()` é linear e
invertível, então a posição de cada objeto volta para o ponto do PDF e cai como
pixel em cima do bitmap rasterizado. Azul = onde o mapa diz; vermelho = onde o
objeto está; a linha entre os dois é o desvio.

A cena é lida AO VIVO pelo socket do blender-mcp (porta 9876), com o Blender
aberto. Com `--blend` lê do arquivo, sem depender do addon.

Uso:
    .venv/Scripts/python.exe scripts/sobrepor_planta.py
    .venv/Scripts/python.exe scripts/sobrepor_planta.py --zoom 3
"""

import argparse
import json
import socket
import sys
import unicodedata
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import terreno

RAIZ = Path(__file__).resolve().parent.parent
PDF = RAIZ / "reference" / "Mapa_AGROSHOW26.pdf"

# cores BGR
AZUL = (255, 140, 0)      # onde a PLANTA diz
VERMELHO = (40, 40, 235)  # onde o OBJETO está
LINHA = (0, 215, 255)     # o desvio


def normalizar(s):
    """Casa rótulo da planta com nome de objeto: sem acento, sem caixa, sem
    sufixo `.001` do Blender, sem os prefixos que o gerador acrescenta."""
    s = s.split(".")[0]
    for pre in ("Letreiro_", "Apoio_", "Etiqueta_", "Zona_", "Estimado_"):
        if s.startswith(pre):
            s = s[len(pre):]
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(s.upper().replace("-", " ").split())


# ---------------------------------------------------------------- cena viva

def _socket(tipo, params=None, timeout=180.0):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    s.connect(("localhost", 9876))
    s.sendall(json.dumps({"type": tipo, "params": params or {}}).encode("utf-8"))
    pedacos = []
    while True:
        d = s.recv(65536)
        if not d:
            break
        pedacos.append(d)
        try:
            return json.loads(b"".join(pedacos).decode("utf-8"))
        except json.JSONDecodeError:
            continue
    raise RuntimeError("resposta incompleta do addon")


CODIGO_CENA = r"""
import bpy, json
saida = []
for c in bpy.data.collections:
    for o in c.objects:
        saida.append({"n": o.name, "c": c.name,
                      "x": round(o.location.x, 3), "y": round(o.location.y, 3),
                      "z": round(o.location.z, 3), "t": o.type})
print("CENA_JSON:" + json.dumps(saida, ensure_ascii=False))
"""


def ler_cena_viva():
    r = _socket("execute_code", {"code": CODIGO_CENA})
    txt = r.get("result", {}).get("result", "")
    if "CENA_JSON:" not in txt:
        raise RuntimeError(f"addon nao devolveu a cena: {str(r)[:300]}")
    return json.loads(txt.split("CENA_JSON:", 1)[1].strip().splitlines()[0])


def ler_cena_do_blend(caminho):
    """Sem Blender aberto: usa o proprio blender em background."""
    import subprocess
    import tempfile
    bl = r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
    tmp = Path(tempfile.gettempdir()) / "cena_posicoes.json"
    codigo = (
        "import bpy, json\n"
        "s=[]\n"
        "for c in bpy.data.collections:\n"
        "    for o in c.objects:\n"
        "        s.append({'n':o.name,'c':c.name,'x':round(o.location.x,3),"
        "'y':round(o.location.y,3),'z':round(o.location.z,3),'t':o.type})\n"
        f"open(r'{tmp}','w',encoding='utf-8').write(json.dumps(s,ensure_ascii=False))\n"
    )
    ps = Path(tempfile.gettempdir()) / "_ler_cena.py"
    ps.write_text(codigo, encoding="utf-8")
    subprocess.run([bl, str(caminho), "--background", "--python", str(ps)],
                   capture_output=True, check=False)
    return json.loads(tmp.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- desenho

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zoom", type=float, default=2.5,
                    help="rasterizacao do PDF; 2.5 da 3600x2025")
    ap.add_argument("--blend", default=None,
                    help="ler do .blend em vez do Blender aberto")
    ap.add_argument("--saida", default="out/conferencia/sobreposto-planta.png")
    args = ap.parse_args()

    import pymupdf

    dados = terreno.carregar_mapa(RAIZ / terreno.MAPA_PADRAO)
    origem = dados["_origem"]

    doc = pymupdf.open(PDF)
    pag = doc[0]
    pix = pag.get_pixmap(matrix=pymupdf.Matrix(args.zoom, args.zoom))
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR if pix.n == 3 else cv2.COLOR_RGBA2BGR)

    # pt do PDF -> pixel do raster
    kx = pix.w / dados["prancha"]["largura_pt"]
    ky = pix.h / dados["prancha"]["altura_pt"]

    def mundo_para_px(mx, my):
        x_pt = mx / terreno.ESCALA + origem[0]
        y_pt = -my / terreno.ESCALA + origem[1]
        return int(round(x_pt * kx)), int(round(y_pt * ky))

    objetos = (ler_cena_do_blend(args.blend) if args.blend else ler_cena_viva())
    print(f"objetos lidos da cena: {len(objetos)}")

    # rotulos da planta, por nome normalizado
    planta = {}
    for z in dados["zonas"]:
        planta.setdefault(normalizar(z["rotulo"]), []).append((z["x"], z["y"]))

    # so compara objeto que tem rotulo correspondente na planta
    pares, sem_par = [], []
    vistos = set()
    for o in objetos:
        chave = normalizar(o["n"])
        if chave in vistos:
            continue
        if chave in planta:
            vistos.add(chave)
            x_pt, y_pt = planta[chave][0]
            alvo = terreno.para_mundo(x_pt, y_pt, origem)
            pares.append((o, alvo, chave))
        elif o["c"] in ("BASE", "ESTIMADO") and o["t"] == "MESH":
            sem_par.append(o)

    tela = img.copy()
    desvios = []
    for o, alvo, chave in pares:
        px_obj = mundo_para_px(o["x"], o["y"])
        px_map = mundo_para_px(alvo[0], alvo[1])
        d = float(np.hypot(o["x"] - alvo[0], o["y"] - alvo[1]))
        desvios.append((d, chave, o["c"]))

        cv2.line(tela, px_map, px_obj, LINHA, 2, cv2.LINE_AA)
        cv2.circle(tela, px_map, 9, AZUL, 2, cv2.LINE_AA)
        cv2.drawMarker(tela, px_obj, VERMELHO, cv2.MARKER_CROSS, 20, 3)
        cv2.putText(tela, f"{chave[:26]} {d:.0f}m", (px_obj[0] + 12, px_obj[1] - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 4, cv2.LINE_AA)
        cv2.putText(tela, f"{chave[:26]} {d:.0f}m", (px_obj[0] + 12, px_obj[1] - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, VERMELHO, 1, cv2.LINE_AA)

    # legenda
    cv2.rectangle(tela, (20, 20), (720, 150), (255, 255, 255), -1)
    cv2.rectangle(tela, (20, 20), (720, 150), (0, 0, 0), 2)
    cv2.circle(tela, (48, 58), 9, AZUL, 2)
    cv2.putText(tela, "onde a PLANTA diz", (70, 64), cv2.FONT_HERSHEY_SIMPLEX,
                0.65, (0, 0, 0), 2, cv2.LINE_AA)
    cv2.drawMarker(tela, (48, 96), VERMELHO, cv2.MARKER_CROSS, 20, 3)
    cv2.putText(tela, "onde o OBJETO esta na cena", (70, 102),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 0), 2, cv2.LINE_AA)
    cv2.putText(tela, f"{len(pares)} objetos casados por rotulo", (70, 136),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (90, 90, 90), 1, cv2.LINE_AA)

    saida = RAIZ / args.saida
    saida.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(saida), tela)

    desvios.sort(reverse=True)
    print(f"\nraster: {pix.w}x{pix.h} px   escala: {terreno.ESCALA} m/pt")
    print(f"casados por rotulo: {len(pares)}   sem par na planta: {len(sem_par)}")
    if desvios:
        ds = [d for d, _, _ in desvios]
        print(f"desvio  mediana {np.median(ds):.1f} m   maximo {max(ds):.1f} m"
              f"   acima de 10 m: {sum(1 for d in ds if d > 10)}")
        print("\nos 15 maiores desvios:")
        for d, nome, col in desvios[:15]:
            print(f"  {d:8.1f} m  {nome[:40]:<40} [{col}]")
    print(f"\ngravado: {saida}")


if __name__ == "__main__":
    main()
