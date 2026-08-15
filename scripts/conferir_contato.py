#!/usr/bin/env python3
"""
Portao de CONTATO: o que tem de se encostar esta encostado?

Este projeto ja tinha portao de COLISAO (`build_scene` afasta o que nao pode se
tocar) e portao de CAMERA (`conferir_camera.py`). Faltava o oposto, e a doutrina
o coloca em primeiro lugar na secao 3.1: *"Contato e a coisa mais importante da
cena. O ponto onde o objeto encosta no chao e onde o olho decide se aquilo
existe."* Peca no ar nao joga sombra de contato, e sombra de contato e o sinal
mais forte de peso que existe.

Nao fazia falta enquanto tudo era caixa solta no chao. Passou a fazer quando a
concha entrou (laje sobre porao, cobertura sobre parede) e quando 52 predios
foram vestidos sobre um terreno que TEM declive: caixa posta pela cota do
centroide fica com o canto no ar quando o chao sobe.

Tres testes, e cada um responde uma pergunta diferente:

  1. PARES DECLARADOS -- as pecas de `build_scene.CONTATOS_EXIGIDOS` (a concha)
     tem de encostar uma na outra, sem vao e sem enfiar. Reusa a funcao do
     proprio gerador, para nao existirem duas reguas para a mesma pergunta
     (armadilha 19: construtor e conferidor com regua diferente e ter dois
     juizes).
  2. APOIO -- todo objeto tem de estar apoiado em ALGO: no chao (Terreno ou
     Entorno) ou em outra peca embaixo dele. Objeto no ar sem nada embaixo e
     defeito sem ambiguidade, e e este teste que reprova.
  3. AFUNDAMENTO -- quanto de cada objeto esta abaixo do chao. Aqui o script
     MEDE e RELATA, e so reprova acima de `--afundamento-fatal`, que nasce
     desligado. Motivo escrito: parte do afundamento medido hoje e consequencia
     das cotas dos patamares, que sao ESTIMADAS (pendencia 8 com o cliente).
     Reprovar por um numero derivado de estimativa seria trocar um erro
     declarado por um conserto inventado.

A medida do apoio usa DUAS familias de pontos e fica com a melhor delas, porque
cada uma sozinha erra num caso conhecido -- e os dois casos ja apareceram aqui:

  - VERTICE DE BASE nao ve telhado inclinado. A cobertura da concha tem os oito
    vertices na ponta do beiral, que esta no ar de proposito;
  - COLUNA DE GRADE nao ve parede fina. A grade cai no meio de um predio sem
    piso e o primeiro raio para cima acerta o forro do telhado a 6 m.

E o apoio em OUTRA PECA nao se mede por raio para baixo, e sim por distancia
entre superficies, nos dois sentidos. Raio para baixo a partir do beiral da
concha desce 9 m ate o chao e conclui "nada embaixo" num contato de 20 m2.

Bounding box esta descartado desde a primeira tentativa, e o motivo esta escrito
no `conferir_contato` do gerador: a bbox de um telhado inclinado tem a base la
na frente, 1,4 m abaixo do fundo.

    blender --background --python scripts/conferir_contato.py -- --blend out/cena.blend
    python scripts/conferir_contato.py --blend out/cena.blend      # com bpy do pip

Sai com codigo 1 se reprovar. E para rodar antes de qualquer fila de render.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy
import mathutils

import build_scene

V = mathutils.Vector

# Colecoes que entram no teste de apoio. LETREIROS fica FORA de proposito: o
# letreiro e' texto flutuante por projeto, dimensionado pela regra de 8% da
# altura do quadro -- ele nao encosta em nada e nao deve encostar.
COLECOES = ("BASE", "EVENTO", "ESTIMADO", "POVOAMENTO", "AREA_DE_ESPERA",
            "MOBILIARIO")
CHAO = ("Terreno", "Entorno")

# Peca que sobe do chao POR PROJETO, com o motivo escrito na funcao que a
# constroi. Nao e' anistia: e' a diferenca entre defeito e decisao declarada.
# Prefixo do nome -> (folga permitida em metros, onde a decisao esta escrita).
FOLGA_DECLARADA = {
    "Via_": (0.06, "estruturas.via: a fita sobe 6 cm porque coplanar com o "
                   "terreno da z-fighting, e 6 cm nao aparecem nesta decupagem"),
}

# 5 cm. Nao e' numero de gosto: e' a menor folga que ainda seria vista como
# objeto no ar num plano rasante de 6 m de altura (a 6 m, 5 cm ocupa menos de um
# pixel em 2760 px de largura, mas a SOMBRA de contato se abre bem antes que a
# folga apareca). Abaixo disso e' ruido de float da propria construcao.
TOLERANCIA_APOIO = 0.05
# Quantos vertices de base amostrar por objeto. Os 1.681 proxies do povoamento
# tornam isto uma conta de tempo, e vertice de base de caixa sao 4.
LIMITE_VERTICES = 120


def _chao_em(x, y, alvos):
    """Cota do chao em (x,y).

    A ORDEM de `alvos` e' a regra, e ela custou uma medicao errada: o `Terreno`
    manda onde existe, e o `Entorno` so vale fora dele. A primeira versao pegava
    a superficie MAIS ALTA das duas e acusou 1.123 objetos afundados -- entre
    eles gente de 1,70 m com 2,5 m de terra em cima. Nao era afundamento: dentro
    do recinto o `Entorno` e uma malha grossa que passa por cima da bacia
    escavada, e ele estava sendo lido como chao onde o chao e o terreno
    detalhado.
    """
    for alvo in alvos:
        inv = alvo.matrix_world.inverted()
        org = inv @ V((x, y, 400.0))
        d = (inv.to_3x3() @ V((0, 0, -1))).normalized()
        try:
            bateu, onde, _, _ = alvo.ray_cast(org, d)
        except RuntimeError:
            continue
        if bateu:
            return (alvo.matrix_world @ onde).z
    return None


def _folga_declarada(nome):
    for prefixo, (folga, motivo) in FOLGA_DECLARADA.items():
        if nome.startswith(prefixo):
            return folga, motivo
    return 0.0, None


def _sob_o_objeto(o, x, y, z_de):
    """Cota da face de BAIXO do proprio objeto na vertical (x,y).

    Raio subindo de bem abaixo dele. E o que enxerga telhado inclinado, que a
    selecao por vertice mais baixo nao enxerga: a cobertura da concha encosta na
    parede la atras e o vertice mais baixo dela e a ponta do beiral, na frente,
    com 9 m de ar embaixo.
    """
    inv = o.matrix_world.inverted()
    org = inv @ V((x, y, z_de))
    d = (inv.to_3x3() @ V((0, 0, 1))).normalized()
    try:
        bateu, onde, _, _ = o.ray_cast(org, d)
    except RuntimeError:
        return None
    return (o.matrix_world @ onde).z if bateu else None


def _bbox_mundo(o):
    cs = [o.matrix_world @ mathutils.Vector(c) for c in o.bound_box]
    return (min(c.x for c in cs), min(c.y for c in cs), min(c.z for c in cs),
            max(c.x for c in cs), max(c.y for c in cs), max(c.z for c in cs))


def _distancia_entre(a, b, limite_vertices=LIMITE_VERTICES):
    """Menor distancia entre as superficies de dois objetos.

    Mede nos DOIS sentidos, e e por isso que funciona: o vertice de A pode estar
    longe da superficie de B e mesmo assim as duas se tocarem. A cobertura da
    concha e o caso -- ela e uma caixa de 8 vertices, todos nas pontas do
    beiral, e quem esta ENCOSTADO nela sao os vertices do TOPO DA PAREDE.
    Perguntar so de um lado devolve 'nada embaixo' num contato de 20 m2.
    """
    melhor = None
    for de, para in ((a, b), (b, a)):
        M = de.matrix_world
        inv = para.matrix_world.inverted()
        verts = de.data.vertices
        passo = max(1, len(verts) // limite_vertices)
        for i in range(0, len(verts), passo):
            p = M @ verts[i].co
            try:
                ok, perto, _, _ = para.closest_point_on_mesh(inv @ p)
            except RuntimeError:
                return None
            if not ok:
                continue
            d = ((para.matrix_world @ perto) - p).length
            if melhor is None or d < melhor:
                melhor = d
    return melhor


def _apoio_em_peca(o, candidatos, tolerancia):
    """Alguma peca ABAIXO encosta neste objeto? Devolve (distancia, nome)."""
    ax0, ay0, az0, ax1, ay1, az1 = _bbox_mundo(o)
    meio_a = (az0 + az1) / 2.0
    melhor = None
    for outro in candidatos:
        if outro.name == o.name:
            continue
        bx0, by0, bz0, bx1, by1, bz1 = _bbox_mundo(outro)
        if bx1 < ax0 - tolerancia or bx0 > ax1 + tolerancia:
            continue
        if by1 < ay0 - tolerancia or by0 > ay1 + tolerancia:
            continue
        if bz1 < az0 - tolerancia:          # topo do outro abaixo da base: nao toca
            continue
        if (bz0 + bz1) / 2.0 >= meio_a:     # so vale quem esta EMBAIXO
            continue
        d = _distancia_entre(o, outro)
        if d is not None and (melhor is None or d < melhor[0]):
            melhor = (d, outro.name)
    return melhor if melhor else (None, None)


def medir_apoio(cena, dg, alvos_chao, colecoes=COLECOES):
    """Um registro por objeto: vao ate o chao, apoio em peca, afundamento."""
    vistos = set()
    fichas = []
    pendentes = []
    for cnome in colecoes:
        col = bpy.data.collections.get(cnome)
        if col is None:
            continue
        for o in col.objects:
            if o.name in vistos or o.name in CHAO:
                continue
            if o.type != "MESH" or o.hide_render or o.hide_viewport:
                continue
            if o.name.startswith("Etiqueta"):
                continue
            if not o.data.vertices:
                continue
            vistos.add(o.name)

            M = o.matrix_world
            mundo = [M @ v.co for v in o.data.vertices]
            zmin = min(v.z for v in mundo)
            xs = [v.x for v in mundo]
            ys = [v.y for v in mundo]

            # DUAS familias de pontos de apoio, e o objeto fica com a MELHOR
            # delas. Sozinha, cada uma erra num caso conhecido:
            #  - vertice de base nao ve telhado inclinado (o beiral e o ponto
            #    mais baixo, e ele esta no ar de proposito);
            #  - coluna de grade nao ve parede fina (a grade cai no vao do
            #    predio sem piso e mede o forro do telhado, 6 m acima).
            pontos = [(v.x, v.y, v.z) for v in mundo
                      if v.z <= zmin + 0.05][:LIMITE_VERTICES]
            n = 5
            for i in range(n):
                for j in range(n):
                    x = xs and min(xs) + (max(xs) - min(xs)) * (i + 0.5) / n
                    y = ys and min(ys) + (max(ys) - min(ys)) * (j + 0.5) / n
                    z = _sob_o_objeto(o, x, y, zmin - 1.0)
                    if z is not None:
                        pontos.append((x, y, z))

            vaos, afundamentos = [], []
            for x, y, z in pontos:
                cz = _chao_em(x, y, alvos_chao)
                if cz is None:
                    continue
                vaos.append(z - cz)
                afundamentos.append(cz - z)
            # afundamento le o objeto inteiro, nao so a base
            afunda = None
            if mundo:
                fundos = []
                for v in mundo[:LIMITE_VERTICES]:
                    cz = _chao_em(v.x, v.y, alvos_chao)
                    if cz is not None:
                        fundos.append(cz - v.z)
                if fundos:
                    afunda = max(max(fundos), 0.0)

            folga, motivo = _folga_declarada(o.name)
            ficha = {
                "objeto": o.name,
                "colecao": cnome,
                "vao_ao_chao_m": None if not vaos else round(min(vaos), 4),
                "afundamento_m": None if afunda is None else round(afunda, 4),
                "apoio_em": None,
                "vao_ao_apoio_m": None,
                "folga_declarada_m": folga or None,
                "_folga_por": motivo,
            }
            if vaos and min(vaos) > TOLERANCIA_APOIO + folga:
                pendentes.append((o, ficha))
            fichas.append(ficha)

    # Quem nao encosta no chao pode estar apoiado em OUTRA PECA. Este segundo
    # passo roda so para esses -- e' caro (distancia superficie a superficie) e
    # so faz sentido em quem ja sabemos que esta no ar.
    universo = [bpy.data.objects[n] for n in vistos]
    for o, ficha in pendentes:
        d, quem = _apoio_em_peca(o, universo, TOLERANCIA_APOIO)
        if d is not None:
            ficha["vao_ao_apoio_m"] = round(d, 4)
            ficha["apoio_em"] = quem
    return fichas


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--blend", required=True)
    ap.add_argument("--tolerancia", type=float, default=TOLERANCIA_APOIO,
                    help="vao maximo, em metros, para considerar que encosta")
    ap.add_argument("--afundamento-fatal", dest="afundamento_fatal", type=float,
                    default=None,
                    help="reprova objeto afundado mais que isto (metros). "
                         "Desligado por padrao -- ver o cabecalho do arquivo")
    ap.add_argument("--json", dest="saida_json", default=None,
                    help="grava a medida objeto a objeto neste caminho")
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    args = ap.parse_args(argv)

    bpy.ops.wm.open_mainfile(filepath=str(Path(args.blend).resolve()))
    bpy.context.view_layer.update()
    cena = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    alvos_chao = [bpy.data.objects[n] for n in CHAO if n in bpy.data.objects]
    if not alvos_chao:
        raise SystemExit("ABORTADO -- a cena nao tem Terreno nem Entorno: "
                         "sem chao nao ha o que conferir")

    reprovas = []

    # ---------------------------------------------------------------- teste 1
    print("1. PARES DECLARADOS (a mesma regua do gerador)")
    falhas_par, linhas = build_scene.conferir_contato(
        tolerancia=build_scene.TOLERANCIA_CONTATO, abortar=False)
    for l in linhas:
        print(l)
    for a, b, f in falhas_par:
        reprovas.append(f"par {b} sobre {a}: "
                        f"{'peca ausente' if f is None else f'{f:+.3f} m'}")

    # ---------------------------------------------------------------- teste 2
    print(f"\n2. APOIO -- todo objeto encosta em algo (tolerancia "
          f"{args.tolerancia*100:.0f} cm)")
    fichas = medir_apoio(cena, dg, alvos_chao)
    sem_medida = [f for f in fichas if f["vao_ao_chao_m"] is None]
    no_ar = []
    por_peca = []
    for f in fichas:
        vao = f["vao_ao_chao_m"]
        limite = args.tolerancia + (f["folga_declarada_m"] or 0.0)
        if vao is None or vao <= limite:
            continue
        va = f["vao_ao_apoio_m"]
        if va is not None and va <= limite:
            por_peca.append(f)
        else:
            no_ar.append(f)

    print(f"   {len(fichas)} objetos medidos")
    print(f"   apoiados no chao ......... "
          f"{len(fichas) - len(no_ar) - len(por_peca) - len(sem_medida)}")
    print(f"   apoiados em outra peca ... {len(por_peca)}")
    print(f"   sem chao sob eles ........ {len(sem_medida)} "
          f"(fora da extensao do terreno -- nao reprova)")
    if por_peca:
        print("   -- os que se apoiam em peca, e nao no chao (confira com o "
              "olho: medicao nao diz se o apoio faz sentido):")
        for f in sorted(por_peca, key=lambda f: -f["vao_ao_chao_m"]):
            print(f"      {f['objeto']:<42} sobre {f['apoio_em']}")
    print(f"   NO AR .................... {len(no_ar)}")
    for f in sorted(no_ar, key=lambda f: -f["vao_ao_chao_m"])[:30]:
        apoio = ("nada embaixo" if f["apoio_em"] is None
                 else f"{f['apoio_em']} a {f['vao_ao_apoio_m']:+.2f} m")
        print(f"     {f['objeto']:<42} {f['vao_ao_chao_m']:+7.2f} m do chao   "
              f"({apoio})")
        reprovas.append(f"no ar: {f['objeto']} a {f['vao_ao_chao_m']:+.2f} m "
                        f"do chao, {apoio}")

    # ---------------------------------------------------------------- teste 3
    print("\n3. AFUNDAMENTO -- quanto esta abaixo do chao (medida, nao veredito)")
    afundados = sorted((f for f in fichas if (f["afundamento_m"] or 0) > 0.30),
                       key=lambda f: -f["afundamento_m"])
    print(f"   {len(afundados)} objetos com mais de 30 cm afundados")
    for f in afundados[:20]:
        print(f"     {f['objeto']:<42} {f['afundamento_m']:6.2f} m  [{f['colecao']}]")
    if len(afundados) > 20:
        print(f"     ... e mais {len(afundados)-20}")
    if args.afundamento_fatal is not None:
        for f in afundados:
            if f["afundamento_m"] > args.afundamento_fatal:
                reprovas.append(f"afundado: {f['objeto']} "
                                f"{f['afundamento_m']:.2f} m")

    if args.saida_json:
        alvo = Path(args.saida_json)
        alvo.parent.mkdir(parents=True, exist_ok=True)
        alvo.write_text(json.dumps({
            "_o_que_e": "medida de contato objeto a objeto, tirada do .blend",
            "_blend": str(Path(args.blend).resolve()),
            "_tolerancia_apoio_m": args.tolerancia,
            "_como_foi_medido": ("vao do vertice de base ate a superficie de "
                                 "chao mais alta em (x,y); apoio em peca por "
                                 "raio para baixo a partir de cada vertice de "
                                 "base, ignorando o proprio objeto"),
            "resumo": {
                "objetos": len(fichas),
                "no_ar": len(no_ar),
                "apoiados_em_peca": len(por_peca),
                "afundados_acima_de_30cm": len(afundados),
            },
            "objetos": fichas,
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\nmedida gravada em {alvo}")

    print("\n" + "=" * 62)
    if reprovas:
        print(f"  {len(reprovas)} REPROVA(S) DE CONTATO:")
        for r in reprovas[:40]:
            print(f"    - {r}")
        if len(reprovas) > 40:
            print(f"    ... e mais {len(reprovas)-40}")
        print("=" * 62)
        raise SystemExit(1)
    print("  contato conferido: nada no ar, e os pares declarados encostam.")
    print("=" * 62)


if __name__ == "__main__":
    main()
