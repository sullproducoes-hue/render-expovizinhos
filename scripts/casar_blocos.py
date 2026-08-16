#!/usr/bin/env python3
"""Casa cada bloco novo do Natan com a peca que a cena JA constroi.

Ordem dele em 15/08: *"pode substituir"* -- o bloco dele vence e o duplicado
sai. Mas ele tambem disse, sobre a lista de colados: *"nessa questao preciso ver
exatamente do que esta falando"*. Entao este script NAO decide sozinho: ele
propoe o par, classifica a confianca e desenha a prova.

Tres classes, e a diferenca entre elas importa:

  SUBSTITUI       o bloco dele e a mesma construcao que a cena ja faz. A peca
                  velha vai para DESCARTADO (`nada se apaga`).
  ABSORVE ZONA    varias tendas dele ocupam UMA zona estimada da planta
                  ("Expositores Externo"). A zona sai; as tendas ficam.
  CONVIVE         esta perto, mas nao e a mesma coisa. Tenda a 28 m do
                  PAVILHAO 1 nao substitui o pavilhao -- e' vizinha.

O criterio nao e' so distancia. Distancia sozinha aprovaria a tenda vizinha; o
que decide e' distancia PEQUENA junto com o texto da nota dele batendo com o
rotulo da planta.

Uso:
    .venv/Scripts/python.exe scripts/casar_blocos.py
    .venv/Scripts/python.exe scripts/casar_blocos.py --imagens
"""

import argparse
import json
import math
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import terreno

RAIZ = Path(__file__).resolve().parent.parent
AJUSTES = RAIZ / "data" / "ajustes-manuais.json"
SAIDA = RAIZ / "data" / "casamento-blocos.json"

# Zona que e' ROTULO SOBRE CHAO e que as pecas dele DETALHAM: a zona estimada
# sai e as tendas dele ficam no lugar dela.
ZONAS_ABSORVIVEIS = {"EXPOSITORES EXTERNO", "ESTACIONAMENTO"}

# Isto nao case com nada, nunca. Talude e' RELEVO (terreno.PATAMARES), poste e'
# poste, trilha e' via, bosque e' vegetacao. A primeira versao deste script
# "absorvia" 6 blocos dele para dentro de Talude e Poste -- o que apagaria
# relevo medido para pos uma tenda no lugar.
NAO_CASAM = {
    "TALUDE", "POSTE", "SUPERPOSTE", "TRILHA", "BOSQUE", "MATA NATIVA",
    "AREA RESTRITA", "ESPACO P/ MESAS", "ESPACO P MESAS",
}

# Rotulos que a cena constroi mas que NAO sao edificacao -- a arena e' a bacia
# do terreno (ver terreno.PATAMARES). Substituir por um bloco seria criar um
# caixao em cima do relevo.
NAO_SAO_EDIFICACAO = {"ARENA DE RODEIO"}


def normalizar(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(s.upper().replace("-", " ").replace(".", " ").split())


PARADAS = {"DE", "DO", "DA", "DOS", "DAS", "E", "A", "O", "AS", "OS", "EM",
           "COM", "PARA", "UM", "UMA", "NO", "NA", "QUE", "TEM", "ONDE"}


def palavras(s):
    return {p for p in normalizar(s).split() if len(p) > 2 and p not in PARADAS}


def parecenca(nota, rotulo):
    """Quanto o texto da nota dele cobre o rotulo da planta, de 0 a 1."""
    a, b = palavras(nota), palavras(rotulo)
    if not a or not b:
        return 0.0
    return len(a & b) / len(b)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--imagens", action="store_true",
                    help="desenha a prova de cada par sobre a planta")
    args = ap.parse_args()

    doc = json.loads(AJUSTES.read_text(encoding="utf-8-sig"))
    novos = doc.get("blocos_novos", [])

    dados = terreno.carregar_mapa(RAIZ / terreno.MAPA_PADRAO)
    origem = dados["_origem"]
    existentes = []
    for z in dados["zonas"]:
        mx, my = terreno.para_mundo(z["x"], z["y"], origem)
        existentes.append({"rotulo": z["rotulo"], "x": mx, "y": my})

    casos = []
    for b in novos:
        nota = b.get("nota_do_natan") or ""
        bx, by = b["x_m"], b["y_m"]
        cands = []
        for e in existentes:
            if normalizar(e["rotulo"]) in NAO_CASAM:
                continue
            d = math.hypot(bx - e["x"], by - e["y"])
            if d > 32:
                continue
            cands.append((d, parecenca(nota, e["rotulo"]), e["rotulo"]))
        if not cands:
            casos.append({"bloco": b["nome"], "classe": "NOVO", "par": None,
                          "dist": None, "nota": nota})
            continue

        # A escolha do par, em ordem -- texto sozinho nao basta e distancia
        # sozinha tambem nao. "Saguao Aberto, para praca de alimentacao" casava
        # com `Praca de Alimentacao` a 11 m enquanto o `SAGUAO ABERTO` colado a
        # 3 m ficava de fora, so' porque a nota citava a praca.
        colados = [c for c in cands if c[0] <= 6.0]
        if colados:                       # colado manda; texto so' desempata
            colados.sort(key=lambda t: (-t[1], t[0]))
            d, sim, rot = colados[0]
        else:
            cands.sort(key=lambda t: (-t[1], t[0]))
            d, sim, rot = cands[0]
        rot_n = normalizar(rot)

        if rot_n in NAO_SAO_EDIFICACAO:
            classe = "NAO E EDIFICACAO"
        elif rot_n in ZONAS_ABSORVIVEIS:
            classe = "ABSORVE ZONA" if (sim >= 0.4 or d <= 20) else "CONVIVE"
        elif sim >= 0.5 and d <= 12:
            classe = "SUBSTITUI"
        elif d <= 4 and sim > 0:
            classe = "SUBSTITUI"
        elif d <= 4:
            classe = "SUBSTITUI?"      # colado, mas o texto nao confirma
        else:
            classe = "CONVIVE"

        casos.append({"bloco": b["nome"], "classe": classe, "par": rot,
                      "dist": round(d, 1), "sim": round(sim, 2), "nota": nota})

    ordem = ["SUBSTITUI", "SUBSTITUI?", "ABSORVE ZONA", "NAO E EDIFICACAO",
             "CONVIVE", "NOVO"]
    for cl in ordem:
        deste = [c for c in casos if c["classe"] == cl]
        if not deste:
            continue
        print(f"\n{'=' * 76}\n{cl}  ({len(deste)})\n{'=' * 76}")
        if cl == "CONVIVE":
            print("  (fica como esta; o vizinho da planta continua de pe)")
            print("  " + ", ".join(c["bloco"] for c in deste))
            continue
        if cl == "NOVO":
            print("  (nao havia nada perto -- entra limpo)")
            print("  " + ", ".join(c["bloco"] for c in deste))
            continue
        for c in deste:
            alvo = f"{c['par']} ({c['dist']} m)" if c["par"] else "-"
            print(f"  {c['bloco']:<12} -> {alvo:<38} {c['nota'][:34]}")

    resumo = {c: sum(1 for x in casos if x["classe"] == c) for c in ordem}
    SAIDA.write_text(json.dumps(
        {"o_que_e": "proposta de casamento bloco-do-Natan x peca-existente; "
                    "PRECISA DO SIM DELE antes de apagar qualquer peca",
         "resumo": resumo, "casos": casos}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    print(f"\n{resumo}")
    print(f"gravado: {SAIDA}")

    if args.imagens:
        desenhar(casos, dados, origem)


def desenhar(casos, dados, origem):
    """Prova visual: cada par ligado por uma linha, sobre a planta."""
    import cv2
    import numpy as np
    import pymupdf

    zoom = 3.0
    pix = pymupdf.open(RAIZ / "reference" / "Mapa_AGROSHOW26.pdf")[0] \
        .get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR if pix.n == 3 else cv2.COLOR_RGBA2BGR)

    doc = json.loads(AJUSTES.read_text(encoding="utf-8-sig"))
    porNome = {b["nome"]: b for b in doc["blocos_novos"]}
    porRotulo = {}
    for z in dados["zonas"]:
        porRotulo.setdefault(z["rotulo"], terreno.para_mundo(z["x"], z["y"], origem))

    def px(mx, my):
        return (int(round((mx / terreno.ESCALA + origem[0]) * zoom)),
                int(round((-my / terreno.ESCALA + origem[1]) * zoom)))

    COR = {"SUBSTITUI": (60, 60, 235), "SUBSTITUI?": (40, 160, 235),
           "ABSORVE ZONA": (200, 90, 40)}
    for c in casos:
        if c["classe"] not in COR or not c["par"]:
            continue
        b = porNome[c["bloco"]]
        p1 = px(b["x_m"], b["y_m"])
        p2 = px(*porRotulo[c["par"]])
        cor = COR[c["classe"]]
        cv2.line(img, p1, p2, cor, 3, cv2.LINE_AA)
        cv2.drawMarker(img, p1, cor, cv2.MARKER_TILTED_CROSS, 26, 4)
        cv2.circle(img, p2, 11, cor, 3, cv2.LINE_AA)
        rot = f"{c['bloco']} = {c['par'][:22]}"
        cv2.putText(img, rot, (p1[0] + 14, p1[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 255, 255), 6, cv2.LINE_AA)
        cv2.putText(img, rot, (p1[0] + 14, p1[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.62, cor, 2, cv2.LINE_AA)

    faixa = np.full((150, img.shape[1], 3), 255, np.uint8)
    itens = [("SUBSTITUI - a peca velha sai", COR["SUBSTITUI"], 45),
             ("SUBSTITUI? - colado, mas a nota nao confirma", COR["SUBSTITUI?"], 90),
             ("ABSORVE ZONA - as tendas ocupam a zona estimada", COR["ABSORVE ZONA"], 135)]
    for txt, cor, y in itens:
        cv2.line(faixa, (40, y - 6), (130, y - 6), cor, 5)
        cv2.putText(faixa, txt, (150, y), cv2.FONT_HERSHEY_SIMPLEX, 1.0,
                    (0, 0, 0), 2, cv2.LINE_AA)
    saida = RAIZ / "out" / "conferencia" / "casamento-blocos.png"
    cv2.imwrite(str(saida), np.vstack([faixa, img]))
    print(f"gravado: {saida}")


if __name__ == "__main__":
    main()
