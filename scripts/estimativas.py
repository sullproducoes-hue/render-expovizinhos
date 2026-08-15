#!/usr/bin/env python3
"""Resolve o tamanho ESTIMADO das zonas que a planta nomeia mas nao desenha.

Por que existe: `extrair_footprints.py` mede o desenho e recusa o que nao da
para medir -- 35 zonas ficaram sem forma, e elas sao metade do recinto (praca de
alimentacao aberta, banheiros, portaria, estacionamentos, mangueiras). O Natan
autorizou em 14/08: *"pode fazer com uma estimativa aproximada"*.

**A separacao e o ponto deste modulo.** Medida e estimativa nunca se misturam:
- o que foi medido vive em `data/footprints.json` e nao passa por aqui;
- o que e estimado vive em `data/estimativas.json`, uma tabela declarada por
  tipo, com o fundamento de cada numero escrito ao lado;
- todo objeto gerado daqui sai com `estimado = True` e o fundamento colado nele,
  entao da para achar e trocar sem procurar.

Quando chegar print, medida de campo ou planta vetorial de uma zona, apaga-se a
entrada dela em `estimativas.json` e o gerador passa a usar o dado real.

Nao importa bpy: roda em qualquer python, e por isso da para conferir a lista
antes de abrir o Blender.

Uso:
    .venv/Scripts/python.exe scripts/estimativas.py
"""

import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def carregar(caminho=None):
    p = Path(caminho) if caminho else RAIZ / "data" / "estimativas.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def _angulos_dos_rotulos(caminho=None):
    """rotulo -> angulo com que a planta ESCREVE o nome, em graus de pagina.

    O rumo das estruturas nao e chutado: o rotulo de um galpao e escrito no eixo
    dele. `data/locais.json` guarda esse angulo para os 142 locais.
    """
    p = Path(caminho) if caminho else RAIZ / "data" / "locais.json"
    if not p.exists():
        return {}
    d = json.loads(p.read_text(encoding="utf-8"))
    saida = {}
    for l in d.get("locais", []):
        nome = l.get("texto_no_mapa") or l.get("nome")
        if nome is None:
            continue
        saida.setdefault((nome, round(l["x_pt"], 1), round(l["y_pt"], 1)),
                         l.get("angulo_graus", 0.0))
    return saida


def _giro_do_rotulo(angulos, rotulo, x_pt, y_pt, tolerancia=1.5):
    """Angulo de pagina -> giro no mundo.

    O sinal inverte porque a pagina tem y para baixo e o mundo tem y para o
    norte. E a mesma relacao que ja liga `RUMO_PORTAL = 73.0` ao angulo -73,2
    com que a planta escreve o rotulo do portal.
    """
    melhor, dmelhor = None, float("inf")
    for (nome, ax, ay), ang in angulos.items():
        if nome != rotulo:
            continue
        d = abs(ax - x_pt) + abs(ay - y_pt)
        if d < dmelhor:
            melhor, dmelhor = ang, d
    if melhor is None or dmelhor > tolerancia:
        return 0.0, False
    return (-melhor) % 360.0, True


def resolver(footprints=None, tabela=None, angulos=None):
    """Uma entrada por zona sem footprint, ja com tamanho, giro e procedencia.

    Devolve (estimados, recusados). `recusados` sao as zonas que este modulo se
    recusa a estimar, com o motivo -- as que ja tem construcao propria na cena e
    as que nenhum tipo cobre. Recusa nomeada, nunca silencio.
    """
    tabela = tabela if tabela is not None else carregar()
    if tabela is None:
        return [], [("(tabela)", "data/estimativas.json nao existe")]

    p = RAIZ / "data" / "footprints.json"
    fp = footprints if footprints is not None else (
        json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"itens": []})
    angulos = angulos if angulos is not None else _angulos_dos_rotulos()

    # As zonas cuja MEDIDA foi recusada (confianca "baixa": a mancha e quase toda
    # a tinta da palavra) sumiam em silencio -- nao entravam como medida e este
    # laco nem olhava para elas. Cada uma agora tem destino escrito no contrato,
    # e quem nao tiver sai em `recusados`, nunca em silencio.
    recusadas = tabela.get("medida_recusada_vira_estimativa", {}).get("zonas", {})

    estimados, recusados = [], []
    for it in fp["itens"]:
        rotulo = it["rotulo"]
        de_medida_recusada = False
        if it.get("metodo") not in ("so o rotulo", "sem mancha"):
            if it.get("confianca") != "baixa":
                continue
            decisao = recusadas.get(rotulo)
            if decisao is None:
                recusados.append((rotulo, "medida recusada pelo extrator e sem "
                                          "decisao declarada em "
                                          "medida_recusada_vira_estimativa"))
                continue
            if decisao["decisao"] != "estimar":
                recusados.append((rotulo, decisao["porque"]))
                continue
            de_medida_recusada = True

        if rotulo in tabela["nao_estimar"]:
            recusados.append((rotulo, tabela["nao_estimar"][rotulo]))
            continue

        tipo_nome = (recusadas[rotulo]["tipo"] if de_medida_recusada
                     else tabela["por_rotulo"].get(rotulo))
        if tipo_nome is None:
            recusados.append((rotulo, "nenhum tipo declarado para este rotulo"))
            continue
        tipo = tabela["tipos"][tipo_nome]

        cota = it.get("area_cotada_m2")
        if "proporcao" in tipo:
            if not cota:
                recusados.append((rotulo, f"tipo '{tipo_nome}' precisa de area "
                                          "cotada e esta zona nao tem"))
                continue
            razao = tipo["proporcao"]
            profundidade = (cota / razao) ** 0.5
            largura = profundidade * razao
            fonte = f"area cotada na planta ({cota:.0f} m²), proporcao {razao:g}:1 assumida"
        else:
            largura = tipo["largura_m"]
            profundidade = tipo["profundidade_m"]
            fonte = "tabela de estimativa, por tipo"

        giro, do_rotulo = _giro_do_rotulo(angulos, rotulo, it["x_pt"], it["y_pt"])
        estimados.append({
            "rotulo": rotulo,
            "categoria": it["categoria"],
            "x_pt": it["x_pt"], "y_pt": it["y_pt"],
            "tipo": tipo_nome,
            "forma": tipo["forma"],
            "largura_m": round(largura, 2),
            "profundidade_m": round(profundidade, 2),
            "altura_m": tipo["altura_m"],
            "giro_graus": round(giro, 1),
            "giro_do_rotulo": do_rotulo,
            "estimado": True,
            "de_medida_recusada": de_medida_recusada,
            "procedencia": f"{fonte}. {tipo['fundamento']}",
        })
    return estimados, recusados


def main():
    est, rec = resolver()
    tabela = carregar()
    print(f"ESTIMATIVAS RESOLVIDAS: {len(est)}   recusadas: {len(rec)}\n")
    print(f"{'zona':32s} {'tipo':22s} {'tamanho':>16s} {'alt':>5s} {'giro':>7s}")
    for e in sorted(est, key=lambda e: (e["tipo"], e["rotulo"])):
        giro = f"{e['giro_graus']:6.1f}" + ("" if e["giro_do_rotulo"] else "*")
        print(f"  {e['rotulo'][:30]:32s} {e['tipo']:22s} "
              f"{e['largura_m']:6.1f} x{e['profundidade_m']:6.1f} {e['altura_m']:5.1f} {giro:>7s}")
    print("\n  * giro nao veio do rotulo: a planta nao registra angulo para ele")

    if rec:
        print(f"\nRECUSADAS ({len(rec)}) -- e por que:")
        for rotulo, motivo in rec:
            print(f"  {rotulo[:34]:36s} {motivo}")

    fracas = [e for e in est if "MAIS FRACA" in e["procedencia"]
              or "mais fraco" in e["procedencia"]]
    if fracas:
        print(f"\nAS MAIS FRACAS ({len(fracas)}) -- trocar assim que houver print dele:")
        for e in fracas:
            print(f"  {e['rotulo'][:34]:36s} {e['largura_m']:.0f} x {e['profundidade_m']:.0f} m")
    print(f"\nautoridade: {tabela['autoridade']}")


if __name__ == "__main__":
    main()
