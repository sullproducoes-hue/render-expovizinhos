#!/usr/bin/env python3
"""
Le a selecao que ele exportou da pagina e transforma em coisa acionavel.

    .venv/Scripts/python.exe scripts/colher_selecao.py
    .venv/Scripts/python.exe scripts/colher_selecao.py --copiar

Sem argumento, procura o `selecao-acervo-agroshow.json` mais recente na pasta
de Downloads e no proprio `out/acervo/`.

O que sai:

    data/selecao-acervo.json          a selecao, versionada (o anterior vira
                                      selecao-acervo-<data>.json -- nada se apaga)
    out/acervo/SELECAO.md             o relatorio por plano, com CAMINHO ABSOLUTO,
                                      video de origem e timecode de cada quadro
    out/acervo/selecionados/<plano>/  com --copiar, o JPG original, resolucao
                                      nativa, renomeado com plano e timecode

E ele confere aqui se o arquivo ainda esta la: caminho que sumiu sai listado.
"""

import argparse
import json
import os
import shutil
import sys
import unicodedata
import re
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
NOME = "selecao-acervo-agroshow.json"


def slug(t):
    t = unicodedata.normalize("NFKD", str(t)).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]+", "-", t).strip("-").lower() or "sem-nome"


def achar():
    alvos = []
    for d in (Path.home() / "Downloads", RAIZ / "out" / "acervo", RAIZ,
              Path.home() / "Desktop"):
        if d.exists():
            alvos += list(d.glob("selecao-acervo-agroshow*.json"))
    if not alvos:
        return None
    return max(alvos, key=lambda p: p.stat().st_mtime)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arquivo", type=Path)
    ap.add_argument("--copiar", action="store_true",
                    help="copiar os JPG marcados SIM para out/acervo/selecionados/")
    ap.add_argument("--tambem-talvez", action="store_true",
                    help="copiar tambem os TALVEZ")
    a = ap.parse_args()

    arq = a.arquivo or achar()
    if not arq or not arq.exists():
        print("Nao achei a selecao exportada.")
        print("Abra out/acervo/ACERVO.html, marque, clique em 'Exportar selecao'")
        print(f"e rode de novo -- ou passe --arquivo caminho/para/{NOME}")
        return 1
    print(f"Lendo {arq}  ({datetime.fromtimestamp(arq.stat().st_mtime):%d/%m/%Y %H:%M})")
    sel = json.loads(arq.read_text(encoding="utf-8-sig"))
    itens = sel.get("itens", [])
    if not itens:
        print("A selecao esta vazia.")
        return 1

    sim = [i for i in itens if i["marca"] == "SIM"]
    talvez = [i for i in itens if i["marca"] == "TALVEZ"]
    nao = [i for i in itens if i["marca"] == "NAO"]
    coment = [i for i in itens if i.get("comentario")]
    print(f"  {len(sim)} SIM · {len(talvez)} TALVEZ · {len(nao)} NAO · "
          f"{len(coment)} com comentario")

    sumidos = [i for i in itens if not Path(i["arquivo"]).exists()]
    if sumidos:
        print(f"  ! {len(sumidos)} caminhos nao existem mais em disco "
              f"(o HD esta conectado?)")
        for i in sumidos[:5]:
            print(f"      {i['arquivo']}")

    # ------------------------------------------------------------- versionar
    destino = RAIZ / "data" / "selecao-acervo.json"
    if destino.exists():
        velho = json.loads(destino.read_text(encoding="utf-8"))
        carimbo = (velho.get("_gerado") or "anterior")[:19].replace(":", "-")
        guardado = destino.with_name(f"selecao-acervo-{carimbo}.json")
        if not guardado.exists():
            shutil.copy2(destino, guardado)
            print(f"  a selecao anterior virou {guardado.name}")
    sel["_colhido_em"] = datetime.now().isoformat(timespec="seconds")
    sel["_arquivo_de_origem"] = str(arq)
    sel["_caminhos_ausentes"] = [i["arquivo"] for i in sumidos]
    destino.write_text(json.dumps(sel, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Gravado {destino}")

    # ------------------------------------------------------------- relatorio
    por_plano = {}
    for i in itens:
        por_plano.setdefault(i.get("plano") or "(sem local)", []).append(i)

    L = [
        "# Selecao do acervo — AGROSHOW 2026",
        "",
        f"Exportada da pagina em {sel.get('_gerado','?')[:19].replace('T',' ')}, "
        f"colhida em {sel['_colhido_em'][:19].replace('T',' ')}.",
        "",
        f"**{len(sim)} SIM · {len(talvez)} TALVEZ · {len(nao)} NAO · "
        f"{len(coment)} com comentario.**",
        "",
        "Cada linha traz o caminho absoluto do JPG, o video de origem e o timecode —",
        "e o que responde *onde esta o que eu selecionei*. Para voltar ao video na",
        "edicao, o timecode e o mesmo do nome do arquivo.",
        "",
    ]
    if sumidos:
        L += [f"> **{len(sumidos)} caminhos nao existem mais em disco.** "
              f"Conferir se o HD esta conectado antes de concluir que sumiram.", ""]

    for plano in sorted(por_plano, key=lambda k: (k == "(sem local)", k)):
        grupo = sorted(por_plano[plano],
                       key=lambda i: ({"SIM": 0, "TALVEZ": 1, "NAO": 2}.get(i["marca"], 3),
                                      -float(i.get("nota") or 0)))
        L += [f"## {plano}   ({len(grupo)})", ""]
        for i in grupo:
            falta = "" if Path(i["arquivo"]).exists() else "  **[ARQUIVO AUSENTE]**"
            L.append(f"### {i['marca']} · {i['pasta']} · {i['timecode']}{falta}")
            if i.get("comentario"):
                L.append(f"> {i['comentario']}")
            L += [
                "",
                f"- quadro: `{i['arquivo']}`",
                f"- video: `{i.get('video') or '(nao localizado)'}`",
                f"- timecode {i['timecode']} ({i['segundos']} s) · "
                f"{i.get('largura')}x{i.get('altura')} · {i.get('periodo')}"
                + (f" · voo de {i['hora_do_voo']}" if i.get("hora_do_voo") else ""),
                f"- medida: nota {i.get('nota')} · etiqueta {i.get('etiqueta')} · "
                f"nitidez {i.get('nitidez')} · luma {i.get('luma')} · estouro {i.get('estouro')}%",
                f"- local: {i.get('classificacao')}"
                + (f" · sugestao {i['sugestao']}" if i.get("sugestao") else ""),
                "",
            ]

    rel = RAIZ / "out" / "acervo" / "SELECAO.md"
    rel.parent.mkdir(parents=True, exist_ok=True)
    rel.write_text("\n".join(L), encoding="utf-8")
    print(f"Gravado {rel}")

    # ---------------------------------------------------------------- copiar
    if a.copiar:
        alvo = RAIZ / "out" / "acervo" / "selecionados"
        quais = sim + (talvez if a.tambem_talvez else [])
        n = 0
        for i in quais:
            o = Path(i["arquivo"])
            if not o.exists():
                continue
            d = alvo / slug(i.get("plano") or "sem-local")
            d.mkdir(parents=True, exist_ok=True)
            nome = f"{i['marca']}_{slug(i['pasta'])}_{i['timecode'].replace(':','-')}{o.suffix}"
            shutil.copy2(o, d / nome)
            n += 1
        print(f"Copiados {n} quadros em resolucao nativa para {alvo}")
    else:
        print("(use --copiar para trazer os JPG marcados para out/acervo/selecionados/)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
