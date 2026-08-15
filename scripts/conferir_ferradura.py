#!/usr/bin/env python3
"""Confere o rumo da ABERTURA da bacia contra o aereo nadir de 13/08.

    .venv/Scripts/python.exe scripts/conferir_ferradura.py

Em 14/08 a ferradura foi deduzida da PLANTA, por duas testemunhas indiretas que
concordaram: no setor de 240 a 360 graus nao ha **nenhum** dos 15 `Talude` e
**nenhum** dos 93 estandes da serie C. Dai saiu `data/bacia.json`: arrimo em
~210 graus de arco, abertura de ~120 graus para SUL-SUDESTE.

Aquilo era inferencia sobre desenho. **O video `1 (2)` de 13/08 e um nadir de
drone e mostra a ferradura direto** -- as arquibancadas concentricas aparecem
como arcos aninhados, e da para ver de que lado elas nao fecham.

## Como se tira azimute de uma foto sem bussola

A foto nao sabe onde e o norte. Mas no MESMO quadro esta a fileira de pavilhoes,
e o rumo dela ja esta medido no desenho: `RUMO_PAVILHOES` resolve em azimute
**108 graus** (`docs/CONFERENCIA-POSICAO.md`, e a armadilha da convencao esta
registrada la -- o valor 341,0 e escrito como azimute e aplicado como angulo
matematico, e da certo por sorte).

Entao mede-se o ANGULO ENTRE as duas direcoes dentro da imagem, que nao depende
de saber o norte, e soma-se ao rumo conhecido:

    azimute_da_abertura = 108 + angulo(eixo_dos_pavilhoes -> abertura)

O quadro e nadir, entao a projecao e ortografica em primeira ordem e angulo
medido na imagem e angulo no mundo. Foto aerea nao e espelhada, entao o sentido
horario na tela e o sentido horario visto de cima, que e o sentido em que o
azimute cresce.

**Fica uma ambiguidade de 180 graus, e ela e honesta:** o eixo dos pavilhoes e
uma reta, e 108 e 288 sao a mesma reta. Quem desempata e a planta -- e como a
planta ja disse que o setor de 240 a 360 nao tem talude nenhum, so uma das duas
respostas sobrevive. As duas fontes concordando e o resultado; nao e uma fonte
so com duas contas.

Os pontos abaixo foram lidos na folha com grade de `out/linear-preview/`, em
pixel do quadro original (3840x2160), e estao declarados para qualquer um
conferir com a mesma folha.
"""

import json
import math
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

QUADRO = "1 (2)__0076s"

# --- pontos lidos no quadro, em pixel do original -----------------------------
# eixo dos pavilhoes: as duas pontas do galpao branco comprido do alto
PAVILHAO_A = (1760, 140)
PAVILHAO_B = (2800, 820)

# a bacia: centro dos arcos concentricos, e um ponto no meio da boca aberta
BACIA_CENTRO = (1820, 1600)
BACIA_BOCA = (1820, 2100)

AZIMUTE_PAVILHOES = 108.0
"""Rumo da fileira de pavilhoes, medido no footprint do desenho em 14/08."""

def azimute_da_planta():
    """Centro da boca segundo `data/bacia.json`, convertido para rumo de mapa.

    **A convencao daquele arquivo NAO e a da bussola**, e ele diz isso na cara:
    *"0 graus = +x (leste do mapa), 90 = +y (norte do mapa), anti-horario"*. Na
    primeira versao deste script eu escrevi 165 a mao dizendo que era o que o
    arquivo dizia -- nao era, era o que eu tinha construido de cabeca. Agora sai
    da conta, e a conta esta aqui:

        rumo_de_mapa = 90 - phi          (phi = azimute na convencao do bacia.json)

    O setor vazio de la e [240, 360] em phi, entao o centro da boca esta em
    phi = 300, o que da rumo de mapa 150. O rumo VERDADEIRO seria 150 + 11,5
    (data/luz.json), mas aqui nao interessa: o eixo dos pavilhoes tambem esta em
    rumo de mapa, e comparar duas coisas no mesmo referencial dispensa converter."""
    b = json.loads((RAIZ / "data" / "bacia.json").read_text(encoding="utf-8"))
    v = b["a_medicao"]["testemunha_2_estandes_serie_c"]["setor_vazio_graus"]
    phi_centro = (v[0] + v[1]) / 2.0
    return (90.0 - phi_centro) % 360.0


AZIMUTE_DA_PLANTA = None  # calculado em main(), a partir de data/bacia.json

TOLERANCIA = 20.0
"""Quanto o aereo pode divergir da planta e ainda ser a mesma resposta.

20 graus e maior que a incerteza de ler ponta de galpao e centro de arco numa
folha reduzida (que e de ~5 graus), e menor que a largura da propria boca, que
tem 120 graus. Divergencia acima disso nao e ruido de leitura: e as duas fontes
discordando, e ai NAO se escolhe -- vira pendencia com o quadro recortado."""


def angulo_na_imagem(p, q):
    """Angulo do vetor p->q, em graus, horario a partir do eixo +x.

    A imagem tem y para baixo, entao girar de +x para +y e horario na tela --
    que e o mesmo sentido em que o azimute cresce numa vista de cima."""
    return math.degrees(math.atan2(q[1] - p[1], q[0] - p[0])) % 360.0


def main():
    global AZIMUTE_DA_PLANTA
    AZIMUTE_DA_PLANTA = azimute_da_planta()
    a_pav = angulo_na_imagem(PAVILHAO_A, PAVILHAO_B)
    a_boca = angulo_na_imagem(BACIA_CENTRO, BACIA_BOCA)
    entre = (a_boca - a_pav) % 360.0

    cand = [(AZIMUTE_PAVILHOES + entre) % 360.0,
            (AZIMUTE_PAVILHOES + 180.0 + entre) % 360.0]

    print("=" * 74)
    print(f"FERRADURA DA BACIA -- conferencia contra o aereo {QUADRO}")
    print("=" * 74)
    print(f"  eixo dos pavilhoes na imagem : {a_pav:6.1f} graus (horario de +x)")
    print(f"  boca da bacia na imagem      : {a_boca:6.1f} graus")
    print(f"  angulo ENTRE as duas         : {entre:6.1f} graus  "
          "<- e este que nao depende de saber o norte")
    print(f"\n  eixo dos pavilhoes no mundo  : azimute {AZIMUTE_PAVILHOES:.1f} "
          "(medido no desenho, 14/08)")
    print(f"  -> abertura da bacia         : azimute {cand[0]:.1f} OU {cand[1]:.1f}")
    print("     (a reta dos pavilhoes tem dois sentidos; a foto nao os separa)")

    escolhido = min(cand, key=lambda c: abs((c - AZIMUTE_DA_PLANTA + 180) % 360 - 180))
    desvio = abs((escolhido - AZIMUTE_DA_PLANTA + 180) % 360 - 180)
    passa = desvio <= TOLERANCIA

    print(f"\n  a planta (data/bacia.json) diz : azimute {AZIMUTE_DA_PLANTA:.1f}")
    print(f"  o candidato que sobrevive      : azimute {escolhido:.1f}")
    print(f"  desvio                         : {desvio:.1f} graus  "
          f"(tolerancia {TOLERANCIA:.0f})")
    print(f"\n  VEREDITO: {'CONFERE' if passa else 'NAO CONFERE -- vira pendencia'}")
    if passa:
        print("  Duas fontes que nao se falam: a planta (por ausencia de talude e"
              "\n  de estande no setor) e a foto de drone (pela boca visivel).")
    else:
        print("  NAO escolher entre elas. Recortar o quadro e levar para ele.")

    d = RAIZ / "data" / "ferradura-conferida.json"
    d.write_text(json.dumps({
        "_procedencia": "registro — conferencia da ferradura contra aereo nadir de 13/08",
        "quadro": QUADRO,
        "metodo": ("angulo entre o eixo dos pavilhoes e a boca da bacia, medido "
                   "dentro da imagem; somado ao azimute do eixo, que vem do "
                   "desenho. Nadir, entao angulo na imagem = angulo no mundo."),
        "pontos_px": {"pavilhao_a": PAVILHAO_A, "pavilhao_b": PAVILHAO_B,
                      "bacia_centro": BACIA_CENTRO, "bacia_boca": BACIA_BOCA},
        "angulo_entre_graus": round(entre, 1),
        "azimute_pavilhoes": AZIMUTE_PAVILHOES,
        "candidatos": [round(c, 1) for c in cand],
        "ambiguidade": "180 graus — a reta dos pavilhoes tem dois sentidos e a foto nao os separa. Desempatada pela planta.",
        "azimute_da_planta": AZIMUTE_DA_PLANTA,
        "escolhido": round(escolhido, 1),
        "desvio_graus": round(desvio, 1),
        "tolerancia_graus": TOLERANCIA,
        "veredito": "CONFERE" if passa else "NAO CONFERE",
    }, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\ngravado: {d}")
    print("=" * 74)


if __name__ == "__main__":
    main()
