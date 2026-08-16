#!/usr/bin/env python3
"""
Reconstroi o INDICE.md da pasta de extracao a partir do disco.

    .venv/Scripts/python.exe scripts/refazer_indice_extracao.py \
        --pasta "F:/Extração quadros expo 2025"

POR QUE ISTO EXISTE, e e' um erro meu: o `extrair_quadros.py` REGRAVA o
INDICE.md inteiro a cada execucao, so' com os videos daquela rodada. Em
15/08/2026 extrai um video novo naquela pasta e o indice de 316 KB, com 151
voos, virou um de 1,2 KB com um voo so'.

O conteudo e' inteiramente recuperavel do disco -- o nome de cada quadro
carrega o timecode, e a duracao sai do ffprobe do video original. O que NAO
se recupera e' a ORDEM em que as secoes estavam, que era a ordem em que ele
rodou a extracao. Aqui elas saem ordenadas pela data de modificacao da pasta,
que e a melhor aproximacao possivel dessa ordem.

O formato de saida e' o mesmo, byte a byte, do `escrever_indice()` dele --
inclusive a coluna Bloco vazia e o cabecalho.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
VIDEO_EXT = {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".mts"}
PASTAS_DE_VIDEO = [
    Path(r"E:\Projetos todos\Mapa - agroshow\Brutos Expo"),
    Path(r"E:\Projetos todos\Mapa - agroshow\Brutos Expo\agroshow extrator somente"),
]
RE_Q = re.compile(r"^q(\d+)_(\d{2})-(\d{2})-(\d{2})$")


def nome_limpo(texto):
    return "".join(c if c.isalnum() or c in "-_ " else "_" for c in texto).strip()


def tc_legivel(seg):
    s = int(seg)
    return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}"


def duracao(video):
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", str(video)],
            capture_output=True, text=True, timeout=60)
        return float(r.stdout.strip())
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pasta", required=True, type=Path)
    ap.add_argument("--seco", action="store_true", help="so' mostrar, nao gravar")
    a = ap.parse_args()

    mapa = {}
    for d in PASTAS_DE_VIDEO:
        if d.exists():
            for f in d.rglob("*"):
                if f.is_file() and f.suffix.lower() in VIDEO_EXT:
                    mapa.setdefault(nome_limpo(f.stem), f)

    pastas = [p for p in a.pasta.iterdir() if p.is_dir() and (p / "quadros").is_dir()]
    pastas.sort(key=lambda p: p.stat().st_mtime)

    linhas = [
        "# Quadros extraidos",
        "",
        "Gerado por `scripts/extrair_quadros.py`.",
        "",
        "A coluna **Bloco** esta vazia de proposito: preencha com o numero do",
        "bloco de `docs/prompts-higgsfield.md` que cada quadro serve como",
        "referencia. Quadro real vale mais que geracao — onde houver footage",
        "aproveitavel, ele entra no lugar da imagem de IA.",
        "",
        "> **Reconstruido em 15/08/2026** por `scripts/refazer_indice_extracao.py`,",
        "> a partir do disco. O extrator regrava este arquivo inteiro a cada",
        "> rodada, e uma extracao avulsa apagou as 151 secoes. Conteudo integral;",
        "> a ordem das secoes segue a data da pasta, nao a ordem original.",
        "",
        "> **`docs/prompts-higgsfield.md` NAO EXISTE** em nenhuma das pastas do",
        "> projeto (conferido em 15/08). A coluna Bloco continua sem fonte de",
        "> numeracao. Enquanto isso, a triagem vive em",
        "> `render-expovizinhos/out/acervo/ACERVO.html`, que marca, comenta e",
        "> guarda o caminho em disco de cada quadro.",
        "",
    ]

    n_q = 0
    faltando = []
    for pasta in pastas:
        jpgs = sorted((pasta / "quadros").glob("*.jpg"))
        if not jpgs:
            continue
        quadros = []
        for j in jpgs:
            m = RE_Q.match(j.stem)
            t = (int(m.group(2)) * 3600 + int(m.group(3)) * 60 + int(m.group(4))) if m else 0
            quadros.append((j.name, t))
        n_q += len(quadros)

        vid = mapa.get(nome_limpo(pasta.name))
        dur = duracao(vid) if vid else None
        if dur is None:
            dur = quadros[-1][1]          # ultima marca; o extrator deixa 2% de folga
            faltando.append(pasta.name)
        nome = vid.name if vid else pasta.name

        folhas_dir = pasta / "folhas" if (pasta / "folhas").is_dir() else pasta
        n_folhas = len(list(folhas_dir.glob("contato-*.jpg")))

        linhas += [
            f"## {nome}",
            "",
            f"Duracao {tc_legivel(dur)} · {len(quadros)} quadros · "
            f"{n_folhas} folha(s) de contato",
            "",
            f"Quadros: `{pasta / 'quadros'}`",
            f"Folhas:  `{folhas_dir}`",
            "",
            "| Quadro | Timecode | Bloco |",
            "|---|---|---|",
        ]
        linhas += [f"| `{n}` | {tc_legivel(t)} | |" for n, t in quadros]
        linhas.append("")

    texto = "\n".join(linhas)
    print(f"{len(pastas)} pastas, {n_q} quadros, {len(texto)/1024:.0f} KB")
    if faltando:
        print(f"  ! sem video para medir duracao ({len(faltando)}): "
              f"{', '.join(faltando[:6])}{' ...' if len(faltando) > 6 else ''}")
        print("    nesses a duracao saiu do timecode do ultimo quadro (2% menor)")
    if a.seco:
        return 0
    alvo = a.pasta / "INDICE.md"
    alvo.write_text(texto, encoding="utf-8")
    print(f"Gravado {alvo}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
