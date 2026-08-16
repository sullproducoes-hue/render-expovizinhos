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
    """Um plano vira N clipes que cabem no teto da IA de video.

    Divide em partes iguais -- parte curta demais no fim fica com cara de
    sobra, e o corte aparece. Encadeia pelo ultimo quadro: o clipe seguinte
    nasce do frame final do anterior, que e o que segura a continuidade.
    """
    if not duracao_s:
        return []
    if duracao_s <= TETO_CLIPE_S:
        return [{"n": 1, "de_s": 0.0, "ate_s": duracao_s,
                 "duracao_s": round(duracao_s, 1), "primeiro_quadro": "a imagem gerada do plano"}]
    n = int(-(-duracao_s // TETO_CLIPE_S))          # teto da divisao
    passo = duracao_s / n
    return [{
        "n": i + 1,
        "de_s": round(i * passo, 1),
        "ate_s": round((i + 1) * passo, 1),
        "duracao_s": round(passo, 1),
        "primeiro_quadro": ("a imagem gerada do plano" if i == 0
                            else f"o ULTIMO quadro do clipe {i}"),
    } for i in range(n)]


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
        "clipes_a_gerar": sum(len(r["clipes"]) for r in registros),
        "planos_que_partem_em_dois": sum(1 for r in registros if len(r["clipes"]) > 1),
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

    L.append(f"\n## O teto de {TETO_CLIPE_S:.0f} s — três planos não cabem num clipe só\n")
    L.append(f"A IA de vídeo (Seedance V1.5 Pro) gera de {PISO_CLIPE_S:.0f} a "
             f"{TETO_CLIPE_S:.0f} s por clipe. **{r['planos_que_partem_em_dois']} planos passam "
             f"disso, e os três são diferenciais** — justamente os que têm mais tela.\n")
    L.append("\nEles não viram um prompt: viram dois, e o segundo começa no "
             "**último quadro do primeiro**. Sem isso o corte aparece.\n")
    L.append("\n| plano | dur. total | vira | cada clipe |")
    L.append("|---|---|---|---|")
    for p in d["planos"]:
        if len(p["clipes"]) > 1:
            L.append(f"| **{p['plano']}** {p['local'][:28]} | {p['duracao_s']} s | "
                     f"{len(p['clipes'])} clipes | {p['clipes'][0]['duracao_s']} s cada |")
    L.append(f"\nTotal a gerar: **{r['clipes_a_gerar']} clipes** para "
             f"{r['planos']} planos.\n")

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
            L.append("\n\n**Prompt de imagem:**\n")
            L.append("```")
            L.append(p["prompts"]["imagem"])
            L.append("```")
            L.append("\n**Negativo:**\n")
            L.append("```")
            L.append(p["prompts"]["imagem_negativo"])
            L.append("```")
            L.append("\n**Prompt de movimento (Seedance):**\n")
            L.append("```")
            L.append(p["prompts"]["animacao"])
            L.append("```")
            if len(p["clipes"]) > 1:
                L.append(f"\n> **Este plano não cabe num clipe só** ({p['duracao_s']} s "
                         f"contra o teto de {TETO_CLIPE_S:.0f} s). São "
                         f"{len(p['clipes'])} gerações com o mesmo prompt acima:\n>")
                for c in p["clipes"]:
                    L.append(f"> - clipe {c['n']} · {c['de_s']}–{c['ate_s']} s · "
                             f"primeiro quadro = {c['primeiro_quadro']}")
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
        bloq = (f'<p class="bloq"><b>Bloqueio:</b> {e(p["bloqueio"])}</p>'
                if p["bloqueio"] else "")
        corte = ""
        if len(p["clipes"]) > 1:
            linhas = "".join(
                f"<li>clipe {c['n']} · {c['de_s']}–{c['ate_s']} s · "
                f"primeiro quadro = <b>{e(c['primeiro_quadro'])}</b></li>"
                for c in p["clipes"])
            corte = (f'<div class="corte"><b>Não cabe num clipe só</b> — '
                     f'{p["duracao_s"]} s contra o teto de {TETO_CLIPE_S:.0f} s. '
                     f'{len(p["clipes"])} gerações com este mesmo prompt:'
                     f'<ul>{linhas}</ul></div>')
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
        <div class="pbox"><h3>prompt de imagem <button class="cop">copiar</button></h3>
          <pre>{e(pr.get('imagem',''))}</pre></div>
        <div class="pbox"><h3>negativo <button class="cop">copiar</button></h3>
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
            f"## Prompt de imagem\n```\n{pr.get('imagem','')}\n```\n\n"
            f"## Negativo\n```\n{pr.get('imagem_negativo','')}\n```\n\n"
            f"## Movimento (Seedance)\n```\n{pr.get('animacao','')}\n```\n\n"
            + ("" if len(p["clipes"]) <= 1 else
               f"### Este plano vira {len(p['clipes'])} clipes\n"
               f"{p['duracao_s']} s nao cabem no teto de {TETO_CLIPE_S:.0f} s.\n\n"
               + "".join(f"- clipe {c['n']} · {c['de_s']}–{c['ate_s']} s · "
                         f"primeiro quadro = {c['primeiro_quadro']}\n"
                         for c in p["clipes"]) + "\n")
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
