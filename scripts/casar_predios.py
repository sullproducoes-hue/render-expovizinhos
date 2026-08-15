#!/usr/bin/env python3
"""
Casa cada predio PROVADO NO FOOTAGE com uma zona da planta -- por criterio
escrito, nao por olhar e achar.

E a pendencia 3a de `data/formas-quinta.json`, e ela e o gargalo declarado da
etapa 3: *"sem isso a forma medida nao sabe onde pousar"*. O predio redondo tem
uma orbita completa de drone provando que ele e um poligono de ~10 faces com
dois pavimentos, e na cena ele e uma caixa -- porque ninguem sabe QUAL zona da
planta e ele.

O que este script faz, e o que ele NAO faz:

  FAZ  -- pontua cada zona da planta contra a assinatura do predio filmado,
          criterio a criterio, com o peso e o motivo escritos, e grava a conta
          inteira em `data/casamento-predios.json`;
  NAO FAZ -- nao troca geometria nenhuma, nao renomeia zona e nao decide
          nomenclatura. Casamento so vira geometria depois de conferido, e a
          regra do projeto e dura: *construir sobre footprint errado e pior que
          nao construir*.

E ele **so declara casamento quando o primeiro colocado ganha do segundo por uma
margem declarada**. Empate vira `sem_veredito` com o que falta escrito -- que e
o oposto de arbitrar, e e o que a serie de erros de 14 e 15/08 ensinou: duas
fontes fracas concordando nao viram uma forte.

Dois casos ja sabidos entram como CONTROLE, e o script tem de reencontra-los
sozinho: o PALCO (a concha, casada com a zona `PALCO PALCO` em 15/08, D028) e as
MANGUEIRAS (que tem rotulo proprio na planta). Metodo que nao acerta o que ja se
sabe nao serve para o que nao se sabe.

    python3 scripts/casar_predios.py                 # roda e imprime a conta
    python3 scripts/casar_predios.py --json data/casamento-predios.json

Roda sem `bpy` e sem GPU.
"""

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import terreno

RAIZ = Path(__file__).resolve().parent.parent

# O primeiro colocado tem de ganhar do segundo por isto para virar proposta.
# 0,15 em nota de 0 a 1: menos que isso, e' ruido de peso, e peso e' escolha
# minha. O numero esta aqui em cima de proposito, para ser discutido.
MARGEM = 0.15


def _razao(l, p):
    if not l or not p:
        return None
    return max(l, p) / min(l, p)


# --------------------------------------------------------------------------
# As assinaturas. Cada criterio carrega o QUADRO que o sustenta -- criterio sem
# quadro atras nao entra, porque seria eu inventando o predio.
# --------------------------------------------------------------------------
ASSINATURAS = {
    "PREDIO_REDONDO": {
        "o_que_e": "poligono regular de ~10 faces, dois pavimentos, varanda em "
                   "volta, telhado de quatro aguas de baixa inclinacao",
        "quadros": ["1 (5)", "1 (6)", "1 (7)", "1 (8)", "1 (9)", "1 (10)", "1 (11)"],
        "criterios": [
            {"tipo": "razao_bbox", "alvo": 1.0, "tolerancia": 0.30, "peso": 3,
             "porque": "a bbox de um poligono regular e quase quadrada; a de um "
                       "galpao de duas aguas nao e"},
            {"tipo": "area_minima", "valor": 500.0, "eliminatorio": True,
             "porque": "1 (10) mostra dezenas de pessoas na varanda de um predio "
                       "de dois pavimentos. Uma casa de 13 x 12 m nao comporta a "
                       "orbita nem o publico"},
            {"tipo": "perto_de_rotulo", "rotulo": "ESTACIONAMENTO", "max_m": 90.0,
             "peso": 3,
             "porque": "1 (5) enquadra o predio COM o estacionamento cheio de "
                       "carros no mesmo quadro -- e o carro e um dos datums"},
            {"tipo": "vizinho_retangular", "max_m": 60.0, "razao_min": 1.6,
             "peso": 1,
             "porque": "1 (10) mostra um anexo RETANGULAR encostado nele, que e "
                       "outro volume"},
        ],
    },
    "GALERIA_DE_PILARES": {
        "o_que_e": "cobertura longa e aberta sobre pilares claros",
        "quadros": ["1 (6)__0003s", "1 (6)__0012s"],
        "criterios": [
            {"tipo": "razao_bbox", "alvo": 4.0, "tolerancia": 2.0, "peso": 2,
             "porque": "e uma galeria: comprida e estreita"},
            {"tipo": "area_minima", "valor": 300.0, "eliminatorio": True,
             "porque": "cobertura de estande nao aparece assim no quadro"},
            {"tipo": "forma_declarada", "valor": "cobertura", "peso": 3,
             "porque": "aberta e sem parede -- e o que a declaracao de altura "
                       "chama de `cobertura`"},
        ],
    },
    "GALPAO_AZUL_E_TIJOLO": {
        "o_que_e": "galpao de alvenaria vermelha com telhado e pilastras azuis",
        "quadros": ["1 (17)__0006s", "1 (17)__0037s", "1 (16)"],
        "criterios": [
            {"tipo": "razao_bbox", "alvo": 2.5, "tolerancia": 1.5, "peso": 1,
             "porque": "galpao de duas aguas, mais comprido que largo"},
            {"tipo": "area_minima", "valor": 300.0, "eliminatorio": True,
             "porque": "o portao de chapa do quadro tem porte de galpao"},
        ],
        "_aviso": "a assinatura deste e' quase toda COR (vermelho + azul), e a "
                  "planta e' um bitmap cinza sem cor de edificacao. Os criterios "
                  "geometricos sozinhos nao separam um galpao dos outros -- "
                  "espera-se `sem_veredito`, e isso e' resultado, nao falha",
    },
    # -------------------------------------------------------------- controles
    "PALCO_CONCHA": {
        "o_que_e": "CONTROLE -- a concha permanente, ja casada com `PALCO PALCO` "
                   "em 15/08 (D028). O script tem de reencontrar isto sozinho",
        "quadros": ["1 (4)"],
        "resposta_conhecida": "PALCO PALCO",
        "criterios": [
            {"tipo": "razao_bbox", "alvo": 1.15, "tolerancia": 0.35, "peso": 2,
             "porque": "boca larga e pouca profundidade, quase quadrada em planta"},
            {"tipo": "area_minima", "valor": 200.0, "eliminatorio": True,
             "porque": "a caixa cenica do 1 (4) e' de porte de palco, nao de bar"},
            {"tipo": "categoria", "valor": "arena", "peso": 3,
             "porque": "a concha olha para a pista; a planta classifica a zona "
                       "dela como `arena`"},
        ],
    },
}


def carregar_zonas():
    fp = json.loads((RAIZ / "data" / "footprints.json").read_text(encoding="utf-8"))
    mapa = terreno.carregar_mapa(str(RAIZ / "data" / "mapa_agroshow26.json"))
    origem = mapa["_origem"]
    alturas = json.loads(
        (RAIZ / "data" / "estimativas.json").read_text(encoding="utf-8"))
    # a forma declarada das zonas MEDIDAS mora em
    # estimativas.json -> altura_das_zonas_medidas -> zonas. Aqui so a altura e
    # a forma sao estimadas; o footprint e medido.
    formas = {}
    bloco = alturas.get("altura_das_zonas_medidas", {}).get("zonas", {})
    for rot, decl in bloco.items():
        if isinstance(decl, dict) and "forma" in decl:
            formas[rot] = decl["forma"]

    zonas = []
    for it in fp["itens"]:
        x, y = terreno.para_mundo(it["x_pt"], it["y_pt"], origem)
        l, p = it.get("largura_m"), it.get("profundidade_m")
        zonas.append({
            "rotulo": it["rotulo"],
            "categoria": it.get("categoria"),
            "confianca": it.get("confianca"),
            "x_m": round(x, 1), "y_m": round(y, 1),
            "largura_m": l, "profundidade_m": p,
            "area_m2": round(l * p, 1) if l and p else None,
            "razao": round(_razao(l, p), 3) if _razao(l, p) else None,
            "forma_declarada": formas.get(it["rotulo"]),
            "preenchimento": it.get("preenchimento"),
            "metodo": it.get("metodo"),
        })
    return zonas


def _dist(a, b):
    return math.hypot(a["x_m"] - b["x_m"], a["y_m"] - b["y_m"])


def avaliar(zona, zonas, criterios):
    """Devolve (nota 0..1, provas, eliminada_por) para uma zona."""
    provas, peso_total, soma = [], 0.0, 0.0
    for c in criterios:
        tipo = c["tipo"]
        if tipo == "area_minima":
            area = zona["area_m2"] or 0.0
            ok = area >= c["valor"]
            provas.append(f"area {area:.0f} m2 {'>=' if ok else '<'} "
                          f"{c['valor']:.0f} m2 (eliminatorio)")
            if not ok:
                return 0.0, provas, f"area de {area:.0f} m2"
            continue

        if tipo == "razao_bbox":
            if zona["razao"] is None:
                nota, texto = 0.0, "sem footprint medido: razao desconhecida"
            else:
                erro = abs(zona["razao"] - c["alvo"])
                nota = max(0.0, 1.0 - erro / c["tolerancia"])
                texto = (f"razao {zona['razao']:.2f} contra alvo {c['alvo']:.2f} "
                         f"(tolerancia {c['tolerancia']:.2f}) -> {nota:.2f}")
        elif tipo == "perto_de_rotulo":
            alvos = [z for z in zonas
                     if c["rotulo"].upper() in z["rotulo"].upper()
                     and z["rotulo"] != zona["rotulo"]]
            if not alvos:
                nota, texto = 0.0, f"nenhum rotulo {c['rotulo']} na planta"
            else:
                d = min(_dist(zona, a) for a in alvos)
                nota = max(0.0, 1.0 - d / c["max_m"])
                texto = (f"{c['rotulo']} mais proximo a {d:.0f} m "
                         f"(limite {c['max_m']:.0f} m) -> {nota:.2f}")
        elif tipo == "vizinho_retangular":
            viz = [z for z in zonas
                   if z["rotulo"] != zona["rotulo"] and z["razao"]
                   and z["razao"] >= c["razao_min"]
                   and _dist(zona, z) <= c["max_m"]]
            nota = 1.0 if viz else 0.0
            texto = (f"vizinho retangular a menos de {c['max_m']:.0f} m: "
                     + (", ".join(f"{z['rotulo']} ({_dist(zona, z):.0f} m)"
                                  for z in sorted(viz, key=lambda z: _dist(zona, z))[:2])
                        if viz else "nenhum"))
        elif tipo == "categoria":
            nota = 1.0 if zona["categoria"] == c["valor"] else 0.0
            texto = f"categoria {zona['categoria']} contra {c['valor']} -> {nota:.2f}"
        elif tipo == "forma_declarada":
            nota = 1.0 if zona["forma_declarada"] == c["valor"] else 0.0
            texto = (f"forma declarada {zona['forma_declarada']} contra "
                     f"{c['valor']} -> {nota:.2f}")
        else:
            raise SystemExit(f"criterio desconhecido: {tipo}")

        soma += nota * c["peso"]
        peso_total += c["peso"]
        provas.append(f"[peso {c['peso']}] {texto}")
    return (soma / peso_total if peso_total else 0.0), provas, None


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", dest="saida",
                    default=str(RAIZ / "data" / "casamento-predios.json"))
    ap.add_argument("--margem", type=float, default=MARGEM)
    args = ap.parse_args()

    zonas = carregar_zonas()
    medidas = [z for z in zonas if z["confianca"] in ("alta", "media")]
    print(f"{len(zonas)} zonas na planta, {len(medidas)} com footprint que serve\n")

    saida = {
        "_o_que_e": ("casamento PROPOSTO entre os predios provados no footage de "
                     "13/08 e as zonas da planta. Nao e' medida de campo e nao "
                     "virou geometria: e' ranking por criterio declarado"),
        "_regra": ("so vira proposta quando o primeiro ganha do segundo por "
                   f"{args.margem:.2f} em nota de 0 a 1. Empate vira "
                   "sem_veredito, com o que falta escrito"),
        "_nao_faz": ("nao troca geometria, nao renomeia zona, nao decide "
                     "nomenclatura -- nomenclatura e posicao de area sao "
                     "material de venda de espaco fisico"),
        "margem": args.margem,
        "predios": {},
    }

    for nome, ass in ASSINATURAS.items():
        print("=" * 70)
        print(f"{nome} -- {ass['o_que_e']}")
        print(f"  quadros: {', '.join(ass['quadros'])}")
        if ass.get("_aviso"):
            print(f"  AVISO: {ass['_aviso']}")

        notas = []
        for z in medidas:
            nota, provas, elim = avaliar(z, zonas, ass["criterios"])
            if elim:
                continue
            notas.append((nota, z, provas))
        notas.sort(key=lambda t: -t[0])

        for nota, z, _ in notas[:5]:
            print(f"    {nota:.3f}  {z['rotulo'][:36]:<38}"
                  f"{z['largura_m']:6.1f} x {z['profundidade_m']:<6.1f}"
                  f" ({z['x_m']:+.0f}, {z['y_m']:+.0f})")

        bloco = {
            "o_que_e": ass["o_que_e"],
            "quadros_que_provam": ass["quadros"],
            "criterios": ass["criterios"],
            "ranking": [{"nota": round(n, 4), "rotulo": z["rotulo"],
                         "x_m": z["x_m"], "y_m": z["y_m"],
                         "largura_m": z["largura_m"],
                         "profundidade_m": z["profundidade_m"],
                         "provas": p}
                        for n, z, p in notas[:5]],
        }
        if ass.get("_aviso"):
            bloco["_aviso"] = ass["_aviso"]

        if len(notas) == 0:
            bloco["veredito"] = "sem_candidato"
            bloco["o_que_falta"] = ("nenhuma zona com footprint passou os "
                                    "criterios eliminatorios")
            print("  VEREDITO: sem candidato")
        elif len(notas) == 1 or (notas[0][0] - notas[1][0]) >= args.margem:
            bloco["veredito"] = "proposto"
            bloco["zona"] = notas[0][1]["rotulo"]
            # a mancha do primeiro colocado e' confiavel? Preenchimento baixo e'
            # a assinatura de mancha CONTAMINADA -- foi assim que o
            # PAVILHAO - EQUINOS apareceu maior que os irmaos em 14/08: 0,71 do
            # proprio retangulo, contra 0,99 dos cinco.
            preench = notas[0][1].get("preenchimento")
            if preench is not None and preench < 0.80:
                bloco["ressalva_da_mancha"] = (
                    f"preenchimento {preench:.3f} do proprio retangulo. Abaixo "
                    "de 0,80 e' a assinatura de mancha contaminada (o "
                    "PAVILHAO - EQUINOS deu 0,71 contra 0,99 dos irmaos), e o "
                    "ROTULO desta zona pode nao ser o do predio que a mancha "
                    "desenha")
            bloco["vantagem_sobre_o_segundo"] = round(
                notas[0][0] - (notas[1][0] if len(notas) > 1 else 0.0), 4)
            if bloco["vantagem_sobre_o_segundo"] < 2 * args.margem:
                bloco["margem_apertada"] = True
                bloco["_leia_assim"] = (
                    "a vantagem mal passou do limiar. Isto e' o primeiro "
                    "colocado, nao e' o predio identificado -- trate como "
                    "candidato principal e nao como resposta")
            bloco["ainda_precisa_de"] = (
                "confirmacao antes de virar geometria: um quadro que mostre a "
                "zona e o predio no mesmo enquadramento, ou a palavra dele")
            print(f"  VEREDITO: PROPOSTO -> {notas[0][1]['rotulo']} "
                  f"(vantagem {bloco['vantagem_sobre_o_segundo']:.3f})")
        else:
            bloco["veredito"] = "sem_veredito"
            bloco["empate_entre"] = [notas[0][1]["rotulo"], notas[1][1]["rotulo"]]
            bloco["o_que_falta"] = (
                "os dois primeiros ficaram dentro da margem. Separa: um quadro "
                "nadir que pegue o predio, ou a palavra dele sobre qual zona e")
            print(f"  VEREDITO: sem veredito -- {notas[0][1]['rotulo']} e "
                  f"{notas[1][1]['rotulo']} a {notas[0][0]-notas[1][0]:.3f}")

        if ass.get("resposta_conhecida"):
            acertou = bloco.get("zona") == ass["resposta_conhecida"]
            bloco["controle"] = {
                "resposta_conhecida": ass["resposta_conhecida"],
                "acertou": bool(acertou),
            }
            print(f"  CONTROLE: resposta conhecida {ass['resposta_conhecida']} "
                  f"-> {'ACERTOU' if acertou else 'ERROU'}")

        saida["predios"][nome] = bloco
        print()

    alvo = Path(args.saida)
    alvo.parent.mkdir(parents=True, exist_ok=True)
    alvo.write_text(json.dumps(saida, ensure_ascii=False, indent=1),
                    encoding="utf-8")
    print(f"gravado: {alvo}")

    controles = [b for b in saida["predios"].values() if "controle" in b]
    erraram = [b for b in controles if not b["controle"]["acertou"]]
    if erraram:
        print("\nATENCAO: o metodo errou um controle. Enquanto isso nao fechar, "
              "o ranking dos demais nao vale como proposta.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
