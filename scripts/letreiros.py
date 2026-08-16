#!/usr/bin/env python3
"""Titulos e letreiros -- passo 3 do fluxo de 5 passos do Natan.

O texto nao e meu: sai do audio dele, palavra por palavra
(`data/letreiros.json`, com o minuto citado em cada linha). O que este arquivo
resolve e ONDE a letra mora e QUE TAMANHO ela tem, e nenhuma das duas coisas e
gosto.

ONDE -- ordem dele em 15/08/2026 (DECISOES.md D045): "inclui a letra embutida no
painel usa as imagens extraidas". As imagens foram lidas e estao levantadas em
`docs/COMO-O-PARQUE-ESCREVE.md`: o parque tem seis modos de escrever e em nenhum
deles a letra flutua. Ela mora numa superficie -- tabua pendurada no portal,
faixa aplicada na fachada, chapa parafusada na parede. Perguntado como aplicar
nos 16, ele escolheu PELO LUGAR, e o lugar de cada um esta declarado no campo
`suporte` do contrato.

TAMANHO -- duas regras, e ate 15/08 so a primeira era conferida:

    PISO   titulo >= 8% da altura do quadro, apoio >= 4%     (regra de entrega)
    TETO   a linha inteira cabe em 90% do quadro             (nova)

O piso vale no instante em que a camera esta MAIS LONGE; o teto, no instante em
que ela esta MAIS PERTO. Num push-in os dois instantes sao pontas opostas do
mesmo plano, e garantir um nao garante o outro -- foi assim que 9 dos 16
letreiros sairam fora do quadro com o portao de 8% passando verde.

    fracao_altura(t) = h * f / (D(t) * sensor_vertical)
    fracao_largura(t) = W * f / (D(t) * sensor_horizontal)

O sensor do Blender e 36 mm na horizontal. O VERTICAL sai da proporcao da cena:
18,0 mm em 2:1, 20,25 mm em 16:9. A proporcao e lida da cena, nao escrita aqui,
porque em 15/08 ela mudou por ordem dele (D044) e uma constante teria mentido.

O que faz o teto ser cumprivel e a PRANCHA: painel tem largura declarada, e o
Blender quebra a linha dentro dela (`text_boxes`). Sem prancha, uma frase de
comprimento imprevisivel so tem uma linha e nada a segura.

Rodar a conferencia nao precisa de Blender:

    python scripts/letreiros.py --conferir
"""

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

RAIZ = Path(__file__).resolve().parent.parent
CONTRATO = RAIZ / "data" / "letreiros.json"

SENSOR_HORIZONTAL_MM = 36.0
SEGURANCA = 0.90          # area de seguranca da entrega, igual a do portao
AMOSTRAS_DO_PERCURSO = 33  # instantes medidos dentro do plano

# Acima disto a fachada esta de esguelha demais. O numero sai da TIPOGRAFIA, e
# nao de gosto: girar a fachada comprime a linha por cosseno sem mexer na
# altura da letra, ou seja, condensa. A 65 graus sobram 42% da largura, e a
# Archivo Narrow ja e' condensada de fabrica -- comprimir de novo pela metade
# transforma a palavra em cerca de estacas. A 55 graus sobram 57%, que ainda
# le. Nao vale para o painel plantado, que gira para a camera porque nao esta
# preso a nada.
OBLIQUIDADE_MAX_GRAUS = 65.0

# Menos que isto em quadro e' pisca-pisca: o letreiro nao da' tempo de ser lido
# e a troca chama mais atencao que o texto. Dois segundos e' a regra de leitura
# de legenda para uma linha curta, e aqui a linha tem no maximo tres.
TEMPO_MINIMO_S = 2.0

# Um letreiro nao pode servir uma faixa de distancia grande demais. Se ele for
# dimensionado para o instante mais LONGE, no instante mais PERTO ele aparece
# aumentado pela mesma razao -- e o teto de 90%% do quadro estoura. O numero sai
# do teto, nao de gosto: uma frase entra com 11,5%% de altura, e 11,5%% x 2,2 da
# 25%%, que e' o maximo que uma linha ocupa sem virar cartaz. Acima disso a
# janela de exibicao encolhe pela ponta mais distante -- o letreiro so' acende
# quando ja da' para ler. No P14 a camera parte a 148 m da Fazendinha e chega a
# 30: sem esta trava, a letra saia com 13,5 m de altura.
RAZAO_MAX_DE_DISTANCIA = 2.2


# --------------------------------------------------------------------------
# Matematica -- roda sem bpy

def sensor_vertical_mm(largura_px, altura_px):
    """36 mm e a horizontal; a vertical cai da proporcao (sensor_fit AUTO)."""
    return SENSOR_HORIZONTAL_MM * altura_px / largura_px


def distancias_no_plano(plano, ponto, centro, amostras=AMOSTRAS_DO_PERCURSO,
                        t_ini=0.0, t_fim=1.0):
    """(menor, maior) distancia da camera ate `ponto`, no trecho [t_ini, t_fim].

    Nao e a distancia ate o ALVO: e ate o letreiro. A diferenca entre as duas
    e' metade do defeito de 15/08 -- o letreiro estava puxado para a frente do
    alvo e a camera do push-in passava rente a ele.

    E nao e o plano inteiro: e' o trecho em que ele aparece. Medir fora da
    janela de exibicao dimensiona o letreiro por um instante que ninguem ve.
    """
    import planos as planos_mod
    ds = []
    for i in range(amostras):
        t = t_ini + (t_fim - t_ini) * i / (amostras - 1)
        pos, _ = planos_mod.amostra(plano, t, centro)
        ds.append(math.dist(pos, ponto))
    return min(ds), max(ds)


def dimensionar(fracao_piso, d_maior, d_menor, lente_mm, sv_mm):
    """Devolve (altura_da_letra_m, largura_maxima_da_prancha_m).

    A altura sai do PISO na distancia maior -- e o minimo que cumpre a regra de
    entrega, e nao ha razao para passar dele: letra maior so gasta largura.
    A largura maxima sai do TETO na distancia menor.
    """
    h = fracao_piso * d_maior * sv_mm / lente_mm
    w = SEGURANCA * d_menor * SENSOR_HORIZONTAL_MM / lente_mm
    return h, w


def altura_maxima(d_menor, lente_mm, sv_mm):
    return SEGURANCA * d_menor * sv_mm / lente_mm


# --------------------------------------------------------------------------
# Blender

def _bpy():
    import bpy
    return bpy


def _fonte(caminho):
    bpy = _bpy()
    p = Path(caminho)
    if not p.exists():
        raise SystemExit(
            f"ABORTADO -- fonte do contrato nao existe: {p}\n"
            f"Isto era um AVISO ate 15/08 e o letreiro saia na fonte padrao do "
            f"Blender sem ninguem ver. Fonte ausente agora para o build, pela "
            f"mesma razao que legendas.py aborta (delta 0029 do Claudio).")
    for f in bpy.data.fonts:
        if f.filepath == str(p):
            return f
    return bpy.data.fonts.load(str(p))


def _mat(nome, cor, rugosidade=0.6, emissao=0.0):
    bpy = _bpy()
    mat = bpy.data.materials.get(nome)
    if mat:
        return mat
    mat = bpy.data.materials.new(nome)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*cor, 1.0)
    bsdf.inputs["Roughness"].default_value = rugosidade
    if emissao and "Emission Color" in bsdf.inputs:
        bsdf.inputs["Emission Color"].default_value = (*cor, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emissao
    mat.diffuse_color = (*cor, 1.0)
    return mat


def _caixa(nome, larg, alt, esp, col, mat):
    """Prancha centrada na origem: X = largura, Y = espessura, Z = altura."""
    bpy = _bpy()
    x, y, z = larg / 2, esp / 2, alt / 2
    verts = [(-x, -y, -z), (x, -y, -z), (x, y, -z), (-x, y, -z),
             (-x, -y, z), (x, -y, z), (x, y, z), (-x, y, z)]
    faces = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1),
             (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    me = bpy.data.meshes.new(nome)
    me.from_pydata(verts, [], faces)
    me.update()
    obj = bpy.data.objects.new(nome, me)
    obj.data.materials.append(mat)
    col.objects.link(obj)
    return obj


def _cilindro(nome, raio, altura, col, mat, lados=8):
    bpy = _bpy()
    verts, faces = [], []
    for i in range(lados):
        a = 2 * math.pi * i / lados
        verts.append((raio * math.cos(a), raio * math.sin(a), -altura / 2))
    for i in range(lados):
        a = 2 * math.pi * i / lados
        verts.append((raio * math.cos(a), raio * math.sin(a), altura / 2))
    for i in range(lados):
        j = (i + 1) % lados
        faces.append((i, j, j + lados, i + lados))
    faces.append(tuple(range(lados - 1, -1, -1)))
    faces.append(tuple(range(lados, 2 * lados)))
    me = bpy.data.meshes.new(nome)
    me.from_pydata(verts, [], faces)
    me.update()
    obj = bpy.data.objects.new(nome, me)
    obj.data.materials.append(mat)
    col.objects.link(obj)
    return obj


def _texto(nome, conteudo, altura_m, largura_caixa_m, fonte, mat, col):
    """Texto que QUEBRA dentro de uma caixa de largura declarada.

    `text_boxes[0].width` esta em unidades de mundo e NAO e escalado por `size`
    -- medido no Blender 5.2, nao suposto: com size=2 e caixa=20 o bloco sai com
    18,18 m; com size=1 e caixa=10, com 9,09 m. E' isso que da ao letreiro uma
    largura maxima cumprivel.
    """
    bpy = _bpy()
    dados = bpy.data.curves.new(nome, type="FONT")
    dados.body = conteudo
    if fonte:
        dados.font = fonte
    dados.size = altura_m
    dados.extrude = 0.0
    dados.align_x = "CENTER"
    dados.align_y = "TOP"
    if largura_caixa_m:
        dados.text_boxes[0].width = largura_caixa_m
    obj = bpy.data.objects.new(nome, dados)
    obj.data.materials.append(mat)
    col.objects.link(obj)
    bpy.context.view_layer.update()
    return obj


def _medir(obj):
    bpy = _bpy()
    bpy.context.view_layer.update()
    d = obj.dimensions
    return d.x, d.z if d.z > 1e-6 else d.y


def _encaixar_texto(obj, normal, centro_xy, topo_z):
    """Poe o texto de pe, virado para `normal`, com o bloco centrado em
    `centro_xy` e o topo em `topo_z`.

    Nao basta mandar `align_x=CENTER`: com uma caixa de texto, a caixa nasce NA
    ORIGEM e cresce para um lado, entao a origem do objeto nao e' o meio do
    bloco. Colocar a origem no centro do painel deixava o texto inteiro
    deslocado meia largura para a direita -- e era isso, e nao a camera, que
    punha metade dos letreiros para fora da borda. Medido pelo `bound_box`
    depois de escrito, que e' a unica fonte que sabe onde o bloco ficou.
    """
    import mathutils
    bpy = _bpy()
    _orientar_texto(obj, normal)
    bpy.context.view_layer.update()

    bb = [mathutils.Vector(c) for c in obj.bound_box]      # local
    cx = (min(v.x for v in bb) + max(v.x for v in bb)) / 2  # meio horizontal
    ty = max(v.y for v in bb)                               # topo vertical
    R = obj.rotation_euler.to_matrix()
    desloc = R @ mathutils.Vector((-cx, -ty, 0.0))
    obj.location = (centro_xy[0] + desloc.x,
                    centro_xy[1] + desloc.y,
                    topo_z + desloc.z)
    bpy.context.view_layer.update()


def _orientar_texto(obj, normal):
    """Poe o texto de pe, virado para `normal` (horizontal, unitaria).

    R_x(90) leva o +Z do texto para -Y; o giro em Z de (alfa + 90) leva -Y ate
    a normal pedida. Conferido nos dois eixos antes de virar codigo.
    """
    a = math.atan2(normal[1], normal[0])
    obj.rotation_euler = (math.pi / 2, 0.0, a + math.pi / 2)


def _orientar_prancha(obj, normal):
    """A prancha nasce com a face em +Y; gira para que +Y vire `normal`."""
    a = math.atan2(normal[1], normal[0])
    obj.rotation_euler = (0.0, 0.0, a - math.pi / 2)


def em_quadro(cena, cam, objs, quadro, seguranca=SEGURANCA):
    """O conjunto inteiro cabe na area de seguranca neste quadro?

    Mede com `world_to_camera_view`, que e' a mesma funcao do portao de
    conferencia -- de proposito: gerador e portao concordando por construcao
    valem mais que duas contas independentes que um dia divergem.
    """
    import mathutils
    from bpy_extras.object_utils import world_to_camera_view
    bpy = _bpy()

    cena.frame_set(quadro)
    dg = bpy.context.evaluated_depsgraph_get()
    cam_av = cam.evaluated_get(dg)
    margem = (1.0 - seguranca) / 2.0
    lo, hi = margem, 1.0 - margem
    for o in objs:
        oa = o.evaluated_get(dg)
        for c in oa.bound_box:
            p = world_to_camera_view(cena, cam_av,
                                     oa.matrix_world @ mathutils.Vector(c))
            if p.z <= 0 or not (lo <= p.x <= hi) or not (lo <= p.y <= hi):
                return False
    return True


def _janela_do_ponto(cena, cam, ponto, q_ini, q_fim, passo=3, folga=0.70):
    """Trecho (t_ini, t_fim) em que o ANCORADOURO cabe numa area menor que a de
    seguranca. E' a estimativa barata que precede a construcao: a prancha ainda
    nao existe, entao mede-se o ponto e reserva-se `folga` de tela em volta
    dela para o painel que vai nascer ali.
    """
    import mathutils
    from bpy_extras.object_utils import world_to_camera_view
    bpy = _bpy()
    margem = (1.0 - folga) / 2.0
    lo, hi = margem, 1.0 - margem
    v = mathutils.Vector(ponto)
    dentro = []
    quadros = list(range(q_ini, q_fim + 1, passo)) or [q_ini]
    for q in quadros:
        cena.frame_set(q)
        dg = bpy.context.evaluated_depsgraph_get()
        p = world_to_camera_view(cena, cam.evaluated_get(dg), v)
        dentro.append(p.z > 0 and lo <= p.x <= hi and lo <= p.y <= hi)
    if not any(dentro):
        return 0.0, 1.0            # nunca cabe: mede o plano inteiro e reprova
    span = max(1, q_fim - q_ini)
    qs = [q for q, ok in zip(quadros, dentro) if ok]
    return (min(qs) - q_ini) / span, (max(qs) - q_ini) / span


def _aparar_por_distancia(plano, ponto, centro, t0, t1, passos=33):
    """Encolhe a janela pela ponta mais distante ate a razao caber em
    RAZAO_MAX_DE_DISTANCIA. Devolve (t0, t1).

    Nao mexe na ponta perto: e' ela que manda no teto de 90%. Quem cede e' a
    ponta longe, e ceder ali significa acender o letreiro mais tarde -- o que
    e' a decisao certa de qualquer jeito, porque a 148 m ninguem le placa.
    """
    import planos as planos_mod
    ts = [t0 + (t1 - t0) * i / (passos - 1) for i in range(passos)]
    ds = [math.dist(planos_mod.amostra(plano, t, centro)[0], ponto) for t in ts]
    d_min = min(ds)
    limite = d_min * RAZAO_MAX_DE_DISTANCIA
    bons = [t for t, d in zip(ts, ds) if d <= limite]
    if not bons:
        return t0, t1
    return min(bons), max(bons)


def janela_em_quadro(cena, cam, objs, q_ini, q_fim, passo=3):
    """Maior trecho contiguo do plano em que o letreiro cabe no quadro.

    Devolve (inicio, fim) em quadros, ou None. Existe porque num sobrevoo a
    mira VIAJA: no P09 ela anda 45 m durante o plano, e um letreiro plantado
    esta em quadro num pedaco do plano e fora no resto. Ate 15/08 ele ficava
    aceso o plano inteiro e saia deslizando para fora da tela.
    """
    marcas = list(range(q_ini, q_fim + 1, passo))
    if marcas[-1] != q_fim:
        marcas.append(q_fim)
    dentro = [em_quadro(cena, cam, objs, q) for q in marcas]

    melhor, atual = None, None
    for q, ok in zip(marcas, dentro):
        if ok and atual is None:
            atual = [q, q]
        elif ok:
            atual[1] = q
        elif atual is not None:
            if melhor is None or atual[1] - atual[0] > melhor[1] - melhor[0]:
                melhor = atual
            atual = None
    if atual is not None and (melhor is None
                              or atual[1] - atual[0] > melhor[1] - melhor[0]):
        melhor = atual
    return tuple(melhor) if melhor else None


def _so_no_proprio_plano(objs, ini, fim, fps, respiro_s=0.5):
    """Acende o letreiro so' no trecho em que ele existe e cabe.

    Sem isto os 16 ficam na cena o filme inteiro e aparecem ao fundo dos
    outros planos. Meio segundo de respiro em cada ponta: ligar no quadro exato
    do corte faz o texto piscar junto com a troca de camera.

    As chaves ficam em quadros ADJACENTES, entao a curva entre elas nunca e
    amostrada e nao e preciso forcar interpolacao CONSTANT.
    """
    respiro = max(1, int(round(respiro_s * fps)))
    if fim - ini > 2 * respiro:
        ini, fim = ini + respiro, fim - respiro
    for obj in objs:
        for quadro, oculto in ((ini - 1, True), (ini, False),
                               (fim, False), (fim + 1, True)):
            obj.hide_render = oculto
            obj.hide_viewport = oculto
            obj.keyframe_insert("hide_render", frame=quadro)
            obj.keyframe_insert("hide_viewport", frame=quadro)


# --------------------------------------------------------------------------
# Suportes: onde a letra encosta

def _caixa_mundo(obj):
    import mathutils
    cantos = [obj.matrix_world @ mathutils.Vector(c) for c in obj.bound_box]
    xs = [c.x for c in cantos]
    ys = [c.y for c in cantos]
    zs = [c.z for c in cantos]
    return (min(xs), max(xs)), (min(ys), max(ys)), (min(zs), max(zs))


def _fachada(hosp, de_onde, olhando_para=None):
    """Face do hospedeiro virada para `de_onde`, com a faixa deslizada ate
    `olhando_para` (por padrao, o proprio observador).

    Sao dois pontos diferentes de proposito. QUAL face recebe a faixa depende
    de onde a camera esta -- e' a face que ela ve. ONDE na face a faixa fica
    depende de para onde a camera OLHA: nos camarotes, que tem 48 m de
    comprimento e ficam de lado em relacao a arena, a faixa deslizada ate a
    camera caia fora do enquadramento inteiro, e a mesma faixa deslizada ate a
    mira cai no meio da tela.

    Devolve (centro_xy, normal, largura_da_face, z_base, z_topo).

    Mede no espaco LOCAL do objeto e so' depois leva ao mundo. A primeira
    versao usava a caixa alinhada ao mundo, e isso mente em objeto girado: o
    PortalCeleiro esta a 92 graus por ordem dele (D043), entao a caixa de mundo
    dava 3,2 m de largura onde o portal tem 24 -- e a frase do P02 quebrou em
    seis linhas dentro de uma tabua de 7 m. Erro caro e mudo: a prancha existia,
    so' que estreita.

    E' aproximacao de caixa, e vale dizer: predio com planta em L ganharia a
    faixa na face errada. Nenhum dos 8 hospedeiros declarados tem planta em L.
    """
    import mathutils
    bb = [mathutils.Vector(c) for c in hosp.bound_box]      # local
    lx0 = min(v.x for v in bb); lx1 = max(v.x for v in bb)
    ly0 = min(v.y for v in bb); ly1 = max(v.y for v in bb)
    cxl, cyl = (lx0 + lx1) / 2, (ly0 + ly1) / 2
    larg_x, larg_y = lx1 - lx0, ly1 - ly0

    M = hosp.matrix_world
    R = M.to_3x3()
    escala = hosp.matrix_world.to_scale()
    faces = [
        (mathutils.Vector((cxl, ly0, 0.0)), mathutils.Vector((0, -1, 0)),
         larg_x * abs(escala.x)),
        (mathutils.Vector((cxl, ly1, 0.0)), mathutils.Vector((0, 1, 0)),
         larg_x * abs(escala.x)),
        (mathutils.Vector((lx0, cyl, 0.0)), mathutils.Vector((-1, 0, 0)),
         larg_y * abs(escala.y)),
        (mathutils.Vector((lx1, cyl, 0.0)), mathutils.Vector((1, 0, 0)),
         larg_y * abs(escala.y)),
    ]
    (_, _), (_, _), (z0, z1) = _caixa_mundo(hosp)

    # A camera esta DENTRO da pegada? Desde 15/08 a noite ela passa por dentro
    # dos galpoes, por ordem dele, e la' dentro nao existe fachada virada para
    # ela: toda face aponta para fora. A letra entao vai na face do FUNDO, pelo
    # lado de dentro, olhando de volta para quem entra -- que e' exatamente o
    # que o footage mostra (chapa verde na parede vermelha, referencia D).
    lx0w, lx1w = min(v.x for v in bb), max(v.x for v in bb)
    ly0w, ly1w = min(v.y for v in bb), max(v.y for v in bb)
    local = M.inverted() @ mathutils.Vector((de_onde[0], de_onde[1], 0.0))
    dentro = (lx0w <= local.x <= lx1w) and (ly0w <= local.y <= ly1w)

    alvo = mathutils.Vector((de_onde[0], de_onde[1], 0.0))
    melhor, melhor_dot = None, -2.0
    for p_local, n_local, larg in faces:
        p = M @ p_local
        n = (R @ n_local)
        n.z = 0.0
        if n.length < 1e-6:
            continue
        n.normalize()
        v = mathutils.Vector((alvo.x - p.x, alvo.y - p.y, 0.0))
        if v.length < 1e-6:
            continue
        d = n.dot(v.normalized())
        # Por dentro, a face boa e' a que da as COSTAS para a camera: e' a do
        # fundo do corredor. Inverte o criterio e depois inverte a normal, para
        # a letra encarar quem esta dentro.
        if dentro:
            d = -d
        if d > melhor_dot:
            melhor_dot, melhor = d, ((p.x, p.y), (n.x, n.y), larg)
    centro, normal, larg = melhor
    if dentro:
        normal = (-normal[0], -normal[1])

    # A faixa nao vai no MEIO da fachada: vai no trecho que a camera enxerga.
    # A Praca de Alimentacao tem 145 m de laje e o PAVILHAO - GADO LEITE tem
    # 57; nos dois a camera passa rente ou por dentro da pegada, e uma faixa
    # centrada ficava atras dela. Desliza o ancoradouro ate a projecao da
    # camera sobre a fachada, presa a 60% do meio para nao sair do predio.
    mira = olhando_para or de_onde
    eixo = (-normal[1], normal[0])
    t = ((mira[0] - centro[0]) * eixo[0] + (mira[1] - centro[1]) * eixo[1])
    limite = larg * 0.22
    t = max(-limite, min(limite, t))
    centro = (centro[0] + eixo[0] * t, centro[1] + eixo[1] * t)
    return centro, normal, larg * 0.46, z0, z1


def _vao_do_portal(hosp, de_onde):
    """Centro, normal e largura do VAO de um portal.

    O vao e' o eixo horizontal mais largo do objeto, medido no espaco local. A
    normal e' o eixo perpendicular, com o sinal que aponta para o observador --
    porque a tabua tem duas faces e quem le e' quem chega.
    """
    import mathutils
    bb = [mathutils.Vector(c) for c in hosp.bound_box]
    lx = max(v.x for v in bb) - min(v.x for v in bb)
    ly = max(v.y for v in bb) - min(v.y for v in bb)
    esc = hosp.matrix_world.to_scale()
    M, R = hosp.matrix_world, hosp.matrix_world.to_3x3()

    if lx * abs(esc.x) >= ly * abs(esc.y):
        larg = lx * abs(esc.x)
        n = R @ mathutils.Vector((0, 1, 0))
    else:
        larg = ly * abs(esc.y)
        n = R @ mathutils.Vector((1, 0, 0))
    n.z = 0.0
    n.normalize()

    centro_local = mathutils.Vector((
        (max(v.x for v in bb) + min(v.x for v in bb)) / 2,
        (max(v.y for v in bb) + min(v.y for v in bb)) / 2, 0.0))
    c = M @ centro_local
    if n.dot(mathutils.Vector((de_onde[0] - c.x, de_onde[1] - c.y, 0.0))) < 0:
        n = -n
    (_, _), (_, _), (z0, z1) = _caixa_mundo(hosp)
    return (c.x, c.y), (n.x, n.y), larg, z0, z1


def _normal_para(ponto, de_onde):
    vx, vy = de_onde[0] - ponto[0], de_onde[1] - ponto[1]
    n = math.hypot(vx, vy) or 1.0
    return (vx / n, vy / n)


# --------------------------------------------------------------------------
# Construcao

def construir(dados_mapa, col_pai, centro_arena, pacote_planos, abortar=True):
    """Devolve (objetos_postos, reprovados).

    `abortar=False` existe para UM caso: montar a cena de conferencia que
    mostra a ele o defeito que o portao pegou. A cena sai carimbada -- cada
    letreiro reprovado ganha `letreiro_reprovado` no objeto -- e nao serve de
    entrega. Nao e' um jeito de passar por cima do portao: o build normal
    aborta, e quem chamar com False esta dizendo em codigo que quer a prova.
    """
    bpy = _bpy()
    import terreno
    import planos as planos_mod

    if not CONTRATO.exists():
        return 0, 0

    cont = json.loads(CONTRATO.read_text(encoding="utf-8"))
    fonte = _fonte(cont["tipografia"]["arquivo"])
    escala = cont["escala_por_nivel"]
    pain = cont["painel"]

    cena = bpy.context.scene
    sv = sensor_vertical_mm(cena.render.resolution_x, cena.render.resolution_y)

    mat_letra = _mat("MAT_LETREIRO", cont["cor"]["texto"], 0.6,
                     cont["cor"]["emissao"])
    mat_prancha = _mat("MAT_LETREIRO_PRANCHA", (0.32, 0.20, 0.12), 0.75)
    mat_faixa = _mat("MAT_LETREIRO_FAIXA", (0.93, 0.93, 0.92), 0.55)
    mat_ferro = _mat("MAT_LETREIRO_FERRO", (0.18, 0.18, 0.19), 0.45)

    col = bpy.data.collections.new("LETREIROS")
    col_pai.children.link(col)

    por_id = {p["id"]: p for p in pacote_planos["planos"]}
    postos, reprovados, relatorio = 0, [], []

    for item in cont["letreiros"]:
        pid = item["plano"]
        plano = por_id.get(pid)
        if plano is None:
            print(f"  aviso: {pid} nao existe em planos.json -- "
                  f"'{item['texto'][:30]}' nao foi posto")
            continue

        alvo = plano.get("alvo", {})
        p = terreno.ponto_da_zona(dados_mapa, alvo.get("rotulo", ""),
                                  alvo.get("ocorrencia", 0))
        if p is None:
            print(f"  aviso: alvo de {pid} nao existe na planta -- "
                  f"'{item['texto'][:30]}' nao foi posto")
            continue

        sup = item["suporte"]
        modo = sup["modo"]
        hosp = (bpy.data.objects.get(sup["objeto_na_cena"])
                if sup.get("objeto_na_cena") else None)
        if sup.get("objeto_na_cena") and hosp is None:
            raise SystemExit(
                f"ABORTADO -- {pid} declara suporte no objeto "
                f"{sup['objeto_na_cena']!r}, que nao existe na cena.\n"
                f"Suporte e' declarado em data/letreiros.json justamente para "
                f"nao casar por nome parecido (armadilha 38).")

        # Camera e mira no MEIO do plano. A mira do meio importa tanto quanto a
        # camera: em plano com `_alvo_fim` ela viaja, e plantar o letreiro no
        # alvo inicial e' plantar onde a camera so' olha no primeiro segundo.
        # No meio, ele nasce centrado e sai de quadro pelas duas pontas, que a
        # janela abaixo apara.
        cam_meio, mira_meio = planos_mod.amostra(plano, 0.5, centro_arena)
        p = (mira_meio[0], mira_meio[1])
        f = float(plano["lente_mm"])
        frac = escala[item["nivel"]]["fracao_da_altura"]

        objs, ancora, normal, larg_disp, z_centro = _assentar(
            modo, hosp, p, cam_meio, centro_arena, terreno, plano, mira_xy=p)

        # Dimensionar contra o plano INTEIRO castiga o letreiro pelo instante
        # em que ele nem esta em quadro. No P11 a mira viaja e a camera chega a
        # 80 m do painel numa ponta do sobrevoo -- dimensionado por esses 80 m,
        # a letra saia com 3,71 m e a prancha com 11 m de altura, para ser lida
        # a 19 m. A conta agora vale so' o trecho em que ele aparece.
        cam = bpy.data.objects.get(f"CAM_{pid}")
        q_ini, q_fim = plano["_quadro_ini"], plano["_quadro_fim"]
        t0, t1 = _janela_do_ponto(cena, cam, (ancora[0], ancora[1], z_centro),
                                  q_ini, q_fim) if cam else (0.0, 1.0)
        t0, t1 = _aparar_por_distancia(
            plano, (ancora[0], ancora[1], z_centro), centro_arena, t0, t1)
        d_menor, d_maior = distancias_no_plano(
            plano, (ancora[0], ancora[1], z_centro), centro_arena,
            t_ini=t0, t_fim=t1)
        h, w_teto = dimensionar(frac, d_maior, d_menor, f, sv)
        h_teto = altura_maxima(d_menor, f, sv)

        margem = pain["margem_fracao"] * h
        # A prancha nao pode passar do que o quadro aguenta NEM do que o
        # hospedeiro tem de fachada. Quem for menor manda.
        larg_prancha = min(w_teto, larg_disp)
        larg_caixa = max(larg_prancha - 2 * margem, h * 1.2)

        alvo_texto = _texto(f"Letreiro_{pid}", item["texto"], h, larg_caixa,
                            fonte, mat_letra, col)
        bw, bh = _medir(alvo_texto)
        objs.append(alvo_texto)

        apoio_obj = None
        bh_apoio = 0.0
        if item.get("apoio"):
            h_ap = escala["apoio"]["fracao_da_altura"] * d_maior * sv / f
            apoio_obj = _texto(f"Apoio_{pid}", item["apoio"], h_ap, larg_caixa,
                               fonte, mat_letra, col)
            _, bh_apoio = _medir(apoio_obj)
            bh_apoio += h * 0.35          # respiro entre nome e descricao
            objs.append(apoio_obj)

        bloco_alt = bh + bh_apoio
        prancha_alt = bloco_alt + 2 * margem
        prancha_larg = max(bw + 2 * margem, prancha_alt * pain["proporcao_minima"])
        prancha_larg = min(prancha_larg, larg_prancha)

        # -------- veredito, antes de posicionar qualquer coisa
        frac_larg = prancha_larg * f / (d_menor * SENSOR_HORIZONTAL_MM)
        frac_alt_perto = prancha_alt * f / (d_menor * sv)
        frac_alt_longe = h * f / (d_maior * sv)
        # Obliquidade: a letra esta numa superficie, e superficie tem lado.
        # Se a camera olha a fachada de esguelha, nao ha tamanho de letra que
        # salve -- a linha encolhe por cosseno e o texto vira risco. Este teste
        # existe porque no P02 e no P22 a prancha reprovava por ALTURA, e a
        # altura era so' o sintoma: a camera olha o portal a 77 graus da
        # fachada. Reprovar pelo sintoma manda consertar a coisa errada.
        #
        # Medida no MELHOR instante do trecho em que ele aparece, nao no meio
        # do plano. A pergunta certa nao e' "esta de frente na metade?" e sim
        # "existe um momento em que da' para ler?" -- e a janela abaixo cuida
        # de so' acender nesse momento. Medir so' o meio reprovava o P05 por
        # 0,4 grau enquanto a camera passava de frente para ele um segundo
        # depois.
        graus = 180.0
        for i in range(9):
            t = t0 + (t1 - t0) * i / 8
            cam_t, _ = planos_mod.amostra(plano, t, centro_arena)
            v = _normal_para((ancora[0], ancora[1]), cam_t)
            cos = max(-1.0, min(1.0, normal[0] * v[0] + normal[1] * v[1]))
            graus = min(graus, math.degrees(math.acos(cos)))

        estado = "ok"
        if modo != "painel_plantado" and graus > OBLIQUIDADE_MAX_GRAUS:
            estado = f"DE ESGUELHA ({graus:.0f} graus da fachada)"
        elif prancha_alt > h_teto:
            estado = f"ALTO ({prancha_alt:.1f} m, cabe {h_teto:.1f})"
        elif frac_larg > SEGURANCA + 1e-6:
            estado = f"LARGO ({frac_larg*100:.0f}% do quadro)"
        elif frac_alt_longe < frac - 1e-4:
            estado = f"PEQUENO ({frac_alt_longe*100:.1f}%, regra {frac*100:.1f}%)"
        if estado != "ok":
            reprovados.append((pid, estado))

        # -------- prancha e posicionamento
        prancha = _prancha_do_modo(modo, pid, prancha_larg, prancha_alt,
                                   pain["espessura_m"], col,
                                   mat_prancha, mat_faixa, mat_ferro,
                                   ancora, normal, z_centro)
        objs = prancha + objs

        folga = pain["folga_da_letra_m"] + pain["espessura_m"] / 2
        px = ancora[0] + normal[0] * folga
        py = ancora[1] + normal[1] * folga
        topo = z_centro + prancha_alt / 2 - margem
        _encaixar_texto(alvo_texto, normal, (px, py), topo)
        if apoio_obj:
            _encaixar_texto(apoio_obj, normal, (px, py), topo - bh - h * 0.35)

        # -------- quanto tempo ele fica realmente em quadro
        # Aqui quem mede e' o Blender, com a camera do plano montada. Tudo que
        # veio antes foi conta de distancia, e distancia nao ve a mira viajar.
        fps = pacote_planos["fps"]
        dur_s = (q_fim - q_ini) / fps
        janela = janela_em_quadro(cena, cam, objs, q_ini, q_fim) if cam else None
        visivel_s = (janela[1] - janela[0]) / fps if janela else 0.0

        if estado == "ok":
            if janela is None:
                estado = "NUNCA EM QUADRO"
            elif visivel_s < TEMPO_MINIMO_S:
                estado = f"SO {visivel_s:.1f}s em quadro (de {dur_s:.1f}s)"
            if estado != "ok":
                reprovados.append((pid, estado))

        for o in objs:
            o["texto_do_cliente"] = item["texto"]
            o["audio"] = item["audio"]
            o["modo_do_letreiro"] = modo
            o["segundos_em_quadro"] = round(visivel_s, 2)
            o["procedencia"] = ("suporte declarado em data/letreiros.json; "
                                "modo levantado do footage, "
                                "docs/COMO-O-PARQUE-ESCREVE.md")
            if estado != "ok":
                o["letreiro_reprovado"] = estado
        _so_no_proprio_plano(objs, *(janela or (q_ini, q_fim)), fps)
        postos += len(objs)
        relatorio.append((pid, modo, d_menor, d_maior, h, prancha_larg,
                          prancha_alt, frac_alt_longe, visivel_s, dur_s, estado))

    _imprimir(relatorio, postos, reprovados,
              cena.render.resolution_x, cena.render.resolution_y, sv)
    if reprovados and abortar:
        raise SystemExit(
            f"ABORTADO -- {len(reprovados)} letreiro(s) reprovados: "
            + "; ".join(f"{p} {e}" for p, e in reprovados) + "\n"
            f"Ate 15/08 isto passava verde porque so' o PISO de 8% era "
            f"conferido, e o piso nao e' o teto.\n"
            f"Para MOSTRAR o defeito em quadro sem furar o portao: "
            f"build_scene.py --letreiros-so-avisam")
    if reprovados:
        print(f"  AVISO: {len(reprovados)} reprovados, e esta cena so' serve "
              f"de CONFERENCIA -- objetos carimbados com `letreiro_reprovado`")
    return postos, len(reprovados)


def _assentar(modo, hosp, alvo_xy, cam_meio, centro, terreno, plano,
              mira_xy=None):
    """Onde a prancha encosta. Devolve (objs_extra, ancora_xy, normal,
    largura_disponivel, z_do_centro)."""
    if modo in ("letra_no_painel", "chapa_na_parede"):
        (cx, cy), normal, larg, z0, z1 = _fachada(hosp, cam_meio, mira_xy)
        altura_parede = z1 - z0
        # A faixa senta no alto da parede, que e onde o parque poe: no Recinto
        # de Leiloes ela ocupa a marquise, acima das aberturas.
        fatia = 0.80 if modo == "letra_no_painel" else 0.60
        z = z0 + altura_parede * fatia
        return [], (cx, cy), normal, larg, z

    if modo == "placa_suspensa":
        # A tabua atravessa o VAO, e o vao e' sempre o eixo mais largo do
        # portal -- nao o que a camera calha de encarar. Usar `_fachada` aqui
        # deixaria a placa com a largura da espessura do portal (3,2 m) quando
        # a camera chegasse pelo lado, e foi o que aconteceu na primeira volta.
        (cx, cy), normal, larg, z0, z1 = _vao_do_portal(hosp, cam_meio)
        z = z1 - (z1 - z0) * 0.34      # pendurada sob a travessa
        return [], (cx, cy), normal, larg * 0.72, z

    # painel_plantado: o unico que inventa estrutura, e por isso e o ultimo
    # recurso. Fica no proprio alvo -- aproximar era o que quebrava o push-in.
    normal = _normal_para(alvo_xy, cam_meio)
    z_chao = terreno.elevacao(alvo_xy[0], alvo_xy[1], centro)
    z = z_chao + float(plano.get("mira_alt_m", 3.0)) + 1.2
    # E precisa passar por cima do que estiver plantado ali. No P11 a mira do
    # meio cai EM CIMA da fileira de pavilhoes, e a prancha nascia dentro do
    # telhado: o portao aprovava (cabia no quadro) e o still mostrava a segunda
    # linha do texto serrada pela cumeeira. Portao que mede enquadramento nao
    # ve interseccao -- quem viu foi o quadro.
    teto = _teto_por_perto(alvo_xy, raio=30.0)
    if teto is not None:
        z = max(z, teto + 1.5)
    return [], (alvo_xy[0], alvo_xy[1]), normal, 1e9, z


def _teto_por_perto(xy, raio=30.0):
    """Topo da coisa mais alta construida em volta de `xy`, ou None.

    Olha so' o que e' edificacao -- vegetacao e povoamento ficam de fora de
    proposito: arvore se atravessa sem parecer erro, telhado nao.
    """
    bpy = _bpy()
    import mathutils
    fora = {"POVOAMENTO", "LETREIROS", "CAMERA", "MOBILIARIO", "DESCARTADO"}
    alto = None
    for o in bpy.data.objects:
        if o.type != "MESH" or {c.name for c in o.users_collection} & fora:
            continue
        if o.name.startswith(("Arvore", "Arbusto", "Grama", "Via_", "Terreno")):
            continue
        d = math.dist((o.matrix_world.translation.x, o.matrix_world.translation.y), xy)
        if d > raio:
            continue
        topo = max((o.matrix_world @ mathutils.Vector(c)).z for c in o.bound_box)
        alto = topo if alto is None else max(alto, topo)
    return alto


def _prancha_do_modo(modo, pid, larg, alt, esp, col, mat_prancha, mat_faixa,
                     mat_ferro, ancora, normal, z):
    """Constroi a superficie onde a letra vai, no vocabulario do lugar."""
    feitos = []
    if modo == "letra_no_painel":
        faixa = _caixa(f"Faixa_{pid}", larg, alt, esp * 0.6, col, mat_faixa)
        faixa.location = (ancora[0], ancora[1], z)
        _orientar_prancha(faixa, normal)
        feitos.append(faixa)

    elif modo == "chapa_na_parede":
        chapa = _caixa(f"Chapa_{pid}", larg, alt, esp * 0.4, col, mat_faixa)
        chapa.location = (ancora[0], ancora[1], z)
        _orientar_prancha(chapa, normal)
        feitos.append(chapa)

    elif modo == "placa_suspensa":
        tabua = _caixa(f"Tabua_{pid}", larg, alt, esp, col, mat_prancha)
        tabua.location = (ancora[0], ancora[1], z)
        _orientar_prancha(tabua, normal)
        feitos.append(tabua)
        # Duas correntes ate a travessa, como na Pista de Laco (referencia A).
        for lado in (-1, 1):
            c = _cilindro(f"Corrente_{pid}_{'DE'[lado > 0]}", 0.035, alt * 0.55,
                          col, mat_ferro, lados=6)
            dx, dy = -normal[1], normal[0]      # perpendicular horizontal
            c.location = (ancora[0] + dx * larg * 0.33 * lado,
                          ancora[1] + dy * larg * 0.33 * lado,
                          z + alt * 0.77)
            feitos.append(c)

    else:  # painel_plantado
        tabua = _caixa(f"Prancha_{pid}", larg, alt, esp, col, mat_prancha)
        tabua.location = (ancora[0], ancora[1], z)
        _orientar_prancha(tabua, normal)
        feitos.append(tabua)
        pe = z - alt / 2
        for lado in (-1, 1):
            m = _cilindro(f"Montante_{pid}_{'DE'[lado > 0]}", 0.10, pe * 0 + 3.0,
                          col, mat_ferro)
            dx, dy = -normal[1], normal[0]
            m.location = (ancora[0] + dx * larg * 0.42 * lado,
                          ancora[1] + dy * larg * 0.42 * lado,
                          pe - 1.5 + 0.2)
            feitos.append(m)
    return feitos


def _imprimir(relatorio, postos, reprovados, larg_px, alt_px, sv):
    print(f"  letreiros .......... {postos} objetos "
          f"({len(relatorio)} letreiros)")
    print(f"     quadro {larg_px}x{alt_px} "
          f"({larg_px/alt_px:.3f}:1), sensor vertical {sv:.2f} mm")
    print(f"     {'plano':5} {'modo':16} {'perto':>6} {'longe':>6} "
          f"{'letra':>6} {'prancha':>13} {'% alt':>6} {'em quadro':>12}  estado")
    for (pid, modo, dmin, dmax, h, pl, pa, fa, vis, dur, est) in relatorio:
        print(f"     {pid:5} {modo:16} {dmin:5.0f}m {dmax:5.0f}m "
              f"{h:5.2f}m {pl:5.1f}x{pa:4.1f}m {fa*100:5.1f}% "
              f"{vis:5.1f}s de{dur:5.1f}s  {est}")
    if not reprovados:
        print("     todos cumprem o PISO (>= regra), o TETO (<= 90% do quadro) "
              "e ficam em quadro")


# --------------------------------------------------------------------------
# Conferencia sem Blender

def _conferir():
    """Pre-voo puro: quanta largura cada plano oferece, e quanta a frase pede.

    Nao substitui o build -- a largura real do bloco quem mede e o Blender,
    porque quem quebra a linha e' ele. Serve para ver, sem abrir a cena, quais
    planos estao no limite.
    """
    import planos as planos_mod
    from terreno import carregar_mapa, centro_da_arena

    cont = json.loads(CONTRATO.read_text(encoding="utf-8"))
    dados = carregar_mapa()
    centro = centro_da_arena(dados)
    pacote = planos_mod.carregar(dados=dados)
    por_id = {p["id"]: p for p in pacote["planos"]}
    escala = cont["escala_por_nivel"]

    larg_px, alt_px = 2560, 1440
    sv = sensor_vertical_mm(larg_px, alt_px)
    print(f"pre-voo em {larg_px}x{alt_px} ({larg_px/alt_px:.3f}:1), "
          f"sensor vertical {sv:.2f} mm\n")
    print(f"{'plano':5} {'modo':16} {'perto':>6} {'longe':>6} {'letra':>6} "
          f"{'larg max':>9}  {'razao':>6}")
    for item in cont["letreiros"]:
        p = por_id.get(item["plano"])
        if p is None:
            continue
        alvo = p.get("_alvo")
        if not alvo:
            continue
        z = 0.0
        dmin, dmax = distancias_no_plano(p, (alvo[0], alvo[1], z), centro)
        f = float(p["lente_mm"])
        frac = escala[item["nivel"]]["fracao_da_altura"]
        h, w = dimensionar(frac, dmax, dmin, f, sv)
        print(f"{item['plano']:5} {item['suporte']['modo']:16} {dmin:5.0f}m "
              f"{dmax:5.0f}m {h:5.2f}m {w:8.1f}m  {w/h:5.1f}x")
    print("\n'razao' e' quantas alturas de letra cabem na largura maxima. "
          "Frase\nque precise de mais que isso tem de quebrar em linhas.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--conferir", action="store_true")
    a = ap.parse_args()
    if a.conferir:
        _conferir()
    else:
        ap.print_help()
