#!/usr/bin/env python3
"""Confere o que data/texturas.json promete -- e ele apontava para um vazio.

O contrato dizia, desde 14/08, que "conferir e o que scripts/conferir_texturas.py
faz". O arquivo nunca existiu. Um ponteiro para um script que nao existe e pior
que nenhum ponteiro: ele parece uma garantia e nao e. Esta e a entrada fina; a
conta mora em scripts/texturas.py:conferir(), que ja estava escrita e certa.

Alem da conta, aqui se confere o que so se ve em disco:

* todo mapa que o contrato pede esta la;
* o Diffuse e mesmo NEUTRO (se tiver cor, a cor medida e multiplicada duas
  vezes -- ver `por_que_o_diffuse_e_neutro` no contrato);
* o Albedo tem mesmo, por canal e em linear, a cor medida como media;
* a normal e OpenGL e nao DirectX -- o azul nunca desce de 0,5 e o verde tem
  media 0,5.

Uso:
    python scripts/conferir_texturas.py            # confere tudo
    python scripts/conferir_texturas.py --so-conta # so a conta da variacao
"""

import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

import texturas  # noqa: E402  -- a conta mora la


CONTRATO = RAIZ / "data" / "texturas.json"
SAIDA = RAIZ / "assets" / "textura"
TOLERANCIA_COR = 0.02      # 2% -- o JPEG de qualidade 95 sozinho ja custa ~0,3%
TOLERANCIA_NEUTRO = 0.01   # desvio maximo entre canais de um mapa dito neutro


def _srgb_para_linear(v):
    import numpy as np
    return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)


def _ler(caminho):
    """imdecode e nao imread: o projeto mora em 'E:\\I.A Edit' e imread do
    OpenCV nao abre caminho com acento no Windows."""
    import cv2
    import numpy as np
    img = cv2.imdecode(np.fromfile(str(caminho), dtype=np.uint8),
                       cv2.IMREAD_COLOR)
    if img is None:
        raise SystemExit(f"nao abriu: {caminho}")
    return img


def conferir_arquivos():
    import numpy as np

    contrato = json.loads(CONTRATO.read_text(encoding="utf-8"))
    res = contrato.get("resolucao", "2k")
    tudo_ok = True

    for material, item in contrato["itens"].items():
        slug = item["slug"]
        print(f"\n{material}  ({slug})")

        # 1. os arquivos que o contrato pede
        for mapa in item["mapas"]:
            alvo = texturas.caminho_mapa(slug, mapa, res)
            if alvo is None:
                print(f"   FALTA  {slug}_{mapa}_{res}")
                tudo_ok = False
            else:
                print(f"   ok     {alvo.name}")

        # 2. o Diffuse tem que ser neutro
        if item.get("usa_variacao_de_cor"):
            d = texturas.caminho_mapa(slug, "Diffuse", res)
            if d is not None:
                img = _ler(d).astype(np.float64) / 255.0
                m = img.reshape(-1, 3).mean(axis=0)
                desvio = float(m.max() - m.min())
                veredito = "ok" if desvio <= TOLERANCIA_NEUTRO else "COLORIDO"
                if veredito != "ok":
                    tudo_ok = False
                print(f"   Diffuse neutro: desvio entre canais {desvio:.4f}  "
                      f"{veredito}")

        # 3. o Albedo tem que ter a cor medida como media linear
        alvo_cor = item.get("cor_alvo_linear_rgb")
        a = SAIDA / f"{slug}_Albedo_{res}.jpg"
        if alvo_cor and a.exists():
            lin = _srgb_para_linear(_ler(a).astype(np.float64) / 255.0)
            m = lin.reshape(-1, 3).mean(axis=0)[::-1]   # cv2 e BGR
            erro = [abs(m[i] - alvo_cor[i]) / max(alvo_cor[i], 1e-9)
                    for i in range(3)]
            veredito = "ok" if max(erro) <= TOLERANCIA_COR else "FORA"
            if veredito != "ok":
                tudo_ok = False
            print("   albedo  alvo " + " ".join(f"{v:.4f}" for v in alvo_cor)
                  + "  medido " + " ".join(f"{v:.4f}" for v in m)
                  + "  erro " + " ".join(f"{100*v:.2f}%" for v in erro)
                  + f"  {veredito}")

        # 4. normal OpenGL e nao DirectX
        n = texturas.caminho_mapa(slug, "nor_gl", res)
        if n is not None:
            img = _ler(n).astype(np.float64) / 255.0
            azul, verde = img[..., 0], img[..., 1]   # BGR
            # z de uma normal de superficie nunca aponta para dentro
            ok_azul = azul.min() >= 0.5
            # sem viés de direcao: numa superficie sem inclinacao media, 0,5
            ok_verde = abs(verde.mean() - 0.5) < 0.02
            if not (ok_azul and ok_verde):
                tudo_ok = False
            print(f"   normal  azul min {azul.min():.3f} "
                  f"({'ok' if ok_azul else 'Z NEGATIVO'})   "
                  f"verde medio {verde.mean():.3f} "
                  f"({'ok' if ok_verde else 'VIESADO'})")

    return tudo_ok


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--so-conta", action="store_true",
                    help="so a conta da variacao (texturas.py:conferir)")
    args = ap.parse_args()

    print("== a conta da variacao (scripts/texturas.py:conferir) ==")
    conta_ok = texturas.conferir()
    if args.so_conta:
        return 0 if conta_ok else 1

    print("\n== o que so se ve em disco ==")
    disco_ok = conferir_arquivos()

    print("\n" + ("TUDO OK" if (conta_ok and disco_ok) else "TEM COISA FORA"))
    return 0 if (conta_ok and disco_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
