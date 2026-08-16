#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PLANO B — a esteira de quadros gerados por IA, plano a plano.

O Plano A constroi a cena no Blender. O Plano B pega o footage real que ja
existe em disco, gera a imagem final por IA a partir dele, e anima cada imagem.
Este script nao gera imagem nenhuma: ele **organiza a esteira**, que e o que
estava faltando.

Ele responde tres perguntas, na ordem em que elas aparecem na bancada:

  1. QUAL ARQUIVO eu abro para este plano?   -> resolve as referencias de
     data/quadros-ia.json contra o catalogo de 9.980 quadros de
     data/acervo-quadros.json, e devolve o CAMINHO ABSOLUTO do JPG em disco.
  2. QUE PROMPT eu colo?                     -> monta o prompt de imagem e o
     prompt de movimento a partir dos contratos ja escritos do projeto
     (planos, luz, povoamento, letreiros, restricoes do cliente).
  3. ONDE eu salvo o que voltar?             -> uma pasta por plano, com o
     mesmo nome em todo lugar.

Saidas:
    data/plano-b.json          o registro de maquina
    PLANO-B.md                 o runbook, na ordem de trabalho
    out/plano-b/PLANO-B.html   a pagina navegavel, offline, com copiar-caminho
    out/plano-b/P01..P22/      o esqueleto de pastas (com --criar-pastas)

Uso:
    python3 scripts/plano_b.py                   # gera JSON + MD + HTML
    python3 scripts/plano_b.py --criar-pastas    # + o esqueleto de pastas
    python3 scripts/plano_b.py --plano P19       # so um plano, no terminal
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / "data"
SAIDA = RAIZ / "out" / "plano-b"


# ---------------------------------------------------------------- utilidades

def _ler(nome: str):
    with open(DADOS / nome, encoding="utf-8") as f:
        return json.load(f)


def _chave(s: str) -> str:
    """Normaliza nome de video/pasta para comparacao: sem extensao, sem acento,
    so alfanumerico. E o que faz '1 (15).mp4' casar com a pasta '1 (15)'."""
    s = os.path.splitext(s.strip())[0].lower()
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "", s)


# ------------------------------------------------------- resolucao das placas

def indexar_acervo(acervo: dict) -> dict:
    """pasta normalizada -> lista de quadros daquela pasta, ordenada por tempo."""
    por_pasta: dict[str, list] = {}
    for q in acervo["quadros"]:
        por_pasta.setdefault(_chave(q["pasta"]), []).append(q)
    for lista in por_pasta.values():
        lista.sort(key=lambda q: q.get("tc_s") or 0)
    return por_pasta


def resolver(ref: dict, por_pasta: dict, raizes: dict, vizinhos: int = 2) -> dict:
    """Uma referencia de quadros-ia.json vira arquivo em disco.

    Devolve sempre o mesmo formato, inclusive quando nao resolve — plano sem
    placa e informacao, nao e buraco a esconder.
    """
    saida = {
        "video": ref["video"],
        "raiz": ref["raiz"],
        "tc_s": ref.get("tc"),
        "papel": ref.get("papel"),
        "confianca": ref.get("confianca"),
        "porque": ref.get("porque"),
        "resolvido": False,
        "motivo_nao_resolvido": None,
        "arquivo": None,
        "thumb": None,
        "alternativas": [],
    }

    # Referencia que nao e video: a raiz ja aponta o arquivo inteiro. E o caso
    # da foto do portal, que e a unica imagem que existe do portal celeiro e
    # abre e fecha o filme — nao pode sair como "nao resolve".
    raiz_dec = raizes.get(ref["raiz"], "")
    if raiz_dec and os.path.splitext(raiz_dec)[1] and _chave(raiz_dec).endswith(_chave(ref["video"])):
        saida.update(resolvido=True, arquivo=raiz_dec, thumb=None,
                     fora_do_acervo=True,
                     nota=None, tier=None, periodo="foto do cliente, nao e footage")
        return saida

    quadros = por_pasta.get(_chave(ref["video"]))
    if not quadros:
        saida["motivo_nao_resolvido"] = (
            f"a raiz '{ref['raiz']}' nao aponta este arquivo e nao ha pasta "
            f"com este nome no catalogo do acervo"
        )
        return saida

    alvo = ref.get("tc")
    if alvo is None:
        # sem timecode: entra o melhor quadro da pasta, pela nota do catalogo
        escolha = max(quadros, key=lambda q: q.get("nota") or 0)
        perto = sorted(quadros, key=lambda q: -(q.get("nota") or 0))[1 : 1 + vizinhos]
    else:
        ordenado = sorted(quadros, key=lambda q: abs((q.get("tc_s") or 0) - alvo))
        # quadro marcado "fraco" nao vira placa se houver vizinho utilizavel
        bons = [q for q in ordenado if q.get("tier") != "fraco"]
        escolha = (bons or ordenado)[0]
        perto = [q for q in (bons or ordenado)[1 : 1 + vizinhos + 1] if q is not escolha]
        perto = perto[:vizinhos]

    saida.update(
        resolvido=True,
        arquivo=escolha["arquivo"],
        thumb=escolha.get("thumb"),
        id=escolha.get("id"),
        tc_do_arquivo=escolha.get("tc"),
        w=escolha.get("w"),
        h=escolha.get("h"),
        em_pe=bool(escolha.get("h", 0) > escolha.get("w", 1)),
        nota=escolha.get("nota"),
        tier=escolha.get("tier"),
        periodo=escolha.get("periodo"),
        alternativas=[
            {"arquivo": q["arquivo"], "tc": q.get("tc"), "nota": q.get("nota"),
             "thumb": q.get("thumb")}
            for q in perto
        ],
    )
    return saida


# ------------------------------------------------------------------- prompts

# O prompt sai dos contratos, nao da minha cabeca. Cada pedaco tem fonte:
#   luz      -> data/luz.json (27/11, 18:15, golden hour, HDRI kloppenheim)
#   camera   -> data/planos.json (lente, altura, movimento, distancia)
#   gente    -> data/povoamento.json (censo tirado do audio do cliente)
#   proibido -> README.md "Restricoes que causam rejeicao"

LUZ_EN = (
    "late-afternoon golden hour, 18:15 on 27 November, sun low at ~10 degrees "
    "above the horizon, long warm raking shadows, clear sky with soft high cloud"
)

BASE_EN = (
    "Ultra-photorealistic photograph, not a 3D render and not an illustration. "
    "Southern Brazil agricultural fairground in Dois Vizinhos, Parana. "
    "Shot on a full-frame camera, natural colour, real atmospheric haze, "
    "believable depth of field, no CGI look, no plastic surfaces, "
    "no oversaturation, no HDR halo"
)

NEGATIVO_EN = (
    "cartoon, illustration, 3D render, videogame, CGI, plastic skin, "
    "distorted faces, extra limbs, warped text, unreadable signage, "
    "watermark, logo overlay, oversaturated colours, fisheye distortion, "
    "grandstand bleachers around the rodeo arena"
)

# TETO DURO DA IA DE VIDEO. O Seedance V1.5 Pro aceita 4 a 12 s por clipe.
# Plano mais longo que isso NAO e um prompt -- sao dois, e o segundo comeca no
# ultimo quadro do primeiro. Descoberto conferindo o catalogo de modelos, nao
# suposto: tres planos do filme passam do teto (P06 17,5 s, P14 18,5 s,
# P08 13,5 s) e os tres sao diferenciais, que e onde doeria mais descobrir tarde.
TETO_CLIPE_S = 12.0
PISO_CLIPE_S = 4.0


def cortar_em_clipes(duracao_s: float | None) -> list[dict]:
    """A duracao do plano se divide entre as TOMADAS que ele comporta.

    Ordem dele de 16/08 -- geral, medio e detalhe por bloco -- muda a conta. Um
    plano nao e mais UMA tomada longa: sao ate tres, e o corte entre elas e o que
    da ritmo. Cada tomada e um clipe proprio, gerado da sua propria imagem.

    Quantas cabem e aritmetica, nao gosto: o Seedance nao gera abaixo de 4 s,
    entao um plano de 5 s comporta UMA tomada e um de 12 s comporta tres. Plano
    curto continua sendo uma tomada so -- picar 5 s em tres da 1,7 s cada, que
    nao e corte, e piscada.

    Efeito colateral bom: dividido assim, **nenhuma tomada passa dos 12 s**. O
    teto que obrigava P06, P08 e P14 a virar dois clipes encadeados deixou de
    morder. A guarda continua no codigo porque duracao muda, e no dia que mudar
    e melhor a conta reclamar do que o Seedance recusar.
    """
    if not duracao_s:
        return []
    n = max(1, min(len(ESCALAS), int(duracao_s // PISO_CLIPE_S)))
    passo = duracao_s / n
    clipes = []
    for i in range(n):
        esc = ESCALAS[i]
        if passo > TETO_CLIPE_S:                     # guarda: nao deve acontecer hoje
            sub = int(-(-passo // TETO_CLIPE_S))
            for j in range(sub):
                clipes.append({
                    "n": len(clipes) + 1, "escala": esc["id"], "rotulo": esc["rotulo"],
                    "duracao_s": round(passo / sub, 1),
                    "primeiro_quadro": (f"a imagem {esc['id']} do plano" if j == 0
                                        else f"o ULTIMO quadro do clipe {len(clipes)}"),
                })
        else:
            clipes.append({
                "n": i + 1, "escala": esc["id"], "rotulo": esc["rotulo"],
                "duracao_s": round(passo, 1),
                "primeiro_quadro": f"a imagem {esc['id']} do plano",
            })
    for c, ini in zip(clipes, [sum(x["duracao_s"] for x in clipes[:i])
                              for i in range(len(clipes))]):
        c["de_s"] = round(ini, 1)
        c["ate_s"] = round(ini + c["duracao_s"], 1)
    return clipes


# AS TRES ESCALAS. Ordem dele, 16/08: "esse ficou plano geral, quero um mediano
# e um detalhes de cada bloco, com angulos diferentes".
#
# Nao e invencao nova: e a LEI DO DETALHAMENTO que FILA-CENA.md ja escreveu para
# a cena 3D -- <= 8 m HERO, 8-30 m MEDIO, > 30 m FUNDO -- aplicada agora ao
# enquadramento da IA em vez da densidade de malha. A mesma regua nos dois planos.
#
# O AZIMUTE MUDA JUNTO, e isso nao e enfeite. Tres escalas do mesmo ponto de
# vista cortam como zoom, e zoom em corte parece erro. Angulo diferente e o que
# faz o corte ler como outra camera -- que e o que ele pediu.
ESCALAS = [
    {
        "id": "geral",
        "rotulo": "PLANO GERAL",
        "faixa_m": "> 30 m",
        "delta_azimute_deg": 0,
        "papel": "estabelece o lugar: onde estou, qual o tamanho disto",
        "camera_en": ("from a drone {alt:.0f} m above the ground, roughly {dist:.0f} m "
                      "from the subject, looking down at a shallow angle — the whole "
                      "area reads at once, the ground plane still reads, this is not "
                      "a top-down map view"),
        "lente_mm": None,          # usa a lente declarada do plano
    },
    {
        "id": "medio",
        "rotulo": "PLANO MÉDIO",
        "faixa_m": "8 a 30 m",
        "delta_azimute_deg": 55,
        "papel": "mostra a atividade: o que as pessoas estão fazendo aqui",
        "camera_en": ("from a low drone about 12 m above the ground, roughly 25 m from "
                      "the subject, gentle downward tilt — people read full-figure, "
                      "faces and gestures are legible, the activity is the subject and "
                      "the wider site is only context at the edges of frame"),
        "lente_mm": 35,
    },
    {
        "id": "detalhe",
        "rotulo": "DETALHE",
        "faixa_m": "≤ 8 m",
        "delta_azimute_deg": -40,
        "papel": "vende: textura, mão, rosto, produto, o material de perto",
        "camera_en": ("at eye level, camera about 1,6 m above the ground and 3 to 6 m "
                      "from the subject, shallow depth of field with the background "
                      "falling soft — a person's point of view standing right there, "
                      "NOT an aerial and NOT a drone shot"),
        "lente_mm": 50,
    },
]

# O QUE O MEDIO E O DETALHE OLHAM, bloco a bloco. Sai do audio do cliente
# (docs/brief-audios.md) e do povoamento: o detalhe tem que ser a coisa que
# aquele bloco VENDE, nao um recorte qualquer do plano geral.
RECORTE_EN = {
    "P01": ("families arriving on foot between the parked pickups, carrying "
            "folding chairs and cool boxes, walking toward the entrance",
            "a mud-splashed pickup wheel and boot stepping down onto the gravel, "
            "the entrance banner soft in the background"),
    "P02": ("a family walking through the timber portal opening, looking up at "
            "the hanging sign as they pass under it",
            "the weathered vertical board cladding and its wrought-iron lantern "
            "and hardware, low sun raking across the grain of the wood"),
    "P03": ("visitors at a trade booth inside the pavilion, an exhibitor leaning "
            "over the counter explaining a product",
            "two hands closing a handshake over a booth counter, brochures and a "
            "branded banner soft behind"),
    "P04": ("families seated at the long tables of the covered food court, plates "
            "and drinks on the boards, queue at the service counters behind",
            "a plate of grilled meat, rice and salad being set down on the table, "
            "steam rising, hands reaching in"),
    "P05": ("visitors walking the central aisle between machinery stands, one "
            "group stopped in front of a display",
            "a manufacturer's badge and painted sheet metal on a display machine, "
            "reflections of the low sun on the paint"),
    "P06": ("farmers behind the market stalls handing produce to buyers across "
            "the counter, crates stacked at their feet",
            "hands lifting a wooden crate of tomatoes and greens, a wheel of "
            "cheese and jars of preserves on the counter beside it"),
    "P07": ("visitors at an agro-industry tasting counter, a producer pouring a "
            "sample and talking them through it",
            "a small glass of cachaça and slices of salami and cheese on a wooden "
            "board, a hand reaching for one"),
    "P08": ("families seated along the long colonial café tables, plates passing "
            "hand to hand, warm hanging lights above",
            "the table top loaded with breads, cakes, cured meats, cheese and a "
            "cup of coffee being poured, close and warm"),
    "P09": ("people queuing at the food trucks under the trees, others eating at "
            "picnic tables in dappled shade",
            "a hand taking a paper-wrapped sandwich across the food-truck hatch, "
            "the tree canopy soft behind"),
    "P10": ("buyers seated with catalogues in the tiered seating facing the sale "
            "ring, one raising a hand to bid, a single animal in the ring",
            "a raised bidding hand and a catalogue on a knee, the auctioneer's "
            "booth soft in the background"),
    "P11": ("handlers grooming and washing cattle in the open barn, animals tied "
            "at the rail with straw underfoot",
            "a handler's hand running a brush down the flank of a bull, hide and "
            "straw in sharp texture, the barn falling soft behind"),
    "P12": ("cattle led on halters in a line across the grass judging arena, "
            "judges walking between them, spectators along the rail",
            "a gloved hand on a halter rope beside the animal's head, the judge's "
            "clipboard soft behind"),
    "P13": ("visitors walking between the outdoor stands and marquees, exhibitors "
            "talking to them beside the equipment on the grass",
            "a stand banner and product laid out on a trestle table, a visitor's "
            "hand picking one up"),
    "P14": ("children at the low wooden fence of the children's farm feeding the "
            "sheep and goats, parents standing behind them watching",
            "a small child's hand holding out feed to a goat's muzzle over the "
            "fence rail, warm and close"),
    "P15": ("children riding ponies led at a walk around the ring by a handler, "
            "a border collie working the sheep behind them",
            "a child's boots in the stirrups and small hands gripping the saddle "
            "horn, the pony's mane in the low sun"),
    "P16": ("buyers walking the line of tractors and harvesters, one climbing the "
            "steps into a cab while a salesman talks from the ground",
            "the treads of a huge tractor tyre with a person standing beside it "
            "for scale, manufacturer's paint and badge sharp"),
    "P17": ("buyers walking the line of pickups and boats on trailers, a dealer "
            "opening a truck door for a couple",
            "a boat's outboard motor and polished hull on its trailer, low sun "
            "reflecting off the paint"),
    "P18": ("the crowd on the show ground at dusk, hands up, faces lit by the "
            "stage lighting from the front",
            "a few faces in the front of the crowd lit warm by the stage lights, "
            "hands raised, everything behind falling into bokeh"),
    "P19": ("the bucking bull and mounted rider mid-buck seen from the arena rail, "
            "dust up, the crowd's hats and shoulders in the near foreground",
            "the rider's gloved hand gripping the bull rope and his spurred boot "
            "against the bull's flank, dust hanging in the low sun"),
    "P20": ("the performer at the front of the stage with the crowd's raised hands "
            "in the foreground, stage lights on",
            "the singer at the microphone lit warm from the side, the stage "
            "lighting rig soft behind"),
    "P21": ("groups of people talking business across the grounds — handshakes "
            "beside machinery, folders and phones out",
            "two men shaking hands over a signed sheet on a truck bonnet, the "
            "fairground soft and busy behind them"),
    "P22": ("visitors walking out through the timber portal at dusk, backs to "
            "camera, the last light behind them",
            "the timber portal's hanging sign lit from below at dusk, the grain of "
            "the board and the lantern glow close"),
}


MOVIMENTO_EN = {
    "subida": "slow vertical crane-up, camera rising steadily while holding the subject centred",
    "push-in": "slow steady push-in, camera advancing straight toward the subject at constant speed",
    "orbita": "slow orbital arc around the subject, camera holding distance and height",
    "travelling": "slow lateral tracking move, camera sliding sideways at constant speed",
    "sobrevoo": "smooth aerial fly-over, camera advancing forward above the ground",
}

# Traducao do censo para linguagem de prompt. A contagem vem do JSON.
ESPECIE_EN = {
    "pessoa": "visitors",
    "touro": "bucking bull",
    "bovino_leite": "dairy cattle",
    "bovino_cara_branca": "Hereford and Braford cattle",
    "bovino_nelore": "Nelore beef cattle",
    "ovino": "sheep and goats",
    "equino": "horses",
    "cao": "border collie dogs",
}

# Ambiente do povoamento -> plano. O nome da zona nao e o id do plano.
ZONA_DO_PLANO = {
    "P03": ["Expositores Industria/Comércio e Serviços"],
    "P04": ["Praça de Alimentação Coberta"],
    "P05": ["Expositores Industria/Comércio e Serviços"],
    "P09": ["Praça de Alimentação Aberta"],
    "P10": ["RECINTO DE LEILÕES"],
    "P11": ["PAVILHÃO - GADO LEITE", "PAVILHÃO - NÚCLEO CARA BRANCA",
            "PAVILHÃO - GADO CORTE", "PAVILHÃO - OVINOS E CAPRINOS",
            "PAVILHÃO - EQUÍNOS"],
    "P12": ["PISTA DE JULGAMENTOS"],
    "P13": ["Expositores Externo"],
    "P14": ["Fazendinha"],
    "P15": ["Fazendinha"],
    "P16": ["Exposição de Máquinas,Equipamentos e Veículos e Implementos"],
    "P18": ["Área de Show"],
    "P19": ["ARENA DE RODEIO"],
    "P20": ["Área de Show"],
}

# O que precisa estar em quadro, por plano, dito em ingles de prompt.
# Sai do audio do cliente e do docs/BRIEFING.md.
CONTEUDO_EN = {
    "P01": "wide gravel parking field full of parked pickup trucks and cars, "
           "families walking toward the entrance gate, tree-lined access avenue",
    "P02": "large rustic timber entrance portal in barn style — vertical board "
           "cladding, ceramic tile roof, economical construction, a hanging "
           "wooden sign across the opening, visitors walking through",
    "P03": "long exhibition pavilion with brick walls and corrugated metal roof, "
           "commercial trade booths under the roof, banners, visitors browsing",
    "P04": "covered food court with long rows of tables and chairs, food service "
           "counters along one side, families eating, overhead roof structure",
    "P05": "second exhibition pavilion, same construction as the first, trade "
           "stands and machinery displays, visitors walking the central aisle",
    "P06": "producer's market — open-sided stalls with wooden crates of fresh "
           "produce, cheeses, preserves and cured meats, farmers behind the "
           "counters talking to buyers",
    "P07": "agro-industry stands: small-scale food processing displays, "
           "stainless equipment, tasting counters, branded booths",
    "P08": "colonial café — long tables laid with breads, cakes, cured meats, "
           "cheese and coffee, warm hanging lights, families seated eating",
    "P09": "open-air food court in a grove of trees, food trucks and stalls "
           "around the edge, picnic tables in dappled shade, people queuing",
    "P10": "livestock auction ring — circular sale ring with a raised "
           "auctioneer's booth, tiered seating facing the ring, buyers seated "
           "with catalogues, a single animal in the ring",
    "P11": "row of open livestock barns, animals in individual pens with straw "
           "bedding, handlers grooming them, feed and water troughs",
    "P12": "grass judging arena, cattle led on halters by handlers in a line, "
           "judges in the centre, spectators along the rail",
    "P13": "outdoor exhibitor area on grass, open stands and marquees, "
           "equipment displayed on the ground, visitors walking between them",
    "P14": "children's farm area — small rustic barn, pony rides, pens with "
           "sheep and goats, a border collie herding demonstration, families "
           "with small children watching",
    "P15": "the same children's farm area seen closer: the pony ring and the "
           "animal pens, children feeding the animals over a low wooden fence",
    "P16": "agricultural machinery exhibition — tractors, combine harvesters, "
           "seeders and implements lined up on gravel, buyers inspecting them, "
           "manufacturer flags",
    # A placa deste plano e emprestada do P16 e mostra TRATORES. O prompt tem
    # de mandar a troca de forma explicita, senao a IA devolve trator.
    "P17": "vehicle and nautical display area. KEEP the layout of the reference "
           "image — the same tree-lined avenue, the same row of units parked at "
           "the same angle, the same ground and the same light — but REPLACE "
           "every tractor and farm implement with pickup trucks, SUVs and "
           "motorboats and jet-skis sitting on road trailers. No agricultural "
           "machinery anywhere in the frame. Dealer banners beside the units, "
           "buyers walking the line",
    "P18": "large open show ground filling with a crowd at dusk, stage lighting "
           "towers, sound system, the crowd facing the stage",
    "P19": "rodeo arena — an oval dirt track with a bucking bull and a mounted "
           "rider, chutes at one end, a stage facing the arena and VIP boxes "
           "along the sides. THERE ARE NO GRANDSTAND BLEACHERS around this "
           "arena: only the track, the side boxes and the facing stage",
    "P20": "main stage at dusk, a performer singing, stage lighting on, the "
           "crowd below with hands raised",
    "P21": "high wide aerial of the whole fairground at dusk, every area lit, "
           "tents, pavilions, the arena and the show field all readable at once",
    "P22": "the same rustic timber barn portal seen from inside the grounds, "
           "visitors walking out through it, night falling behind them",
}

TENDAS_EN = (
    "white peaked event marquees and tents pitched across the grounds, "
    "guy ropes and steel poles visible"
)


# PLACA EMPRESTADA. Plano sem imagem nenhuma no acervo pega a placa de um
# vizinho -- nao pela aparencia do conteudo, mas pela IMPLANTACAO: mesma
# alameda, mesma arvore, mesma hora, mesma altura de camera. O que muda e o que
# esta exposto no chao, e isso o prompt troca.
#
# Ordem do Natan, 16/08: "usa a imagem de referencia dos tratores para trocar
# por motos nauticas". P17 e o unico plano do filme sem placa propria.
PLACAS_EMPRESTADAS = {
    "P17": {
        "de": "P16",
        "porque": "Ordem dele em 16/08. O acervo nao tem um unico quadro da area "
                  "de veiculos e nauticos. A alameda de maquinas do P16 da a "
                  "IMPLANTACAO certa -- fila de equipamentos sob as arvores, "
                  "mesma hora, mesma altura -- e o prompt troca o que esta "
                  "exposto: sai trator, entra picape e barco sobre carreta.",
    },
}


def povoar_en(plano_id: str, povoamento: dict) -> str:
    """O censo do audio do cliente vira frase de prompt."""
    zonas = ZONA_DO_PLANO.get(plano_id, [])
    if not zonas:
        return ""
    pedacos = []
    for amb in povoamento["ambientes"]:
        if amb.get("zona") not in zonas:
            continue
        especie = ESPECIE_EN.get(amb.get("tipo"))
        if not especie:
            continue
        n = amb.get("quantos") or 0
        if n >= 200:
            pedacos.append(f"a dense crowd of several hundred {especie}")
        elif n >= 40:
            pedacos.append(f"roughly {n} {especie}")
        elif n > 1:
            pedacos.append(f"{n} {especie}")
        else:
            pedacos.append(f"one {especie}")
    return ", ".join(pedacos)


def montar_escalas(plano: dict, povoamento: dict, cam: dict) -> list[dict]:
    """Um plano vira TRES imagens: geral, medio e detalhe, de angulos diferentes.

    O geral herda a camera declarada do plano. O medio e o detalhe descem para as
    faixas da LEI DO DETALHAMENTO e giram o azimute, porque tres escalas do mesmo
    ponto de vista cortam como zoom.

    O DETALHE nao leva o povoamento nem as tendas: a 3-6 m nao cabe multidao no
    quadro, e mandar "roughly 55 visitors" num plano de mao e o jeito mais rapido
    de a IA encher o fundo de gente derretida.
    """
    pid = plano["id"]
    az = (cam.get("azimute_deg") or 0)
    alt = cam.get("alt_fim_m") or cam.get("alt_ini_m") or 20
    dist = cam.get("dist_fim_m") or cam.get("dist_ini_m") or 60
    medio_en, detalhe_en = RECORTE_EN.get(pid, ("", ""))
    gente = povoar_en(pid, povoamento)

    saida = []
    for esc in ESCALAS:
        lente = esc["lente_mm"] or plano.get("lente_mm")
        camera = esc["camera_en"].format(alt=alt, dist=dist)

        if esc["id"] == "geral":
            assunto, com_gente, com_tendas = CONTEUDO_EN.get(pid, ""), True, True
        elif esc["id"] == "medio":
            assunto, com_gente, com_tendas = medio_en, True, True
        else:
            assunto, com_gente, com_tendas = detalhe_en, False, False

        partes = [BASE_EN, assunto]
        if com_tendas:
            partes.append(TENDAS_EN)
        if com_gente and gente:
            partes.append(gente)
        partes += [LUZ_EN, f"{lente} mm lens {camera}",
                   "16:9 horizontal frame, 2560x1440"]

        saida.append({
            "escala": esc["id"],
            "rotulo": esc["rotulo"],
            "faixa_m": esc["faixa_m"],
            "papel": esc["papel"],
            "azimute_deg": round((az + esc["delta_azimute_deg"]) % 360, 1),
            "lente_mm": lente,
            "prompt": ". ".join(p for p in partes if p) + ".",
        })
    return saida


def montar_prompt(plano: dict, letreiro: dict | None, povoamento: dict) -> dict:
    pid = plano["id"]
    lente = plano.get("lente_mm")
    cam = plano.get("camera") or {}
    alt_i = cam.get("alt_ini_m")
    alt_f = cam.get("alt_fim_m")
    alt = alt_f if alt_f is not None else alt_i
    dist = cam.get("dist_fim_m") or cam.get("dist_ini_m")

    if alt is None:
        enquadramento = f"{lente} mm lens"
    elif alt <= 3:
        enquadramento = (f"{lente} mm lens at eye level, camera about {alt:.0f} m "
                         f"above the ground — a standing person's point of view")
    elif alt <= 18:
        enquadramento = (f"{lente} mm lens from a low drone, camera about "
                         f"{alt:.0f} m above the ground, roughly {dist:.0f} m from "
                         f"the subject, slight downward tilt")
    else:
        enquadramento = (f"{lente} mm lens from a drone about {alt:.0f} m above "
                         f"the ground, roughly {dist:.0f} m from the subject, "
                         f"looking down at a shallow angle — the ground plane "
                         f"still reads, this is not a top-down map view")

    gente = povoar_en(pid, povoamento)
    partes = [BASE_EN, CONTEUDO_EN.get(pid, ""), TENDAS_EN]
    if gente:
        partes.append(gente)
    partes += [LUZ_EN, enquadramento, "16:9 horizontal frame, 2560x1440"]
    imagem = ". ".join(p for p in partes if p) + "."

    mov = MOVIMENTO_EN.get(plano.get("movimento"), plano.get("movimento", ""))
    animacao = (
        f"{mov}. Duration {min(plano.get('duracao_s') or 0, TETO_CLIPE_S)} seconds. "
        f"The camera moves slowly and deliberately at a constant speed — this is "
        f"a drone shot, not a fast fly-through. Everything in the frame stays "
        f"physically consistent: people walk, flags and banners move in a light "
        f"breeze, animals shift naturally, the light does not change. "
        f"No morphing, no warping architecture, no drifting text, no zoom."
    )

    return {
        "imagem": imagem,
        "imagem_negativo": NEGATIVO_EN,
        "animacao": animacao,
        "escalas": montar_escalas(plano, povoamento, cam),
        "letreiro_na_tela": (letreiro or {}).get("texto"),
        "letreiro_apoio": (letreiro or {}).get("apoio"),
        "_letreiro_nota": "O letreiro NAO entra no prompt — entra na edicao, "
                          "depois. IA geradora escreve texto torto.",
    }


# --------------------------------------------------------------------- monta

def montar() -> dict:
    ia = _ler("quadros-ia.json")
    acervo = _ler("acervo-quadros.json")
    planos_j = _ler("planos.json")
    letreiros_j = _ler("letreiros.json")
    povoamento = _ler("povoamento.json")
    luz = _ler("luz.json")

    por_pasta = indexar_acervo(acervo)
    por_id = {p["id"]: p for p in planos_j["planos"]}
    letr = {l["plano"]: l for l in letreiros_j["letreiros"]}

    registros = []
    placas_por_plano: dict[str, list] = {}
    for local in ia["locais"]:
        placas_por_plano[local["plano"]] = [
            resolver(r, por_pasta, ia["raizes"]) for r in (local.get("reais") or [])]

    for local in ia["locais"]:
        pid = local["plano"]
        plano = por_id.get(pid, {})
        placas = placas_por_plano[pid]

        # Plano sem placa propria toma emprestada a do vizinho declarado. O
        # emprestimo fica MARCADO na placa -- ela nao vira placa dele.
        emprestimo = PLACAS_EMPRESTADAS.get(pid)
        if emprestimo and not placas:
            for origem in placas_por_plano.get(emprestimo["de"], []):
                if not origem["resolvido"]:
                    continue
                copia = dict(origem)
                copia["emprestada_de"] = emprestimo["de"]
                copia["porque_emprestada"] = emprestimo["porque"]
                copia["confianca"] = "emprestada"
                placas.append(copia)

        resolvidas = [p for p in placas if p["resolvido"]]

        # O estado do plano é uma conta, não uma opinião.
        if emprestimo and resolvidas:
            estado, porque = ("PLACA EMPRESTADA",
                              f"sem placa propria; usa a do {emprestimo['de']} por ordem dele")
        elif not placas:
            estado, porque = "SEM PLACA", "nenhuma referencia de imagem existe para este plano"
        elif not resolvidas:
            estado, porque = "PLACA NAO RESOLVE", "as referencias existem mas nenhuma virou arquivo em disco"
        elif local.get("bloqueio"):
            estado, porque = "PRONTO COM RESSALVA", "tem placa em disco, mas ha bloqueio registrado"
        else:
            estado, porque = "PRONTO", "tem placa em disco e nenhum bloqueio"

        registros.append({
            "plano": pid,
            "local": local["local"],
            "titulo_na_tela": (letr.get(pid) or {}).get("texto"),
            "diferencial": local.get("diferencial", False),
            "duracao_s": plano.get("duracao_s"),
            "lente_mm": plano.get("lente_mm"),
            "movimento": plano.get("movimento"),
            "altura_m": (plano.get("camera") or {}).get("alt_fim_m"),
            "estado": estado,
            "porque_o_estado": porque,
            "bloqueio": local.get("bloqueio"),
            "cena_3d": local.get("cena_3d"),
            "pasta_de_trabalho": f"out/plano-b/{pid}",
            "clipes": cortar_em_clipes(plano.get("duracao_s")),
            "placas": placas,
            "prompts": montar_prompt(plano, letr.get(pid), povoamento) if plano else None,
        })

    resumo = {
        "planos": len(registros),
        "imagens_a_gerar": sum(len((r["prompts"] or {}).get("escalas", [])) for r in registros),
        "clipes_a_gerar": sum(len(r["clipes"]) for r in registros),
        "planos_com_tres_tomadas": sum(1 for r in registros if len(r["clipes"]) == 3),
        "prontos": sum(1 for r in registros if r["estado"] == "PRONTO"),
        "com_ressalva": sum(1 for r in registros if r["estado"] == "PRONTO COM RESSALVA"),
        "sem_placa": sum(1 for r in registros if r["estado"] in ("SEM PLACA", "PLACA NAO RESOLVE")),
        "placas_resolvidas": sum(len([p for p in r["placas"] if p["resolvido"]]) for r in registros),
        "placas_totais": sum(len(r["placas"]) for r in registros),
        "duracao_total_s": round(sum(r["duracao_s"] or 0 for r in registros), 1),
    }

    return {
        "_o_que_isto_e": [
            "A esteira do PLANO B: footage real em disco -> imagem gerada por IA -> animacao.",
            "Uma linha por plano do filme, na ordem em que o filme roda.",
            "Nada aqui e gerado: sao os arquivos que ja existem, cruzados com os",
            "contratos ja escritos do projeto (planos, luz, povoamento, letreiros).",
        ],
        "_o_que_isto_nao_e": [
            "Nao e julgamento de imagem: nenhuma placa foi conferida a olho aqui.",
            "A escolha do quadro dentro do voo e por PROXIMIDADE DE TIMECODE contra a",
            "ancora de data/quadros-ia.json, com desempate pela etiqueta do acervo.",
            "Quadro escolhido assim pode estar errado — por isso a pagina mostra alternativas.",
        ],
        "_fontes": {
            "placas": "data/quadros-ia.json (as ancoras conferidas a olho em 15/08)",
            "arquivos": "data/acervo-quadros.json (9.980 quadros medidos)",
            "camera": "data/planos.json",
            "luz": f"data/luz.json — {luz['momento']['data']} {luz['momento']['hora']}",
            "gente_e_bicho": "data/povoamento.json (censo tirado do audio do cliente)",
            "letreiros": "data/letreiros.json",
        },
        "_restricoes_que_causam_rejeicao": [
            "Arena de rodeio SEM ARQUIBANCADA — so pista, camarotes dos lados, palco de frente.",
            "A palavra 'Kids' e proibida — use Fazendinha.",
            "Portal em conceito celeiro, versao economica.",
            "Quatro diferenciais com mais tela: Fazendinha, Rodeio, Cafe Colonial, Mercado do Produtor.",
        ],
        "_resumo": resumo,
        "planos": registros,
    }


# ---------------------------------------------------------------------- saida

def escrever_md(d: dict) -> str:
    r = d["_resumo"]
    L = []
    L.append("# PLANO B — a esteira, plano a plano\n")
    L.append("> Gerado por `scripts/plano_b.py`. Não editar à mão — editar a fonte e regerar.\n")
    L.append(f"**{r['planos']} planos · {r['duracao_total_s']} s de filme · "
             f"{r['placas_resolvidas']} de {r['placas_totais']} placas resolvem para arquivo em disco.**\n")
    L.append(f"{r['prontos']} prontos · {r['com_ressalva']} prontos com ressalva · "
             f"{r['sem_placa']} sem placa utilizável.\n")

    L.append("\n## O ciclo, por plano — sempre os mesmos cinco passos\n")
    L.append("| # | passo | onde |")
    L.append("|---|---|---|")
    L.append("| 1 | abrir a **placa** (o quadro real do footage) | caminho absoluto, na página ou neste arquivo |")
    L.append("| 2 | colar o **prompt de imagem** + a placa no gerador | prompt abaixo, por plano |")
    L.append("| 3 | baixar o que voltar | `out/plano-b/PXX/gerado/` |")
    L.append("| 4 | colar a imagem aprovada + o **prompt de movimento** no Seedance | prompt abaixo |")
    L.append("| 5 | baixar o clipe | `out/plano-b/PXX/video/` |")

    L.append("\n**A imagem gerada é a placa do plano seguinte quando os dois olham o mesmo lugar** "
             "(P14→P15, P19→P20, P02→P22). Isso é o que segura a continuidade do filme.\n")

    L.append("\n## As três escalas — ordem dele, 16/08\n")
    L.append("> *\"esse ficou plano geral, quero um mediano e um detalhes de cada "
             "bloco, com ângulos diferentes\"*\n")
    L.append("\nCada bloco rende **três imagens**, não uma. Não é escala nova "
             "inventada aqui: é a **LEI DO DETALHAMENTO** que o `FILA-CENA.md` já "
             "escreveu para a cena 3D, aplicada ao enquadramento da IA.\n")
    L.append("\n| escala | faixa | lente | ângulo | o que faz |")
    L.append("|---|---|---|---|---|")
    for esc in ESCALAS:
        gira = ("o azimute do plano" if not esc["delta_azimute_deg"]
                else f"{esc['delta_azimute_deg']:+d}° do plano")
        L.append(f"| **{esc['rotulo']}** | {esc['faixa_m']} | "
                 f"{esc['lente_mm'] or 'a do plano'} mm | {gira} | {esc['papel']} |")
    L.append("\n**O ângulo gira junto, e isso não é enfeite.** Três escalas do "
             "mesmo ponto de vista cortam como zoom, e zoom em corte parece erro. "
             "Ângulo diferente é o que faz o corte ler como outra câmera.\n")
    L.append("\n**O detalhe não leva multidão nem tenda no prompt.** A 3–6 m não "
             "cabe multidão no quadro, e mandar *\"roughly 55 visitors\"* num plano "
             "de mão é o jeito mais rápido de encher o fundo de gente derretida.\n")

    L.append("\n### Ângulo se pede na IMAGEM, nunca no vídeo\n")
    L.append("O Seedance move a câmera **dentro de um plano contínuo** — órbita, "
             "push-in, sobrevoo. Ele não corta. Pedir \"vários ângulos\" no prompt "
             "de vídeo devolve câmera à deriva ou morfagem.\n")
    L.append("\n**Corte é edição, não é movimento de câmera.** Cada ângulo é uma "
             "imagem própria → um clipe próprio → e o corte acontece na timeline.\n")

    L.append("\n## Quantas tomadas cada plano comporta\n")
    L.append(f"O Seedance não gera abaixo de **{PISO_CLIPE_S:.0f} s**. Então a "
             f"duração do plano decide quantas tomadas cabem: plano de 5 s comporta "
             f"uma, de 12 s comporta três. Picar 5 s em três dá 1,7 s cada — não é "
             f"corte, é piscada.\n")
    L.append("\n**Gere sempre as três imagens** de qualquer jeito: as que não "
             "viram clipe servem de escolha e de reserva se a primeira não fechar.\n")
    L.append("\n| tomadas | planos | dur. de cada |")
    L.append("|---|---|---|")
    from collections import defaultdict
    porn = defaultdict(list)
    for p in d["planos"]:
        porn[len(p["clipes"])].append(p)
    for n in sorted(porn, reverse=True):
        ids = " ".join(x["plano"] for x in porn[n])
        faixa = sorted({x["clipes"][0]["duracao_s"] for x in porn[n]})
        L.append(f"| **{n}** | {ids} | {faixa[0]} a {faixa[-1]} s |")
    L.append(f"\n**{r['imagens_a_gerar']} imagens** e **{r['clipes_a_gerar']} clipes** "
             f"para {r['planos']} planos.\n")
    L.append(f"\nDividido assim, **nenhuma tomada passa dos {TETO_CLIPE_S:.0f} s** — "
             f"o teto que obrigava P06, P08 e P14 a virar dois clipes encadeados "
             f"deixou de morder. A guarda continua no código porque duração muda.\n")

    L.append("\n## Ordem de trabalho — não é a ordem do filme\n")
    L.append("O filme roda P01→P22. O **trabalho** não: começa pelo que tem mais tela "
             "e pelo que pode travar.\n")

    ondas = [
        ("Onda 1 — os quatro diferenciais",
         "mais tempo de tela, e os três com material mais fino. Se algo falhar, falha aqui.",
         ["P06", "P08", "P14", "P15", "P19"]),
        ("Onda 2 — abertura e fechamento",
         "o portal abre e fecha o filme; a mesma imagem serve nos dois, espelhada.",
         ["P01", "P02", "P21", "P22"]),
        ("Onda 3 — o corpo do percurso",
         "planos de 5 a 11 s, o miolo. Rodam em série, sem decisão nova.",
         ["P03", "P04", "P05", "P07", "P09", "P10", "P11", "P12", "P13", "P16", "P18", "P20"]),
        ("Onda 4 — o plano de placa emprestada",
         "P17 é o único do filme sem imagem própria no acervo. Por ordem dele "
         "(16/08), usa a placa das máquinas do P16 pela implantação — mesma "
         "alameda, mesma hora — e o prompt troca trator por picape e barco. "
         "Vai por último porque é o único que depende de a troca convencer.",
         ["P17"]),
    ]
    por_id = {p["plano"]: p for p in d["planos"]}
    for titulo, nota, ids in ondas:
        L.append(f"\n### {titulo}\n")
        L.append(f"*{nota}*\n")
        L.append("| plano | local | dur. | estado |")
        L.append("|---|---|---|---|")
        for pid in ids:
            p = por_id.get(pid)
            if not p:
                continue
            L.append(f"| **{pid}** | {p['local']} | {p['duracao_s']} s | {p['estado']} |")

    L.append("\n---\n\n## Os planos, na ordem do filme\n")
    for p in d["planos"]:
        marca = " ·diferencial·" if p["diferencial"] else ""
        L.append(f"\n### {p['plano']} — {p['local']}{marca}\n")
        L.append(f"`{p['estado']}` · {p['duracao_s']} s · {p['lente_mm']} mm · "
                 f"{p['movimento']} · câmera a {p['altura_m']} m\n")
        if p["titulo_na_tela"]:
            L.append(f"**Letreiro na tela:** {p['titulo_na_tela']} "
                     f"— *entra na edição, nunca no prompt.*\n")
        if p["bloqueio"]:
            L.append(f"\n> **Bloqueio:** {p['bloqueio']}\n")

        L.append("\n**Placas** (abrir estas):\n")
        if not p["placas"]:
            L.append("\n*Nenhuma. Este plano não tem imagem de referência no projeto.*\n")
        for pl in p["placas"]:
            if pl["resolvido"]:
                extra = " · **EM PÉ, o filme é deitado**" if pl.get("em_pe") else ""
                L.append(f"\n- `{pl['arquivo']}`  \n"
                         f"  {pl['papel']} · {pl['confianca']} · {pl.get('periodo')} · "
                         f"nota {pl.get('nota')}{extra}  \n"
                         f"  *{pl['porque']}*")
                if pl.get("emprestada_de"):
                    L.append(f"  \n  **Emprestada do {pl['emprestada_de']}.** "
                             f"{pl['porque_emprestada']}")
            else:
                L.append(f"\n- **{pl['video']}** — não resolve: {pl['motivo_nao_resolvido']}  \n"
                         f"  *{pl['porque']}*")

        if p["prompts"]:
            for esc in p["prompts"]["escalas"]:
                L.append(f"\n\n**{esc['rotulo']}** · {esc['faixa_m']} · "
                         f"{esc['lente_mm']} mm · azimute {esc['azimute_deg']}° — "
                         f"*{esc['papel']}*\n")
                L.append("```")
                L.append(esc["prompt"])
                L.append("```")
            L.append("\n**Negativo (vale nas três):**\n")
            L.append("```")
            L.append(p["prompts"]["imagem_negativo"])
            L.append("```")
            L.append("\n**Prompt de movimento (Seedance):**\n")
            L.append("```")
            L.append(p["prompts"]["animacao"])
            L.append("```")
            L.append(f"\n> **{p['duracao_s']} s comportam {len(p['clipes'])} tomada"
                     f"{'s' if len(p['clipes']) > 1 else ''}:**\n>")
            for c in p["clipes"]:
                L.append(f"> - clipe {c['n']} · **{c['rotulo']}** · "
                         f"{c['de_s']}–{c['ate_s']} s ({c['duracao_s']} s) · "
                         f"primeiro quadro = {c['primeiro_quadro']}")
            if len(p["clipes"]) < len(ESCALAS):
                L.append(f">\n> As outras {len(ESCALAS) - len(p['clipes'])} imagens "
                         f"não viram clipe aqui — gere assim mesmo, servem de "
                         f"escolha e de reserva.")
            L.append(">")
        L.append(f"\n**Salvar em:** `{p['pasta_de_trabalho']}/gerado/` e "
                 f"`{p['pasta_de_trabalho']}/video/`\n")

    return "\n".join(L) + "\n"


def escrever_html(d: dict) -> str:
    r = d["_resumo"]
    cor = {"PRONTO": "#2f7d32", "PRONTO COM RESSALVA": "#b06000",
           "PLACA EMPRESTADA": "#7a5aa0",
           "SEM PLACA": "#a02020", "PLACA NAO RESOLVE": "#a02020"}
    e = html.escape

    cards = []
    for p in d["planos"]:
        placas = []
        for pl in p["placas"]:
            if pl["resolvido"]:
                # Sem miniatura quando a placa nao vem do acervo (foto do cliente).
                visual = (f'<img loading="lazy" src="../acervo/{e(pl["thumb"])}" alt="">'
                          if pl.get("thumb")
                          else '<div class="semthumb">foto do cliente<br>abrir do disco</div>')
                alts = "".join(
                    f'<button class="cam" data-c="{e(a["arquivo"])}" title="{e(a["arquivo"])}">'
                    f'alt {e(str(a.get("tc") or ""))}</button>'
                    for a in pl["alternativas"])
                pe = '<b class="av">EM PÉ</b>' if pl.get("em_pe") else ""
                empr = (f'<p class="empr"><b>Placa emprestada do {e(pl["emprestada_de"])}.</b> '
                        f'{e(pl["porque_emprestada"])}</p>'
                        if pl.get("emprestada_de") else "")
                placas.append(f"""
        <div class="placa">
          {visual}
          <div class="pinfo">
            <div class="tags"><b>{e(pl['papel'] or '')}</b> · {e(pl['confianca'] or '')}
              · {e(pl.get('periodo') or '')} · nota {e(str(pl.get('nota') or ''))} {pe}</div>
            <button class="cam principal" data-c="{e(pl['arquivo'])}">copiar caminho</button>
            {alts}
            <code>{e(pl['arquivo'])}</code>
            {empr}
            <p>{e(pl['porque'] or '')}</p>
          </div>
        </div>""")
            else:
                placas.append(f"""
        <div class="placa nao">
          <div class="semthumb">sem arquivo</div>
          <div class="pinfo">
            <div class="tags"><b>{e(pl['video'])}</b></div>
            <p class="alerta">não resolve: {e(pl['motivo_nao_resolvido'] or '')}</p>
            <p>{e(pl['porque'] or '')}</p>
          </div>
        </div>""")
        if not placas:
            placas = ['<p class="alerta">Nenhuma placa. Este plano não tem imagem de referência.</p>']

        pr = p["prompts"] or {}
        escalas_html = "".join(
            f'<div class="pbox esc-{esc["escala"]}">'
            f'<h3><span class="escrot">{e(esc["rotulo"])}</span> '
            f'{esc["faixa_m"]} · {esc["lente_mm"]} mm · azimute {esc["azimute_deg"]}° '
            f'<button class="cop">copiar</button></h3>'
            f'<p class="escpapel">{e(esc["papel"])}</p>'
            f'<pre>{e(esc["prompt"])}</pre></div>'
            for esc in pr.get("escalas", []))
        bloq = (f'<p class="bloq"><b>Bloqueio:</b> {e(p["bloqueio"])}</p>'
                if p["bloqueio"] else "")
        linhas = "".join(
            f"<li>clipe {c['n']} · <b>{e(c['rotulo'])}</b> · "
            f"{c['de_s']}–{c['ate_s']} s ({c['duracao_s']} s) · "
            f"da imagem <b>{e(c['escala'])}</b></li>"
            for c in p["clipes"])
        sobra = len(ESCALAS) - len(p["clipes"])
        corte = (f'<div class="corte"><b>{p["duracao_s"]} s comportam '
                 f'{len(p["clipes"])} tomada{"s" if len(p["clipes"]) > 1 else ""}</b>'
                 f'<ul>{linhas}</ul>'
                 + (f'<i>As outras {sobra} imagens não viram clipe aqui — gere '
                    f'assim mesmo, servem de escolha e de reserva.</i>'
                    if sobra > 0 else '')
                 + '</div>') if p["clipes"] else ""
        letr = (f'<p class="letr"><b>Letreiro:</b> {e(p["titulo_na_tela"])} '
                f'<i>— entra na edição, nunca no prompt</i></p>'
                if p["titulo_na_tela"] else "")

        cards.append(f"""
    <section class="card" id="{p['plano']}" data-estado="{e(p['estado'])}"
             data-dif="{'1' if p['diferencial'] else '0'}">
      <header>
        <h2>{p['plano']} — {e(p['local'])}</h2>
        <span class="sel" style="background:{cor.get(p['estado'],'#555')}">{e(p['estado'])}</span>
        {'<span class="dif">diferencial</span>' if p['diferencial'] else ''}
      </header>
      <p class="meta">{p['duracao_s']} s · {p['lente_mm']} mm · {e(p['movimento'] or '')}
         · câmera a {p['altura_m']} m · salvar em <code>out/plano-b/{p['plano']}/</code></p>
      {letr}{bloq}
      <div class="placas">{''.join(placas)}</div>
      <div class="prompts">
        {escalas_html}
        <div class="pbox"><h3>negativo — vale nas três <button class="cop">copiar</button></h3>
          <pre>{e(pr.get('imagem_negativo',''))}</pre></div>
        <div class="pbox"><h3>movimento — Seedance <button class="cop">copiar</button></h3>
          <pre>{e(pr.get('animacao',''))}</pre>{corte}</div>
      </div>
    </section>""")

    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>PLANO B — AGROSHOW 2026</title>
<style>
 :root {{ --bg:#14140f; --pa:#1e1e18; --tx:#e8e4d8; --mu:#9a9484; --ln:#33322a; }}
 * {{ box-sizing:border-box }}
 body {{ margin:0; background:var(--bg); color:var(--tx);
   font:15px/1.55 -apple-system,Segoe UI,Roboto,sans-serif }}
 header.topo {{ position:sticky; top:0; z-index:9; background:var(--pa);
   border-bottom:1px solid var(--ln); padding:12px 20px }}
 h1 {{ margin:0 0 4px; font-size:18px }}
 .resumo {{ color:var(--mu); font-size:13px }}
 .filtros {{ margin-top:8px; display:flex; gap:6px; flex-wrap:wrap }}
 .filtros button {{ background:#2a2a22; color:var(--tx); border:1px solid var(--ln);
   border-radius:4px; padding:4px 10px; cursor:pointer; font-size:13px }}
 .filtros button.on {{ background:#4a4a38; border-color:#6a6a50 }}
 main {{ padding:20px; max-width:1200px; margin:0 auto }}
 .card {{ background:var(--pa); border:1px solid var(--ln); border-radius:8px;
   padding:16px; margin-bottom:18px }}
 .card header {{ display:flex; gap:10px; align-items:center; flex-wrap:wrap }}
 h2 {{ margin:0; font-size:17px }}
 .sel,.dif {{ font-size:11px; padding:2px 8px; border-radius:10px; color:#fff }}
 .dif {{ background:#6a4a9a }}
 .meta {{ color:var(--mu); font-size:13px; margin:6px 0 }}
 .bloq {{ background:#3a2a10; border-left:3px solid #b06000; padding:8px 10px;
   margin:8px 0; font-size:13px }}
 .letr {{ font-size:13px; color:#d8cfa8 }}
 .placas {{ display:grid; gap:10px; margin:12px 0 }}
 .placa {{ display:flex; gap:12px; background:#191914; border:1px solid var(--ln);
   border-radius:6px; padding:10px }}
 .placa img,.semthumb {{ width:210px; height:118px; object-fit:cover; flex:none;
   border-radius:4px; background:#000 }}
 .semthumb {{ display:flex; align-items:center; justify-content:center;
   color:var(--mu); font-size:12px; border:1px dashed var(--ln) }}
 .pinfo {{ min-width:0; flex:1 }}
 .tags {{ font-size:12px; color:var(--mu); margin-bottom:6px }}
 .av {{ color:#e0a020 }}
 .placa code {{ display:block; font-size:11px; color:#8fae8f; word-break:break-all;
   margin:6px 0 }}
 .placa p {{ font-size:12.5px; color:var(--mu); margin:0 }}
 .alerta {{ color:#e07070 }}
 button.cam,button.cop {{ background:#2a2a22; color:var(--tx); border:1px solid var(--ln);
   border-radius:4px; padding:3px 9px; cursor:pointer; font-size:12px; margin-right:5px }}
 button.principal {{ background:#3a4a2a; border-color:#5a7a3a }}
 button.copiado {{ background:#2f7d32 !important }}
 .prompts {{ display:grid; gap:10px }}
 .pbox h3 {{ font-size:12px; color:var(--mu); text-transform:uppercase;
   letter-spacing:.06em; margin:0 0 5px; display:flex; align-items:center; gap:8px }}
 pre {{ background:#101008; border:1px solid var(--ln); border-radius:5px; padding:10px;
   margin:0; white-space:pre-wrap; font-size:12.5px; color:#cfc9b4 }}
 .escrot {{ background:#3a4a2a; color:#d8e8c0; padding:2px 8px; border-radius:3px;
   letter-spacing:.04em }}
 .esc-medio .escrot {{ background:#2a4055; color:#c8dcf0 }}
 .esc-detalhe .escrot {{ background:#553a2a; color:#f0d8c0 }}
 .escpapel {{ font-size:12px; color:var(--mu); margin:0 0 5px; font-style:italic }}
 .empr {{ background:#2a2038; border-left:3px solid #7a5aa0; padding:6px 9px;
   margin:6px 0; font-size:12px; color:#cfc0e0; border-radius:0 4px 4px 0 }}
 .corte {{ background:#3a2a10; border-left:3px solid #b06000; padding:8px 10px;
   margin-top:8px; font-size:12.5px; border-radius:0 4px 4px 0 }}
 .corte ul {{ margin:6px 0 0; padding-left:18px; color:var(--mu) }}
 .oculto {{ display:none }}
</style></head><body>
<header class="topo">
  <h1>PLANO B — AGROSHOW 2026 · a esteira de quadros</h1>
  <div class="resumo">{r['planos']} planos · {r['duracao_total_s']} s ·
    {r['placas_resolvidas']}/{r['placas_totais']} placas em disco ·
    {r['prontos']} prontos · {r['com_ressalva']} com ressalva ·
    {r['sem_placa']} sem placa</div>
  <div class="filtros">
    <button class="on" data-f="todos">todos</button>
    <button data-f="dif">só diferenciais</button>
    <button data-f="ok">prontos</button>
    <button data-f="prob">com ressalva ou sem placa</button>
  </div>
</header>
<main>{''.join(cards)}</main>
<script>
document.addEventListener('click', function(ev) {{
  var b = ev.target.closest('button'); if (!b) return;
  if (b.classList.contains('cam') || b.classList.contains('cop')) {{
    var t = b.classList.contains('cam') ? b.dataset.c
          : b.closest('.pbox').querySelector('pre').textContent;
    navigator.clipboard.writeText(t).then(function() {{
      var v = b.textContent; b.textContent = 'copiado'; b.classList.add('copiado');
      setTimeout(function(){{ b.textContent = v; b.classList.remove('copiado'); }}, 1100);
    }});
    return;
  }}
  if (b.dataset.f) {{
    document.querySelectorAll('.filtros button').forEach(function(x){{ x.classList.remove('on'); }});
    b.classList.add('on');
    var f = b.dataset.f;
    document.querySelectorAll('.card').forEach(function(c) {{
      var e = c.dataset.estado, mostra =
        f === 'todos' ? true :
        f === 'dif'   ? c.dataset.dif === '1' :
        f === 'ok'    ? e === 'PRONTO' :
                        e !== 'PRONTO';
      c.classList.toggle('oculto', !mostra);
    }});
  }}
}});
</script></body></html>
"""


def criar_pastas(d: dict) -> int:
    n = 0
    for p in d["planos"]:
        base = RAIZ / p["pasta_de_trabalho"]
        for sub in ("placa", "gerado", "video"):
            (base / sub).mkdir(parents=True, exist_ok=True)
        leia = base / "LEIA.md"
        placas = "\n".join(
            f"- `{pl['arquivo']}`" if pl["resolvido"]
            else f"- (não resolve) {pl['video']}"
            for pl in p["placas"]) or "- nenhuma"
        pr = p["prompts"] or {}
        leia.write_text(
            f"# {p['plano']} — {p['local']}\n\n"
            f"{p['estado']} · {p['duracao_s']} s · {p['lente_mm']} mm · {p['movimento']}\n\n"
            f"## Placas\n{placas}\n\n"
            + "".join(
                f"## {esc['rotulo']} · {esc['faixa_m']} · {esc['lente_mm']} mm · "
                f"azimute {esc['azimute_deg']}°\n{esc['papel']}\n\n"
                f"```\n{esc['prompt']}\n```\n\n"
                for esc in pr.get("escalas", []))
            + f"## Negativo (vale nas tres)\n```\n{pr.get('imagem_negativo','')}\n```\n\n"
            f"## Movimento (Seedance)\n```\n{pr.get('animacao','')}\n```\n\n"
            + (f"### {p['duracao_s']} s comportam {len(p['clipes'])} tomada(s)\n\n"
               + "".join(f"- clipe {c['n']} · {c['rotulo']} · "
                         f"{c['de_s']}–{c['ate_s']} s ({c['duracao_s']} s) · "
                         f"primeiro quadro = {c['primeiro_quadro']}\n"
                         for c in p["clipes"])
               + ("" if len(p["clipes"]) >= len(ESCALAS) else
                  f"\nAs outras {len(ESCALAS) - len(p['clipes'])} imagens nao viram "
                  f"clipe aqui. Gere assim mesmo: servem de escolha e de reserva.\n")
               + "\n" if p["clipes"] else "")
            + f"## Onde salvar\n"
            f"- `placa/` — cópia do quadro real, se você quiser tudo junto\n"
            f"- `gerado/` — a imagem que voltar da IA\n"
            f"- `video/` — o clipe que voltar do Seedance\n",
            encoding="utf-8")
        n += 1
    return n


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--criar-pastas", action="store_true",
                    help="cria out/plano-b/PXX/{placa,gerado,video} e o LEIA.md de cada")
    ap.add_argument("--plano", help="imprime só um plano no terminal, sem escrever nada")
    args = ap.parse_args()

    d = montar()

    if args.plano:
        p = next((x for x in d["planos"] if x["plano"] == args.plano.upper()), None)
        if not p:
            print(f"plano {args.plano} nao existe", file=sys.stderr)
            return 2
        print(json.dumps(p, ensure_ascii=False, indent=2))
        return 0

    SAIDA.mkdir(parents=True, exist_ok=True)
    (DADOS / "plano-b.json").write_text(
        json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    (RAIZ / "PLANO-B.md").write_text(escrever_md(d), encoding="utf-8")
    (SAIDA / "PLANO-B.html").write_text(escrever_html(d), encoding="utf-8")

    r = d["_resumo"]
    print(f"data/plano-b.json        {r['planos']} planos")
    print(f"PLANO-B.md               o runbook, na ordem de trabalho")
    print(f"out/plano-b/PLANO-B.html a pagina — dois cliques, offline")
    print(f"  placas em disco: {r['placas_resolvidas']}/{r['placas_totais']}"
          f"  ·  prontos {r['prontos']}  ressalva {r['com_ressalva']}"
          f"  sem placa {r['sem_placa']}")

    if args.criar_pastas:
        print(f"  pastas criadas: {criar_pastas(d)} x out/plano-b/PXX/"
              f"{{placa,gerado,video}} + LEIA.md")

    # Portao: se menos de 80% das placas resolvem, algo quebrou na leitura.
    if r["placas_totais"] and r["placas_resolvidas"] / r["placas_totais"] < 0.8:
        print("PORTAO VERMELHO: menos de 80% das placas resolvem para arquivo",
              file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
