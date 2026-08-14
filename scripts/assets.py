#!/usr/bin/env python3
"""Baixa asset CC0 (Poly Haven, ambientCG) e escreve o manifesto de procedencia.

Verba zero: so entra o que e CC0 ou equivalente. Cada arquivo baixado grava
nome, autor, licenca, URL e md5 em assets/_procedencia.json, e o MANIFESTO.md
e reescrito desse JSON -- nunca a mao.

So stdlib: roda no venv e dentro do Python do Blender, igual terreno.py.

Uso:
    python scripts/assets.py --listar-hdri
    python scripts/assets.py --hdri belfast_sunset_puresky kloppenheim_06_puresky
    python scripts/assets.py --manifesto
"""

import argparse
import hashlib
import json
import shutil
import sys
import urllib.error
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ASSETS = RAIZ / "assets"
PROCEDENCIA = ASSETS / "_procedencia.json"

API_PH = "https://api.polyhaven.com"

# Sem User-Agent os dois hosts devolvem 403 para urllib. E o erro mais bobo daqui.
CABECALHO = {"User-Agent": "render-expovizinhos/1.0 (contato via github)"}

# 4K e nao 8K: 17 MB contra 67 MB em disco, 67 MB contra 268 MB de VRAM. O ceu
# ocupa ~30% de um quadro de 2760 px, servido por ~340 px de fonte equirretangular
# em 4K. 8K nao aparece no painel P2,9 e custa 4x a memoria.
RES_HDRI = "4k"

# 2k e nao 4k, e o motivo esta em data/texturas.json ("por_que_2k"): 8 GB de
# VRAM na 4060, e o painel P2,9 entrega 1379 x 690 nativos.
RES_TEXTURA = "2k"


def _abrir(url, timeout=60):
    return urllib.request.urlopen(
        urllib.request.Request(url, headers=CABECALHO), timeout=timeout)


def _json(url):
    with _abrir(url, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def _md5(caminho):
    h = hashlib.md5()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def _baixar(url, destino, md5_esperado=None):
    """Baixa para .parcial e so renomeia no fim: interrupcao nao deixa
    arquivo truncado passando por bom."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    parcial = destino.with_suffix(destino.suffix + ".parcial")
    with _abrir(url) as r, open(parcial, "wb") as f:
        shutil.copyfileobj(r, f)

    if md5_esperado:
        obtido = _md5(parcial)
        if obtido != md5_esperado:
            parcial.unlink()
            raise SystemExit(
                f"md5 nao confere para {destino.name}: "
                f"esperado {md5_esperado}, obtido {obtido}")

    parcial.replace(destino)
    return destino


# --------------------------------------------------------------------------
# Poly Haven

def listar_hdri_golden_hour():
    """Os candidatos de campo aberto em sunrise-sunset, com a latitude.

    A latitude importa: um HDRI capturado perto de -25,7 tem o mesmo arco solar
    de Dois Vizinhos. Hemisferio norte tem o arco espelhado e denuncia.
    """
    bruto = _json(f"{API_PH}/assets?t=hdris&c=sunrise-sunset")
    linhas = []
    for slug, v in bruto.items():
        cats = set(v.get("categories", []))
        if "urban" in cats or "indoor" in cats:
            continue
        info = None
        try:
            info = _json(f"{API_PH}/info/{slug}")
        except urllib.error.URLError:
            pass
        coords = (info or {}).get("coords") or [None, None]
        linhas.append({
            "slug": slug,
            "lat": coords[0],
            "evs_cap": (info or {}).get("evs_cap"),
            "downloads": v.get("download_count", 0),
            "pure_sky": "pure skies" in cats,
        })
    linhas.sort(key=lambda d: abs((d["lat"] or 999) + 25.73))
    return linhas


def baixar_hdri(slug, res=RES_HDRI):
    arquivos = _json(f"{API_PH}/files/{slug}")
    info = _json(f"{API_PH}/info/{slug}")

    entrada = arquivos.get("hdri", {}).get(res, {}).get("hdr")
    if not entrada:
        raise SystemExit(f"{slug}: nao existe hdri/{res}/hdr na API")

    destino = ASSETS / "hdri" / f"{slug}_{res}.hdr"
    if destino.exists() and _md5(destino) == entrada.get("md5"):
        print(f"  {slug}: ja esta em disco e o md5 confere")
    else:
        print(f"  {slug}: baixando {entrada['size'] / 1e6:.1f} MB...")
        _baixar(entrada["url"], destino, entrada.get("md5"))

    return {
        "arquivo": str(destino.relative_to(RAIZ)).replace("\\", "/"),
        "tipo": "hdri",
        "nome": info.get("name", slug),
        "fonte": "Poly Haven",
        "licenca": "CC0",
        "autores": sorted(info.get("authors", {}).keys()),
        "url": f"https://polyhaven.com/a/{slug}",
        "md5": entrada.get("md5"),
        "bytes": entrada.get("size"),
        "resolucao": res,
        # coords e evs_cap decidem a escolha; ficam gravados para a proxima sessao
        # nao ter que ir na API de novo perguntar por que este e nao outro.
        "coords": info.get("coords"),
        "evs_cap": info.get("evs_cap"),
    }


def baixar_textura(slug, mapas, res=RES_TEXTURA):
    """Baixa SO os mapas pedidos de uma textura do Poly Haven.

    Baixar o pacote inteiro seria 8 mapas por classe, e metade nunca e ligada:
    AO nao entra em cena de sol aberto (o Cycles calcula oclusao de verdade),
    Displacement pediria subdivisao real num terreno que ja tem 800 m, e o
    `arm` empacota tres canais que este contrato usa separados.

    Cada mapa vira uma entrada propria na procedencia, com md5 proprio: o que
    se confere e o arquivo, nao o pacote.
    """
    arquivos = _json(f"{API_PH}/files/{slug}")
    info = _json(f"{API_PH}/info/{slug}")
    entradas = []

    for mapa in mapas:
        por_res = arquivos.get(mapa, {}).get(res, {})
        entrada = por_res.get("jpg") or por_res.get("png")
        if not entrada:
            raise SystemExit(
                f"{slug}: nao existe {mapa}/{res} em jpg nem png "
                f"(mapas disponiveis: {sorted(arquivos)})")

        sufixo = Path(entrada["url"]).suffix or ".jpg"
        destino = ASSETS / "textura" / f"{slug}_{mapa}_{res}{sufixo}"
        if destino.exists() and _md5(destino) == entrada.get("md5"):
            print(f"  {slug}/{mapa}: ja esta em disco e o md5 confere")
        else:
            print(f"  {slug}/{mapa}: baixando {entrada['size'] / 1e6:.1f} MB...")
            _baixar(entrada["url"], destino, entrada.get("md5"))

        entradas.append({
            "arquivo": str(destino.relative_to(RAIZ)).replace("\\", "/"),
            "tipo": "textura",
            "nome": f"{info.get('name', slug)} — {mapa}",
            "fonte": "Poly Haven",
            "licenca": "CC0",
            "autores": sorted(info.get("authors", {}).keys()),
            "url": f"https://polyhaven.com/a/{slug}",
            "md5": entrada.get("md5"),
            "bytes": entrada.get("size"),
            "resolucao": res,
            "mapa": mapa,
            # o lado real e o numero que decide se a textura serve: ver
            # data/texturas.json, "por_que_aerial".
            "lado_mm": info.get("dimensions"),
        })

    return entradas


def baixar_do_contrato():
    """Le data/texturas.json e baixa exatamente o que ele declara.

    O contrato manda; o script nao escolhe asset. Assim `--texturas` e
    reprodutivel: quem clonar o repositorio roda isto e tem os mesmos
    arquivos, conferidos por md5.
    """
    contrato = json.loads((RAIZ / "data" / "texturas.json").read_text(
        encoding="utf-8"))
    res = contrato.get("resolucao", RES_TEXTURA)
    entradas = []
    for material, item in contrato["itens"].items():
        print(f"{material}: {item['slug']}  ({item['lado_m']} m de lado)")
        entradas += baixar_textura(item["slug"], item["mapas"], res)
    return entradas


# --------------------------------------------------------------------------
# Procedencia e manifesto

def _carregar_procedencia():
    if PROCEDENCIA.exists():
        return json.loads(PROCEDENCIA.read_text(encoding="utf-8"))
    return {"itens": []}


def registrar(entradas):
    pacote = _carregar_procedencia()
    por_arquivo = {i["arquivo"]: i for i in pacote["itens"]}
    for e in entradas:
        por_arquivo[e["arquivo"]] = e
    pacote["itens"] = sorted(por_arquivo.values(), key=lambda i: i["arquivo"])
    PROCEDENCIA.parent.mkdir(parents=True, exist_ok=True)
    PROCEDENCIA.write_text(json.dumps(pacote, indent=1, ensure_ascii=False),
                           encoding="utf-8")
    return pacote


def escrever_manifesto():
    pacote = _carregar_procedencia()
    itens = pacote["itens"]

    linhas = [
        "# assets/ — o que entrou, de onde, e sob que licença",
        "",
        "Verba zero: só entra CC0 ou equivalente.",
        "",
        "Gerado por `python scripts/assets.py --manifesto` a partir de",
        "`assets/_procedencia.json`. **Não edite à mão.**",
        "",
        "Os binários não são versionados (ver `assets/.gitignore`) — este",
        "manifesto é que vai para o git, e `scripts/assets.py` rebaixa tudo",
        "a partir dele. Quem clonar o repositório roda o script e tem os",
        "mesmos arquivos, conferidos por md5.",
        "",
    ]

    for tipo, titulo in (("hdri", "Céu"), ("textura", "Texturas"),
                         ("vegetacao", "Vegetação")):
        do_tipo = [i for i in itens if i.get("tipo") == tipo]
        if not do_tipo:
            continue
        linhas += [f"## {titulo}", "",
                   "| arquivo | asset | fonte | licença | autores | URL | md5 |",
                   "|---|---|---|---|---|---|---|"]
        for i in do_tipo:
            autores = ", ".join(i.get("autores") or []) or "—"
            md5 = (i.get("md5") or "")[:12]
            linhas.append(
                f"| `{i['arquivo']}` | {i['nome']} | {i['fonte']} | "
                f"{i['licenca']} | {autores} | {i['url']} | `{md5}` |")
        linhas.append("")

    hdris = [i for i in itens if i.get("tipo") == "hdri" and i.get("coords")]
    if hdris:
        linhas += ["## Por que estes HDRIs", "",
                   "A latitude do céu decide: um HDRI capturado perto de −25,7°",
                   "tem o mesmo arco solar de Dois Vizinhos (−25,73144).",
                   "Hemisfério norte tem o arco espelhado e denuncia.",
                   "",
                   "| asset | latitude | longitude | `evs_cap` |",
                   "|---|---|---|---|"]
        for i in hdris:
            lat, lon = i["coords"][0], i["coords"][1]
            linhas.append(f"| {i['nome']} | {lat:.3f} | {lon:.3f} | "
                          f"{i.get('evs_cap', '—')} |")
        linhas += ["",
                   "`evs_cap` baixo (10–12) quer dizer disco solar estourado e",
                   "macio: o HDRI entrega céu, ambiente e reflexo, e a luz SUN",
                   "entrega a chave. Um HDRI de sol íntegro somado a uma SUN",
                   "produz **duas sombras**.",
                   ""]

    alvo = ASSETS / "MANIFESTO.md"
    alvo.parent.mkdir(parents=True, exist_ok=True)
    alvo.write_text("\n".join(linhas), encoding="utf-8")
    print(f"manifesto escrito: {alvo}  ({len(itens)} itens)")


def _gitignore():
    """Binario nao versiona; o manifesto e a procedencia sim."""
    alvo = ASSETS / ".gitignore"
    if alvo.exists():
        return
    alvo.parent.mkdir(parents=True, exist_ok=True)
    alvo.write_text(
        "# Binario de asset CC0 nao versiona: o MANIFESTO.md e o\n"
        "# _procedencia.json bastam para rebaixar tudo com md5 conferido.\n"
        "*\n"
        "!.gitignore\n"
        "!MANIFESTO.md\n"
        "!_procedencia.json\n",
        encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--listar-hdri", action="store_true",
                    help="candidatos golden hour ordenados por proximidade da latitude")
    ap.add_argument("--hdri", nargs="+", metavar="SLUG",
                    help="baixa estes HDRIs em 4k .hdr")
    ap.add_argument("--texturas", action="store_true",
                    help="baixa os mapas que data/texturas.json declara")
    ap.add_argument("--manifesto", action="store_true",
                    help="reescreve assets/MANIFESTO.md a partir da procedencia")
    args = ap.parse_args()

    if args.listar_hdri:
        for d in listar_hdri_golden_hour()[:25]:
            lat = f"{d['lat']:+.3f}" if d["lat"] is not None else "   ?  "
            print(f"  {d['slug']:34s} lat={lat}  evs={str(d['evs_cap']):>4}  "
                  f"{'pure-sky' if d['pure_sky'] else '        '}  "
                  f"dl={d['downloads']}")
        return

    if args.hdri:
        _gitignore()
        entradas = [baixar_hdri(s) for s in args.hdri]
        registrar(entradas)
        escrever_manifesto()
        return

    if args.texturas:
        _gitignore()
        entradas = baixar_do_contrato()
        registrar(entradas)
        escrever_manifesto()
        return

    if args.manifesto:
        escrever_manifesto()
        return

    ap.print_help()


if __name__ == "__main__":
    sys.exit(main())
