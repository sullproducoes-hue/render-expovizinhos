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

LOCAIS_PADRAO = Path(__file__).resolve().parent.parent / "data" / "locais.json"


def completar_com_locais(dados, caminho=LOCAIS_PADRAO):
    """Acrescenta as zonas que o extrator antigo deixava cair.

    O `extract_map.py` so aceitava rotulo que estivesse numa lista branca
    escrita a mao, e 50 dos 118 nomes do mapa nao estavam nela -- entre eles a
    Fazendinha, a Area de Show e os Expositores Externos, que sao pedidos do
    roteiro. O `auditar_mapa.py` le todos, e aqui eles entram como zona para que
    `data/planos.json` possa mirar neles pelo nome.

    So entra nome que ainda nao existe: quem ja estava fica como estava, para
    nao mexer na ordem que `achar_zona` enxerga.
    """
    caminho = Path(caminho)
    if not caminho.exists():
        return dados

    ja_tem = {z["rotulo"] for z in dados["zonas"]}
    for lo in json.loads(caminho.read_text(encoding="utf-8"))["locais"]:
        if lo["nome"] in ja_tem or lo.get("e_frase"):
            continue
        dados["zonas"].append({
            "rotulo": lo["nome"],
            "categoria": "roteiro" if lo["camada"] == "roteiro" else "planta",
            "x": lo["x_pt"],
            "y": lo["y_pt"],
            "_do_auditor": True,
        })
    return dados


def carregar_mapa(caminho=MAPA_PADRAO, completar=True):
    """Le a planta extraida e crava a origem no centro da prancha."""
    dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
    dados["_origem"] = (dados["prancha"]["largura_pt"] / 2,
                        dados["prancha"]["altura_pt"] / 2)
    if completar:
        completar_com_locais(dados)
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

# --------------------------------------------------------------------------
# A bacia nao e um cilindro -- ver data/bacia.json
#
# Duas testemunhas independentes da planta concordam: de 240 a 360 graus de
# azimute NAO ha nenhuma das 15 anotacoes "Talude" e NENHUM dos 93 estandes da
# serie C. O arrimo envolve ~210 graus e a bacia fica ABERTA em ~120 -- que e
# por onde o palco olha para a pista e por onde animal e veiculo chegam em
# nivel.
#
# (O RETOMAR dizia "aberta para nordeste". Estava errado: nordeste e azimute
# ~45 e la estao QUATRO dos 15 taludes. A abertura aponta para sul-sudeste.)
#
# A mudanca so alcanca o que a medicao alcanca: os taludes medidos vao ate
# 137 m, entao em r = 150 m os dois setores se reencontram na mesma cota. O
# platao do recinto continua em 10 m em todos os rumos -- abrir ate a borda
# rebaixaria em 10 m a AREA RESTRITA, o bosque e a mata sem uma unica medida
# que peca isso.
ABERTURA_INICIO = 240.0   # graus
ABERTURA_FIM = 360.0
ABERTURA_TRANSICAO = 20.0
PISO_ABERTO_R = 78.0      # ate onde o chao da pista se estende no setor aberto
REENCONTRO_R = 150.0      # onde os dois setores voltam a mesma cota

# O perfil do setor aberto: mesma cota final, outro caminho ate ela.
PATAMARES_ABERTO = [
    (0.0, PISO_ABERTO_R, 0.0, 0.0),
    (PISO_ABERTO_R, REENCONTRO_R, 0.0, 10.0),
    (REENCONTRO_R, 9999.0, 10.0, 10.0),
]


def _smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def _perfil(r, bandas):
    for r_int, r_ext, z_int, z_ext in bandas:
        if r < r_ext:
            if r <= r_int:
                return z_int
            return z_int + (z_ext - z_int) * _smoothstep((r - r_int) / (r_ext - r_int))
    return bandas[-1][3]


def peso_aberto(azimute_deg):
    """Quanto o ponto pertence ao setor SEM arrimo, de 0 a 1.

    Corte reto deixaria uma parede radial de 3,5 m que nenhuma planta mostra,
    entao as duas pontas do setor entram por smoothstep.
    """
    a = azimute_deg % 360.0
    if not (ABERTURA_INICIO <= a < ABERTURA_FIM):
        return 0.0
    # quanto o ponto esta para DENTRO do setor, medido da ponta mais proxima
    dentro = min(a - ABERTURA_INICIO, ABERTURA_FIM - a)
    return _smoothstep(dentro / ABERTURA_TRANSICAO)


def elevacao(x, y, centro_arena):
    """Altura do terreno em metros, para um ponto do mundo.

    A bacia e modelada por bandas radiais, nao por DEM. Os DEMs globais
    disponiveis (SRTM, Copernicus, NASADEM, AW3D30) sao todos de ~30 m: num
    recinto de 800 m isso da cerca de 27 amostras de ponta a ponta, e os
    patamares de poucos metros que o cliente descreve simplesmente somem.

    Desde 14/08 ela tambem depende do AZIMUTE: ver o bloco acima e
    data/bacia.json. Fora de r = 150 m os dois perfis dao o mesmo valor, entao
    nada longe da arena mudou.
    """
    dx, dy = x - centro_arena[0], y - centro_arena[1]
    r = math.hypot(dx, dy)
    z_arrimo = _perfil(r, PATAMARES)
    if r >= REENCONTRO_R:
        return z_arrimo          # os dois perfis coincidem: nem calcula o azimute
    w = peso_aberto(math.degrees(math.atan2(dy, dx)))
    if w <= 0.0:
        return z_arrimo
    return z_arrimo + (_perfil(r, PATAMARES_ABERTO) - z_arrimo) * w


def polar(centro, raio_m, azimute_deg):
    """Ponto a `raio_m` do centro, no azimute dado (0 = +x, anti-horario)."""
    a = math.radians(azimute_deg)
    return (centro[0] + raio_m * math.cos(a),
            centro[1] + raio_m * math.sin(a))
