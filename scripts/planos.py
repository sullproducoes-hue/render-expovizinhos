#!/usr/bin/env python3
"""
Decupagem do filme: le data/planos.json, resolve cada plano contra a planta,
confere as velocidades e monta as cameras no Blender.

Por que existe: o percurso antigo era uma curva bezier unica por 16 pontos em
128 s. Medido contra a planta, isso da 1.152 m a 9,0 m/s -- 32 km/h. A faixa
cinematografica de drone e 1,3-2,2 m/s em orbita e push-in e 3,6-6,7 m/s em
sobrevoo. A 9 m/s nao se le placa, nao se reconhece area e nao se sente
escala, que e exatamente o que o cliente comprou.

A saida e cortar em planos. Cada plano tem alvo, lente, altura, movimento e
duracao proprios, declarados em dados. O corte tambem paga o resto: so se
renderiza o que esta em quadro (decisivo com 8-12 GB de VRAM), plano que
quebra se re-renderiza sozinho, e os quatro diferenciais ganham mais tela sem
esticar o filme.

Este modulo NAO importa bpy no topo. Rodar a conferencia nao precisa de
Blender nem de GPU:

    python3 scripts/planos.py --conferir
    python3 scripts/planos.py --tabela        # markdown para docs/PLANOS.md
"""

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from terreno import (carregar_mapa, centro_da_arena, elevacao, polar,
                     ponto_da_zona)

PLANOS_PADRAO = "data/planos.json"

# Faixas de velocidade, em m/s. Fora delas o plano nao le.
FAIXAS = {
    "push-in":    (1.3, 2.2),
    "orbita":     (1.3, 2.2),
    "travelling": (1.3, 2.2),
    "subida":     (1.3, 6.7),   # grua abre mais rapido sem quebrar a leitura
    "sobrevoo":   (3.6, 6.7),
}

AMOSTRAS = 64   # resolucao da medicao do caminho


# --------------------------------------------------------------------------
# Resolucao dos alvos

def resolver_alvo(alvo, dados, centro):
    """Devolve (x, y) em metros, ou levanta erro dizendo o que falta.

    Quatro tipos, na ordem de confiabilidade:
      rotulo   -- posicao real de um rotulo da planta
      polar    -- raio e azimute em volta do centro da arena (bacia medida)
      relativo -- deslocamento a partir de um rotulo (usado onde a planta e muda)
      xy       -- coordenada crua, ultimo recurso
    """
    tipo = alvo.get("tipo")

    if tipo == "rotulo":
        p = ponto_da_zona(dados, alvo["rotulo"], alvo.get("ocorrencia", 0))
        if p is None:
            raise ValueError(f"rotulo {alvo['rotulo']!r} nao existe na planta")
        return p

    if tipo == "polar":
        return polar(centro, alvo["raio_m"], alvo["azimute_deg"])

    if tipo == "relativo":
        p = ponto_da_zona(dados, alvo["rotulo"], alvo.get("ocorrencia", 0))
        if p is None:
            raise ValueError(f"rotulo base {alvo['rotulo']!r} nao existe na planta")
        return (p[0] + alvo.get("dx_m", 0.0), p[1] + alvo.get("dy_m", 0.0))

    if tipo == "xy":
        return (alvo["x"], alvo["y"])

    raise ValueError(f"tipo de alvo desconhecido: {tipo!r}")


# --------------------------------------------------------------------------
# Geometria do movimento

def amostra(plano, t, centro):
    """Posicao da camera e ponto de mira no instante t (0..1).

    O movimento e linear em t de proposito. A pesquisa de cinematografia de
    drone e explicita: velocidade constante e o que faz o movimento parecer
    deliberado. Aceleracao dentro do plano so entra se for declarada.
    """
    c = plano["camera"]
    s = plano.get("suavizacao", 0.0)
    if s:
        # smoothstep parcial: s=1 suaviza total, s=0 fica linear
        t = (1.0 - s) * t + s * (t * t * (3.0 - 2.0 * t))

    ax, ay = plano["_alvo"]
    if plano.get("_alvo_fim"):
        fx, fy = plano["_alvo_fim"]
        ax, ay = ax + (fx - ax) * t, ay + (fy - ay) * t

    az = c["azimute_deg"] + c.get("giro_deg", 0.0) * t
    dist = c["dist_ini_m"] + (c["dist_fim_m"] - c["dist_ini_m"]) * t
    alt = c["alt_ini_m"] + (c["alt_fim_m"] - c["alt_ini_m"]) * t

    cx, cy = polar((ax, ay), dist, az)
    cz = elevacao(cx, cy, centro) + alt
    mz = elevacao(ax, ay, centro) + plano.get("mira_alt_m", 3.0)
    return (cx, cy, cz), (ax, ay, mz)


def medir(plano, centro, amostras=AMOSTRAS):
    """Comprimento do caminho, velocidade media e velocidade de pico."""
    pontos = [amostra(plano, i / (amostras - 1), centro)[0]
              for i in range(amostras)]
    trechos = [math.dist(pontos[i], pontos[i - 1]) for i in range(1, len(pontos))]
    total = sum(trechos)
    dt = plano["duracao_s"] / (amostras - 1)
    return {
        "comprimento_m": total,
        "v_media": total / plano["duracao_s"],
        "v_pico": max(trechos) / dt if dt else 0.0,
    }


# --------------------------------------------------------------------------
# Carga

def carregar(caminho=PLANOS_PADRAO, dados=None):
    """Le a decupagem, resolve os alvos e crava as faixas de quadros."""
    doc = json.loads(Path(caminho).read_text(encoding="utf-8"))
    if dados is None:
        dados = carregar_mapa()
    centro = centro_da_arena(dados)
    fps = doc.get("fps", 30)

    planos, quadro = [], 1
    for p in doc["planos"]:
        p["_alvo"] = resolver_alvo(p["alvo"], dados, centro)
        p["_alvo_fim"] = (resolver_alvo(p["alvo_fim"], dados, centro)
                          if p.get("alvo_fim") else None)
        p["_quadros"] = int(round(p["duracao_s"] * fps))
        p["_quadro_ini"] = quadro
        p["_quadro_fim"] = quadro + p["_quadros"] - 1
        quadro = p["_quadro_fim"] + 1
        p.update({"_" + k: v for k, v in medir(p, centro).items()})
        planos.append(p)

    return {"planos": planos, "fps": fps, "centro": centro,
            "total_quadros": quadro - 1, "dados": dados}


# --------------------------------------------------------------------------
# Conferencia

def conferir(pacote, estrito=True):
    """Imprime a tabela e devolve a lista de problemas encontrados."""
    problemas = []
    fps = pacote["fps"]

    print(f"{'id':4} {'mov':11} {'dur':>5} {'lente':>6} {'metros':>7} "
          f"{'v.med':>6} {'v.pico':>7} {'faixa':>11}  ancora      titulo")
    print("-" * 108)

    for p in pacote["planos"]:
        lo, hi = FAIXAS[p["movimento"]]
        fora = not (lo <= p["_v_pico"] <= hi)
        marca = "  FORA" if fora else ""
        print(f"{p['id']:4} {p['movimento']:11} {p['duracao_s']:5.1f} "
              f"{p['lente_mm']:5}mm {p['_comprimento_m']:7.1f} "
              f"{p['_v_media']:6.2f} {p['_v_pico']:7.2f} "
              f"{lo:4.1f}-{hi:<4.1f} {p['ancora']:<10}  {p['titulo'][:34]}{marca}")

        if fora:
            problemas.append(
                f"{p['id']}: pico de {p['_v_pico']:.2f} m/s fora da faixa "
                f"{lo}-{hi} para {p['movimento']}")
        if p["movimento"] not in FAIXAS:
            problemas.append(f"{p['id']}: movimento desconhecido")
        if p["peso"] == "diferencial" and p["duracao_s"] < 8.0:
            problemas.append(
                f"{p['id']}: diferencial com {p['duracao_s']:.1f}s -- "
                f"o cliente pediu mais tela para os quatro")

    dur = pacote["total_quadros"] / fps
    print("-" * 108)
    print(f"  {len(pacote['planos'])} planos · {pacote['total_quadros']} quadros · "
          f"{dur:.0f} s ({dur/60:.1f} min) a {fps} fps")

    estimadas = [p["id"] for p in pacote["planos"] if p["ancora"] == "estimada"]
    derivadas = [p["id"] for p in pacote["planos"] if p["ancora"] == "derivada"]
    if derivadas:
        print(f"  derivadas da bacia (raios medidos): {', '.join(derivadas)}")
    if estimadas:
        print(f"  ESTIMADAS, nao existem na planta: {', '.join(estimadas)} "
              f"-- confirmar com o cliente")

    if problemas:
        print("\nPROBLEMAS:")
        for x in problemas:
            print(f"  - {x}")
    else:
        print("\n  todas as velocidades dentro da faixa cinematografica.")

    return problemas


def tabela_markdown(pacote):
    """Decupagem em markdown, para docs/PLANOS.md."""
    linhas = ["| # | Título na tela | Movimento | Lente | Dur. | m/s | Âncora |",
              "|---|---|---|---|---|---|---|"]
    for p in pacote["planos"]:
        titulo = p["titulo"] or "—"
        peso = " **·**" if p["peso"] == "diferencial" else ""
        linhas.append(
            f"| {p['id']}{peso} | {titulo} | {p['movimento']} | "
            f"{p['lente_mm']} mm | {p['duracao_s']:.1f} s | "
            f"{p['_v_media']:.1f} | {p['ancora']} |")
    return "\n".join(linhas)


# --------------------------------------------------------------------------
# Construcao no Blender (so aqui o bpy entra)

def montar_cameras(pacote, colecao, com_shake=True):
    """Cria uma camera por plano, com mira propria e marcador na timeline.

    A camera mira um alvo (constraint Track To) em vez de carregar inclinacao
    fixa. Era esse o defeito do percurso antigo: 18 graus fixos faziam a
    camera ver telhado de estande.
    """
    import bpy
    import math as _m

    cena = bpy.context.scene
    # Comeca no primeiro quadro do primeiro plano dado, nao sempre em 1: com
    # --plano ativo no build_scene.py, os planos escolhidos guardam a
    # numeracao absoluta do filme inteiro, e pode nao comecar em 1.
    cena.frame_start = pacote["planos"][0]["_quadro_ini"] if pacote["planos"] else 1
    cena.frame_end = pacote["total_quadros"]
    cena.render.fps = pacote["fps"]

    for p in pacote["planos"]:
        alvo = bpy.data.objects.new(f"MIRA_{p['id']}", None)
        alvo.empty_display_type = "SPHERE"
        alvo.empty_display_size = 2.0
        colecao.objects.link(alvo)

        dados_cam = bpy.data.cameras.new(f"CAM_{p['id']}")
        dados_cam.lens = float(p["lente_mm"])
        cam = bpy.data.objects.new(f"CAM_{p['id']}", dados_cam)
        colecao.objects.link(cam)

        mirar = cam.constraints.new("TRACK_TO")
        mirar.target = alvo
        mirar.track_axis = "TRACK_NEGATIVE_Z"
        mirar.up_axis = "UP_Y"

        # Duas chaves bastam: o movimento e linear dentro do plano.
        for quadro, t in ((p["_quadro_ini"], 0.0), (p["_quadro_fim"], 1.0)):
            pos, mira = amostra(p, t, pacote["centro"])
            cam.location = pos
            cam.keyframe_insert("location", frame=quadro)
            alvo.location = mira
            alvo.keyframe_insert("location", frame=quadro)

        for obj in (cam, alvo):
            _linearizar(obj)

        marcador = cena.timeline_markers.new(p["id"], frame=p["_quadro_ini"])
        marcador.camera = cam

        if com_shake:
            _aplicar_shake(cam, p)

    cena.camera = bpy.data.objects.get(f"CAM_{pacote['planos'][0]['id']}")
    return len(pacote["planos"])


def _linearizar(obj):
    """Interpolacao linear nas chaves. Bezier automatica inventa aceleracao."""
    ad = obj.animation_data
    if not ad or not ad.action:
        return
    acao = ad.action
    curvas = list(getattr(acao, "fcurves", []))
    if not curvas:
        # Da 4.4 em diante as fcurves vivem em layers > strips > channelbags
        for camada in getattr(acao, "layers", []):
            for faixa in getattr(camada, "strips", []):
                for saco in getattr(faixa, "channelbags", []):
                    curvas.extend(saco.fcurves)
    for fc in curvas:
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"


def _aplicar_shake(cam, plano):
    """Camera Shakify, se estiver instalado. Grátis, GPL, dados CC0.

    Movimento perfeito le como maquete. Se o addon nao estiver la, avisa e
    segue -- nao e motivo para derrubar a geracao da cena.
    """
    import bpy
    preset = {"sobrevoo": "INVESTIGATION", "subida": "INVESTIGATION"}.get(
        plano["movimento"], "HANDHELD_TRIPOD_MEDIUM")
    try:
        anterior = bpy.context.view_layer.objects.active
        bpy.context.view_layer.objects.active = cam
        bpy.ops.camerashakify.add_shake(type=preset)
        cam.camera_shakify.shake_list[-1].influence = 0.35
        bpy.context.view_layer.objects.active = anterior
    except Exception:
        if not getattr(_aplicar_shake, "_avisou", False):
            print("  aviso: Camera Shakify nao instalado -- camera sai limpa "
                  "demais. extensions.blender.org/add-ons/camera-shakify")
            _aplicar_shake._avisou = True


def montar_marcos(pacote, colecao):
    """Cones apontando de onde cada plano comeca para o que ele mira.

    Existem para o Twinmotion, que importa geometria mas NAO importa camera
    animada. Os cones viajam no FBX e dizem onde cravar cada chave la dentro.
    """
    import bpy
    import bmesh
    from mathutils import Vector

    feitos = 0
    for p in pacote["planos"]:
        for rotulo, t in (("INI", 0.0), ("FIM", 1.0)):
            pos, mira = amostra(p, t, pacote["centro"])
            malha = bpy.data.meshes.new(f"MARCO_{p['id']}_{rotulo}")
            obj = bpy.data.objects.new(malha.name, malha)
            colecao.objects.link(obj)

            bm = bmesh.new()
            bmesh.ops.create_cone(bm, cap_ends=True, segments=8,
                                  radius1=1.6, radius2=0.0, depth=5.0)
            bm.to_mesh(malha)
            bm.free()

            obj.location = pos
            direcao = Vector(mira) - Vector(pos)
            obj.rotation_euler = direcao.to_track_quat("Z", "Y").to_euler()
            obj["plano"] = p["id"]
            obj["lente_mm"] = p["lente_mm"]
            obj["duracao_s"] = p["duracao_s"]
            feitos += 1
    return feitos


# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--planos", default=PLANOS_PADRAO)
    ap.add_argument("--mapa", default=None)
    ap.add_argument("--conferir", action="store_true",
                    help="confere velocidades e ancoras; sai com erro se algo fugir")
    ap.add_argument("--tabela", action="store_true",
                    help="imprime a decupagem em markdown")
    args = ap.parse_args()

    dados = carregar_mapa(args.mapa) if args.mapa else carregar_mapa()
    pacote = carregar(args.planos, dados)

    if args.tabela:
        print(tabela_markdown(pacote))
        return

    problemas = conferir(pacote)
    if args.conferir and problemas:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
