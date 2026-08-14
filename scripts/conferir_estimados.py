#!/usr/bin/env python3
"""As caixas estimadas caem em cima de alguma coisa que foi medida?

Estimativa erra tamanho -- isso e esperado e esta declarado. O que nao pode
passar e uma estimativa **atropelar geometria medida**: um estacionamento de
60 x 40 m em cima de um pavilhao aparece no sobrevoo e nao tem desculpa.

Compara a pegada (bounding box no plano XY) de cada objeto da colecao ESTIMADO
com a de cada objeto de BASE e lista quem se cruza, com quanto de area comum.

Uso:
    blender --background out/cena.blend --python scripts/conferir_estimados.py
"""

import bpy

LIMITE = 0.10        # ate 10% da pegada estimada em cima de algo medido, passa


def pegada(obj):
    xs = [(obj.matrix_world @ v.co).x for v in obj.data.vertices]
    ys = [(obj.matrix_world @ v.co).y for v in obj.data.vertices]
    return min(xs), min(ys), max(xs), max(ys)


def cruzamento(a, b):
    dx = min(a[2], b[2]) - max(a[0], b[0])
    dy = min(a[3], b[3]) - max(a[1], b[1])
    return dx * dy if dx > 0 and dy > 0 else 0.0


def main():
    est = bpy.data.collections.get("ESTIMADO")
    base = bpy.data.collections.get("BASE")
    if est is None or base is None:
        print("cena sem as colecoes ESTIMADO/BASE")
        return

    todos = [(o.name, pegada(o)) for o in base.objects
             if o.type == "MESH" and o.name not in ("Terreno", "PistaArena", "Entorno")]
    solidos = [t for t in todos if not t[0].startswith("Via_")]
    vias = [t for t in todos if t[0].startswith("Via_")]
    print(f"conferindo {len(est.objects)} estimados contra {len(solidos)} solidos "
          f"({len(vias)} vias contadas a parte)\n")

    achados, com_via = 0, 0
    for o in est.objects:
        if o.type != "MESH":
            continue
        p = pegada(o)
        area = max((p[2] - p[0]) * (p[3] - p[1]), 1e-6)
        for nome, q in solidos:
            c = cruzamento(p, q)
            if c / area > LIMITE:
                print(f"  {o.name[:32]:34s} cobre {c/area*100:5.1f}% da propria "
                      f"pegada em cima de {nome}")
                achados += 1
        com_via += any(cruzamento(p, q) / area > LIMITE for _, q in vias)

    print(f"\ncruzamentos com SOLIDO acima de {LIMITE*100:.0f}%: {achados}")
    if not achados:
        print("nenhuma estimativa atropela geometria medida")
    # Via e fita diagonal lida do bitmap: a caixa envolvente dela cobre um
    # retangulo enorme e daria falso positivo em quase tudo. Alem disso portao,
    # quiosque e banheiro ficam mesmo na beira da via. Fica so o numero.
    print(f"encostam em via (esperado, nao e erro): {com_via}")


if __name__ == "__main__":
    main()
