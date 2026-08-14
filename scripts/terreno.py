#!/usr/bin/env python3
"""
Nucleo compartilhado da cena: escala, bacia da arena e leitura da planta.

Este modulo NAO importa bpy de proposito. Ele e a unica fonte das constantes
geometricas do projeto, e tanto o gerador da cena (build_scene.py) quanto a
decupagem (planos.py) leem daqui. Assim a conferencia de camera roda em
qualquer python, sem Blender e sem GPU -- que e o que permite conferir o filme
antes de gastar uma noite de render.

Escala: derivada da propria planta. Os 39 estandes da serie C tem 100 m² (lado
de 10 m) e ficam encostados em fileira; a mediana da distancia entre rotulos
consecutivos e 17,82 pt, o que da 0,5611 m/pt. A serie A nao serve para o
mesmo calculo porque ha corredor entre os modulos.

NAO CONFERIDA com medida real em campo. Ver ESTADO.md, pendencia 3.
"""

import json
import math
from pathlib import Path

# --------------------------------------------------------------------------
# Constantes geometricas -- fonte unica

ESCALA = 0.5611          # metros por ponto de PDF (derivada da serie C)
ALTURA_ESTANDE = 3.2     # m -- tenda/estande padrao de feira
ALTURA_PAVILHAO = 7.0    # m -- pavilhao de animais

# Bacia da arena, em bandas radiais a partir do centro da pista.
# (raio_interno_m, raio_externo_m, z_interno_m, z_externo_m)
#
# Os RAIOS sao dado: os 93 estandes da serie C se agrupam em aneis a 72-90 m e
# 108-113 m do centro, as 15 anotacoes de "Talude" caem nas faixas de
# transicao, e o audio do cliente descreve tres niveis.
#
# As ALTURAS sao ESTIMADAS por proporcao. Um quadro de drone lateral da arena
# confirma em minutos -- ajuste aqui antes do render final.
PATAMARES = [
    (0.0,    45.0,  0.0,  0.0),   # pista da arena
    (45.0,   62.0,  0.0,  3.5),   # talude para o patamar dos shows
    (62.0,   78.0,  3.5,  3.5),   # area de shows / camarotes
    (78.0,   95.0,  3.5,  7.0),   # talude para o primeiro anel
    (95.0,  125.0,  7.0,  7.0),   # anel de maquinas e veiculos
    (125.0, 150.0,  7.0, 10.0),   # talude para o plato geral
    (150.0, 9999.0, 10.0, 10.0),  # plato do restante do recinto
]

MAPA_PADRAO = "data/mapa_agroshow26.json"


# --------------------------------------------------------------------------
# Planta

def carregar_mapa(caminho=MAPA_PADRAO):
    """Le a planta extraida e crava a origem no centro da prancha."""
    dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
    dados["_origem"] = (dados["prancha"]["largura_pt"] / 2,
                        dados["prancha"]["altura_pt"] / 2)
    return dados


def para_mundo(x_pt, y_pt, origem):
    """Converte ponto do PDF para metros no mundo.

    O PDF tem origem no canto superior esquerdo com y crescendo para baixo;
    o Blender tem y crescendo para o norte. Dai a inversao de sinal em y.
    """
    return ((x_pt - origem[0]) * ESCALA,
            -(y_pt - origem[1]) * ESCALA)


def achar_zona(dados, rotulo, ocorrencia=0):
    """Zona pelo rotulo. Ordena por posicao real, nao pela ordem de extracao.

    Essa ordenacao importa: um briefing anterior travou o bloco dos animais
    porque leu os rotulos na ordem de extracao do texto do PDF.
    """
    achados = [z for z in dados["zonas"] if z["rotulo"] == rotulo]
    if not achados:
        return None
    achados.sort(key=lambda z: (z["y"], z["x"]))
    return achados[min(ocorrencia, len(achados) - 1)]


def ponto_da_zona(dados, rotulo, ocorrencia=0):
    """Posicao da zona em metros no mundo, ou None se o rotulo nao existir."""
    z = achar_zona(dados, rotulo, ocorrencia)
    if z is None:
        return None
    return para_mundo(z["x"], z["y"], dados["_origem"])


def centro_da_arena(dados):
    p = ponto_da_zona(dados, "ARENA DE RODEIO")
    if p is None:
        raise SystemExit("planta sem 'ARENA DE RODEIO' -- a bacia nao tem centro")
    return p


# --------------------------------------------------------------------------
# Bacia

def elevacao(x, y, centro_arena):
    """Altura do terreno em metros, para um ponto do mundo.

    A bacia e modelada por bandas radiais, nao por DEM. Os DEMs globais
    disponiveis (SRTM, Copernicus, NASADEM, AW3D30) sao todos de ~30 m: num
    recinto de 800 m isso da cerca de 27 amostras de ponta a ponta, e os
    patamares de poucos metros que o cliente descreve simplesmente somem.
    """
    r = math.hypot(x - centro_arena[0], y - centro_arena[1])
    for r_int, r_ext, z_int, z_ext in PATAMARES:
        if r < r_ext:
            if r <= r_int:
                return z_int
            t = (r - r_int) / (r_ext - r_int)
            t = t * t * (3.0 - 2.0 * t)   # smoothstep no talude
            return z_int + (z_ext - z_int) * t
    return PATAMARES[-1][3]


def polar(centro, raio_m, azimute_deg):
    """Ponto a `raio_m` do centro, no azimute dado (0 = +x, anti-horario)."""
    a = math.radians(azimute_deg)
    return (centro[0] + raio_m * math.cos(a),
            centro[1] + raio_m * math.sin(a))
