#!/usr/bin/env python3
"""
Gera a cena 3D do Parque de Exposicoes de Dois Vizinhos para a AGROSHOW 2026,
a partir da planta extraida em data/mapa_agroshow26.json.

Constroi terreno, os 134 estandes instanciados, os pavilhoes, a arena e as
cameras dos planos do filme (data/planos.json, resolvidas por scripts/planos.py).
Deixa tudo em colecoes separadas para que a camada permanente (terreno,
pavilhoes) sobreviva a troca da camada do evento (estandes, palco, sinalizacao)
no ano seguinte.

Uso:
    blender --background --python scripts/build_scene.py -- --out cena.blend
    blender --background --python scripts/build_scene.py -- --relevo dem.png

Ou com o modulo bpy instalado (pip install bpy):
    python3 scripts/build_scene.py --out cena.blend

Constroi so a regiao de um plano (ou lista de planos), para caber em GPU de
8-12 GB sem carregar o recinto inteiro:

    python3 scripts/build_scene.py --plano P19 --out out/P19.blend

Exporta para o Twinmotion (Plano A da proposta de render). O FBX carrega
BASE + EVENTO + cones da coleção MARCOS_CAMERA -- um cone por ponta de plano,
porque o Twinmotion importa geometria mas nao importa camera animada:

    python3 scripts/build_scene.py --export-fbx out/cena.fbx

Escala, bacia da arena e leitura da planta vivem em scripts/terreno.py -- e a
fonte unica, compartilhada com scripts/planos.py. Escala 0,5611 m/pt, derivada
da propria planta. NAO CONFERIDA com medida real em campo.
"""

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy
import bmesh
from mathutils import Vector

import estruturas
import planos as planos_mod
import terreno

# --------------------------------------------------------------------------
# Constantes proprias do gerador (geometria e bacia vivem em terreno.py)

LARGURA_RENDER = 2760    # 2:1, 2x o nativo do painel P2,9 (1379x690)
ALTURA_RENDER = 1380

COLECOES = ["BASE", "EVENTO", "CAMERA", "MARCOS_CAMERA", "LUZ"]

RAIZ = Path(__file__).resolve().parent.parent

# Rumo das estruturas, em graus. Nao sao chute: saem do angulo com que a planta
# escreve o rotulo de cada uma -- `angulo_graus` em data/locais.json. O rotulo
# de um galpao e escrito no eixo dele.
RUMO_PAVILHOES = 341.0   # a fileira corre norte-sul, levemente girada
RUMO_PORTAL = 73.0       # de frente para quem chega pela Dorvalino Tosi
RUMO_PALCO = 334.0       # de frente para a arena


# --------------------------------------------------------------------------
# Utilitarios de cena

def limpar_cena():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def criar_colecoes():
    for nome in COLECOES:
        col = bpy.data.collections.new(nome)
        bpy.context.scene.collection.children.link(col)
    return {c.name: c for c in bpy.data.collections}


def caixa(nome, largura, profundidade, altura, colecao):
    """Cria uma caixa com a base apoiada em z=0."""
    malha = bpy.data.meshes.new(nome)
    obj = bpy.data.objects.new(nome, malha)
    colecao.objects.link(obj)

    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector((largura, profundidade, altura)),
                    verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector((0, 0, altura / 2)), verts=bm.verts)
    bm.to_mesh(malha)
    bm.free()
    return obj


# --------------------------------------------------------------------------
# Materiais

# (nome, cor base RGB, rugosidade, metalico)
MATERIAIS = {
    "MAT_TERRENO":  ((0.13, 0.22, 0.07), 0.95, 0.0),
    "MAT_LONA":     ((0.82, 0.81, 0.78), 0.55, 0.0),
    "MAT_PAVILHAO": ((0.55, 0.56, 0.58), 0.45, 0.3),
    "MAT_ARENA":    ((0.38, 0.28, 0.18), 0.90, 0.0),
    "MAT_ASFALTO":  ((0.09, 0.09, 0.10), 0.80, 0.0),
}


def criar_materiais():
    """Materiais base. Sao ponto de partida para o acabamento -- troque por
    PBR com textura (Poly Haven, ambientCG: ambos CC0) na etapa de lapidacao.
    No terreno, antes de textura nova: ruido de baixa frequencia (escala 1-3)
    em Overlay a 0,2-0,35 sobre a cor base quebra o padrao repetido visto do
    alto -- e o que mais entrega CG num terreno de 800 m, nao a textura."""
    feitos = {}
    for nome, (cor, rug, met) in MATERIAIS.items():
        mat = bpy.data.materials.new(nome)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (*cor, 1.0)
            bsdf.inputs["Roughness"].default_value = rug
            if "Metallic" in bsdf.inputs:
                bsdf.inputs["Metallic"].default_value = met
        feitos[nome] = mat
    return feitos


def aplicar(obj, mat):
    if obj.data and hasattr(obj.data, "materials"):
        obj.data.materials.clear()
        obj.data.materials.append(mat)


# --------------------------------------------------------------------------
# Corte por regiao -- o que segura a cena em 8-12 GB de VRAM

def bbox_dos_planos(planos_sel, centro, margem=80.0):
    """Caixa envolvente (x0, x1, y0, y1) das cameras e miras dos planos dados.

    Margem de 80 m cobre o maior estande (100 m², lado 10 m) mais folga de
    enquadramento. Usada para construir so o que aparece nos planos pedidos
    -- decisivo numa GPU de 8-12 GB, que nao segura o recinto inteiro vestido.
    """
    xs, ys = [], []
    for p in planos_sel:
        for t in (0.0, 1.0):
            pos, mira = planos_mod.amostra(p, t, centro)
            xs += [pos[0], mira[0]]
            ys += [pos[1], mira[1]]
    return (min(xs) - margem, max(xs) + margem,
            min(ys) - margem, max(ys) + margem)


def dentro(bbox, x, y):
    if bbox is None:
        return True
    x0, x1, y0, y1 = bbox
    return x0 <= x <= x1 and y0 <= y <= y1


# --------------------------------------------------------------------------
# Construcao

def construir_arena(centro_arena, col, mats):
    """Piso de terra da pista, no fundo da bacia."""
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=45.0, depth=0.4,
                                        location=(centro_arena[0],
                                                  centro_arena[1], 0.1))
    obj = bpy.context.active_object
    obj.name = "PistaArena"
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    col.objects.link(obj)
    aplicar(obj, mats["MAT_ARENA"])
    return obj


def construir_terreno(dados, col, centro_arena, relevo=None):
    """Terreno da prancha inteira, esculpido na bacia da arena.

    Constroi sempre a prancha inteira, mesmo com --plano ativo: e uma unica
    malha, o custo de esculpir alguns vertices a mais e desprezivel perto do
    que --plano economiza em estandes e pavilhoes instanciados.

    Com --relevo, um heightmap em escala de cinza entra por deslocamento por
    cima da bacia -- util para o entorno (vale, encostas distantes), onde os
    30 m de resolucao bastam. Para o recinto, quem manda e a bacia.
    """
    larg = dados["prancha"]["largura_pt"] * terreno.ESCALA * 1.2
    prof = dados["prancha"]["altura_pt"] * terreno.ESCALA * 1.2
    div = 400

    bpy.ops.mesh.primitive_grid_add(x_subdivisions=div, y_subdivisions=div,
                                    size=1.0, location=(0, 0, 0))
    obj = bpy.context.active_object
    obj.name = "Terreno"
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    col.objects.link(obj)

    for v in obj.data.vertices:
        v.co.x *= larg
        v.co.y *= prof
        v.co.z = terreno.elevacao(v.co.x, v.co.y, centro_arena)

    if relevo and Path(relevo).exists():
        img = bpy.data.images.load(str(relevo))
        tex = bpy.data.textures.new("RelevoTex", type="IMAGE")
        tex.image = img
        mod = obj.modifiers.new("RelevoEntorno", type="DISPLACE")
        mod.texture = tex
        mod.texture_coords = "UV"
        mod.strength = 20.0
        mod.mid_level = 0.5
        print(f"  relevo do entorno: {relevo}")
    else:
        print("  sem heightmap -- so a bacia derivada da planta")
    return obj


def orientar_estandes(postos):
    """Alinha cada estande ao eixo da sua fileira.

    Estandes vizinhos numa fileira compartilham o eixo da fileira, entao a
    direcao ate o vizinho mais proximo serve de referencia. Isso resolve tanto
    as grades ortogonais quanto os arcos concentricos da arena, sem precisar
    tratar os dois casos separadamente.

    Com --plano ativo, so os estandes dentro da bbox entram nesta lista -- a
    orientacao de um estande na borda do corte pode ficar imprecisa se o
    vizinho mais proximo dele ficou de fora. Aceitavel: e um corte de trabalho,
    nao a build de entrega.
    """
    for i, (obj, x, y) in enumerate(postos):
        melhor, dist_melhor = None, float("inf")
        for j, (_, x2, y2) in enumerate(postos):
            if i == j:
                continue
            d = (x - x2) ** 2 + (y - y2) ** 2
            if d < dist_melhor:
                dist_melhor, melhor = d, (x2, y2)
        if melhor is None or dist_melhor > 40.0 ** 2:
            continue
        obj.rotation_euler = (0.0, 0.0,
                              math.atan2(melhor[1] - y, melhor[0] - x))


def construir_estandes(dados, col, centro_arena, bbox=None):
    """Instancia os estandes a partir de dois modulos base.

    39 estandes de 100 m² e 35 de 25 m² sao instancias, nao modelagens
    separadas. Os demais recebem caixa propria dimensionada pela area.
    """
    modulos = {}
    for area, lado in ((100.0, 10.0), (25.0, 5.0)):
        base = caixa(f"MODULO_{int(area)}m2", lado, lado, terreno.ALTURA_ESTANDE, col)
        base.hide_render = base.hide_viewport = True
        modulos[area] = base

    origem = dados["_origem"]
    contagem = {"instanciado": 0, "proprio": 0, "fora_do_corte": 0}
    postos = []

    for st in dados["estandes"]:
        area = st.get("area_m2")
        if area is None:
            continue
        x, y = terreno.para_mundo(st["x"], st["y"], origem)
        if not dentro(bbox, x, y):
            contagem["fora_do_corte"] += 1
            continue

        if area in modulos:
            obj = bpy.data.objects.new(st["codigo"], modulos[area].data)
            col.objects.link(obj)
            contagem["instanciado"] += 1
        else:
            lado = math.sqrt(area)
            obj = caixa(st["codigo"], lado, lado, terreno.ALTURA_ESTANDE, col)
            contagem["proprio"] += 1

        obj.location = (x, y, terreno.elevacao(x, y, centro_arena))
        obj["area_m2"] = area
        obj["serie"] = st["serie"]
        postos.append((obj, x, y))

    orientar_estandes(postos)
    return contagem


def construir_pavilhoes(dados, col, centro_arena, bbox=None):
    """Pavilhoes de animais: 5 de 720 m² e 1 de 560 m².

    Proporcao 60 x 12 m assumida para os de 720 -- confira em campo. A ordem
    fisica norte->sul e gado leite, nucleo cara branca, gado corte, ovinos e
    caprinos, pequenos animais, equinos.
    """
    origem = dados["_origem"]
    feitos = 0
    for z in dados["zonas"]:
        if z["categoria"] != "pavilhoes" or "PAVILHÃO -" not in z["rotulo"]:
            continue
        x, y = terreno.para_mundo(z["x"], z["y"], origem)
        if not dentro(bbox, x, y):
            continue
        area = 560.0 if "EQUÍNOS" in z["rotulo"] else 720.0
        profundidade = 12.0
        largura = area / profundidade
        # Galpao de duas aguas, nao caixa: o telhado e o que se ve do alto no
        # sobrevoo do P11, e caixa chapada denuncia CG antes de qualquer
        # textura. A orientacao segue a fileira, que corre norte-sul.
        obj = estruturas.pavilhao(z["rotulo"], x, y,
                                  terreno.elevacao(x, y, centro_arena),
                                  largura, profundidade, col,
                                  rumo_graus=RUMO_PAVILHOES)
        obj["area_m2"] = area
        feitos += 1
    return feitos


def construir_estruturas(dados, col, centro_arena, bbox=None):
    """Portal, palco e camarotes -- as tres que o filme mais mostra.

    O portal abre e fecha o filme (P02 e P22), o palco e o P20, e os camarotes
    aparecem em todo plano da arena. Ate 14/08 os tres eram caixa ou nem isso.
    """
    origem = dados["_origem"]
    feitos = []

    def posicao(rotulo, ocorrencia=0):
        p = terreno.ponto_da_zona(dados, rotulo, ocorrencia)
        if p is None or not dentro(bbox, p[0], p[1]):
            return None
        return p[0], p[1], terreno.elevacao(p[0], p[1], centro_arena)

    p = posicao("Portal de Entrada")
    if p:
        feitos.append(estruturas.portal("PortalCeleiro", *p, col,
                                        rumo_graus=RUMO_PORTAL))

    p = posicao("PALCO")
    if p:
        feitos.append(estruturas.palco("Palco", *p, col,
                                       rumo_graus=RUMO_PALCO))

    # Os dois camarotes ladeiam a arena -- restricao 1 do cliente, e o mapa
    # desenha os dois. Cada um aponta para o centro da pista.
    for rotulo in ("CAMAROTES - LADO A", "CAMAROTES - LADO B"):
        p = posicao(rotulo)
        if not p:
            continue
        rumo = math.degrees(math.atan2(centro_arena[1] - p[1],
                                       centro_arena[0] - p[0]))
        feitos.append(estruturas.camarote(rotulo, *p, col, rumo_graus=rumo))

    return feitos


def construir_vias(col, centro_arena, bbox=None, caminho=None):
    """As vias lidas do bitmap da planta, viradas em fita de pista.

    So entra o que `scripts/extrair_vias.py` marcou como via de verdade -- o
    resto do que a deteccao pega e moldura de prancha e caixa de carimbo.
    """
    caminho = Path(caminho or RAIZ / "data" / "vias.json")
    if not caminho.exists():
        print("  sem data/vias.json -- rode scripts/extrair_vias.py")
        return 0

    dados_vias = json.loads(caminho.read_text(encoding="utf-8"))
    feitas = 0
    for v in dados_vias["vias"]:
        if not v.get("e_via"):
            continue
        pontos = [(x, y) for x, y in v["pontos_m"]
                  if dentro(bbox, x, y)]
        if len(pontos) < 2:
            continue
        obj = estruturas.via(f"Via_{v['id']}", pontos, col,
                             lambda x, y: terreno.elevacao(x, y, centro_arena))
        if obj:
            obj["tipo"] = v.get("tipo")
            obj["rotulo_mais_proximo"] = v.get("rotulo_mais_proximo")
            feitas += 1
    return feitas


def configurar_render(cena, motor="cycles"):
    cena.render.resolution_x = LARGURA_RENDER
    cena.render.resolution_y = ALTURA_RENDER
    cena.render.resolution_percentage = 100
    cena.render.fps = 30
    cena.render.image_settings.file_format = "PNG"
    cena.render.film_transparent = False
    escolher_motor(cena, motor)

    if cena.render.engine == "CYCLES":
        configurar_cycles(cena)
    else:
        configurar_eevee(cena)

    # Ceu de fim de tarde em 2:1 e um degrade grande; painel LED costuma
    # trabalhar em 8 bits e bandeia. Dither e a primeira defesa, sem custo.
    cena.render.dither_intensity = 1.0
    print(f"  motor de render ..... {cena.render.engine}")


def escolher_motor(cena, pedido="cycles"):
    """Crava o motor pedido, e ABORTA se ele nao existir.

    O codigo antigo tentava 'BLENDER_EEVEE_NEXT' e, no except, caia em Cycles.
    No Blender 5.2 o identificador voltou a ser 'BLENDER_EEVEE' -- entao o
    except disparava sempre e a cena saia em **Cycles CPU, em silencio**, com
    o resto do arquivo (overscan, motion blur por acumulacao) configurado para
    EEVEE. Um render de 4.635 quadros comecaria e nao terminaria nunca, e
    ninguem saberia por que.

    Motor e declaracao, nao tentativa. Se o pedido nao existe nesta build, o
    programa para e diz qual existe.
    """
    if pedido == "cycles":
        garantir_addon_cycles()

    candidatos = {
        "cycles": ["CYCLES"],
        # 'NEXT' e o nome da 4.2 a 4.5; a 5.x voltou ao nome curto.
        "eevee": ["BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"],
    }[pedido]

    # Atribui e CONFERE. Nao da para consultar a lista antes: o enum de
    # `render.engine` so anuncia os motores embutidos, e o Cycles, que e addon,
    # nao aparece nele nem quando esta ligado e funcionando. Consultando a
    # lista, o gerador abortava dizendo que a build nao tem Cycles -- e tinha.
    for nome in candidatos:
        try:
            cena.render.engine = nome
        except TypeError:
            continue
        if cena.render.engine == nome:
            return nome

    raise SystemExit(
        f"nao consegui cravar o motor {pedido!r} nesta build do Blender "
        f"(tentei {candidatos}). O render NAO vai sair no motor pedido.")


def garantir_addon_cycles():
    """Religa o addon do Cycles, que `limpar_cena()` derruba.

    `bpy.ops.wm.read_factory_settings()` -- usado para nascer com a cena vazia
    -- volta as preferencias de fabrica e, com elas, desabilita os addons da
    sessao. O Cycles some do enum de motores e o gerador aborta dizendo que a
    build nao tem Cycles, o que e falso. Religar aqui custa nada e evita o
    diagnostico errado.
    """
    import addon_utils
    for nome in ("cycles", "bl_ext.blender_org.cycles"):
        try:
            addon_utils.enable(nome, default_set=False, persistent=True)
        except Exception:
            continue
        if "cycles" in bpy.context.preferences.addons:
            return True
    return "cycles" in bpy.context.preferences.addons


def configurar_cycles(cena):
    """A configuracao que o Natan ditou em 14/08, gravada na cena.

    Ele abre o .blend e renderiza: nada aqui e para ser remarcado a mao.
    Max samples 128 com limiar de ruido 0,1 -- o limiar e quem manda, e os 128
    sao o teto para o pixel que nao converge. Denoise ligado no fim, prefiltro
    Fast, qualidade Balanced, na GPU.
    """
    c = cena.cycles
    c.device = "GPU"
    c.samples = 128
    c.use_adaptive_sampling = True
    c.adaptive_threshold = 0.1
    c.use_denoising = True
    for atributo, valor in (("denoising_use_gpu", True),
                            ("denoising_prefilter", "FAST"),
                            ("denoising_quality", "BALANCED"),
                            ("use_fast_gi", True)):
        if hasattr(c, atributo):
            setattr(c, atributo, valor)

    # Sem isto o Blender aceita device='GPU' e renderiza na CPU assim mesmo:
    # o device so vale se houver placa habilitada nas preferencias.
    habilitar_gpu()

    cena.render.use_motion_blur = True
    print(f"  cycles .............. {c.samples} samples, limiar "
          f"{c.adaptive_threshold}, denoise "
          f"{getattr(c, 'denoising_prefilter', '?')}/"
          f"{getattr(c, 'denoising_quality', '?')}")


def habilitar_gpu():
    """Liga a placa nas preferencias do Cycles, tentando OptiX e depois CUDA.

    `cycles.device = 'GPU'` sozinho nao basta: se nenhum dispositivo estiver
    marcado nas preferencias, o Cycles cai para a CPU sem reclamar. Numa RTX
    4060 isso e a diferenca entre minutos e uma noite.
    """
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
    except KeyError:
        print("  AVISO: addon cycles indisponivel; render vai para a CPU")
        return None

    for tipo in ("OPTIX", "CUDA", "HIP", "ONEAPI", "METAL"):
        try:
            prefs.compute_device_type = tipo
        except TypeError:
            continue
        prefs.get_devices()
        placas = [d for d in prefs.devices if d.type == tipo]
        if not placas:
            continue
        for d in prefs.devices:
            d.use = (d.type == tipo)
        print(f"  gpu ................. {tipo}: "
              f"{', '.join(d.name for d in placas)}")
        return tipo

    print("  AVISO: nenhuma GPU encontrada; render vai para a CPU")
    return None


def configurar_eevee(cena):
    """Alternativa rapida, para conferencia -- nao e o motor da entrega."""
    # Overscan: com camera em movimento, efeitos de tela do EEVEE (SSR, SSAO)
    # somem perto da borda do quadro. 5-10% os traz de volta.
    for alvo, atributo, valor in (
            (cena.eevee, "use_overscan", True),
            (cena.eevee, "overscan_size", 7.0),
            (cena.render, "use_motion_blur", True),
            (cena.eevee, "motion_blur_steps", 6),
            (cena.eevee, "taa_render_samples", 64)):
        if hasattr(alvo, atributo):
            setattr(alvo, atributo, valor)


def construir_ceu(cena):
    """Ceu procedural de fim de tarde.

    Substitua por um HDRI real na lapidacao -- e o que mais aproxima do
    golden hour combinado com o material de drone. Poly Haven tem HDRIs CC0.
    """
    mundo = bpy.data.worlds.new("Mundo")
    cena.world = mundo
    mundo.use_nodes = True
    nos = mundo.node_tree.nodes
    fundo = nos.get("Background")
    if fundo:
        fundo.inputs["Color"].default_value = (0.35, 0.48, 0.72, 1.0)
        fundo.inputs["Strength"].default_value = 1.2
    return mundo


def construir_luz(col):
    """Sol em golden hour, coerente com o LOOK LOCK das imagens de apoio.

    Substitua pelo addon Sun Position com -25,73144 / -53,07627 e o horario
    do evento assim que a lapidacao comecar. Sol errado denuncia CG mais
    rapido que qualquer polígono."""
    import math
    dados_sol = bpy.data.lights.new("Sol", type="SUN")
    dados_sol.energy = 3.0
    dados_sol.angle = math.radians(0.526)
    sol = bpy.data.objects.new("Sol", dados_sol)
    sol.rotation_euler = (math.radians(65), 0, math.radians(-135))
    col.objects.link(sol)
    return sol


# --------------------------------------------------------------------------
# Exportacao para o Twinmotion (Plano A)

def exportar_fbx(caminho):
    """BASE + EVENTO + os cones de MARCOS_CAMERA, sem as cameras animadas.

    O Twinmotion importa geometria mas nao importa camera animada -- os cones
    dizem ao Natan onde cravar cada chave la dentro. object_types={'MESH'}
    deixa de fora tanto as cameras reais quanto as miras (empties), que nao
    tem uso no Twinmotion.
    """
    Path(caminho).parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.fbx(
        filepath=str(Path(caminho).resolve()),
        use_selection=False,
        object_types={"MESH"},
        apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_ALL",
        axis_forward="Y",
        axis_up="Z",
        global_scale=1.0,
    )


# --------------------------------------------------------------------------

def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dados", default="data/mapa_agroshow26.json")
    ap.add_argument("--planos-json", dest="planos_json", default="data/planos.json")
    ap.add_argument("--motor", choices=("cycles", "eevee"), default="cycles",
                    help="motor gravado na cena. cycles e o da entrega, com a "
                         "configuracao que o Natan ditou; eevee e so para "
                         "conferencia rapida")
    ap.add_argument("--relevo", default=None,
                    help="heightmap em escala de cinza para deslocar o terreno")
    ap.add_argument("--out", default=None, help="salva um .blend no caminho")
    ap.add_argument("--export-fbx", default=None,
                    help="exporta BASE+EVENTO+MARCOS_CAMERA em FBX, para o Twinmotion")
    ap.add_argument("--plano", default=None,
                    help="constroi so a regiao dos planos com este id "
                         "(ou lista separada por virgula, ex: P13,P14,P15). "
                         "Sem isso, constroi o recinto inteiro")
    ap.add_argument("--sem-camera", action="store_true",
                    help="pula a montagem das cameras -- so para conferir geometria")
    args = ap.parse_args(argv)

    dados = terreno.carregar_mapa(args.dados)

    limpar_cena()
    cols = criar_colecoes()
    centro = terreno.centro_da_arena(dados)
    mats = criar_materiais()

    pacote = planos_mod.carregar(args.planos_json, dados=dados)
    selecionados = pacote["planos"]
    if args.plano:
        ids_pedidos = set(args.plano.split(","))
        selecionados = [p for p in pacote["planos"] if p["id"] in ids_pedidos]
        faltando = ids_pedidos - {p["id"] for p in selecionados}
        if faltando:
            raise SystemExit(f"plano(s) inexistente(s) em {args.planos_json}: {sorted(faltando)}")

    bbox = bbox_dos_planos(selecionados, centro) if args.plano else None
    if bbox:
        print(f"corte por --plano {args.plano}: "
              f"x [{bbox[0]:.0f}, {bbox[1]:.0f}]  y [{bbox[2]:.0f}, {bbox[3]:.0f}]")

    print("construindo terreno...")
    terreno_obj = construir_terreno(dados, cols["BASE"], centro, args.relevo)
    aplicar(terreno_obj, mats["MAT_TERRENO"])
    construir_arena(centro, cols["BASE"], mats)

    print("construindo pavilhoes...")
    n_pav = construir_pavilhoes(dados, cols["BASE"], centro, bbox)
    for o in cols["BASE"].objects:
        if "PAVILHÃO" in o.name:
            aplicar(o, mats["MAT_PAVILHAO"])

    print("construindo portal, palco e camarotes...")
    feitas = construir_estruturas(dados, cols["BASE"], centro, bbox)
    for o in feitas:
        aplicar(o, mats["MAT_PAVILHAO"] if "Camarote" not in o.name
                else mats["MAT_LONA"])

    print("construindo vias...")
    n_vias = construir_vias(cols["BASE"], centro, bbox)
    for o in cols["BASE"].objects:
        if o.name.startswith("Via_"):
            aplicar(o, mats["MAT_ASFALTO"])

    print("construindo estandes...")
    cont = construir_estandes(dados, cols["EVENTO"], centro, bbox)
    for o in cols["EVENTO"].objects:
        aplicar(o, mats["MAT_LONA"])

    n_cam = 0
    if not args.sem_camera:
        print("montando cameras dos planos...")
        n_cam = planos_mod.montar_cameras(pacote if not args.plano
                                          else {**pacote, "planos": selecionados,
                                                "total_quadros": max(p["_quadro_fim"] for p in selecionados)},
                                          cols["CAMERA"])

    n_marcos = 0
    if args.export_fbx:
        n_marcos = planos_mod.montar_marcos(pacote, cols["MARCOS_CAMERA"])

    construir_luz(cols["LUZ"])
    construir_ceu(bpy.context.scene)
    configurar_render(bpy.context.scene, args.motor)

    larg_m = dados["prancha"]["largura_pt"] * terreno.ESCALA
    prof_m = dados["prancha"]["altura_pt"] * terreno.ESCALA
    dur_s = pacote["total_quadros"] / pacote["fps"]

    print("\n" + "=" * 58)
    print(f"  escala .............. {terreno.ESCALA} m/pt")
    print(f"  extensao do terreno . {larg_m:.0f} x {prof_m:.0f} m")
    print(f"  pavilhoes ........... {n_pav} (duas aguas, nao caixa)")
    print(f"  estruturas .......... {len(feitas)}: "
          f"{', '.join(o.name for o in feitas) or 'nenhuma'}")
    print(f"  vias ................ {n_vias}")
    print(f"  estandes ............ {cont['instanciado']} instanciados "
          f"+ {cont['proprio']} proprios"
          + (f" (+{cont['fora_do_corte']} fora do corte)" if bbox else ""))
    print(f"  planos ............... {len(selecionados)} de {len(pacote['planos'])}"
          + (f" (corte --plano {args.plano})" if args.plano else " (filme completo)"))
    print(f"  cameras montadas ..... {n_cam}")
    if args.export_fbx:
        print(f"  marcos de camera ..... {n_marcos} (2 por plano, ida e volta)")
    print(f"  render .............. {LARGURA_RENDER}x{ALTURA_RENDER} "
          f"({LARGURA_RENDER/ALTURA_RENDER:.0f}:1)")
    print(f"  duracao do filme ..... {pacote['total_quadros']} quadros "
          f"({dur_s:.0f} s a {pacote['fps']} fps)")
    print(f"  patamares ........... arena 0 m -> shows {terreno.PATAMARES[2][2]} m "
          f"-> anel {terreno.PATAMARES[4][2]} m -> plato {terreno.PATAMARES[6][2]} m")
    print("=" * 58)

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(Path(args.out).resolve()))
        print(f"\nsalvo: {args.out}")

    if args.export_fbx:
        exportar_fbx(args.export_fbx)
        print(f"exportado para o Twinmotion: {args.export_fbx}")


if __name__ == "__main__":
    main()
