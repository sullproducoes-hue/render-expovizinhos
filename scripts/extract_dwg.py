#!/usr/bin/env python3
"""
Extrai a camada de texto do DWG oficial da AGROSHOW 2026 com coordenadas CAD.

ACHADO CRITICO sobre este DWG (AC1018 / AutoCAD 2004):
    O arquivo NAO contem geometria vetorial da planta. O inventario completo,
    varrendo todos os blocos, e: 4883 TEXT, 1 LINE, 1 SOLID, 2 HATCH solidos
    e 1 IMAGE de 1806x1383 px -- exatamente o mesmo bitmap embutido no PDF.
    Nao ha LWPOLYLINE, POLYLINE, ARC, CIRCLE nem SPLINE.

    Ou seja: o DWG e o mesmo desenho rasterizado com uma camada de texto por
    cima, provavelmente um PDF importado para o CAD. Ele NAO desbloqueia
    extracao de contorno, e qualquer plano baseado em "separar camadas por cor
    no Illustrator" falha, porque nao existe preenchimento vetorial a
    selecionar.

    E a camada de texto tambem nao ajuda: 4483 dos 4523 textos sao caracteres
    soltos, gravados glifo a glifo -- outra assinatura de PDF importado. Apenas
    40 sao rotulos legiveis, e sao a camada de anotacao vermelha sobreposta.

    Conclusao pratica: a extracao do PDF em scripts/extract_map.py continua
    sendo a melhor fonte, porque o PDF preserva as palavras montadas (134
    codigos de estande e 181 areas cotadas). Use este script apenas para
    auditar o DWG, nao como fonte de dados.

Pre-requisitos:
    pip install ezdxf
    DWG convertido para DXF com LibreDWG:  dwg2dxf -o mapa.dxf mapa.dwg

Uso:
    python3 scripts/extract_dwg.py mapa.dxf -o data/
"""

import argparse
import collections
import json
import re
from pathlib import Path

import ezdxf

RE_CODIGO = re.compile(r"^[A-Z]{1,2}[-–]\s?\d{1,3}$")
RE_AREA = re.compile(r"^([\d.]+[,.]\d{2})\s*m2?²?$", re.IGNORECASE)
RE_COTA = re.compile(r"^\d{1,3}[,.]\d{1,2}$")

GEOMETRIA_DESENHO = {
    "LINE", "LWPOLYLINE", "POLYLINE", "CIRCLE", "ARC",
    "ELLIPSE", "SPLINE", "3DFACE", "MESH", "REGION",
}


def inventario(doc):
    """Conta toda entidade do arquivo, inclusive dentro de blocos."""
    contagem = collections.Counter()
    for bloco in doc.blocks:
        for e in bloco:
            contagem[e.dxftype()] += 1
    return contagem


def coletar_textos(doc):
    """Todo TEXT/MTEXT do arquivo, com coordenada de insercao."""
    itens = []
    for bloco in doc.blocks:
        for e in bloco:
            if e.dxftype() not in ("TEXT", "MTEXT"):
                continue
            texto = (e.plain_text() if e.dxftype() == "MTEXT"
                     else e.dxf.text).strip()
            if not texto:
                continue
            p = e.dxf.insert
            itens.append({
                "texto": texto,
                "x": round(float(p[0]), 3),
                "y": round(float(p[1]), 3),
                "altura": round(float(e.dxf.height), 3),
                "bloco": bloco.name,
            })
    return itens


def classificar(itens):
    """Separa codigos de estande, areas cotadas, cotas soltas e rotulos."""
    grupos = {"codigos": [], "areas": [], "cotas": [], "rotulos": []}
    for it in itens:
        t = it["texto"]
        if RE_CODIGO.match(t):
            it["serie"] = re.split(r"[-–]", t)[0].strip()
            grupos["codigos"].append(it)
        elif RE_AREA.match(t):
            bruto = RE_AREA.match(t).group(1)
            it["area_m2"] = float(bruto.replace(".", "").replace(",", "."))
            grupos["areas"].append(it)
        elif RE_COTA.match(t):
            grupos["cotas"].append(it)
        else:
            grupos["rotulos"].append(it)
    return grupos


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dxf", help="DXF convertido a partir do DWG oficial")
    ap.add_argument("-o", "--out", default="data")
    args = ap.parse_args()

    doc = ezdxf.readfile(args.dxf)
    inv = inventario(doc)
    geom = {k: v for k, v in inv.items() if k in GEOMETRIA_DESENHO}

    itens = coletar_textos(doc)
    grupos = classificar(itens)

    raster = None
    for e in doc.modelspace():
        if e.dxftype() == "IMAGE":
            raster = {
                "largura_px": int(e.dxf.image_size[0]),
                "altura_px": int(e.dxf.image_size[1]),
                "unidades_por_pixel": round(float(e.dxf.u_pixel[0]), 6),
            }

    dados = {
        "fonte": Path(args.dxf).name,
        "dxf_version": doc.dxfversion,
        "insunits": doc.header.get("$INSUNITS"),
        "veredito_geometria": (
            "SEM geometria vetorial da planta. O DWG carrega o mesmo bitmap do "
            "PDF mais uma camada de texto. Nao serve para extrair contorno nem "
            "para separacao de camadas por cor. Para arte vetorial limpa, "
            "redesenhe por cima do raster ou peca o arquivo nativo a quem "
            "desenhou o mapa."
        ),
        "inventario_entidades": dict(inv.most_common()),
        "geometria_de_desenho": geom,
        "raster_embutido": raster,
        "resumo": {
            "textos_totais": len(itens),
            "codigos_estande": len(grupos["codigos"]),
            "series": dict(collections.Counter(
                c["serie"] for c in grupos["codigos"])),
            "areas_cotadas": len(grupos["areas"]),
            "area_total_m2": round(
                sum(a["area_m2"] for a in grupos["areas"]), 2),
            "cotas_soltas": len(grupos["cotas"]),
            "rotulos": len(grupos["rotulos"]),
        },
        "codigos": sorted(grupos["codigos"], key=lambda c: c["texto"]),
        "areas": sorted(grupos["areas"], key=lambda a: -a["area_m2"]),
        "rotulos": grupos["rotulos"],
    }

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    destino = out / "dwg_agroshow26.json"
    destino.write_text(json.dumps(dados, ensure_ascii=False, indent=2), "utf-8")

    r = dados["resumo"]
    print(f"escrito: {destino}")
    print(f"  geometria vetorial de desenho ... {geom if geom else 'NENHUMA'}")
    print(f"  raster embutido ................. "
          f"{raster['largura_px']}x{raster['altura_px']} px")
    print(f"  textos .......................... {r['textos_totais']}")
    print(f"  codigos de estande .............. {r['codigos_estande']} "
          f"{r['series']}")
    print(f"  areas cotadas ................... {r['areas_cotadas']} "
          f"({r['area_total_m2']:.0f} m²)")
    print(f"  rotulos ......................... {r['rotulos']}")


if __name__ == "__main__":
    main()
