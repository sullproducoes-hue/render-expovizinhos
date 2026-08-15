#!/usr/bin/env python3
"""
Monta a pagina de aprovacao das placas de IA: out/quadros-ia/INDICE.html

Uma secao por local do percurso, o quadro 3d ao lado dos quadros reais, o
motivo de cada escolha e o bloqueio escrito quando existe. E o arquivo que
ele abre para dizer sim ou nao ANTES de qualquer geracao.

    .venv/Scripts/python.exe scripts/pagina_quadros.py

A pagina le a QA de pixel de cada quadro 3d na hora (media e desvio) e marca
em vermelho o que nao serve -- quadro preto, chapado ou dentro de geometria.
Isso nao e enfeite: de 22 planos, 6 sairam assim na primeira rodada.
"""

import argparse
import base64
import html
import json
import re
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def slug(texto):
    if not texto:
        return "sem-titulo"
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    t = re.sub(r"[^A-Za-z0-9]+", "-", t).strip("-").lower()
    return t[:44] or "sem-titulo"


def miniatura(arq, largura=760):
    import cv2
    img = cv2.imread(str(arq))
    if img is None:
        return None, None
    h, w = img.shape[:2]
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    qa = (float(g.mean()), float(g.std()))
    if w > largura:
        img = cv2.resize(img, (largura, int(h * largura / w)), interpolation=cv2.INTER_AREA)
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 82])
    if not ok:
        return None, qa
    return base64.b64encode(buf.tobytes()).decode(), qa


def veredito(qa):
    """A regra veio da medicao de 15/08, nao de gosto."""
    if qa is None:
        return "", ""
    media, desvio = qa
    if media < 8:
        return "ruim", "QUADRO PRETO -- camera dentro de geometria"
    if desvio < 18:
        return "ruim", "CHAPADO -- camera colada numa superficie"
    if desvio < 25:
        return "duvida", "pouca variacao -- conferir se a camera nao esta na copa"
    return "ok", ""


CSS = """
:root{color-scheme:dark}
body{background:#141414;color:#e8e8e8;font:15px/1.55 -apple-system,Segoe UI,Roboto,sans-serif;
     margin:0;padding:28px 34px 90px}
h1{font-size:26px;margin:0 0 4px}
h2{font-size:20px;margin:38px 0 2px;padding-top:20px;border-top:1px solid #2e2e2e}
.sub{color:#9a9a9a;font-size:13px;margin:0 0 14px}
.cab{background:#1c1c1c;border:1px solid #2e2e2e;border-radius:10px;padding:16px 20px;margin-bottom:8px}
.cab p{margin:6px 0}
.dif{display:inline-block;background:#4a3a10;color:#ffcf5c;border-radius:4px;
     padding:1px 8px;font-size:12px;font-weight:700;margin-left:8px;vertical-align:2px}
.grade{display:grid;grid-template-columns:repeat(auto-fill,minmax(390px,1fr));gap:16px;margin-top:12px}
.cel{background:#1c1c1c;border:1px solid #2e2e2e;border-radius:9px;overflow:hidden}
.cel img{width:100%;display:block;background:#000}
.tag{font-size:11px;font-weight:700;letter-spacing:.7px;padding:6px 10px 0;color:#7fc3ff}
.tag.real{color:#8fe0a0}
.leg{padding:4px 10px 10px;font-size:12.5px;color:#c2c2c2}
.leg b{color:#e8e8e8}
.ruim{border-color:#8a2b2b}
.ruim .aviso{background:#8a2b2b;color:#fff;font-size:12px;font-weight:700;padding:5px 10px}
.duvida{border-color:#8a6a2b}
.duvida .aviso{background:#8a6a2b;color:#fff;font-size:12px;font-weight:700;padding:5px 10px}
.bloq{background:#3a2020;border-left:4px solid #b04545;padding:10px 14px;margin:10px 0;
      font-size:13.5px;border-radius:0 6px 6px 0}
.conf{font-size:11px;border-radius:3px;padding:1px 6px;margin-left:6px}
.c-confirmado{background:#1e4d2b;color:#a9e8b8}
.c-provavel{background:#4d431e;color:#e8dca9}
.c-nao_confirmado{background:#4d1e1e;color:#e8a9a9}
.nada{color:#c98a8a;font-style:italic;padding:10px 0}
ul.ped{background:#1c1c1c;border:1px solid #2e2e2e;border-radius:10px;padding:14px 20px 14px 38px}
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--catalogo", default=str(RAIZ / "data" / "quadros-ia.json"))
    ap.add_argument("--saida", default=None)
    args = ap.parse_args()

    cat = json.loads(Path(args.catalogo).read_text(encoding="utf-8"))
    base = RAIZ / cat["raizes"]["saida"]
    reprovados = {k: v for k, v in cat.get("_quadros_3d_reprovados", {}).items()
                  if not k.startswith("_")}
    destino = Path(args.saida) if args.saida else base / "INDICE.html"

    p = [f"<!doctype html><html lang=pt-BR><meta charset=utf-8>",
         "<title>AGROSHOW 2026 · placas para IA</title>",
         f"<style>{CSS}</style>",
         "<h1>AGROSHOW 2026 — as placas que entram na IA</h1>",
         "<p class=sub>Um bloco por local do percurso. <b>3D</b> = quadro da cena, diz o "
         "enquadramento. <b>REAL</b> = quadro do footage do proprio recinto, diz como o "
         "lugar e. Nada aqui foi gerado por IA.</p>",
         "<div class=cab>"]
    for linha in cat["_o_que_isto_e"]:
        p.append(f"<p>{html.escape(linha)}</p>")
    p.append("</div><div class=cab>")
    for linha in cat["_criterio"]:
        p.append(f"<p>{html.escape(linha)}</p>")
    p.append("</div>")

    for local in cat["locais"]:
        pasta = base / f"{local['plano']}_{slug(local['local'])}"
        dif = "<span class=dif>DIFERENCIAL</span>" if local["diferencial"] else ""
        p.append(f"<h2>{html.escape(local['plano'])} · {html.escape(local['local'])}{dif}</h2>")
        p.append(f"<p class=sub>na cena 3D hoje: {html.escape(local['cena_3d'])}</p>")
        if local.get("bloqueio"):
            p.append(f"<div class=bloq><b>BLOQUEIO —</b> {html.escape(local['bloqueio'])}</div>")

        p.append("<div class=grade>")
        for arq in sorted((pasta / "3d").glob("*.png")) if (pasta / "3d").is_dir() else []:
            b64, qa = miniatura(arq)
            if b64 is None:
                continue
            classe, aviso = veredito(qa)
            # O olho vence a medicao quando ela nao alcanca: predio ocupando a
            # tela inteira tem duas cores fortes e passa no desvio.
            manual = reprovados.get(f"{local['plano']} {arq.stem}")
            if manual:
                classe, aviso = "ruim", manual
            cls = f"cel {classe}" if classe in ("ruim", "duvida") else "cel"
            p.append(f"<div class='{cls}'>")
            if aviso:
                p.append(f"<div class=aviso>{html.escape(aviso)}</div>")
            p.append(f"<div class=tag>3D · {html.escape(arq.stem)}</div>")
            p.append(f"<img src='data:image/jpeg;base64,{b64}'>")
            p.append(f"<div class=leg>quadro da cena, moldura exata do plano · "
                     f"media {qa[0]:.0f} desvio {qa[1]:.0f}</div></div>")

        arquivos_reais = sorted((pasta / "real").iterdir()) if (pasta / "real").is_dir() else []
        for i, item in enumerate(local["reais"], 1):
            achado = next((a for a in arquivos_reais if a.name.startswith(f"{i}_")), None)
            if achado is None:
                continue
            b64, _ = miniatura(achado)
            if b64 is None:
                continue
            conf = item["confianca"]
            p.append("<div class=cel>")
            p.append(f"<div class='tag real'>REAL · {html.escape(item['papel'])}"
                     f"<span class='conf c-{conf}'>{conf.replace('_',' ')}</span></div>")
            p.append(f"<img src='data:image/jpeg;base64,{b64}'>")
            tc = f" @{item['tc']}s" if item["tc"] is not None else ""
            p.append(f"<div class=leg><b>{html.escape(item['video'])}</b>{tc}<br>"
                     f"{html.escape(item['porque'])}</div></div>")
        p.append("</div>")
        if not local["reais"]:
            p.append("<p class=nada>Nenhum quadro real: o acervo nao tem este local "
                     "identificado.</p>")

    p.append("<h2>O que isto pede a ele</h2><ul class=ped>")
    for ped in cat["_pedidos_que_isto_gera"]:
        p.append(f"<li>{html.escape(ped)}</li>")
    p.append("</ul></html>")

    destino.write_text("\n".join(p), encoding="utf-8")
    mb = destino.stat().st_size / 1e6
    print(f"pagina -> {destino}  ({mb:.1f} MB)")


if __name__ == "__main__":
    main()
