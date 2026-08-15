#!/usr/bin/env python3
"""Mede o granulado dos quadros do passo 0.4 e fecha o relatorio.

    .venv/Scripts/python.exe scripts/medir_ruido.py out/medicao

Roda no VENV, e nao dentro do Blender, por um motivo simples: o Python que vem
embutido no Blender nao tem cv2. A primeira versao media ali dentro e morria no
`import` DEPOIS de gastar os quatro renders -- o trabalho caro feito e o
resultado perdido. Render e medicao sao passos separados desde entao.

**Como o ruido e medido, e por que nao e "olhar".** Desvio-padrao local da
luminancia em janela 3x3, e a MEDIANA disso no quadro. Granulado de amostragem
levanta o desvio local em toda parte; borda de geometria tambem levanta, mas so
numa fracao pequena de pixels -- e a mediana ignora essa fracao. Media, nao:
media seria dominada pelas bordas e diria que o quadro com mais contorno tem
mais ruido, o que e falso.
"""

import json
import sys
from pathlib import Path

import cv2
import numpy as np


def ruido_local(caminho):
    # imdecode/fromfile porque cv2.imread nao abre caminho com acento no
    # Windows -- armadilha 9 do RETOMAR, e o caminho aqui tem virgula e acento.
    img = cv2.imdecode(np.fromfile(str(caminho), dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return None
    lum = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    media = cv2.blur(lum, (3, 3))
    media2 = cv2.blur(lum * lum, (3, 3))
    var = np.maximum(media2 - media * media, 0.0)
    return float(np.median(np.sqrt(var)))


def main():
    raiz = Path(sys.argv[1] if len(sys.argv) > 1 else "out/medicao")
    rel = raiz / "relatorio.json"
    if not rel.exists():
        raise SystemExit(f"nao achei {rel} -- rode scripts/medir_render.py antes")

    dados = json.loads(rel.read_text(encoding="utf-8"))
    print("=" * 72)
    print("RUIDO DOS QUADROS DO PASSO 0.4")
    print("=" * 72)
    for linha in dados["configs"]:
        arq = raiz / linha["arquivo"]
        r = ruido_local(arq) if arq.exists() else None
        linha["ruido_local"] = round(r, 5) if r is not None else None
        print(f"  {linha['config']:24s} {linha['segundos']:7.1f} s   "
              + (f"ruido {r:.5f}" if r is not None else "ARQUIVO AUSENTE"))

    base = next(l for l in dados["configs"] if l["config"].startswith("128/0,1  com"))
    alvo = next(l for l in dados["configs"] if l["config"].startswith("max/0,01 com"))
    cru = next(l for l in dados["configs"] if l["config"].startswith("128/0,1  sem"))

    print("\n  O QUE O DENOISE FAZ SOZINHO (128 samples, com e sem):")
    if cru["ruido_local"] and base["ruido_local"]:
        print(f"    {100.0*(1 - base['ruido_local']/cru['ruido_local']):+.1f}% de ruido, "
              f"{100.0*(base['segundos']/cru['segundos']-1):+.0f}% de tempo")

    print("\n  O NUMERO PARA O NATAN -- as duas COM denoise, como ele renderiza:")
    dtempo = dados["delta_tempo_pct"]
    print(f"    0,01 custa {dtempo:+.0f}% de tempo")
    if base["ruido_local"] and alvo["ruido_local"]:
        druido = 100.0 * (1 - alvo["ruido_local"] / base["ruido_local"])
        dados["delta_ruido_pct"] = round(druido, 1)
        print(f"    e entrega {druido:+.1f}% de ruido local")
        if abs(druido) < 5:
            print("    -> EMPATAM. O denoise ja resolveu o granulado; 0,01 e")
            print("       tempo gasto sem imagem. A config dele de 14/08 se sustenta.")
        else:
            print("    -> ha ganho medivel. A escolha continua sendo dele.")

    rel.write_text(json.dumps(dados, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n  relatorio atualizado  {rel}")
    print("=" * 72)


if __name__ == "__main__":
    main()
