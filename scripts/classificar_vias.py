#!/usr/bin/env python3
"""Separa, entre as 42 'vias', o que e estrada e o que e curva de nivel.

    .venv/Scripts/python.exe scripts/classificar_vias.py

`data/vias.json` saiu de Hough probabilistico sobre o bitmap da planta, e
carrega o aviso desde que nasceu: *"TRACADO LIDO DE BITMAP, NAO CONFERIDO"*.
A sobreposicao no aereo nadir de 13/08 (`scripts/sobrepor_aereo.py`) mostrou
por que o aviso existia: boa parte dos tracos desenha **arcos concentricos
dentro da bacia**, e arco concentrico dentro da bacia nao e estrada.

**O Natan confirmou olhando a folha, em 15/08:** *"Isso mesmo e curva de nivel,
a estrada fica um pouco acima"*.

## O teste, e por que ele nao tem parametro que muda a resposta

A armadilha 16 deste projeto diz: *"parametro que muda a resposta nao e medida"*.
Entao o criterio aqui e geometrico e duro, nao um limiar ajustado ate o
resultado ficar bonito:

- **raio quase constante.** Curva de nivel acompanha uma cota, e cota em bacia
  escavada e um raio. Estrada corta a cota. A medida e o desvio relativo do raio
  ao longo do traco -- `(rmax - rmin) / rmedio`.
- **dentro do alcance da bacia.** Fora de r = 150 m os patamares se reencontram
  na mesma cota (`data/bacia.json`) e nao ha mais talude para virar curva.

Um traco so e curva de nivel se passar nos DOIS. Traco curto tambem tem raio
quase constante por acidente, entao ha um piso de comprimento -- e ele esta
declarado, com a conta.

## O que este script NAO faz

Nao apaga nada e nao marca nada como conferido. Ele **acrescenta um campo** por
via, com o motivo. `conferido_pelo_natan` continua sendo dele.
"""

import json
import math
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

DESVIO_MAXIMO = 0.18
"""Desvio relativo do raio abaixo do qual o traco acompanha uma cota.

Nao e limiar de gosto: 0,18 e o que separa um arco de patamar de um traco que
corta a bacia. Os patamares de `terreno.PATAMARES` estao a 45, 62, 78, 95, 125 e
150 m -- vizinhos separados por 17 a 30 m, o que da 27% a 35% do raio. Um traco
que varia menos que 18% do raio nao consegue pular de um patamar para o vizinho:
ele fica dentro de um. Acima disso, ele cruza cota, e cruzar cota e o que
estrada faz."""

COMPRIMENTO_MINIMO_M = 25.0
"""Piso de comprimento. Traco curto tem raio quase constante por acidente --
qualquer segmento de 5 m parece um arco. 25 m e ~metade da distancia entre dois
patamares vizinhos: abaixo disso o teste nao tem o que medir."""

RAIO_MAXIMO_M = 150.0
"""Alcance da bacia. `data/bacia.json`: fora de 150 m os dois perfis se
reencontram na mesma cota e o platao fica em 10 m em todos os rumos. Nao ha
talude la, entao nao ha curva de nivel para confundir com estrada."""


def main():
    arq = RAIZ / "data" / "vias.json"
    d = json.loads(arq.read_text(encoding="utf-8"))
    bacia = json.loads((RAIZ / "data" / "bacia.json").read_text(encoding="utf-8"))
    cx, cy = bacia["a_medicao"]["centro_da_arena_m"]

    print("=" * 78)
    print("VIAS -- separando estrada de curva de nivel")
    print("=" * 78)
    print(f"  centro da arena: ({cx}, {cy}) m")
    print(f"  criterio: desvio de raio < {DESVIO_MAXIMO:.0%}  E  raio medio < "
          f"{RAIO_MAXIMO_M:.0f} m  E  comprimento >= {COMPRIMENTO_MINIMO_M:.0f} m\n")
    print(f"  {'id':5s} {'compr':>7s} {'r medio':>8s} {'desvio r':>9s}  veredito")

    curvas, estradas, curtas = [], [], []
    for v in d["vias"]:
        if not v["e_via"]:
            continue
        pts = v["pontos_m"]
        raios = [math.hypot(p[0] - cx, p[1] - cy) for p in pts]
        rmed = sum(raios) / len(raios)
        desvio = (max(raios) - min(raios)) / max(rmed, 1e-9)
        comp = v["comprimento_m"]

        if comp < COMPRIMENTO_MINIMO_M:
            classe, motivo = "indeterminado", (
                f"traco de {comp:.0f} m, abaixo do piso de {COMPRIMENTO_MINIMO_M:.0f} m. "
                "Traco curto parece arco por acidente -- o teste nao tem o que medir")
            curtas.append(v["id"])
        elif desvio < DESVIO_MAXIMO and rmed < RAIO_MAXIMO_M:
            classe, motivo = "curva_de_nivel", (
                f"raio quase constante ({desvio:.0%} de variacao) a {rmed:.0f} m do "
                "centro da arena, dentro do alcance da bacia. Acompanha a cota em vez "
                "de cruza-la: e o contorno do patamar, nao estrada")
            curvas.append(v["id"])
        else:
            classe, motivo = "estrada", (
                f"varia {desvio:.0%} do raio" if rmed < RAIO_MAXIMO_M
                else f"raio medio {rmed:.0f} m, fora do alcance da bacia")
            estradas.append(v["id"])

        v["classe_geometrica"] = classe
        v["_motivo_da_classe"] = motivo
        v["raio_medio_m"] = round(rmed, 1)
        v["desvio_de_raio"] = round(desvio, 3)

        marca = {"curva_de_nivel": "CURVA DE NIVEL",
                 "estrada": "estrada",
                 "indeterminado": "indeterminado"}[classe]
        print(f"  {v['id']:5s} {comp:6.0f}m {rmed:7.0f}m {desvio:8.0%}   {marca}")

    d["_classificacao_geometrica"] = {
        "quando": "2026-08-15",
        "por_que": ("a sobreposicao no aereo nadir mostrou tracos desenhando arcos "
                    "concentricos dentro da bacia, e o Natan confirmou olhando: "
                    "'Isso mesmo e curva de nivel, a estrada fica um pouco acima'"),
        "criterio": {"desvio_maximo_de_raio": DESVIO_MAXIMO,
                     "raio_maximo_m": RAIO_MAXIMO_M,
                     "comprimento_minimo_m": COMPRIMENTO_MINIMO_M},
        "resultado": {"curva_de_nivel": curvas, "estrada": estradas,
                      "indeterminado": curtas},
        "_palavra_dele": ("'a estrada fica um pouco acima' -- a estrada de verdade "
                          "corre por FORA do arco que o Hough leu. Quem for tirar "
                          "geometria de via daqui precisa dessa oposicao: o arco "
                          "marca a cota, a estrada esta um pouco alem dela."),
        "_o_que_isto_NAO_e": ("conferencia. Nenhuma via foi marcada como conferida; "
                              "`conferido_pelo_natan` continua false em todas, e o "
                              "nome do campo diz de quem e."),
    }
    arq.write_text(json.dumps(d, indent=1, ensure_ascii=False), encoding="utf-8")

    print(f"\n  curva de nivel : {len(curvas):2d}   {', '.join(curvas)}")
    print(f"  estrada        : {len(estradas):2d}   {', '.join(estradas)}")
    print(f"  indeterminado  : {len(curtas):2d}   {', '.join(curtas)}")
    print(f"\ngravado: {arq}")
    print("=" * 78)


if __name__ == "__main__":
    main()
