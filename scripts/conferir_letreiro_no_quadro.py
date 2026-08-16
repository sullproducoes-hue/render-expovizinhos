#!/usr/bin/env python3
"""Portao: o letreiro de cada plano tem de CABER no quadro daquele plano.

O `letreiros.py` ja conferia o TAMANHO da letra (a regra dos 8% / 4% do painel
LED). Isso e' outra pergunta, e ela nao estava sendo feita: o texto cabe no
enquadramento? Nos stills de 15/08 o P02 e o P22 sairam com a frase cortada nas
duas bordas -- e o P22 e o plano que fecha o filme.

Por que so' apareceu agora: o portal mudou de posicao, girou 92 graus e passou
de 20 para 35 m de largura por ordem dele. A camera e o letreiro ficaram onde
estavam. Nenhum portao anterior olhava essa combinacao.

Mede projetando os cantos do letreiro na camera do plano
(`world_to_camera_view`) e comparando com a area de seguranca de 90% que a
entrega exige. A proporcao sai da cena, nao esta escrita aqui: em 15/08 ela
passou de 2:1 para 16:9 por ordem dele (DECISOES.md D044), e numero de entrega
copiado em dois arquivos e' numero que um dia diverge.

Este portao mede o RESULTADO; `letreiros.py` mede a INTENCAO, antes de
construir, e aborta o build. Os dois existem de proposito: o de la' pode errar
a conta, o de ca' olha o que ficou na cena. Quando os dois concordam, a prova
vale.

Desde 15/08 ele confere o quadro do MEIO e tambem as duas pontas do plano. O
meio sozinho nao pega push-in: no P02 o letreiro cabia no comeco e estourava no
fim, e a media dos dois passava.

Uso:
    blender out/cena.blend --background --python scripts/conferir_letreiro_no_quadro.py
"""

import sys
from pathlib import Path

import bpy
import mathutils
from bpy_extras.object_utils import world_to_camera_view

RAIZ = Path(__file__).resolve().parent.parent
SEGURANCA = 0.90          # 90% da tela, conforme a especificacao de entrega


def cantos_mundo(o):
    return [o.matrix_world @ mathutils.Vector(c) for c in o.bound_box]


def main():
    cena = bpy.context.scene
    marcas = sorted(cena.timeline_markers, key=lambda m: m.frame)
    if not marcas:
        raise SystemExit("cena sem marcador de plano")

    # Desde 15/08 o letreiro nao e' so' texto: tem tabua, faixa, chapa,
    # corrente e montante, e todos aparecem em quadro. Medir so' as letras
    # aprovaria uma prancha cortada ao meio com o texto inteiro dentro.
    PREFIXOS = ("Letreiro_", "Apoio_", "Tabua_", "Faixa_", "Chapa_",
                "Prancha_", "Corrente_", "Montante_")
    por_plano = {}
    for o in bpy.data.objects:
        if o.type not in ("FONT", "MESH"):
            continue
        if not o.name.startswith(PREFIXOS):
            continue
        partes = o.name.split("_")
        plano = next((p for p in partes if p.startswith("P") and p[1:].isdigit()),
                     partes[-1])
        por_plano.setdefault(plano, []).append(o)

    margem = (1.0 - SEGURANCA) / 2.0
    lo, hi = margem, 1.0 - margem

    print(f"{'plano':<7} {'quadro':>7}  {'x':>15}  {'y':>15}   estado")
    ruins = []
    for i, m in enumerate(marcas):
        prox = marcas[i + 1].frame if i + 1 < len(marcas) else cena.frame_end
        plano = (m.camera.name if m.camera else m.name).replace("CAM_", "")
        alvos = por_plano.get(plano)
        if not alvos:
            continue
        cam = m.camera
        if cam is None:
            continue

        # Comeco, meio e fim. Num push-in o pior instante e' sempre uma ponta,
        # e ate 15/08 este portao so' olhava o meio.
        instantes = sorted({m.frame + 1, (m.frame + prox) // 2, prox - 1})
        pior = None
        for quadro in instantes:
            cena.frame_set(quadro)
            # A camera dos planos aponta por constraint TRACK_TO, e constraint
            # so' existe depois que o depsgraph avalia. Lendo `cam.matrix_world`
            # cru, a POSICAO vinha certa e a MIRA vinha do quadro anterior --
            # e' o bastante para o portao inventar "atras da camera" num
            # letreiro que esta na frente. Custou uma rodada inteira de numero
            # sem pe nem cabeca (57.929% da largura).
            dg = bpy.context.evaluated_depsgraph_get()
            cam_av = cam.evaluated_get(dg)
            xs, ys, atras = [], [], False
            for o in alvos:
                # Desde 15/08 o letreiro acende so' no trecho em que cabe no
                # quadro, e objeto escondido nao e' avaliado pelo depsgraph --
                # a matriz que sobra e' velha. Medir quadro apagado devolve
                # numero inventado (ja devolveu 57.929% de largura). Se nao
                # aparece, nao ha o que conferir.
                if o.hide_render:
                    continue
                for p in cantos_mundo(o.evaluated_get(dg)):
                    c = world_to_camera_view(cena, cam_av, p)
                    xs.append(c.x)
                    ys.append(c.y)
                    if c.z <= 0:
                        atras = True
            if not xs:
                continue          # letreiro apagado neste instante
            x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
            if atras:
                estado, grau = "ATRAS DA CAMERA", 4
            elif x0 < 0.0 or x1 > 1.0:
                estado, grau = "CORTADO NA BORDA", 3
            elif x0 < lo or x1 > hi or y0 < lo or y1 > hi:
                estado, grau = "fora da area de 90%", 2
            else:
                estado, grau = "OK", 1
            if pior is None or grau > pior[0]:
                pior = (grau, quadro, x0, x1, y0, y1, estado)

        if pior is None:
            print(f"{plano:<7} {'-':>7}  {'apagado o plano inteiro':>36}")
            ruins.append((plano, "APAGADO O PLANO INTEIRO", 0.0, 0.0))
            continue
        _, quadro, x0, x1, y0, y1, estado = pior
        if estado != "OK":
            ruins.append((plano, estado, x0, x1))
        print(f"{plano:<7} {quadro:>7}  {x0:6.2f}..{x1:6.2f}  {y0:6.2f}..{y1:6.2f}   {estado}")

    print(f"\n{len(ruins)} de {len(por_plano)} planos com letreiro fora do quadro")
    for plano, estado, x0, x1 in ruins:
        largura = x1 - x0
        print(f"  {plano}: {estado} -- o texto ocupa {largura*100:.0f}% da largura "
              f"do quadro (cabe ate 90%)")
    if ruins:
        print("\nNao e' erro de tipografia: e' a camera. O tamanho da letra ja "
              "passa\nna regra dos 8%; o que nao cabe e' a LINHA inteira no "
              "enquadramento.")


if __name__ == "__main__":
    main()
