#!/usr/bin/env python3
"""
Fecha, por MEDIDA, a duvida de procedencia do acervo: os voos `DJI_2025112*`
sao do Parque de Exposicoes de Dois Vizinhos ou de outro recinto?

A duvida esta registrada em DECISOES.md D055. Ela nasceu de duas sessoes do
mesmo dia que se contradiziam: a setima usava 12 desses voos como ancora
confirmada, e a nona escreveu em docs/COMO-O-PARQUE-ESCREVE.md que eles
mostram "outro recinto -- autodromo oval, silos de grao". Eram 71 pastas e
2.770 quadros, cobrindo dez dos vinte e dois planos.

A prova nao precisava de olho: **o drone gravou GPS**. A DJI escreve latitude e
longitude amostra a amostra num stream de dados (`djmd`) dentro do proprio MP4,
e o exiftool -ee le. `_triagem/telemetria/*.resumo.json` ja tinha a mediana de
cada voo desde 14/08 -- ninguem tinha cruzado com a coordenada do recinto.

Este script faz o cruzamento e imprime a distancia de cada voo ate
-25,73144 / -53,07627. O recinto tem 808 x 454 m: qualquer coisa dentro de
~450 m do ponto de referencia esta no terreno.

    python scripts/provar_recinto.py
    python scripts/provar_recinto.py --escrever   # grava data/recinto-gps.json
"""

import argparse
import json
import math
import re
import subprocess
from pathlib import Path

# Local do recinto (ESTADO.md): R. Jorge Amado, Jardim Marcante,
# Dois Vizinhos - PR. E' um ponto DENTRO do terreno, nao o centro geometrico.
REFERENCIA = (-25.73144, -53.07627)

# Meia-diagonal do terreno de 808 x 454 m, com folga. Alem disto o voo nao esta
# mais sobre o recinto.
RAIO_DO_RECINTO_M = 470.0

TELEMETRIA = Path(r"E:\Projetos todos\Mapa - agroshow\Brutos Expo\_triagem\telemetria")
BRUTOS = Path(r"E:\Projetos todos\Mapa - agroshow\Brutos Expo")


def metros(lat, lon):
    """Distancia ate a referencia, em metros. Equirretangular basta: a 400 m o
    erro contra a formula de haversine e' de centimetros."""
    dlat = (lat - REFERENCIA[0]) * 111320.0
    dlon = (lon - REFERENCIA[1]) * 111320.0 * math.cos(math.radians(REFERENCIA[0]))
    return math.hypot(dlat, dlon)


def do_resumo():
    """GPS ja extraido em 14/08, um resumo por voo."""
    achados = {}
    for f in sorted(TELEMETRIA.glob("*.resumo.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        g = d.get("gps") or {}
        if g.get("lat", {}).get("mediana") is None:
            continue
        # O -001/-002 no fim e' sufixo de arquivo partido, nao outro voo:
        # indexar pelos dois nomes, senao a pasta DJI_..._0165_D-001 procura
        # por DJI_..._0165_D e nao acha o proprio resumo dela.
        base = f.name.replace(".resumo.json", "")
        lat, lon = g["lat"]["mediana"], g["lon"]["mediana"]
        reg = {"lat": lat, "lon": lon, "m": round(metros(lat, lon), 1),
               "de": "telemetria/*.resumo.json (14/08)"}
        achados[base] = reg
        achados.setdefault(re.sub(r"-\d{3}$", "", base), reg)
    return achados


def do_exiftool(nome):
    """Ultimo recurso: le o GPS direto do MP4. Serve para os voos que ficaram
    de fora da extracao de 14/08 -- o 0103 era um deles."""
    caminho = BRUTOS / nome
    if not caminho.exists():
        return None
    try:
        saida = subprocess.run(
            ["exiftool", "-ee", "-n", "-q", "-p", "$GPSLatitude,$GPSLongitude",
             str(caminho)],
            capture_output=True, text=True, timeout=180).stdout
    except Exception:
        return None
    pares = [l.split(",") for l in saida.splitlines() if l.count(",") == 1]
    pares = [(float(a), float(b)) for a, b in pares
             if re.match(r"^-?\d+\.\d+$", a) and re.match(r"^-?\d+\.\d+$", b)]
    if not pares:
        return None
    meio = pares[len(pares) // 2]
    return {"lat": meio[0], "lon": meio[1], "m": round(metros(*meio), 1),
            "de": "exiftool -ee no MP4 original"}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--catalogo", default="data/acervo-quadros.json")
    ap.add_argument("--escrever", action="store_true")
    ap.add_argument("--saida", default="data/recinto-gps.json")
    args = ap.parse_args()

    gps = do_resumo()
    cat = json.loads(Path(args.catalogo).read_text(encoding="utf-8"))
    duvidosas = [p for p in cat["pastas"] if p["pasta"].startswith("DJI_2025112")]

    linhas, sem = [], []
    for p in duvidosas:
        m = re.match(r"(DJI_\d{14}_\d{4}_D)", p["pasta"])
        base = m.group(1) if m else None
        achado = gps.get(p["pasta"]) or gps.get(base)
        if achado is None and base:
            achado = do_exiftool(f"{base}.MP4")
            if achado:
                gps[base] = achado
        reg = {"pasta": p["pasta"], "voo_base": base, "quadros": p["n_quadros"]}
        if achado:
            reg.update(achado)
            reg["dentro_do_recinto"] = achado["m"] <= RAIO_DO_RECINTO_M
            linhas.append(reg)
        else:
            reg["de"] = ("sem metadado -- o arquivo e' export estabilizado e o "
                         "estabilizador nao copia o stream djmd; o MP4 original "
                         "nao esta mais no disco")
            sem.append(reg)

    print(f"{'pasta':52} {'quadros':>7} {'m do recinto':>13}  fonte")
    for r in sorted(linhas, key=lambda x: x["m"]):
        print(f"{r['pasta']:52} {r['quadros']:7} {r['m']:13.0f}  {r['de'][:34]}")
    for r in sem:
        print(f"{r['pasta']:52} {r['quadros']:7} {'SEM GPS':>13}")

    n_ok = sum(1 for r in linhas if r["dentro_do_recinto"])
    q_ok = sum(r["quadros"] for r in linhas if r["dentro_do_recinto"])
    q_sem = sum(r["quadros"] for r in sem)
    dists = [r["m"] for r in linhas]
    print("-" * 92)
    print(f"  pastas em duvida ............ {len(duvidosas)}")
    print(f"  com GPS, DENTRO do recinto .. {n_ok} pastas, {q_ok} quadros")
    print(f"  com GPS, FORA ............... {len(linhas) - n_ok} pastas")
    print(f"  sem GPS ..................... {len(sem)} pastas, {q_sem} quadros")
    if dists:
        print(f"  distancia ao ponto de referencia: min {min(dists):.0f} m, "
              f"max {max(dists):.0f} m (raio do recinto: {RAIO_DO_RECINTO_M:.0f} m)")

    doc = {
        "_o_que_isto_prova": (
            "Que os voos DJI_2025112* foram gravados no Parque de Exposicoes de "
            "Dois Vizinhos. Fecha a duvida aberta em DECISOES.md D055 e corrige "
            "o aviso de docs/COMO-O-PARQUE-ESCREVE.md."),
        "_como": (
            "GPS do proprio drone, amostra a amostra, no stream djmd do MP4. "
            "Nao e' inferencia visual: e' a coordenada que o aparelho gravou."),
        "referencia": {"lat": REFERENCIA[0], "lon": REFERENCIA[1],
                       "o_que_e": "R. Jorge Amado, Jardim Marcante, Dois Vizinhos - PR"},
        "raio_do_recinto_m": RAIO_DO_RECINTO_M,
        "resumo": {"pastas_em_duvida": len(duvidosas),
                   "com_gps_dentro": n_ok, "quadros_com_gps_dentro": q_ok,
                   "com_gps_fora": len(linhas) - n_ok,
                   "sem_gps": len(sem), "quadros_sem_gps": q_sem},
        "voos": sorted(linhas, key=lambda x: x["m"]) + sem,
    }
    if args.escrever:
        Path(args.saida).write_text(json.dumps(doc, ensure_ascii=False, indent=1),
                                    encoding="utf-8")
        print(f"  gravado em {args.saida}")


if __name__ == "__main__":
    main()
