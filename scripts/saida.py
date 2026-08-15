#!/usr/bin/env python3
"""Monta a arvore do compositor com os tres slots de saida da cena.

Roda DENTRO do Blender. Contrato declarado em `data/saida.json`.

**O bloqueador que este arquivo existe para resolver.** A decisao do Natan em
15/08 foi "EXR MultiLayer + Cryptomatte". A leitura ingenua disso e ligar
multilayer, `color_depth = 16`, `exr_codec = DWAA` e marcar os passes de
crypto -- e o resultado sai QUEBRADO, em silencio:

- Cryptomatte guarda o hash do nome do objeto como um float 32 dentro do canal.
  A especificacao exige lossless e 32 bits por causa disso.
- **DWAA/DWAB e lossy.** Ele altera o valor do pixel. Num pixel de cor, alterar
  um pouquinho e imperceptivel; num pixel que carrega um HASH, alterar um
  pouquinho e trocar o objeto por outro. A extracao de matte vira ruido.
- **Half tem 10 bits de mantissa.** Nao representa o hash nem sem compressao.

E o defeito nao aparece no render: aparece semanas depois, no dia em que alguem
for isolar uma tenda no Resolve e nao conseguir. Por isso a saida e separada em
tres, e nao em uma:

    beauty  -- imagem: Half + DWAA. Comprime muito e ninguem ve a diferenca.
    data    -- valor: Full Float 32 + ZIP, lossless. Crypto, normal, depth.
    preview -- entrega: PNG 8, com o view transform aplicado.

**A outra armadilha, e ela e por slot:** `save_as_render`. Ligado, o slot recebe
o view transform da cena (AgX). O PNG PRECISA disso -- desligado, sai lavado. O
EXR NAO PODE ter isso -- ligado, o AgX fica assado dentro do arquivo e nao ha
Resolve que desfaca. A mesma chave, invertida entre os slots.

**Nota de API, e ela custou uma rodada:** no Blender 5.x o compositor deixou de
ser `scene.node_tree` e virou `scene.compositing_node_group`, um node group de
verdade; e o File Output trocou `layer_slots`/`file_slots` por
`file_output_items` mais `directory` e `file_name`. Codigo escrito para 4.x
morre com `AttributeError` aqui.

Uso, dentro do Blender:

    from saida import montar
    montar(cena, Path("F:/agroshow/render"))
"""

import json
from pathlib import Path

import bpy

RAIZ = Path(__file__).resolve().parent.parent
CONTRATO = RAIZ / "data" / "saida.json"

# Passe -> (atributo do view layer, nome do socket no no Render Layers).
#
# **Os nomes dos sockets mudaram no Blender 5.x** e sao por extenso: o socket
# do difuso direto chama "Diffuse Direct", nao "DiffDir". Codigo de 4.x liga o
# passe, nao acha o socket e cria um slot que sai PRETO -- sem erro na tela.
# Aqui o nome do socket e o da build, e o rotulo curto (a chave do dicionario)
# e o nome da camada DENTRO do EXR, que e a convencao que os compositores
# esperam achar. Os dois nao sao a mesma coisa e por isso sao dois campos.
PASSES_LUZ = {
    "DiffDir":  ("use_pass_diffuse_direct",    "Diffuse Direct"),
    "DiffInd":  ("use_pass_diffuse_indirect",  "Diffuse Indirect"),
    "GlossDir": ("use_pass_glossy_direct",     "Glossy Direct"),
    "GlossInd": ("use_pass_glossy_indirect",   "Glossy Indirect"),
    "Emit":     ("use_pass_emit",              "Emission"),
    "Env":      ("use_pass_environment",       "Environment"),
    "AO":       ("use_pass_ambient_occlusion", "Ambient Occlusion"),
}

PASSES_DADO = {
    "Normal":   ("use_pass_normal",   "Normal"),
    "Depth":    ("use_pass_z",        "Depth"),
    "Position": ("use_pass_position", "Position"),
    "Vector":   ("use_pass_vector",   "Vector"),
}

# socket da build -> rotulo curto da camada no EXR.
ROTULO = {socket: curto for curto, (_, socket) in
          list(PASSES_LUZ.items()) + list(PASSES_DADO.items())}

# Tipo de socket por passe, e cada um economiza disco quando esta certo.
# Depth e UM canal; Normal e Position sao TRES (XYZ); Cryptomatte precisa dos
# quatro, porque cada camada empacota dois pares (id, cobertura). Declarar
# tudo como RGBA grava um canal morto por pixel em cada quadro -- a 4.635
# quadros e float 32, um canal morto custa 63 GB.
TIPO_DE_SOCKET = {
    "Depth": "FLOAT",
    "Normal": "VECTOR",
    "Position": "VECTOR",
}


def carregar(caminho=None):
    return json.loads(Path(caminho or CONTRATO).read_text(encoding="utf-8"))


def ligar_passes(view_layer, contrato):
    """Liga os passes pedidos e devolve o que de fato ligou.

    Devolve o LIGADO, e nao o pedido, porque build de Blender diferente tem
    passe diferente -- e um slot ligado a um socket inexistente sai preto sem
    erro nenhum na tela.
    """
    ligados = {"luz": [], "dado": [], "crypto": []}

    pedidos_beauty = set(contrato["slots"]["beauty"]["passes"])
    for nome, (attr, socket) in PASSES_LUZ.items():
        if nome in pedidos_beauty and hasattr(view_layer, attr):
            setattr(view_layer, attr, True)
            ligados["luz"].append(socket)

    pedidos_data = set(contrato["slots"]["data"]["passes"])
    for nome, (attr, socket) in PASSES_DADO.items():
        if nome in pedidos_data and hasattr(view_layer, attr):
            setattr(view_layer, attr, True)
            ligados["dado"].append(socket)

    cm = contrato["cryptomatte"]
    view_layer.use_pass_cryptomatte_object = bool(cm.get("objeto"))
    view_layer.use_pass_cryptomatte_material = bool(cm.get("material"))
    view_layer.use_pass_cryptomatte_asset = bool(cm.get("asset"))
    view_layer.pass_cryptomatte_depth = int(cm["levels"])

    # Cada camada de cryptomatte carrega DOIS pares (id, cobertura) nos quatro
    # canais, entao levels=2 da 1 socket e levels=6 da 3. Errar essa conta
    # deixa socket de fora e o matte perde a cauda da cobertura.
    n_camadas = (int(cm["levels"]) + 1) // 2
    for base, ligado in (("CryptoObject", cm.get("objeto")),
                         ("CryptoMaterial", cm.get("material")),
                         ("CryptoAsset", cm.get("asset"))):
        if ligado:
            ligados["crypto"] += [f"{base}{i:02d}" for i in range(n_camadas)]

    return ligados


def _aplicar_formato(fmt, slot):
    # `media_type` PRIMEIRO: no Blender 5.x ele FILTRA o enum de `file_format`.
    # Com media_type em MULTI_LAYER_IMAGE, o unico formato aceito e o EXR
    # multilayer e atribuir "PNG" levanta TypeError. Invertida, a ordem quebra.
    if hasattr(fmt, "media_type"):
        fmt.media_type = ("MULTI_LAYER_IMAGE"
                          if slot["formato"] == "OPEN_EXR_MULTILAYER" else "IMAGE")
    fmt.file_format = slot["formato"]
    fmt.color_depth = str(slot["profundidade"])
    fmt.color_mode = "RGBA" if slot["formato"] == "PNG" else "RGB"
    if slot["formato"].startswith("OPEN_EXR") and slot["codec"] != "NONE":
        fmt.exr_codec = slot["codec"]


def _saida_de_arquivo(nos, nome, slot, raiz_saida, entradas):
    """Cria um no File Output configurado por um slot do contrato."""
    no = nos.new("CompositorNodeOutputFile")
    no.name = no.label = f"SAIDA_{nome}"
    no.directory = str(Path(raiz_saida) / slot["pasta"]) + "\\"
    no.use_file_extension = True
    # O nome vem de `nomear()`, chamado antes de cada quadro. Deixado vazio, o
    # Blender inventa o nome a partir do .blend ou do socket -- o smoke test
    # gravou `Untitled.exr` e `Image.png`, o mesmo arquivo por cima a cada
    # quadro. Nome de arquivo e o que separa render retomavel de render que
    # apaga a si mesmo. Cinco digitos porque e o que o `encode.sh` procura
    # (`%05d.png`) -- quatro digitos entregariam PNG que o ffmpeg nao enxerga.
    no.file_name = "00000"

    _aplicar_formato(no.format, slot)

    # A chave que inverte entre imagem e dado. Ver o docstring do modulo.
    no.save_as_render = bool(slot["save_as_render"])

    multilayer = slot["formato"] == "OPEN_EXR_MULTILAYER"
    no.file_output_items.clear()
    for rotulo, socket in entradas:
        item = no.file_output_items.new(TIPO_DE_SOCKET.get(socket, "RGBA"), rotulo)
        item.save_as_render = bool(slot["save_as_render"])
        # Num multilayer o nome do item e a CAMADA dentro do arquivo. Nos
        # demais formatos ele e COLADO no nome do arquivo, e foi assim que o
        # primeiro smoke gravou `00001Image.png` -- que o `encode.sh` nao acha,
        # porque ele procura `%05d.png`. Nome vazio devolve `00001.png`.
        if not multilayer:
            item.name = ""

    return no


def montar(cena, raiz_saida, contrato=None, verbose=True):
    """Reconstroi a arvore do compositor com os tres slots. Idempotente."""
    contrato = contrato or carregar()
    # ABSOLUTO, sempre. O Blender resolve caminho relativo contra a raiz do
    # DRIVE corrente, nao contra o cwd: `out/provafinal` virou `C:\out\...` no
    # primeiro teste ponta a ponta -- longe do projeto e, pior, longe do F:,
    # que e o disco que tem espaco para o render.
    raiz_saida = Path(raiz_saida).resolve()
    vl = cena.view_layers[0]
    ligados = ligar_passes(vl, contrato)

    cena.use_nodes = True
    arvore = cena.compositing_node_group
    if arvore is None:
        arvore = bpy.data.node_groups.new("COMPOSITOR_AGROSHOW", "CompositorNodeTree")
        cena.compositing_node_group = arvore
    arvore.nodes.clear()

    render = arvore.nodes.new("CompositorNodeRLayers")
    render.name = render.label = "RENDER"
    render.scene = cena
    render.layer = vl.name
    render.location = (-500, 0)

    disponiveis = {s.name for s in render.outputs}

    def presentes(nomes):
        # Filtra pelo que o no de fato oferece. Passe pedido que esta build nao
        # tem sumiria aqui, e e melhor sumir com AVISO do que virar slot preto.
        faltando = [n for n in nomes if n not in disponiveis]
        if faltando and verbose:
            print(f"  AVISO: socket ausente no Render Layers: {faltando}")
        return [n for n in nomes if n in disponiveis]

    plano = {
        "beauty": presentes(["Image"] + ligados["luz"]),
        "data": presentes(ligados["crypto"] + ligados["dado"]),
        "preview": presentes(["Image"]),
    }

    nos_criados = {}
    for i, (nome, sockets) in enumerate(plano.items()):
        if not sockets:
            if verbose:
                print(f"  slot {nome}: NENHUM socket disponivel -- nao criado")
            continue
        # 'Image' vira 'Combined' dentro do EXR: e o nome que todo compositor
        # espera achar, e 'Image' num multilayer confunde quem abre o arquivo.
        # Os demais viram o rotulo curto de sempre ("Diffuse Direct" -> DiffDir).
        entradas = [(("Combined" if s == "Image" else ROTULO.get(s, s))
                     if nome != "preview" else s, s)
                    for s in sockets]

        no = _saida_de_arquivo(arvore.nodes, nome, contrato["slots"][nome],
                               raiz_saida, entradas)
        no.location = (300, 400 - i * 500)
        for j, (_, socket) in enumerate(entradas):
            arvore.links.new(render.outputs[socket], no.inputs[j])
        nos_criados[nome] = no

        if verbose:
            s = contrato["slots"][nome]
            print(f"  slot {nome:8s} {s['formato']:22s} {s['profundidade']}bit "
                  f"{s['codec']:5s} save_as_render={str(s['save_as_render']):5s} "
                  f"{len(entradas)} camada(s): "
                  f"{', '.join(r for r, _ in entradas)}")

    # O `render.filepath` continua existindo so para o `write_still` do Blender
    # nao despejar quadro solto onde nao deve. As saidas de verdade sao os
    # File Output acima.
    cena.render.filepath = str(Path(raiz_saida) / "_descartar_")

    return nos_criados


def nomear(nos, quadro):
    """Crava o numero do quadro no nome dos arquivos dos tres slots.

    Chamar ANTES de cada `bpy.ops.render.render()`. Sem isto o File Output
    grava sempre com o mesmo nome e cada quadro apaga o anterior -- o que
    tambem quebra a retomada do `render_shots.py`, que decide o que ja foi
    feito olhando o arquivo em disco.
    """
    for no in nos.values():
        no.file_name = f"{quadro:05d}"


def caminhos_do_quadro(raiz_saida, quadro, contrato=None):
    """Onde cada slot grava o quadro N. Fonte unica para o teste de existencia.

    O File Output numera sozinho pelo frame CORRENTE da cena, e o
    `render_shots.py` faz `frame_set(quadro)` antes de cada render -- entao o
    numero no nome ja e o quadro certo, sem intervencao.

    O `preview` sai como `preview/00001.png`, que e exatamente o `%05d.png`
    que o `encode.sh` procura. A cadeia de entrega para o telao nao muda.
    """
    contrato = contrato or carregar()
    raiz = Path(raiz_saida).resolve()
    fora = {}
    for nome, slot in contrato["slots"].items():
        ext = ".png" if slot["formato"] == "PNG" else ".exr"
        fora[nome] = raiz / slot["pasta"] / f"{quadro:05d}{ext}"
    return fora
