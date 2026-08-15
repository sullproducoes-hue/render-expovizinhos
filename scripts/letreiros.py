#!/usr/bin/env python3
"""Titulos e letreiros -- passo 3 do fluxo de 5 passos do Natan.

O texto sai do audio dele, palavra por palavra (`data/letreiros.json`, com o
minuto citado em cada linha). O que este arquivo faz e resolver o TAMANHO, e
isso nao e gosto: e a regra de entrega dele.

    "Titulo com no minimo 8% da altura do quadro; apoio nunca abaixo de 4%"

Um texto de altura H, a distancia D, com lente f, ocupa na vertical do quadro:

    fracao = H * f / (D * sensor_vertical_mm)

O sensor do Blender e 36 mm na horizontal; em 2:1 o vertical e 18 mm. Logo

    H = fracao * D * 18 / f

e cada letreiro e dimensionado pelo PLANO que o mostra -- `data/planos.json` ja
declara alvo, lente e distancia dos 22. **Nenhum numero aqui foi escolhido a
olho**, e `--conferir` imprime a fracao obtida de cada um e ACUSA quem cair
abaixo da regra.

O modo padrao e `billboard`: o texto encara a camera daquele plano. E a leitura
de MAPA, que e o que o filme e -- e e o unico modo que garante os 8% em todos os
planos, porque texto girado em relacao a camera encolhe na tela e a conta acima
deixa de valer.
"""

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector

import terreno

RAIZ = Path(__file__).resolve().parent.parent
CONTRATO = RAIZ / "data" / "letreiros.json"

SENSOR_VERTICAL_MM = 18.0   # 36 mm de largura em 2:1


def _fonte(caminho):
    p = Path(caminho)
    if not p.exists():
        print(f"  AVISO: fonte nao encontrada em {p} -- letreiro sai na fonte "
              f"padrao do Blender, que NAO e a declarada no contrato")
        return None
    for f in bpy.data.fonts:
        if f.filepath == str(p):
            return f
    return bpy.data.fonts.load(str(p))


def _material(cont):
    mat = bpy.data.materials.get("MAT_LETREIRO")
    if mat:
        return mat
    cor = cont["cor"]["texto"]
    mat = bpy.data.materials.new("MAT_LETREIRO")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*cor, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.6
    # Emissao fraca por um motivo medido, nao por estilo: varios planos sao
    # CONTRALUZ com o sol a 10 graus. Texto so difuso, de costas para o sol,
    # vira silhueta cinza e a regra dos 8% nao salva o que nao se le.
    if "Emission Color" in bsdf.inputs:
        bsdf.inputs["Emission Color"].default_value = (*cor, 1.0)
        bsdf.inputs["Emission Strength"].default_value = cont["cor"]["emissao"]
    mat.diffuse_color = (*cor, 1.0)
    return mat


def _texto(nome, conteudo, altura_m, fonte, mat, col):
    dados = bpy.data.curves.new(nome, type="FONT")
    dados.body = conteudo
    if fonte:
        dados.font = fonte
    dados.align_x = "CENTER"
    dados.align_y = "CENTER"
    # size = altura da CAIXA da fonte, nao da maiuscula. Dar extrude zero e
    # de proposito: letra com volume pega sombra propria e suja a leitura no
    # painel de 1379 px.
    dados.size = altura_m
    dados.extrude = 0.0
    obj = bpy.data.objects.new(nome, dados)
    obj.data.materials.append(mat)
    col.objects.link(obj)
    return obj


def _so_no_proprio_plano(obj, plano, fps, respiro_s=0.5):
    """Faz o letreiro existir SO durante o plano dele.

    Sem isto os 16 letreiros ficam na cena o filme inteiro e aparecem
    flutuando ao fundo dos outros planos -- que e o defeito que a primeira
    prova mostrou. O texto de um plano nao pode contaminar o vizinho.

    Meio segundo de respiro em cada ponta: o letreiro entra depois que o corte
    aconteceu e sai antes do proximo. Ligar exatamente no quadro do corte faz o
    texto piscar junto com a troca de camera, que le como falha de render.
    """
    respiro = max(1, int(round(respiro_s * fps)))
    ini = plano["_quadro_ini"] + respiro
    fim = plano["_quadro_fim"] - respiro
    if fim <= ini:                      # plano curto demais para respiro
        ini, fim = plano["_quadro_ini"], plano["_quadro_fim"]

    # As chaves ficam em quadros ADJACENTES (ini-1 e ini; fim e fim+1), e por
    # isso nao e preciso forcar interpolacao CONSTANT: nenhum quadro
    # renderizado cai entre duas chaves vizinhas, entao a curva entre elas
    # nunca e amostrada. (A primeira versao tentava percorrer
    # `action.fcurves`, que o Blender 5.2 nao expoe mais -- as actions viraram
    # slotted. O loop era desnecessario desde o comeco.)
    for quadro, oculto in ((ini - 1, True), (ini, False),
                           (fim, False), (fim + 1, True)):
        obj.hide_render = oculto
        obj.hide_viewport = oculto
        obj.keyframe_insert("hide_render", frame=quadro)
        obj.keyframe_insert("hide_viewport", frame=quadro)


def construir(dados_mapa, col_pai, centro_arena, pacote_planos):
    """Devolve (postos, reprovados_na_regra)."""
    if not CONTRATO.exists():
        return 0, 0

    cont = json.loads(CONTRATO.read_text(encoding="utf-8"))
    fonte = _fonte(cont["tipografia"]["arquivo"])
    mat = _material(cont)
    escala = cont["escala_por_nivel"]

    col = bpy.data.collections.new("LETREIROS")
    col_pai.children.link(col)

    por_id = {p["id"]: p for p in pacote_planos["planos"]}
    postos, fora_da_regra = 0, []
    relatorio = []

    for item in cont["letreiros"]:
        plano = por_id.get(item["plano"])
        if plano is None:
            print(f"  aviso: {item['plano']} nao existe em planos.json -- "
                  f"'{item['texto'][:30]}' nao foi posto")
            continue

        alvo = plano.get("alvo", {})
        p = terreno.ponto_da_zona(dados_mapa, alvo.get("rotulo", ""),
                                  alvo.get("ocorrencia", 0))
        if p is None:
            print(f"  aviso: alvo de {item['plano']} nao existe na planta")
            continue

        cam = plano["camera"]
        f = float(plano["lente_mm"])
        # A MAIOR das duas distancias e a que manda, e o motivo e a regra:
        # "no minimo 8%" tem de valer o plano INTEIRO, e o texto e menor na
        # tela quando a camera esta mais longe. Num push-in isso e o inicio;
        # num afastamento, o fim. `max` resolve os dois sem caso especial.
        d = float(max(cam["dist_ini_m"], cam["dist_fim_m"]))

        az = math.radians(cam["azimute_deg"])
        z_base = terreno.elevacao(p[0], p[1], centro_arena)
        pos_cam = Vector((p[0] + d * math.cos(az), p[1] + d * math.sin(az),
                          z_base + float(cam.get("alt_fim_m", 10))))

        # O letreiro nao fica EM CIMA do alvo: ele vem uma fracao do caminho na
        # direcao da camera. Motivo medido, nao gosto -- na primeira prova o
        # letreiro da Fazendinha saiu METADE TAPADO POR UMA ARVORE, porque
        # estava plantado no rotulo, atras do bosque que o proprio plano
        # atravessa. Trazido para a frente, ele passa na frente da vegetacao.
        #
        # E o tamanho e recalculado pela distancia NOVA, entao a fracao na tela
        # continua sendo exatamente a declarada. Aproximar sem refazer a conta
        # deixaria todo letreiro maior que a regra.
        aprox = float(item.get("aproximacao", cont.get("aproximacao", 0.45)))
        d_efetiva = d * (1.0 - aprox)

        frac_t = escala[item["nivel"]]["fracao_da_altura"]
        h_titulo = frac_t * d_efetiva * SENSOR_VERTICAL_MM / f

        px = p[0] + (pos_cam.x - p[0]) * aprox
        py = p[1] + (pos_cam.y - p[1]) * aprox
        z_local = terreno.elevacao(px, py, centro_arena)
        # A altura segue a MIRA do plano, e nao uma cota livre alta. Tentei
        # 17 m para "passar por cima da copa" e o letreiro saiu FORA DO QUADRO:
        # a camera olha para `mira_alt_m`, entao texto muito acima disso nao
        # esta no enquadramento. Quem resolve oclusao aqui e a aproximacao,
        # nao a altura.
        z = z_local + float(plano.get("mira_alt_m", 8)) + h_titulo * 1.2
        p = (px, py)

        obj = _texto(f"Letreiro_{item['plano']}", item["texto"], h_titulo,
                     fonte, mat, col)
        obj.location = (p[0], p[1], z)
        obj.rotation_euler = (pos_cam - Vector((p[0], p[1], z))
                              ).to_track_quat("Z", "Y").to_euler()
        obj["texto_do_cliente"] = item["texto"]
        obj["audio"] = item["audio"]
        obj["fracao_da_altura"] = frac_t
        postos += 1

        if item.get("apoio"):
            frac_a = escala["apoio"]["fracao_da_altura"]
            h_apoio = frac_a * d * SENSOR_VERTICAL_MM / f
            sub = _texto(f"Apoio_{item['plano']}", item["apoio"], h_apoio,
                         fonte, mat, col)
            # embaixo do nome, como ele ditou para a Fazendinha:
            # "o nome e a fazendinha, embaixo a descricao"
            sub.location = (p[0], p[1], z - h_titulo * 1.05)
            sub.rotation_euler = obj.rotation_euler
            sub["texto_do_cliente"] = item["apoio"]
            postos += 1
            if frac_a < 0.04:
                fora_da_regra.append((item["plano"], "apoio", frac_a))

        if frac_t < 0.08 and item["nivel"] != "apoio":
            fora_da_regra.append((item["plano"], item["nivel"], frac_t))

        _so_no_proprio_plano(obj, plano, pacote_planos["fps"])
        if item.get("apoio"):
            _so_no_proprio_plano(col.objects[f"Apoio_{item['plano']}"], plano,
                                 pacote_planos["fps"])

        relatorio.append((item["plano"], item["nivel"], d, f, h_titulo, frac_t))

    print(f"  letreiros .......... {postos} objetos de texto "
          f"({len(relatorio)} letreiros com apoio incluso)")
    print(f"     plano  nivel        dist   lente   altura   % do quadro")
    for pid, niv, d, f, h, fr in relatorio:
        print(f"     {pid:5s}  {niv:11s} {d:5.0f}m  {f:4.0f}mm  {h:6.2f}m   "
              f"{fr*100:5.1f}%")
    if fora_da_regra:
        print(f"  ERRO: {len(fora_da_regra)} letreiros abaixo da regra de "
              f"entrega: {fora_da_regra}")
    else:
        print("     todos dentro da regra de entrega (titulo >= 8%, apoio >= 4%)")
    return postos, len(fora_da_regra)
