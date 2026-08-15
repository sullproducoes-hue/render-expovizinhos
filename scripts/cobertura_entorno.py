#!/usr/bin/env python3
"""Cobertura do solo do entorno: lavoura, mata, agua e cidade, do dado real.

Pendencia 11b. O relevo do entorno ja e real (`relevo_entorno.py`), mas a COR
nao era: os 12 km em volta saiam com a cor da grama do recinto, sem o xadrez de
lavoura e sem a mata -- e o quadro `DJI_20251129182345_0168_D` 00:00:52 mostra a
lavoura subindo em socalco e a mata fechada atras.

**Fonte: ESA WorldCover 10 m, 2021 v200.** Sem chave e sem cadastro, servido em
S3 publico, licenca CC-BY 4.0 (creditada no MANIFESTO). Resolucao de 10 m, que e
tres vezes melhor que o DEM -- entao o desenho do talhao aparece, e talhao e
justamente o que da leitura de lavoura a distancia.

**Nao baixa os 103 MB do azulejo.** O arquivo e um GeoTIFF em blocos e o S3
aceita `Range`, entao um objeto tipo-arquivo por HTTP entrega so os blocos da
janela. Sao ~2 MB em vez de 103.

**E a COR de cada classe e MEDIDA no footage do proprio Natan.** Este e o ponto:
o WorldCover diz *o que* e cada pedaco de chao; `data/materiais-medidos.json`
diz *que cor aquilo tem naquela luz*. Inclusive a lavoura -- a amostra `campo`
foi medida em 14/08 apenas como CONTROLE do metodo ("qualquer um olha e diz que
e verde") e nunca tinha virado material. Ela e exatamente isto: a cor da lavoura
do entorno, no mesmo quadro e na mesma luz do resto.

Uso:
    python scripts/cobertura_entorno.py
"""

import argparse
import json
import math
import sys
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

import relevo_entorno as rel

SAIDA_PNG = RAIZ / "assets" / "relevo" / "entorno_cobertura.png"
SAIDA_META = RAIZ / "data" / "cobertura-entorno.json"

BASE = ("https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/"
        "ESA_WorldCover_10m_2021_v200_{tile}_Map.tif")
CABECALHO = {"User-Agent": "render-expovizinhos/1.0 (contato via github)"}

# Classes do WorldCover e de onde sai a cor de cada uma.
# 'medido' aponta para a amostra em data/materiais-medidos.json.
CLASSES = {
    10: {"nome": "arvore",     "medido": "arvore",
         "por_que": "mata e capao: a copa foi MEDIDA no footage"},
    20: {"nome": "arbustiva",  "medido": None, "cor": [0.150, 0.150, 0.055],
         "por_que": "entre a grama sa medida e a copa medida -- interpolado, declarado"},
    30: {"nome": "campo",      "medido": "grama",
         "por_que": "pastagem: a mesma grama sa medida do recinto"},
    40: {"nome": "lavoura",    "medido": "campo",
         "por_que": "a amostra 'campo' de materiais-medidos.json E a lavoura ao fundo "
                    "do quadro -- foi medida como controle do metodo e nunca tinha "
                    "sido usada. Aqui ela finalmente e o que mediu"},
    50: {"nome": "construido", "medido": None, "cor": [0.190, 0.175, 0.165],
         "por_que": "telhado e asfalto de cidade misturados a 10 m de pixel"},
    60: {"nome": "solo_nu",    "medido": "terra",
         "por_que": "solo exposto: o chao batido medido no recinto"},
    80: {"nome": "agua",       "medido": None, "cor": [0.022, 0.035, 0.048],
         "por_que": "agua doce vista de cima e escura; o brilho vem do reflexo, "
                    "nao do albedo"},
    90: {"nome": "umida",      "medido": "grama",
         "por_que": "vegetacao alagada: sem amostra propria, usa a grama medida"},
    95: {"nome": "mangue",     "medido": "arvore", "por_que": "nao ocorre aqui"},
    100: {"nome": "musgo",     "medido": "grama",  "por_que": "nao ocorre aqui"},
    0:  {"nome": "sem_dado",   "medido": "grama",  "por_que": "buraco no dado"},
}


class ArquivoHTTP:
    """Objeto tipo-arquivo lendo por `Range`. E o que evita baixar 103 MB.

    O `tifffile` so precisa de read/seek/tell. Guarda o que ja leu num dicionario
    de blocos de 512 kB, senao um GeoTIFF em blocos faz centenas de requisicoes
    de poucos bytes cada.
    """

    BLOCO = 512 * 1024

    def __init__(self, url):
        self.url = url
        self.pos = 0
        self.cache = {}
        self.pedidos = 0
        req = urllib.request.Request(url, headers=CABECALHO, method="HEAD")
        with urllib.request.urlopen(req, timeout=60) as r:
            self.tamanho = int(r.headers["Content-Length"])

    def _bloco(self, i):
        if i not in self.cache:
            a = i * self.BLOCO
            b = min(a + self.BLOCO, self.tamanho) - 1
            req = urllib.request.Request(
                self.url, headers={**CABECALHO, "Range": f"bytes={a}-{b}"})
            with urllib.request.urlopen(req, timeout=120) as r:
                self.cache[i] = r.read()
            self.pedidos += 1
        return self.cache[i]

    def read(self, n=-1):
        if n < 0:
            n = self.tamanho - self.pos
        saida = bytearray()
        while n > 0 and self.pos < self.tamanho:
            i, off = divmod(self.pos, self.BLOCO)
            pedaco = self._bloco(i)[off:off + n]
            if not pedaco:
                break
            saida += pedaco
            self.pos += len(pedaco)
            n -= len(pedaco)
        return bytes(saida)

    def seek(self, pos, de=0):
        self.pos = {0: pos, 1: self.pos + pos, 2: self.tamanho + pos}[de]
        return self.pos

    def tell(self):
        return self.pos

    def close(self):
        self.cache.clear()

    seekable = lambda self: True
    readable = lambda self: True
    writable = lambda self: False


def _azulejo(lat, lon):
    """Nome do azulejo de 3 graus que contem o ponto (canto sudoeste)."""
    la = int(math.floor(lat / 3.0) * 3)
    lo = int(math.floor(lon / 3.0) * 3)
    return (f"{'S' if la < 0 else 'N'}{abs(la):02d}"
            f"{'W' if lo < 0 else 'E'}{abs(lo):03d}")


def _srgb(v):
    """linear -> sRGB. O PNG e lido como sRGB pelo Blender; se eu gravasse o
    valor linear cru, a cor medida sairia clara demais no render."""
    return 12.92 * v if v <= 0.0031308 else 1.055 * (v ** (1 / 2.4)) - 0.055


def preparar():
    import numpy as np
    import tifffile
    from PIL import Image

    meta_rel = json.loads((RAIZ / "data" / "relevo-entorno.json").read_text(
        encoding="utf-8"))
    mpp, n = meta_rel["metros_por_pixel"], meta_rel["lado_px"]
    lado_m = meta_rel["lado_m"]

    tile = _azulejo(rel.LAT, rel.LON)
    url = BASE.format(tile=tile)
    print(f"azulejo {tile}")

    arq = ArquivoHTTP(url)
    print(f"  {arq.tamanho/1e6:.0f} MB no S3 -- lendo so a janela por Range")

    with tifffile.TiffFile(arq) as tf:
        pagina = tf.pages[0]
        alt, larg = pagina.imagelength, pagina.imagewidth
        # o azulejo cobre 3 graus a partir do canto NOROESTE
        la0 = math.floor(rel.LAT / 3.0) * 3 + 3      # norte
        lo0 = math.floor(rel.LON / 3.0) * 3          # oeste
        gpp = 3.0 / larg                              # graus por pixel

        # meia-janela em graus: em longitude o grau encolhe com o cosseno
        meio_m = lado_m / 2.0
        dlat = meio_m / 111320.0
        dlon = meio_m / (111320.0 * math.cos(math.radians(rel.LAT)))

        j0 = int((rel.LON - dlon - lo0) / gpp)
        j1 = int((rel.LON + dlon - lo0) / gpp) + 1
        i0 = int((la0 - (rel.LAT + dlat)) / gpp)
        i1 = int((la0 - (rel.LAT - dlat)) / gpp) + 1
        j0, i0 = max(0, j0), max(0, i0)
        j1, i1 = min(larg, j1), min(alt, i1)
        print(f"  janela {i1-i0} x {j1-j0} px de {alt} x {larg}")

        # aszarr() da acesso por BLOCO: so os blocos que a janela toca sao
        # baixados e descomprimidos. Ler a pagina inteira seriam 36000 x 36000
        # = 1,3 GB para uma janela de 2,6 mil pixels de lado.
        import zarr
        with pagina.aszarr() as loja:
            janela = np.asarray(zarr.open(loja, mode="r")[i0:i1, j0:j1])

    print(f"  {arq.pedidos} requisicoes, ~{arq.pedidos*arq.BLOCO/1e6:.1f} MB baixados")

    # reamostra para a MESMA grade do relevo, por vizinho mais proximo:
    # classe nao se interpola (a media de 'agua' com 'mata' nao existe)
    ii = np.clip((np.arange(n) / n * (i1 - i0)).astype(int), 0, i1 - i0 - 1)
    jj = np.clip((np.arange(n) / n * (j1 - j0)).astype(int), 0, j1 - j0 - 1)
    classes = janela[np.ix_(ii, jj)]

    medidos = json.loads((RAIZ / "data" / "materiais-medidos.json").read_text(
        encoding="utf-8"))["itens"]

    rgb = np.zeros((n, n, 3), np.uint8)
    censo = {}
    for cid, info in CLASSES.items():
        masc = classes == cid
        qtd = int(masc.sum())
        if info["medido"]:
            lin = medidos[info["medido"]]["albedo_linear"]
        else:
            lin = info["cor"]
        cor = [int(round(255 * _srgb(min(max(v, 0.0), 1.0)))) for v in lin]
        rgb[masc] = cor
        if qtd:
            censo[info["nome"]] = {
                "classe_worldcover": cid,
                "fracao_pct": round(100.0 * qtd / classes.size, 2),
                "cor_de": (f"MEDIDO: materiais-medidos.json/{info['medido']}"
                           if info["medido"] else "DECLARADO"),
                "albedo_linear": [round(v, 4) for v in lin],
                "por_que": info["por_que"],
            }

    # Amortecimento junto ao recinto, pela mesma razao do DEM: o terreno
    # detalhado vai a ~485 x 273 m e tem a cor MEDIDA da grama. Se o WorldCover
    # puser mata encostada na divisa, aparece uma emenda reta -- e emenda reta e
    # o que se esta consertando. Entao dentro de 600 m e grama medida, e a
    # cobertura real entra inteira so a partir de 1400 m.
    grama = medidos["grama"]["albedo_linear"]
    cor_grama = np.array([255 * _srgb(v) for v in grama])
    meio = (n - 1) / 2.0
    ys, xs = np.mgrid[0:n, 0:n]
    dist = np.hypot(xs - meio, ys - meio) * mpp
    w = np.clip((dist - 600.0) / 800.0, 0.0, 1.0)
    w = (w * w * (3.0 - 2.0 * w))[..., None]
    rgb = (rgb * w + cor_grama * (1.0 - w)).round().astype(np.uint8)

    SAIDA_PNG.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgb).save(SAIDA_PNG)

    meta = {
        "o_que_e": "Cobertura do solo do entorno pintada com as cores MEDIDAS no "
                   "footage. O WorldCover diz o QUE e cada pedaco de chao; o "
                   "materiais-medidos.json diz que COR aquilo tem naquela luz.",
        "fonte_das_classes": "ESA WorldCover 10 m 2021 v200",
        "url": url,
        "licenca": "CC-BY 4.0 — ESA WorldCover project / Contains modified "
                   "Copernicus Sentinel data",
        "fonte_das_cores": "data/materiais-medidos.json (medido no footage do "
                           "recinto) para as classes que tem amostra; declarado "
                           "para as que nao tem, com o motivo escrito",
        "achado": "a amostra 'campo' foi medida em 14/08 como CONTROLE do metodo "
                  "e marcada 'NAO entra em material nenhum'. Ela e a lavoura ao "
                  "fundo do quadro, e e exatamente a classe 40 do WorldCover. "
                  "Deixou de ser so controle.",
        "lado_m": lado_m, "lado_px": n, "metros_por_pixel": mpp,
        "arquivo": str(SAIDA_PNG.relative_to(RAIZ)).replace("\\", "/"),
        "censo": dict(sorted(censo.items(), key=lambda kv: -kv[1]["fracao_pct"])),
    }
    SAIDA_META.write_text(json.dumps(meta, indent=1, ensure_ascii=False),
                          encoding="utf-8")

    print("\ncobertura do entorno:")
    for nome, c in meta["censo"].items():
        print(f"   {nome:12s} {c['fracao_pct']:5.1f}%   {c['cor_de']}")
    print(f"\ngravado: {SAIDA_PNG.relative_to(RAIZ)}")
    print(f"         {SAIDA_META.relative_to(RAIZ)}")
    return meta


def caminho():
    return SAIDA_PNG if (SAIDA_PNG.exists() and SAIDA_META.exists()) else None


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    preparar()
    return 0


if __name__ == "__main__":
    sys.exit(main())
