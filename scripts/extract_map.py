#!/usr/bin/env python3
"""
Extrai a planta da FEIRA AGROSHOW 2026 (Parque de Exposicoes de Dois Vizinhos - PR)
do PDF oficial para JSON estruturado, que serve de fonte de verdade para a
modelagem 3D.

O PDF NAO e vetor CAD: o desenho e um bitmap de 1806x1383 px (90 DPI efetivos
sobre uma prancha de 508 mm) com uma camada de texto por cima. Este script
recupera a camada de texto e as coordenadas de cada rotulo, que e o suficiente
para posicionar estandes e zonas por retracado guiado.

Uso:
    python3 scripts/extract_map.py <caminho-do-pdf> [-o data/]
"""

import argparse
import json
import re
from collections import Counter
from pathlib import Path

import pymupdf

# Rotulos de zona reconhecidos na prancha, agrupados por natureza.
# Usado para classificar cada bloco de texto encontrado.
ZONAS_ANCORA = {
    "arena": ["ARENA DE RODEIO", "PALCO", "PALCO AFTER", "CAMAROTES - LADO A",
              "CAMAROTES - LADO B", "ARENA DO CONHECIMENTO - UTF-PR"],
    "pavilhoes": ["PAVILHÃO - GADO LEITE", "PAVILHÃO - GADO CORTE",
                  "PAVILHÃO - OVINOS E CAPRINOS", "PAVILHÃO - PEQUENOS ANIMAIS",
                  "PAVILHÃO - EQUÍNOS", "PAVILHÃO - NÚCLEO CARRA BRANCA",
                  "PAVILHÃO 1", "PAVILHÃO 2", "PAVILHÃO 3"],
    "alimentacao": ["Praça de Alimentação", "Coberta", "Aberta",
                    "Mercado do Produtor", "Café Colonial", "Cozinha Didática",
                    "ESPAÇO P/ MESAS", "Bar", "É CHURRASCO!"],
    "infra": ["PORTAL", "Portal de Entrada", "BILHETERIA", "CONTROLE SANITÁRIO",
              "ESTACIONAMENTO", "SANITÁRIOS QUIMICOS", "BANHEIROS FEM.",
              "BANHEIROS MASC.", "CHUVEIROS", "EQ. LIMPEZA", "PORTARIA",
              "CCO", "AUDITÓRIO", "RESIDÊNCIA"],
    "pecuaria": ["PISTA DE JULGAMENTOS", "RECINTO DE LEILÕES", "MANGUEIRAS",
                 "LAVAGEM ANIMAIS", "ORDENHADEIRA", "JULGAMENTO RUSTICO",
                 "CASA DO", "MÉDICO", "VETERINÁRIO"],
    "paisagem": ["Bosque", "Mata Nativa", "Talude", "Trilha", "ÁREA RESTRITA"],
    "vias": ["PR 473", "AVENIDA JOSÉ MARCANTE", "AV. VER. DORVALINO TOSI",
             "AVENIDA VINICIUS DE MORAIS", "RUA JORGE AMADO",
             "CRUZEIRO DO IGUAÇU", "DOIS VIZINHOS", "CARROS DE APLICATIVO"],
}

# Legenda de cores da prancha -> categoria de expositor.
LEGENDA = [
    "EDIFICAÇÕES",
    "ALIMENTAÇÃO E BEBIDAS",
    "GALPÃO DO PRODUTOR",
    "CAFÉ COLONIAL E COZINHA",
    "VEÍCULOS E MOTOS NAUTICAS",
    "COOPERATIVAS",
    "MAQUINAS E EQUIPAMENTOS AGRICULAS",
    "AVICULTURA",
    "AGRICULTURA",
]

RE_CODIGO = re.compile(r"^[A-Z]{1,2}[-–]\d{1,3}$")
RE_AREA = re.compile(r"^([\d.]+,\d{2})\s*m²$")
RE_NUMERO = re.compile(r"^[\d.,\s]+$")


def parse_area(texto):
    """'1.234,56 m²' -> 1234.56"""
    m = RE_AREA.match(texto.strip())
    if not m:
        return None
    return float(m.group(1).replace(".", "").replace(",", "."))


def classificar(texto):
    for categoria, rotulos in ZONAS_ANCORA.items():
        if texto in rotulos:
            return categoria
    if texto in LEGENDA:
        return "legenda"
    return None


def extrair(pdf_path):
    doc = pymupdf.open(pdf_path)
    page = doc[0]

    # Cada palavra vem como (x0, y0, x1, y1, texto, bloco, linha, palavra).
    palavras = page.get_text("words")
    # Blocos preservam rotulos multi-palavra ("PAVILHAO - GADO LEITE").
    blocos = []
    for b in page.get_text("blocks"):
        texto = b[4].strip()
        if texto:
            blocos.append({
                "texto": texto,
                "x": round((b[0] + b[2]) / 2, 2),
                "y": round((b[1] + b[3]) / 2, 2),
            })

    codigos = []
    areas = []
    zonas = []

    for w in palavras:
        texto = w[4].strip()
        cx, cy = round((w[0] + w[2]) / 2, 2), round((w[1] + w[3]) / 2, 2)
        if RE_CODIGO.match(texto):
            serie = re.split(r"[-–]", texto)[0]
            codigos.append({"codigo": texto, "serie": serie, "x": cx, "y": cy})

    for b in blocos:
        for linha in b["texto"].split("\n"):
            linha = linha.strip()
            if not linha:
                continue
            area = parse_area(linha)
            if area is not None:
                areas.append({"area_m2": area, "x": b["x"], "y": b["y"]})
                continue
            categoria = classificar(linha)
            if categoria:
                zonas.append({"rotulo": linha, "categoria": categoria,
                              "x": b["x"], "y": b["y"]})

    # Emparelha cada codigo de estande com a area cotada mais proxima.
    # Distancia em pontos PDF; acima do limiar o codigo fica sem area.
    LIMIAR = 40.0
    for c in codigos:
        melhor, dist_melhor = None, float("inf")
        for a in areas:
            d = ((c["x"] - a["x"]) ** 2 + (c["y"] - a["y"]) ** 2) ** 0.5
            if d < dist_melhor:
                melhor, dist_melhor = a, d
        if melhor and dist_melhor <= LIMIAR:
            c["area_m2"] = melhor["area_m2"]
            c["dist_pt"] = round(dist_melhor, 1)

    rect = page.rect
    return {
        "fonte": Path(pdf_path).name,
        "prancha": {
            "largura_mm": round(rect.width / 72 * 25.4, 1),
            "altura_mm": round(rect.height / 72 * 25.4, 1),
            "largura_pt": round(rect.width, 1),
            "altura_pt": round(rect.height, 1),
        },
        "aviso_geometria": (
            "O desenho e um bitmap de 1806x1383 px (~90 DPI na prancha), nao "
            "vetor CAD. Coordenadas aqui sao da camada de texto, em pontos PDF, "
            "com origem no canto superior esquerdo. Servem para posicionar e "
            "conferir, NAO para extrair geometria. Peca o DWG/DXF."
        ),
        "resumo": {
            "codigos_estande": len(codigos),
            "codigos_com_area": sum(1 for c in codigos if "area_m2" in c),
            "series": dict(Counter(c["serie"] for c in codigos)),
            "blocos_com_area": len(areas),
            "area_total_m2": round(sum(a["area_m2"] for a in areas), 2),
            "area_total_ha": round(sum(a["area_m2"] for a in areas) / 10000, 3),
            "zonas_identificadas": len(zonas),
        },
        "estandes": sorted(codigos, key=lambda c: (c["serie"], c["codigo"])),
        "areas": sorted(areas, key=lambda a: -a["area_m2"]),
        "zonas": sorted(zonas, key=lambda z: (z["categoria"], z["rotulo"])),
        "legenda_categorias": LEGENDA,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pdf", help="PDF do mapa (Mapa_AGROSHOW26.pdf)")
    ap.add_argument("-o", "--out", default="data", help="diretorio de saida")
    args = ap.parse_args()

    dados = extrair(args.pdf)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    destino = out / "mapa_agroshow26.json"
    destino.write_text(json.dumps(dados, ensure_ascii=False, indent=2), "utf-8")

    r = dados["resumo"]
    print(f"escrito: {destino}")
    print(f"  estandes ............ {r['codigos_estande']} "
          f"({r['codigos_com_area']} com area cotada)")
    print(f"  series .............. {r['series']}")
    print(f"  blocos com area ..... {r['blocos_com_area']}")
    print(f"  area total .......... {r['area_total_m2']:.0f} m² "
          f"({r['area_total_ha']:.2f} ha)")
    print(f"  zonas ............... {r['zonas_identificadas']}")


if __name__ == "__main__":
    main()
