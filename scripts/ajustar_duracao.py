#!/usr/bin/env python3
"""
Reconcilia a DURACAO dos planos com a faixa de velocidade, depois que o
reenquadramento mexeu na distancia.

Por que existe. `consertar_camera.py` afasta a camera para tirar o telhado da
frente do quadro. Afastar num push-in alonga o caminho, e o caminho dividido
pela mesma duracao da velocidade maior: em 15/08, quatro push-ins sairam da
faixa cinematografica (P04, P06, P08 e P10, entre 2,53 e 3,00 m/s contra o teto
de 2,20).

Havia duas saidas e elas nao sao equivalentes:

  1. encurtar o percurso -- devolve a velocidade e enfraquece o push-in, que e'
     justamente o movimento que faz o assunto crescer na tela;
  2. alongar a duracao -- devolve a velocidade e da MAIS TELA ao plano.

A 2 vence sem empate neste projeto: dois dos quatro planos fora de faixa sao
diferenciais (Mercado do Produtor e Cafe Colonial), e o cliente pediu
nominalmente mais tempo de tela para os quatro diferenciais. Alongar e' o que
ele pediu; encurtar seria trabalhar contra o briefing para salvar um numero.

O alvo nao e' o teto da faixa, e' 2,0 m/s -- com folga, porque o `_v_pico` sobe
de novo se o shake da camera for reamostrado.

    python scripts/ajustar_duracao.py --escrever
"""

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import planos as planos_mod
from terreno import carregar_mapa

ALVO_DENTRO_DA_FAIXA = {
    "push-in": 2.00, "orbita": 2.00, "travelling": 2.00,
    "subida": 5.50, "sobrevoo": 6.00,
}
PASSO_S = 0.5      # duracao sempre em meio segundo -- 15 quadros a 30 fps


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--planos", default="data/planos.json")
    ap.add_argument("--escrever", action="store_true")
    args = ap.parse_args()

    dados = carregar_mapa()
    pacote = planos_mod.carregar(args.planos, dados)
    doc = json.loads(Path(args.planos).read_text(encoding="utf-8"))
    por_id = {p["id"]: p for p in doc["planos"]}

    antes = pacote["total_quadros"]
    mudancas = []
    for p in pacote["planos"]:
        lo, hi = planos_mod.FAIXAS[p["movimento"]]
        if lo <= p["_v_pico"] <= hi:
            continue
        alvo = ALVO_DENTRO_DA_FAIXA[p["movimento"]]
        nova = p["duracao_s"] * p["_v_pico"] / alvo
        nova = math.ceil(nova / PASSO_S) * PASSO_S
        mudancas.append((p["id"], p["duracao_s"], nova, p["_v_pico"], alvo,
                         p["titulo"], p["peso"]))
        if args.escrever:
            alvo_doc = por_id[p["id"]]
            alvo_doc["duracao_antes_1508"] = p["duracao_s"]
            alvo_doc["duracao_s"] = nova
            alvo_doc["por_que_alongou_1508"] = (
                f"o reenquadramento de 15/08 afastou a camera e o pico foi a "
                f"{p['_v_pico']:.2f} m/s, fora da faixa {lo}-{hi} de "
                f"{p['movimento']}. Alongado de {p['duracao_s']:.1f} s para "
                f"{nova:.1f} s para voltar a ~{alvo:.1f} m/s. Alongar em vez de "
                f"encurtar o percurso porque o cliente pediu MAIS tempo de tela, "
                f"nao menos.")

    if not mudancas:
        print("  nenhum plano fora da faixa -- nada a ajustar.")
        return

    print(f"{'plano':6} {'de':>6} {'para':>6} {'pico':>6} {'alvo':>6}  titulo")
    for pid, de, para, pico, alvo, titulo, peso in mudancas:
        estrela = " *" if peso == "diferencial" else ""
        print(f"{pid:6} {de:6.1f} {para:6.1f} {pico:6.2f} {alvo:6.2f}  "
              f"{titulo[:36]}{estrela}")

    if args.escrever:
        Path(args.planos).write_text(json.dumps(doc, ensure_ascii=False, indent=1),
                                     encoding="utf-8")
        novo = planos_mod.carregar(args.planos, dados)
        print(f"\n  quadros: {antes} -> {novo['total_quadros']} "
              f"({novo['total_quadros'] - antes:+d}, "
              f"{(novo['total_quadros'] / antes - 1) * 100:+.1f}%)")
        print(f"  duracao do filme: {antes / 30:.0f} s -> "
              f"{novo['total_quadros'] / 30:.0f} s")
        print("  * = diferencial, e o cliente pediu mais tela para os quatro")
    else:
        print("\n  (nada gravado -- use --escrever)")


if __name__ == "__main__":
    main()
