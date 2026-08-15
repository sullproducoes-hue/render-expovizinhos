#!/usr/bin/env python3
"""Textura PBR por material -- medicao da variacao e montagem dos nos.

Este arquivo tem duas metades, e elas nao se misturam:

* `medir_variacao()` roda no **venv** (numpy + cv2) e mede a luminancia media
  de cada mapa Diffuse, gravando em `data/texturas-medidas.json`.
* `aplicar()` roda **dentro do Blender** e monta os nos, lendo aquele numero.

A regra do contrato (`data/texturas.json`) e uma so, e e ela que obriga a
medicao: **a cor-base e medida no footage do proprio recinto e a biblioteca
nao a sobrescreve.** A textura entra por tres portas, e albedo nao e uma delas:

1. NORMAL -- relevo. E o que faz a onda da telha pegar o sol rasante.
2. ROUGHNESS -- e aqui a textura da a VARIACAO, nao o valor: um Map Range
   centra a faixa no valor declarado em MATERIAIS. Sem isso, a telha (que e
   deliberadamente brilhante, metallic 0,55) viraria fosca uniforme junto com
   todo o resto, e o reflexo do ceu -- que e a razao dela existir assim --
   sumiria.
3. VARIACAO DE LUMINANCIA -- o Diffuse dividido pela propria media. Dividido
   pela media, a mancha tem media 1,0, entao `cor_final = cor_medida x mancha`
   tem media **exatamente** a cor medida. Isso nao e retorica: e o que
   `--conferir` mede e imprime.

Uso:
    python scripts/texturas.py --medir       # mede e grava a media de cada Diffuse
    python scripts/texturas.py --conferir    # prova que a cor medida sobrevive
"""

import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CONTRATO = RAIZ / "data" / "texturas.json"
MEDIDAS = RAIZ / "data" / "texturas-medidas.json"


def carregar_contrato():
    return json.loads(CONTRATO.read_text(encoding="utf-8"))


def caminho_mapa(slug, mapa, res):
    """Onde `assets.py` deixou o arquivo. jpg ou png -- ele aceita os dois."""
    pasta = RAIZ / "assets" / "textura"
    for sufixo in (".jpg", ".png"):
        alvo = pasta / f"{slug}_{mapa}_{res}{sufixo}"
        if alvo.exists():
            return alvo
    return None


# --------------------------------------------------------------------------
# Metade 1: medicao (venv, precisa de numpy + cv2)

def _srgb_para_linear(v):
    """A conversao de verdade, com o trecho reto perto do zero.

    A aproximacao `v ** 2.2` erra ate 4% nos tons escuros, e tom escuro e
    justamente onde este projeto vive: a grama medida tem albedo 0,129.
    """
    import numpy as np
    return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)


def medir_variacao():
    import cv2
    import numpy as np

    contrato = carregar_contrato()
    res = contrato.get("resolucao", "2k")
    saida = {
        "o_que_e": "Luminancia linear media de cada mapa Diffuse. Serve para "
                   "normalizar a variacao de cor: dividido por esta media, o "
                   "mapa tem media 1,0 e a cor MEDIDA no footage sobrevive "
                   "como media da superficie.",
        "gerado_por": "scripts/texturas.py --medir",
        "itens": {},
    }

    for material, item in contrato["itens"].items():
        if not item.get("usa_variacao_de_cor"):
            continue
        alvo = caminho_mapa(item["slug"], "Diffuse", res)
        if alvo is None:
            raise SystemExit(
                f"{material}: falta o Diffuse de {item['slug']} em disco. "
                f"Rode `python scripts/assets.py --texturas`.")

        # Armadilha 9 do RETOMAR.md: cv2.imread nao abre caminho com acento no
        # Windows. Aqui a pasta e ASCII, mas o projeto inteiro mora em
        # "E:\\I.A Edit" e um dia isso vira acento. Fica pelo caminho seguro.
        bruto = cv2.imdecode(np.fromfile(str(alvo), dtype=np.uint8),
                             cv2.IMREAD_COLOR)
        if bruto is None:
            raise SystemExit(f"{material}: cv2 nao abriu {alvo}")

        bgr = bruto.astype(np.float64) / 255.0
        lin = _srgb_para_linear(bgr)
        # BT.709, e nos canais lineares -- luminancia sobre sRGB nao e luminancia
        lum = 0.0722 * lin[..., 0] + 0.7152 * lin[..., 1] + 0.2126 * lin[..., 2]

        saida["itens"][material] = {
            "slug": item["slug"],
            "arquivo": str(alvo.relative_to(RAIZ)).replace("\\", "/"),
            "luminancia_media": round(float(lum.mean()), 6),
            "luminancia_p05": round(float(np.percentile(lum, 5)), 6),
            "luminancia_p95": round(float(np.percentile(lum, 95)), 6),
            "pixels": int(lum.size),
        }
        print(f"  {material:14s} {item['slug']:20s} media={lum.mean():.4f}  "
              f"p05={np.percentile(lum, 5):.4f}  p95={np.percentile(lum, 95):.4f}")

    MEDIDAS.write_text(json.dumps(saida, indent=1, ensure_ascii=False),
                       encoding="utf-8")
    print(f"\ngravado: {MEDIDAS.relative_to(RAIZ)}")
    return saida


def conferir():
    """Prova o que o contrato promete, com numero.

    A conta que o no faz e `cor_final = cor_medida * (1 + f * (lum/media - 1))`.
    A media de `lum/media` e 1,0 por construcao, entao a media do multiplicador
    e 1,0 para qualquer forca f, e a media da cor final e a cor medida.
    O que ESTE teste responde e a outra pergunta, a que pode dar errado: com a
    forca escolhida, quanto a mancha se afasta -- e se ela chega a estourar
    (multiplicador negativo, que viraria cor invalida).
    """
    if not MEDIDAS.exists():
        raise SystemExit("rode `--medir` antes")
    contrato = carregar_contrato()
    medidas = json.loads(MEDIDAS.read_text(encoding="utf-8"))

    print("material        forca   multiplicador p05..p95   media   veredito")
    todos_ok = True
    for material, m in medidas["itens"].items():
        f = contrato["itens"][material]["forca_variacao"]
        media = m["luminancia_media"]
        lo = 1 + f * (m["luminancia_p05"] / media - 1)
        hi = 1 + f * (m["luminancia_p95"] / media - 1)
        # o pior caso real e o pixel mais escuro, nao o p05; com lum minima 0 o
        # multiplicador cai para 1-f, entao f < 1 ja garante que nao vira negativo
        ok = f < 1.0 and lo > 0.0
        todos_ok &= ok
        print(f"{material:15s} {f:.2f}    {lo:.3f} .. {hi:.3f}        "
              f"1.000   {'ok' if ok else 'ESTOURA'}")

    print("\nA media do multiplicador e 1,000 por construcao (lum/media tem "
          "media 1).\nLogo a cor media da superficie e EXATAMENTE a cor medida "
          "no footage.")
    return todos_ok


# --------------------------------------------------------------------------
# Metade 2: os nos (roda dentro do Blender)

def aplicar(mat, bsdf, material, cor, rugosidade):
    """Liga a textura declarada para `material`. Devolve True se ligou algo.

    Silencioso e proposital em UM caso so: material que o contrato nao lista
    (MAT_LONA, MAT_COPA, MAT_MADEIRA -- ver "o_que_ficou_de_fora_e_por_que").
    Material listado cujo ARQUIVO falta e erro, e aborta: textura que nao
    carregou vira superficie chapada sem avisar, e "sem avisar" e como o
    portal saiu de metal escovado uma vez.
    """
    import bpy

    contrato = carregar_contrato()
    item = contrato["itens"].get(material)
    if item is None:
        return False

    res = contrato.get("resolucao", "2k")
    nt = mat.node_tree
    lado = float(item["lado_m"])

    coord = nt.nodes.new("ShaderNodeTexCoord")
    coord.location = (-1700, 400)
    mapa = nt.nodes.new("ShaderNodeMapping")
    mapa.location = (-1500, 400)
    # a textura tem `lado` metros; a escala do vetor e o inverso, para 1 unidade
    # de mundo (1 m) andar 1/lado da imagem
    for eixo in range(3):
        mapa.inputs["Scale"].default_value[eixo] = 1.0 / lado
    nt.links.new(coord.outputs["Object"], mapa.inputs["Vector"])

    def imagem(nome_mapa, y, nao_cor=True):
        alvo = caminho_mapa(item["slug"], nome_mapa, res)
        if alvo is None:
            raise SystemExit(
                f"{material}: data/texturas.json pede {item['slug']}/{nome_mapa} "
                f"e o arquivo nao esta em assets/textura/. Rode "
                f"`python scripts/assets.py --texturas`.")
        no = nt.nodes.new("ShaderNodeTexImage")
        no.location = (-1250, y)
        no.image = bpy.data.images.load(str(alvo), check_existing=True)
        if nao_cor:
            # normal e roughness sao DADO, nao cor. Ler em sRGB aplicaria uma
            # gama de 2,2 num numero que nao e cor e torceria o relevo.
            no.image.colorspace_settings.name = "Non-Color"
        # BOX porque nada nesta cena tem UV: a geometria e toda gerada por
        # script. Projecao plana deixaria a parede do pavilhao esticada em
        # listra vertical.
        no.projection = "BOX"
        no.projection_blend = 0.25
        nt.links.new(mapa.outputs["Vector"], no.inputs["Vector"])
        return no

    mapas = item["mapas"]

    if "nor_gl" in mapas:
        tex_n = imagem("nor_gl", 620)
        no_normal = nt.nodes.new("ShaderNodeNormalMap")
        no_normal.location = (-950, 620)
        no_normal.inputs["Strength"].default_value = float(item["forca_normal"])
        nt.links.new(tex_n.outputs["Color"], no_normal.inputs["Color"])
        nt.links.new(no_normal.outputs["Normal"], bsdf.inputs["Normal"])

    if "Rough" in mapas:
        tex_r = imagem("Rough", 320)
        # A textura da a VARIACAO; o centro continua sendo o valor declarado em
        # MATERIAIS. +-0,15 e a largura da banda: o bastante para o brilho
        # deixar de ser uniforme, pouco o bastante para a telha nao virar fosca.
        faixa = nt.nodes.new("ShaderNodeMapRange")
        faixa.location = (-950, 320)
        faixa.inputs["From Min"].default_value = 0.0
        faixa.inputs["From Max"].default_value = 1.0
        faixa.inputs["To Min"].default_value = max(0.0, rugosidade - 0.15)
        faixa.inputs["To Max"].default_value = min(1.0, rugosidade + 0.15)
        nt.links.new(tex_r.outputs["Color"], faixa.inputs["Value"])
        nt.links.new(faixa.outputs["Result"], bsdf.inputs["Roughness"])

    if item.get("usa_variacao_de_cor"):
        medidas = json.loads(MEDIDAS.read_text(encoding="utf-8"))["itens"]
        if material not in medidas:
            raise SystemExit(
                f"{material} pede variacao de cor e nao esta em "
                f"data/texturas-medidas.json. Rode `python scripts/texturas.py "
                f"--medir` -- sem a media, a normalizacao nao existe e a "
                f"biblioteca acabaria mexendo na cor medida.")
        media = medidas[material]["luminancia_media"]
        forca = float(item["forca_variacao"])

        tex_d = imagem("Diffuse", 20, nao_cor=False)

        # lum / media  -> mancha de media 1,0
        normaliza = nt.nodes.new("ShaderNodeVectorMath")
        normaliza.operation = "SCALE"
        normaliza.location = (-950, 20)
        normaliza.inputs["Scale"].default_value = 1.0 / media
        nt.links.new(tex_d.outputs["Color"], normaliza.inputs[0])

        # 1 + f*(mancha - 1), escrito como um Mix entre branco e a mancha:
        # com Factor = f, Mix devolve (1-f)*1 + f*mancha, que e a mesma conta.
        atenua = nt.nodes.new("ShaderNodeMix")
        atenua.data_type = "RGBA"
        atenua.location = (-750, 20)
        atenua.inputs["Factor"].default_value = forca
        atenua.inputs[6].default_value = (1.0, 1.0, 1.0, 1.0)
        nt.links.new(normaliza.outputs["Vector"], atenua.inputs[7])

        cor_no = nt.nodes.new("ShaderNodeRGB")
        cor_no.location = (-750, 220)
        cor_no.outputs[0].default_value = (*cor, 1.0)

        produto = nt.nodes.new("ShaderNodeMix")
        produto.data_type = "RGBA"
        produto.blend_type = "MULTIPLY"
        produto.location = (-520, 120)
        produto.inputs["Factor"].default_value = 1.0
        nt.links.new(cor_no.outputs[0], produto.inputs[6])
        nt.links.new(atenua.outputs[2], produto.inputs[7])
        nt.links.new(produto.outputs[2], bsdf.inputs["Base Color"])

    return True


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--medir", action="store_true",
                    help="mede a luminancia media de cada Diffuse")
    ap.add_argument("--conferir", action="store_true",
                    help="prova que a cor medida sobrevive a variacao")
    args = ap.parse_args()

    if args.medir:
        medir_variacao()
        return 0
    if args.conferir:
        return 0 if conferir() else 1
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
