#!/usr/bin/env python3
"""Abre o EXR de dado e EXTRAI UM MATTE DE VERDADE. E o portao do passo 0.2.

Roda no venv:

    .venv/Scripts/python.exe scripts/conferir_matte.py out/smoke/data/00001.exr
    .venv/Scripts/python.exe scripts/conferir_matte.py out/smoke/data/00001.exr \\
        --objeto PortalCeleiro --png out/smoke/matte.png

**Por que este arquivo existe.** "Renderizei com Cryptomatte ligado" nao prova
nada. O Blender grava os canais sem reclamar mesmo quando a compressao ja
destruiu o hash -- e o defeito so aparece semanas depois, no dia em que alguem
for isolar um objeto no Resolve e a mascara vier picotada. A unica prova e a
extracao: pegar o nome de um objeto, calcular o hash pela ESPECIFICACAO, e ver
se ele aparece nos ranks gravados com cobertura que faz sentido.

**Como o Cryptomatte funciona, no que importa aqui.** O nome do objeto passa por
MurmurHash3 de 32 bits; o inteiro resultante e reinterpretado como float 32 e
guardado no canal, com um conserto: expoente 0 ou 255 (zero, denormal, infinito
e NaN) e empurrado para 1, senao o valor nao sobrevive a ida e volta. Cada
camada `CryptoObject00` guarda DOIS pares (id, cobertura) nos quatro canais:
R=id0 G=cobertura0 B=id1 A=cobertura1. Um pixel de borda tem dois objetos com
cobertura somando ~1; um pixel cheio tem um so, com cobertura 1.

**O teste de que o arquivo esta INTEIRO** e a cobertura: se a soma das
coberturas de todos os ranks nao for ~1 em cada pixel, ou a compressao mexeu no
dado, ou faltam camadas. E o teste de que o hash sobreviveu e o casamento
exato: o float lido tem que ser BIT A BIT o float calculado. Compressao lossy
erra por pouco -- e por pouco, aqui, e errar tudo.
"""

import argparse
import struct
import sys
from pathlib import Path

import numpy as np

try:
    import OpenEXR
except ImportError:
    raise SystemExit("falta OpenEXR no venv: uv pip install OpenEXR")


def murmur3_32(dados: bytes, semente: int = 0) -> int:
    """MurmurHash3 x86 32 bits. E o hash que a especificacao do Cryptomatte usa.

    Escrito a mao de proposito: e uma dependencia a menos, sao 25 linhas, e
    esta e a peca que precisa estar exatamente certa -- se ela divergir, o
    conferidor acusa arquivo bom de quebrado, que e pior que nao conferir.
    """
    def rotl(x, r):
        return ((x << r) | (x >> (32 - r))) & 0xFFFFFFFF

    c1, c2 = 0xCC9E2D51, 0x1B873593
    h = semente & 0xFFFFFFFF
    n = len(dados)

    for i in range(0, n - n % 4, 4):
        k = struct.unpack_from("<I", dados, i)[0]
        k = (k * c1) & 0xFFFFFFFF
        k = rotl(k, 15)
        k = (k * c2) & 0xFFFFFFFF
        h ^= k
        h = rotl(h, 13)
        h = (h * 5 + 0xE6546B64) & 0xFFFFFFFF

    k = 0
    resto = n % 4
    base = n - resto
    if resto >= 3:
        k ^= dados[base + 2] << 16
    if resto >= 2:
        k ^= dados[base + 1] << 8
    if resto >= 1:
        k ^= dados[base]
        k = (k * c1) & 0xFFFFFFFF
        k = rotl(k, 15)
        k = (k * c2) & 0xFFFFFFFF
        h ^= k

    h ^= n
    h ^= h >> 16
    h = (h * 0x85EBCA6B) & 0xFFFFFFFF
    h ^= h >> 13
    h = (h * 0xC2B2AE35) & 0xFFFFFFFF
    h ^= h >> 16
    return h


def hash_do_nome(nome: str) -> float:
    """Nome -> o float 32 que o Cryptomatte grava no canal de id."""
    h = murmur3_32(nome.encode("utf-8"))
    exponente = (h >> 23) & 0xFF
    if exponente in (0, 255):
        # Zero, denormal, Inf e NaN nao sobrevivem a ida e volta pelo arquivo.
        # A especificacao manda mexer no bit alto do expoente para tirar o
        # valor dessas faixas. Sem isto, objeto com nome "azarado" some.
        h ^= 1 << 23
    return struct.unpack("<f", struct.pack("<I", h))[0]


def canais_do_exr(caminho):
    """Devolve {nome_do_canal: array 2D} de todas as partes do EXR."""
    arq = OpenEXR.File(str(caminho))
    fora = {}
    partes = arq.parts if hasattr(arq, "parts") else [arq.header()]
    for parte in partes:
        prefixo = ""
        nome_parte = None
        if hasattr(parte, "header"):
            nome_parte = parte.header.get("name")
        if nome_parte:
            prefixo = f"{nome_parte}."
        canais = parte.channels if hasattr(parte, "channels") else {}
        for nome, canal in canais.items():
            px = canal.pixels if hasattr(canal, "pixels") else canal
            fora[f"{prefixo}{nome}"] = np.asarray(px)
    return fora, arq


def achar_ranks(canais, familia="CryptoObject"):
    """Agrupa os canais de uma familia em pares (id, cobertura).

    Os canais saem como CryptoObject00.R/.G/.B/.A (ou 'r','g','b','a', ou com
    o nome da camada na frente, dependendo de quem gravou). Aqui a busca e por
    sufixo, para nao depender do arranjo exato de quem escreveu o arquivo.
    """
    import re
    padrao = re.compile(rf"(?:^|\.){re.escape(familia)}(\d\d)\.([RGBArgba])$")
    camadas = {}
    for nome, arr in canais.items():
        m = padrao.search(nome)
        if m:
            camadas.setdefault(m.group(1), {})[m.group(2).upper()] = arr
    ranks = []
    for idx in sorted(camadas):
        c = camadas[idx]
        if {"R", "G"} <= set(c):
            ranks.append((c["R"], c["G"]))
        if {"B", "A"} <= set(c):
            ranks.append((c["B"], c["A"]))
    return ranks


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("exr")
    ap.add_argument("--familia", default="CryptoObject",
                    help="CryptoObject ou CryptoMaterial")
    ap.add_argument("--objeto", default=None,
                    help="nome exato do objeto a isolar. Sem isto, escolhe o "
                         "id mais frequente do quadro e so prova a mecanica")
    ap.add_argument("--png", default=None, help="grava o matte extraido")
    args = ap.parse_args()

    caminho = Path(args.exr)
    if not caminho.exists():
        raise SystemExit(f"nao existe: {caminho}")

    canais, arq = canais_do_exr(caminho)
    print("=" * 66)
    print(f"CONFERIR MATTE -- {caminho.name}  ({caminho.stat().st_size/1e6:.2f} MB)")
    print("=" * 66)
    print(f"  canais no arquivo ... {len(canais)}")
    for nome in sorted(canais)[:40]:
        a = canais[nome]
        print(f"    {nome:34s} {str(a.shape):16s} {a.dtype}")
    if len(canais) > 40:
        print(f"    ... e mais {len(canais)-40}")

    # --- 1. o dado e float 32? -------------------------------------------
    cripto = {n: a for n, a in canais.items() if args.familia in n}
    if not cripto:
        raise SystemExit(f"\nREPROVADO: nenhum canal da familia {args.familia}. "
                         "O passe nao foi gravado.")
    dtypes = {str(a.dtype) for a in cripto.values()}
    print(f"\n  dtype do crypto ..... {dtypes}")
    if dtypes != {"float32"}:
        print("  REPROVADO: cryptomatte precisa ser float 32. Meia precisao "
              "nao representa o hash -- todo matte sai errado.")
        return 1

    ranks = achar_ranks(canais, args.familia)
    print(f"  ranks encontrados ... {len(ranks)}")
    if not ranks:
        raise SystemExit("REPROVADO: canais presentes mas sem par (id, cobertura).")

    # --- 2. a cobertura fecha? (prova de que a compressao nao mexeu) ------
    #
    # **Um pixel de ceu tem cobertura ZERO, e isso e o certo** -- ali nao ha
    # objeto nenhum, so o mundo. A primeira versao deste teste somava tudo e
    # exigia ~1 em todo pixel; reprovou um arquivo bom porque metade do quadro
    # e ceu de fim de tarde. O que de fato acusa defeito e a terceira faixa:
    # pixel que TEM objeto mas cuja cobertura nao fecha em 1 -- ali ou a
    # compressao mexeu no dado, ou faltou camada para o numero de objetos
    # empilhados naquele pixel (levels baixo demais).
    soma = np.zeros_like(ranks[0][1], dtype=np.float64)
    for _, cob in ranks:
        soma += cob

    vazio = soma < 0.001
    fecha = np.isclose(soma, 1.0, atol=0.01)
    parcial = ~vazio & ~fecha
    n = soma.size
    print(f"  sem objeto (ceu) .... {100.0*vazio.mean():6.2f}% dos pixels")
    print(f"  cobertura fecha ..... {100.0*fecha.mean():6.2f}%")
    print(f"  cobertura PARCIAL ... {100.0*parcial.mean():6.2f}%  "
          f"<- e este que acusa defeito")
    if parcial.any():
        print(f"     faixa dos parciais: {soma[parcial].min():.4f} a "
              f"{soma[parcial].max():.4f}")

    com_objeto = (~vazio).sum()
    if com_objeto == 0:
        print("  REPROVADO: nenhum objeto em quadro nenhum -- crypto vazio.")
        return 1
    saude = 100.0 * fecha.sum() / com_objeto
    print(f"  dos pixels COM objeto, fecham: {saude:.2f}%")
    if saude < 95.0:
        print("  REPROVADO: entre os pixels que tem objeto, a cobertura nao "
              "fecha. Ou a compressao e lossy, ou levels e baixo demais para a "
              "quantidade de coisa empilhada (folhagem, tela, transparencia).")
        return 1

    # --- 3. o hash casa BIT A BIT? ---------------------------------------
    ids, cobs = ranks[0]
    if args.objeto:
        alvo = np.float32(hash_do_nome(args.objeto))
        rotulo = args.objeto
    else:
        vals, contagem = np.unique(ids[ids != 0], return_counts=True)
        if not len(vals):
            print("  REPROVADO: nenhum id diferente de zero no rank 0.")
            return 1
        alvo = vals[np.argmax(contagem)]
        rotulo = f"<id mais frequente 0x{struct.unpack('<I', struct.pack('<f', alvo))[0]:08x}>"

    matte = np.zeros_like(cobs, dtype=np.float32)
    achou = 0
    for i, (idc, cob) in enumerate(ranks):
        m = (idc == alvo)
        achou += int(m.sum())
        matte += np.where(m, cob, 0.0).astype(np.float32)

    print(f"\n  objeto .............. {rotulo}")
    if args.objeto:
        print(f"  hash calculado ...... {alvo!r} "
              f"(0x{struct.unpack('<I', struct.pack('<f', np.float32(alvo)))[0]:08x})")
    print(f"  pixels com esse id .. {achou}")
    print(f"  area do matte ....... {matte.sum():.1f} px "
          f"({100.0*matte.mean():.3f}% do quadro)")
    print(f"  faixa do matte ...... {matte.min():.3f} a {matte.max():.3f}")

    if achou == 0:
        print("\n  REPROVADO: o hash nao aparece em nenhum rank.")
        if args.objeto:
            print("  Ou o nome do objeto esta errado, ou ele nao aparece neste")
            print("  quadro, ou a compressao alterou o hash. Rode sem --objeto:")
            print("  se ali o id mais frequente casar, o mecanismo esta vivo e o")
            print("  problema e o nome.")
        return 1

    if args.png:
        import cv2
        alvo_png = Path(args.png)
        alvo_png.parent.mkdir(parents=True, exist_ok=True)
        # imwrite nao abre caminho com acento no Windows -- armadilha 9.
        ok, buf = cv2.imencode(".png", (np.clip(matte, 0, 1) * 255).astype(np.uint8))
        if ok:
            buf.tofile(str(alvo_png))
            print(f"  matte gravado ....... {alvo_png}")

    print("\n  APROVADO: cobertura fecha, dtype certo, hash casa bit a bit.")
    print("=" * 66)
    return 0


if __name__ == "__main__":
    sys.exit(main())
