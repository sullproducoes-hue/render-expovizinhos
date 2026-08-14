#!/usr/bin/env python3
"""
Le TODOS os rotulos da planta AGROSHOW 2026 e escreve data/locais.json.

Existe porque o extrator anterior (scripts/extract_map.py) so aceitava rotulos
que estivessem numa lista branca escrita a mao. Tudo que nao estava na lista era
descartado em silencio -- 50 rotulos de 118, um terco do mapa. Entre os
descartados estavam a Fazendinha, a Area de Show, os Expositores Externos e a
Exposicao de Maquinas: exatamente os lugares que o roteiro do cliente pede e que
o projeto vinha tratando como "sem posicao na planta".

Aqui nada e descartado. Todo texto da prancha entra no JSON, classificado, e o
que nao e lugar (codigo de estande, cota, bussola, legenda, carimbo) fica
guardado em 'descartados' com o motivo.

## As duas camadas

O PDF separa as camadas pela COR do texto, e isso e dado, nao chute:

    #000000  706 spans  planta tecnica (o desenho do arquiteto)
    #ff3131   36 spans  ROTEIRO DO CLIENTE, desenhado por cima
    #767676    8 spans  rosa dos ventos
    #0000ff    1 span   SANEPAR
    #dcdcdc    1 span   ANTENA

A camada vermelha e o roteiro do video: Praca de Alimentacao Coberta e Aberta,
Mercado do Produtor, Cafe Colonial, Fazendinha, Area de Show, Arena de Rodeio,
Palco, os dois Expositores Externos, os dois Estacionamentos, o Portal e a frase
"AGROSHOW - E DAQUI QUE SAI O ALIMENTO QUE SUSTENTA O MUNDO". E a mesma ordem
que o cliente ditou no audio, ja posicionada no mapa.

## Cuidado com a legenda

Os quadradinhos de cor no canto inferior direito (x 925-1090, y 545-715) tem
rotulo de texto igual ao de area do recinto -- "MAQUINAS E EQUIPAMENTOS
AGRICULAS", "VEICULOS E MOTOS NAUTICAS". A coordenada deles e a do quadradinho,
nao a do lugar. Usar como posicao poe a camera no canto da prancha. Aqui eles
saem marcados como 'legenda' e nao entram em 'locais'.

Uso:
    python scripts/auditar_mapa.py                       # usa reference/Mapa_AGROSHOW26.pdf
    python scripts/auditar_mapa.py --pdf outro.pdf -o data/
    python scripts/auditar_mapa.py --relatorio           # so imprime, nao escreve
"""

import argparse
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

import pymupdf

# Escala e origem: as mesmas de scripts/terreno.py, para que a coordenada em
# metros daqui seja a mesma coordenada do mundo no Blender.
ESCALA = 0.5611  # m/pt

COR_PLANTA = 0x000000
COR_ROTEIRO = 0xFF3131
COR_BUSSOLA = 0x767676

# Caixas da prancha que NAO sao o recinto. Coordenadas em pontos de PDF.
CAIXA_LEGENDA = (925.0, 545.0, 1095.0, 715.0)
CAIXA_BUSSOLA = (740.0, 515.0, 835.0, 615.0)
CAIXA_CARIMBO = (900.0, 780.0, 1440.0, 810.0)

RE_CODIGO = re.compile(r"^[A-Z]{1,2}[-–]\d{1,3},?$")
RE_AREA = re.compile(r"^[\d.]+,\d{2}\s*m²$")
RE_COTA = re.compile(r"^\d{1,3},\d{2}$")
RE_DIMENSAO = re.compile(r"^\d+\s*x\s*\d+")
RE_SO_NUMERO = re.compile(r"^[\d.,\s]+$")

# Grafias do mapa que estao erradas ou truncadas. A chave e o que esta escrito
# na prancha; o valor e o nome correto. O texto original fica guardado no JSON
# em 'texto_no_mapa' -- corrigir nao e apagar.
GRAFIA = {
    "Pista de Jugamentos": "Pista de Julgamentos",
    "MAQUINAS E EQUIPAMENTOS AGRICULAS": "Máquinas e Equipamentos Agrícolas",
    "VEÍCULOS E MOTOS NAUTICAS": "Veículos e Motos Náuticas",
    "PAVILHÃO - NÚCLEO CARRA BRANCA": "PAVILHÃO - NÚCLEO CARA BRANCA",
    "Máquinas,Equipamentos e Veículos e Implementos":
        "Máquinas, Equipamentos e Veículos e Implementos",
    "Industria/Comércio e Serviços": "Indústria, Comércio e Serviços",
}

# Rotulos que nao sao lugar: sao frase de campanha, escrita na prancha.
FRASES = {"AGROSHOW - É DAQUI QUE SAI O ALIMENTO QUE SUSTENTA O MUNDO"}

# Lugares cujo rotulo no mapa ja vem com nome e descricao na mesma cadeia. O
# cliente pediu nominalmente que a Fazendinha tenha nome grande e descricao
# pequena embaixo -- e o mapa ja escreve assim. Separar aqui evita que o
# letreiro saia com as duas coisas do mesmo tamanho.
NOME_E_DESCRICAO = {
    "Fazendinha Área Infantil": ("Fazendinha", "Área Infantil"),
}

# Pares que a geometria juntaria mas que sao dois lugares diferentes. Rede de
# seguranca: hoje a regra geometrica ja os separa sozinha, e este conjunto
# existe para o caso de o mapa mudar de diagramacao.
NAO_JUNTAR = {
    ("PR 473", "CRUZEIRO DO IGUAÇU"),
    ("Café Colonial", "Cozinha Didática"),
    ("GALPÃO DO PRODUTOR", "CAFÉ COLONIAL E COZINHA"),
}

# Limiares do encadeamento de linhas (em multiplos do corpo da fonte).
# Uma segunda linha do MESMO rotulo fica logo abaixo da primeira e alinhada com
# ela: deslocamento perpendicular de ~1,3 corpos e deslocamento paralelo quase
# zero. Dois rotulos vizinhos escritos lado a lado -- 'Café Colonial' e 'Cozinha
# Didática', que sao dois lugares -- tem deslocamento paralelo de meio corpo.
# E esse paralelo que separa os dois casos; por bloco do PDF nao separa, porque
# o PDF quebra os blocos onde bem entende.
PARALELO_MAX = 0.35
PERPENDICULAR_MIN = 0.9
PERPENDICULAR_MAX = 1.8
ANGULO_TOL = 3.0
CORPO_TOL = 0.3


def dentro(x, y, caixa):
    x0, y0, x1, y1 = caixa
    return x0 <= x <= x1 and y0 <= y <= y1


def para_mundo(x_pt, y_pt, largura_pt, altura_pt):
    """Ponto do PDF -> metros no mundo do Blender.

    Origem no centro da prancha; y do PDF cresce para baixo e o do Blender para
    o norte, dai a inversao de sinal. Mesma conta de scripts/terreno.py.
    """
    return (
        round((x_pt - largura_pt / 2) * ESCALA, 2),
        round(-(y_pt - altura_pt / 2) * ESCALA, 2),
    )


def classificar_texto(texto):
    """Devolve o motivo de descarte, ou None se o texto for candidato a lugar."""
    if RE_CODIGO.match(texto):
        return "codigo_estande"
    if RE_AREA.match(texto):
        return "cota_area"
    if RE_COTA.match(texto) or RE_DIMENSAO.match(texto):
        return "cota_dimensao"
    if RE_SO_NUMERO.match(texto):
        return "numero_solto"
    return None


def ler_linhas(page):
    """Uma entrada por linha de texto, com cor, posicao, tamanho e rotacao."""
    linhas = []
    for i, bloco in enumerate(page.get_text("dict")["blocks"]):
        for linha in bloco.get("lines", []):
            spans = [s for s in linha["spans"] if s["text"].strip()]
            if not spans:
                continue
            texto = " ".join(s["text"].strip() for s in spans)
            x = sum((s["bbox"][0] + s["bbox"][2]) / 2 for s in spans) / len(spans)
            y = sum((s["bbox"][1] + s["bbox"][3]) / 2 for s in spans) / len(spans)
            dx, dy = linha.get("dir", (1.0, 0.0))
            linhas.append({
                "bloco": i,
                "texto": texto,
                "cor": spans[0]["color"],
                "corpo": round(spans[0]["size"], 1),
                "x": round(x, 2),
                "y": round(y, 2),
                "dir": (dx, dy),
                # Angulo do rotulo na prancha, em graus. Serve para orientar
                # placa e letreiro no 3D sem adivinhar.
                "angulo": round(math.degrees(math.atan2(-dy, dx)), 1),
            })
    return linhas


def e_linha_seguinte(a, b):
    """b e a proxima linha do MESMO rotulo que comeca em a?

    Mede o deslocamento de b em relacao a a nos eixos do proprio texto: quanto
    ele anda na direcao da leitura (paralelo) e quanto desce para a linha de
    baixo (perpendicular). Linha seguinte anda quase nada no paralelo e desce
    cerca de um corpo e meio. Rotulo vizinho anda no paralelo.
    """
    if a["cor"] != b["cor"]:
        return False
    if abs(a["corpo"] - b["corpo"]) > CORPO_TOL:
        return False
    d_ang = abs(a["angulo"] - b["angulo"])
    if min(d_ang, 360.0 - d_ang) > ANGULO_TOL:
        return False
    if (a["texto"], b["texto"]) in NAO_JUNTAR:
        return False
    # Cota nao entra em nome de lugar. Sem isto o rotulo do pavilhao encadeia
    # com a area cotada logo abaixo e vira "PAVILHAO - GADO LEITE 720,00 m2".
    if classificar_texto(a["texto"]) != classificar_texto(b["texto"]):
        return False

    dx, dy = a["dir"]
    vx, vy = b["x"] - a["x"], b["y"] - a["y"]
    paralelo = vx * dx + vy * dy
    perpendicular = vx * (-dy) + vy * dx   # +90 graus: a linha de baixo
    corpo = a["corpo"]
    return (abs(paralelo) <= PARALELO_MAX * corpo
            and PERPENDICULAR_MIN * corpo <= perpendicular
            <= PERPENDICULAR_MAX * corpo)


def juntar_linhas(linhas):
    """Encadeia as linhas de um mesmo rotulo, por geometria.

    Nao da para confiar no bloco do PDF: ele junta 'Exposicao de' com
    'Maquinas,Equipamentos e' mas deixa 'Veiculos e Implementos' num bloco
    proprio, e junta 'PR 473' com 'CRUZEIRO DO IGUACU', que sao dois lugares.
    A geometria do texto e mais confiavel que a diagramacao do arquivo.
    """
    restantes = sorted(linhas, key=lambda l: (l["cor"], l["y"], l["x"]))

    # Quem e a proxima linha de quem. Nao da para varrer em ordem de y: a
    # 'Fazendinha' esta escrita de baixo para cima, entao a segunda linha dela
    # tem y MENOR que a primeira. Monte o encadeamento e so depois descubra
    # quem comeca -- comeca quem nao e continuacao de ninguem.
    proxima_de = {}
    tem_anterior = set()
    for i, a in enumerate(restantes):
        for j, b in enumerate(restantes):
            if i == j or j in tem_anterior or i in proxima_de:
                continue
            if e_linha_seguinte(a, b):
                proxima_de[i] = j
                tem_anterior.add(j)
                break

    juntadas = []
    for i in range(len(restantes)):
        if i in tem_anterior:
            continue
        cadeia, k = [], i
        while k is not None:
            cadeia.append(restantes[k])
            k = proxima_de.get(k)

        base = dict(cadeia[0])
        base["texto"] = " ".join(c["texto"] for c in cadeia)
        base["x"] = round(sum(c["x"] for c in cadeia) / len(cadeia), 2)
        base["y"] = round(sum(c["y"] for c in cadeia) / len(cadeia), 2)
        base["linhas"] = len(cadeia)
        juntadas.append(base)
    return juntadas


def auditar(pdf_path):
    doc = pymupdf.open(pdf_path)
    page = doc[0]
    larg, alt = page.rect.width, page.rect.height

    linhas = ler_linhas(page)
    cores = Counter(ln["cor"] for ln in linhas)

    locais, descartados = [], []
    for ln in juntar_linhas(linhas):
        texto = ln["texto"].strip()
        x, y = ln["x"], ln["y"]

        motivo = classificar_texto(texto)
        if motivo is None:
            if ln["cor"] == COR_BUSSOLA or dentro(x, y, CAIXA_BUSSOLA):
                motivo = "bussola"
            elif dentro(x, y, CAIXA_LEGENDA):
                motivo = "legenda"
            elif dentro(x, y, CAIXA_CARIMBO):
                motivo = "carimbo"

        registro = {
            "texto_no_mapa": texto,
            "x_pt": x,
            "y_pt": y,
            "corpo_pt": ln["corpo"],
            "angulo_graus": ln["angulo"],
        }

        if motivo:
            registro["motivo"] = motivo
            descartados.append(registro)
            continue

        nome = GRAFIA.get(texto, texto)
        descricao = None
        if nome in NOME_E_DESCRICAO:
            nome, descricao = NOME_E_DESCRICAO[nome]

        mx, my = para_mundo(x, y, larg, alt)
        registro.update({
            "nome": nome,
            "camada": "roteiro" if ln["cor"] == COR_ROTEIRO else "planta",
            "x_m": mx,
            "y_m": my,
            "e_frase": nome in FRASES,
        })
        if descricao:
            registro["descricao"] = descricao
        if nome != texto:
            registro["grafia_corrigida"] = True
        locais.append(registro)

    locais.sort(key=lambda r: (r["camada"] != "roteiro", r["nome"]))

    return {
        "fonte": Path(pdf_path).name,
        "escala_m_por_pt": ESCALA,
        "prancha": {"largura_pt": round(larg, 1), "altura_pt": round(alt, 1)},
        "como_ler": (
            "camada 'roteiro' e o texto vermelho (#ff3131) que o cliente mandou "
            "desenhar por cima da planta -- e a ordem do video. camada 'planta' "
            "e o desenho tecnico. x_m/y_m sao metros no mundo do Blender, "
            "origem no centro da prancha. angulo_graus e a inclinacao do rotulo "
            "na prancha, util para orientar placa e letreiro."
        ),
        "aviso_legenda": (
            "os itens em descartados com motivo 'legenda' tem rotulo igual ao de "
            "areas do recinto, mas a coordenada e a do quadradinho de cor no "
            "canto da prancha. NAO usar como posicao."
        ),
        "resumo": {
            "linhas_de_texto": len(linhas),
            "locais": len(locais),
            "locais_do_roteiro": sum(1 for r in locais if r["camada"] == "roteiro"),
            "locais_da_planta": sum(1 for r in locais if r["camada"] == "planta"),
            "descartados": len(descartados),
            "por_motivo": dict(Counter(r["motivo"] for r in descartados)),
            "spans_por_cor": {f"#{c:06x}": n for c, n in cores.most_common()},
        },
        "locais": locais,
        "descartados": descartados,
    }


def imprimir(dados):
    r = dados["resumo"]
    print(f"prancha ............. {dados['prancha']['largura_pt']} x "
          f"{dados['prancha']['altura_pt']} pt")
    print(f"linhas de texto ..... {r['linhas_de_texto']}")
    print(f"locais .............. {r['locais']} "
          f"({r['locais_do_roteiro']} do roteiro + {r['locais_da_planta']} da planta)")
    print(f"descartados ......... {r['descartados']}  {r['por_motivo']}")
    print(f"cores ............... {r['spans_por_cor']}")
    print()
    print("--- camada do roteiro (o que o cliente mandou desenhar) ---")
    for lo in dados["locais"]:
        if lo["camada"] != "roteiro":
            continue
        marca = " [frase]" if lo["e_frase"] else ""
        print(f"  {lo['nome']:52s} ({lo['x_m']:8.1f}, {lo['y_m']:8.1f}) m{marca}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pdf", default="reference/Mapa_AGROSHOW26.pdf")
    ap.add_argument("-o", "--out", default="data")
    ap.add_argument("--relatorio", action="store_true",
                    help="so imprime o relatorio, nao escreve o JSON")
    args = ap.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")
    dados = auditar(args.pdf)
    imprimir(dados)

    if not args.relatorio:
        destino = Path(args.out) / "locais.json"
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(json.dumps(dados, ensure_ascii=False, indent=2), "utf-8")
        print(f"\nescrito: {destino}")


if __name__ == "__main__":
    main()
