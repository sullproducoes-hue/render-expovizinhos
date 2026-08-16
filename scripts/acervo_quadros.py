#!/usr/bin/env python3
"""
Varre o acervo INTEIRO de quadros extraidos, mede cada um e monta o catalogo.

    .venv/Scripts/python.exe scripts/acervo_quadros.py --varrer

Duas raizes, as duas indicadas por ele:

    F:\\Extracao quadros expo 2025                                  (151 pastas)
    E:\\...\\Brutos Expo\\agroshow extrator somente\\extracao        (17 pastas)

O que sai:

    data/acervo-quadros.json     o catalogo versionado, um registro por quadro
    out/acervo/thumbs/...        miniatura de cada quadro (a pagina usa)

O QUE ESTE ARQUIVO NAO FAZ: nao apaga nada, nao move nada e nao escolhe por
ele. A pre-triagem ORDENA e ETIQUETA -- todo quadro continua no catalogo, e o
motivo da etiqueta fica escrito no proprio registro.

Medidas, todas por pixel (nenhuma e opiniao):

    nitidez   variancia do laplaciano, sobre a imagem normalizada a 960 px de
              largura -- sem normalizar, video 4K e video 1080p nao comparam
    luma      media do canal de luminancia (0-255)
    std       desvio do canal de luminancia -- quadro chapado tem std baixo
    estouro   % de pixel acima de 250 (branco estourado)
    escuro    % de pixel abaixo de 10
    dhash     assinatura de 64 bits para achar quadro vizinho quase igual

A NOTA nao e medida, e receita -- esta escrita em `_criterio` no JSON de saida
e pode ser discutida. As medidas acima nao.
"""

import argparse
import json
import os
import re
import sys
import unicodedata
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# --------------------------------------------------------------- as raizes
RAIZES = {
    "expo2025": {
        "quadros": Path(r"F:\Extração quadros expo 2025"),
        "videos": [Path(r"E:\Projetos todos\Mapa - agroshow\Brutos Expo")],
        "rotulo": "Extracao expo 2025 (F:)",
    },
    "quinta": {
        "quadros": Path(r"E:\Projetos todos\Mapa - agroshow\Brutos Expo\agroshow extrator somente\extracao"),
        "videos": [Path(r"E:\Projetos todos\Mapa - agroshow\Brutos Expo\agroshow extrator somente")],
        "rotulo": "Footage de quinta (E:)",
    },
}

VIDEO_EXT = {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".mts"}

# Distancia de Hamming no dhash de 64 bits abaixo da qual dois quadros do MESMO
# video sao tratados como o mesmo enquadramento. Medido em 15/08 sobre 9.824
# quadros: ver `--histograma`.
LIMIAR_PARECIDO = 6

# Faixa de luma esperada por periodo. O periodo e do VIDEO, nao do quadro --
# penalizar quadro escuro num voo noturno enterraria justamente o material que
# ele pediu ("anoitecendo depois entra a logo animada").
FAIXA_LUMA = {
    "noite": (12, 90),
    "fim de tarde": (35, 150),
    "dia": (55, 200),
}
PERIODOS = ("dia", "fim de tarde", "noite")


def nome_limpo(texto):
    """A MESMA funcao do extrair_quadros.py dele -- e assim que a pasta nasceu."""
    return "".join(c if c.isalnum() or c in "-_ " else "_" for c in texto).strip()


def slug(texto):
    t = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    t = re.sub(r"[^A-Za-z0-9]+", "-", t).strip("-").lower()
    return t or "sem-nome"


def mapa_de_slugs(nomes):
    """nome da pasta -> slug UNICO. E preciso ser unico, e quase nao foi.

    `DJI_0953_stabilized_1` e `DJI_0953_stabilized_1_` -- a segunda nasceu de
    `DJI_0953_stabilized_1(1).mp4` -- caem no MESMO slug. Isso fazia 4 quadros
    dividirem `id` e miniatura: marcar um marcava o outro, e a carta mostrava a
    imagem do voo errado. Quatro em 9.980, e silencioso.

    Onde o slug basico se repete, todos os que o dividem ganham 4 hex do md5 do
    nome original. Deterministico e estavel: nao depende de ordem de leitura.
    """
    import hashlib
    from collections import Counter
    base = {n: slug(n) for n in nomes}
    repetidos = {s for s, c in Counter(base.values()).items() if c > 1}
    saida = {}
    for n, s in base.items():
        if s in repetidos:
            s += "-" + hashlib.md5(n.encode("utf-8")).hexdigest()[:4]
        saida[n] = s
    return saida


def hhmmss(seg):
    seg = int(seg)
    return f"{seg // 3600:02d}:{(seg % 3600) // 60:02d}:{seg % 60:02d}"


# ------------------------------------------------------- hora no nome do voo
RE_DJI_TS = re.compile(r"DJI_(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})_")
RE_FLY_TS = re.compile(r"dji_fly_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})_")


def hora_do_nome(pasta):
    """A camera carimba data e hora no nome do arquivo. Isso e medida, nao chute.

    Devolve (iso, hora_decimal) ou (None, None) -- os DJI_09xx nao tem carimbo.
    """
    for rx in (RE_DJI_TS, RE_FLY_TS):
        m = rx.search(pasta + "_")
        if m:
            a, me, d, h, mi, s = (int(x) for x in m.groups())
            return f"{a:04d}-{me:02d}-{d:02d} {h:02d}:{mi:02d}:{s:02d}", h + mi / 60
    return None, None


# ----------------------------------------------------------------- a medida
def medir(tarefa):
    """Roda em processo separado. Devolve o registro cru de UM quadro."""
    import cv2
    import numpy as np

    caminho, destino_thumb, larg_thumb = tarefa
    try:
        bruto = np.frombuffer(Path(caminho).read_bytes(), np.uint8)
    except OSError as e:
        return {"arquivo": caminho, "erro": f"nao pude ler: {e}"}

    # imdecode e nao imread: caminho com acento ("Extracao") faz o imread do
    # OpenCV devolver None no Windows sem levantar erro. Armadilha nova.
    img = cv2.imdecode(bruto, cv2.IMREAD_REDUCED_COLOR_2)
    if img is None:
        img = cv2.imdecode(bruto, cv2.IMREAD_COLOR)
    if img is None:
        return {"arquivo": caminho, "erro": "JPEG ilegivel"}

    h, w = img.shape[:2]
    # o REDUCED_COLOR_2 ja dividiu por 2; o tamanho real e o dobro
    reg = {"arquivo": caminho, "w": w * 2, "h": h * 2}

    if w != 960:
        img_n = cv2.resize(img, (960, max(1, round(h * 960 / w))),
                           interpolation=cv2.INTER_AREA)
    else:
        img_n = img
    g = cv2.cvtColor(img_n, cv2.COLOR_BGR2GRAY)

    reg["nitidez"] = round(float(cv2.Laplacian(g, cv2.CV_64F).var()), 2)
    reg["luma"] = round(float(g.mean()), 2)
    reg["std"] = round(float(g.std()), 2)
    total = g.size
    reg["estouro"] = round(float((g > 250).sum()) * 100 / total, 2)
    reg["escuro"] = round(float((g < 10).sum()) * 100 / total, 2)
    hsv = cv2.cvtColor(img_n, cv2.COLOR_BGR2HSV)
    reg["sat"] = round(float(hsv[:, :, 1].mean()), 1)
    b, gr, r = (float(x) for x in cv2.mean(img_n)[:3])
    reg["rgb"] = [round(r, 1), round(gr, 1), round(b, 1)]

    # dhash 8x8: compara cada pixel com o vizinho da direita
    pq = cv2.resize(g, (9, 8), interpolation=cv2.INTER_AREA)
    bits = (pq[:, 1:] > pq[:, :-1]).flatten()
    reg["dhash"] = "".join("1" if x else "0" for x in bits)

    # fracao de ceu: linha do horizonte nao medida, mas o terco de cima de um
    # quadro aereo baixo e ceu. Serve so' para separar aereo alto de rasante.
    terco = g[: max(1, h // 3)]
    reg["ceu"] = round(float((terco > 150).sum()) * 100 / max(1, terco.size), 1)

    if destino_thumb:
        d = Path(destino_thumb)
        if not d.exists():
            d.parent.mkdir(parents=True, exist_ok=True)
            hh, ww = img.shape[:2]
            th = cv2.resize(img, (larg_thumb, max(1, round(hh * larg_thumb / ww))),
                            interpolation=cv2.INTER_AREA)
            ok, buf = cv2.imencode(".jpg", th, [cv2.IMWRITE_JPEG_QUALITY, 74])
            if ok:
                d.write_bytes(buf.tobytes())
    return reg


def hamming(a, b):
    return sum(1 for x, y in zip(a, b) if x != y)


# ------------------------------------------------------------- o inventario
def inventariar():
    """Acha todo quadro em disco. Nao decide nada, so' lista."""
    itens = []
    for chave, cfg in RAIZES.items():
        base = cfg["quadros"]
        if not base.exists():
            print(f"  ! raiz ausente: {base}")
            continue
        for pasta in sorted(p for p in base.iterdir() if p.is_dir()):
            dq = pasta / "quadros"
            if not dq.is_dir():
                continue
            jpgs = sorted(dq.glob("*.jpg"))
            if not jpgs:
                continue
            folhas = sorted(pasta.glob("contato-*.jpg")) + \
                sorted((pasta / "folhas").glob("contato-*.jpg"))
            itens.append({
                "raiz": chave,
                "pasta": pasta.name,
                "dir": pasta,
                "quadros": jpgs,
                "folhas": [str(f) for f in folhas],
            })
    return itens


def mapear_videos():
    """pasta -> arquivo de video original. A pasta nasceu de nome_limpo(stem)."""
    mapa = {}
    dirs = []
    for cfg in RAIZES.values():
        dirs.extend(cfg["videos"])
    # a pasta com a ordem de edicao no proprio nome entra tambem
    dirs.append(Path(r"E:\Projetos todos\Mapa - agroshow\Brutos Expo"
                     r"\Vídeo IA AGROSHOW 2026\Vídeo IA AGROSHOW 2026"
                     r"\Fala do drone colocar como finalização e anoitecendo"
                     r" depois entra a logo animada"))
    vistos = set()
    for d in dirs:
        if not d.exists() or str(d) in vistos:
            continue
        vistos.add(str(d))
        for f in d.rglob("*"):
            if f.is_file() and f.suffix.lower() in VIDEO_EXT:
                mapa.setdefault(nome_limpo(f.stem), str(f))
    return mapa


# ------------------------------------------------------ locais e as ancoras
def carregar_ancoras():
    """As 44 escolhas a mao de 15/08 viram ancora. Ver DECISOES.md D034."""
    arq = RAIZ / "data" / "quadros-ia.json"
    cat = json.loads(arq.read_text(encoding="utf-8"))
    locais, ancoras = [], []
    for L in cat["locais"]:
        locais.append({
            "plano": L["plano"],
            "local": L["local"],
            "diferencial": bool(L.get("diferencial")),
            "cena_3d": L.get("cena_3d"),
            "bloqueio": L.get("bloqueio"),
        })
        for r in L["reais"]:
            if r.get("tc") is None:
                continue          # a foto do portal nao tem video
            ancoras.append({
                "plano": L["plano"],
                "chave": nome_limpo(Path(r["video"]).stem),
                "tc": float(r["tc"]),
                "papel": r["papel"],
                "confianca": r["confianca"],
                "porque": r["porque"],
            })
    return locais, ancoras


def pos_processar(por_video):
    """Periodo, percentil, parecidos, etiqueta e nota -- tudo a partir das
    medidas ja gravadas. Nao le imagem nenhuma, por isso pode rodar de novo
    quando a regra mudar (`--reetiquetar`) sem os 15 min de leitura de disco.
    """
    import statistics as st

    for pasta, regs in por_video.items():
        regs.sort(key=lambda r: (r["tc_s"], r["q"]))
        lum = st.median(r["luma"] for r in regs)
        iso, hdec = hora_do_nome(pasta)

        # PERIODO: o carimbo da camera vence o brilho da imagem.
        # Medido em 15/08: dos 74 voos com carimbo, 13 gravados entre 21h e 23h
        # sairiam como "crepusculo" pelo brilho -- sao noites de evento com
        # iluminacao artificial forte, e o brilho nao distingue isso de fim de
        # tarde. A hora do arquivo distingue, e e' medida da propria camera.
        if hdec is not None:
            if 6 <= hdec < 17:
                periodo, origem = "dia", "carimbo da camera"
            elif 17 <= hdec < 19:
                periodo, origem = "fim de tarde", "carimbo da camera"
            else:
                periodo, origem = "noite", "carimbo da camera"
        else:
            periodo = "noite" if lum < 45 else ("fim de tarde" if lum < 90 else "dia")
            origem = "brilho da imagem (o arquivo nao tem hora no nome)"

        nits = sorted(r["nitidez"] for r in regs)

        # parecidos: compara com a ANCORA da sequencia, nao com o quadro
        # anterior -- encadear pelo anterior deixa um giro lento virar uma
        # sequencia so' e engole plano diferente.
        seq, ancora = 0, None
        for r in regs:
            if ancora is None or hamming(r["dhash"], ancora["dhash"]) > LIMIAR_PARECIDO:
                seq += 1
                ancora = r
            r["seq"] = seq
        for r in regs:
            i = sum(1 for x in nits if x < r["nitidez"])
            r["nitidez_pct"] = round(i / max(1, len(nits) - 1), 3)
            r["periodo"] = periodo
            r["periodo_de_onde"] = origem
            r["luma_mediana_video"] = round(lum, 1)
            if iso:
                r["hora_do_nome"] = iso
                r["hora_dec"] = round(hdec, 2)
            else:
                r.pop("hora_do_nome", None)
                r.pop("hora_dec", None)

        # representante de cada sequencia = o mais nitido dela
        grupos = {}
        for r in regs:
            grupos.setdefault(r["seq"], []).append(r)
        for s, g in grupos.items():
            melhor = max(g, key=lambda r: r["nitidez"])
            for r in g:
                r["representante"] = (r is melhor)
                r["irmaos_na_sequencia"] = len(g)
                r["parecido_com"] = None if r is melhor else melhor["id"]

        for r in regs:
            lo, hi = FAIXA_LUMA[r["periodo"]]
            motivos = []
            if r["luma"] < 8:
                motivos.append("quadro praticamente preto")
            if r["estouro"] > 25:
                motivos.append(f"estouro de {r['estouro']:.0f}% do quadro")
            if r["std"] < 12:
                motivos.append("chapado, quase sem variacao")
            if r["nitidez_pct"] < 0.10 and r["nitidez"] < 60:
                motivos.append("dos mais borrados do proprio voo")
            if motivos:
                r["tier"] = "fraco"
            elif not r["representante"]:
                r["tier"] = "parecido"
                motivos.append(f"quase igual a {r['parecido_com']} "
                               f"(dhash a <= {LIMIAR_PARECIDO} bits)")
            else:
                r["tier"] = "bom"
            r["motivo_da_etiqueta"] = "; ".join(motivos) or None

            # a nota e receita declarada, nao medida
            f_nit = r["nitidez_pct"]
            if r["luma"] < lo:
                f_exp = max(0.0, r["luma"] / max(1e-6, lo))
            elif r["luma"] > hi:
                f_exp = max(0.0, 1 - (r["luma"] - hi) / 60)
            else:
                f_exp = 1.0
            f_ctr = min(1.0, r["std"] / 55)
            f_est = max(0.0, 1 - r["estouro"] / 25)
            nota = 55 * f_nit + 20 * f_exp + 15 * f_ctr + 10 * f_est
            if r["tier"] == "fraco":
                nota *= 0.45
            elif r["tier"] == "parecido":
                nota *= 0.80
            r["nota"] = round(nota, 1)


def classificar(por_video, ancoras):
    """Poe local em quem tem evidencia, e SO' em quem tem.

    UMA ancora marca UM quadro -- o mais proximo dela no tempo. E o quadro que
    foi olhado a mao em 15/08, e so' ele. Voo com 100 quadros em 2 segundos
    (os `_stabilized` curtos) fazia uma ancora virar 40 'ancoras' na primeira
    versao disto, o que e mentira estatistica.

    O resto do MESMO voo, ate 12 s de distancia, sai como 'perto_da_ancora' --
    mesmo voo, provavelmente o mesmo lugar, mas ninguem olhou.
    Todo o resto sai 'nao_classificado', com sugestao de quais locais aquele
    voo toca em algum instante. Sugestao NAO e classificacao.
    """
    por_chave = {}
    for pasta, regs in por_video.items():
        por_chave.setdefault(nome_limpo(pasta), []).extend(regs)
    for r in (x for regs in por_video.values() for x in regs):
        r["plano"] = None
        r["classificacao"] = "nao_classificado"
        r["sugestao"] = []
        r.pop("porque_o_local", None)

    n_anc = n_perto = 0
    for anc in ancoras:
        alvo = por_chave.get(anc["chave"], [])
        if not alvo:
            continue
        melhor = min(alvo, key=lambda r: (abs(r["tc_s"] - anc["tc"]), -r["nitidez"]))
        if melhor["classificacao"] != "ancora":
            melhor["plano"], melhor["classificacao"] = anc["plano"], "ancora"
            melhor["porque_o_local"] = (
                f"o quadro mais proximo do instante escolhido a mao em 15/08 "
                f"({anc['papel']}, {anc['confianca']}): {anc['porque']}")
            n_anc += 1
        for r in alvo:
            d = abs(r["tc_s"] - anc["tc"])
            if d <= 12 and r["classificacao"] == "nao_classificado":
                r["plano"], r["classificacao"] = anc["plano"], "perto_da_ancora"
                r["porque_o_local"] = (
                    f"a {d:.0f}s de um quadro escolhido a mao para {anc['plano']}; "
                    f"MESMO VOO, mas ninguem olhou este aqui")
                n_perto += 1
            if anc["plano"] not in r["sugestao"]:
                r["sugestao"].append(anc["plano"])
    return n_anc, n_perto


def reclassificar(caminho, reetiquetar=False):
    """Refaz local (e, com --reetiquetar, tambem periodo/etiqueta/nota) sobre
    um catalogo JA MEDIDO.

    A medicao custa 15 min de leitura de 17 GB; as regras de etiqueta e as
    ancoras mudam toda vez que alguem confere um quadro a mao. Separar as duas
    coisas e o que permite mudar de ideia sem reler o disco.
    """
    cat = json.loads(caminho.read_text(encoding="utf-8"))
    por_video = {}
    for r in cat["quadros"]:
        por_video.setdefault(r["pasta"], []).append(r)
    if reetiquetar:
        pos_processar(por_video)
        por_pasta = {p["pasta"]: p for p in cat["pastas"]}
        for pasta, regs in por_video.items():
            if pasta in por_pasta:
                por_pasta[pasta]["periodo"] = regs[0]["periodo"]
                por_pasta[pasta]["hora_do_nome"] = regs[0].get("hora_do_nome")
                por_pasta[pasta]["bons"] = sum(1 for r in regs if r["tier"] == "bom")
        q = cat["quadros"]
        cat["_resumo"].update({
            "bons": sum(1 for r in q if r["tier"] == "bom"),
            "parecidos": sum(1 for r in q if r["tier"] == "parecido"),
            "fracos": sum(1 for r in q if r["tier"] == "fraco"),
            "por_periodo": {p: sum(1 for r in q if r["periodo"] == p) for p in PERIODOS},
            "em_pe": sum(1 for r in q if r["h"] > r["w"]),
        })
    locais, ancoras = carregar_ancoras()
    n_anc, n_perto = classificar(por_video, ancoras)
    cat["locais"] = locais
    cat["_resumo"]["ancoras"] = n_anc
    cat["_resumo"]["perto_da_ancora"] = n_perto
    cat["_resumo"]["nao_classificados"] = sum(
        1 for r in cat["quadros"] if r["classificacao"] == "nao_classificado")
    caminho.write_text(json.dumps(cat, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Reclassificado: {n_anc} ancoras, {n_perto} perto, "
          f"{cat['_resumo']['nao_classificados']} sem local")
    if reetiquetar:
        for k, v in cat["_resumo"].items():
            print(f"  {k}: {v}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--varrer", action="store_true", help="medir tudo e gravar")
    ap.add_argument("--reclassificar", action="store_true",
                    help="so' refazer o local sobre o catalogo ja medido")
    ap.add_argument("--reetiquetar", action="store_true",
                    help="refazer periodo, etiqueta e nota sem reler o disco")
    ap.add_argument("--so", type=int, default=0, help="limitar N quadros (teste)")
    ap.add_argument("--sem-thumb", action="store_true")
    ap.add_argument("--thumb-px", type=int, default=400)
    ap.add_argument("--workers", type=int, default=max(2, (os.cpu_count() or 4) - 2))
    ap.add_argument("--saida", default="data/acervo-quadros.json")
    ap.add_argument("--thumbs", default="out/acervo/thumbs")
    a = ap.parse_args()

    if a.reclassificar or a.reetiquetar:
        return reclassificar(RAIZ / a.saida, reetiquetar=a.reetiquetar)

    print("Inventariando...")
    lotes = inventariar()
    total = sum(len(x["quadros"]) for x in lotes)
    print(f"  {len(lotes)} pastas de video, {total} quadros em disco")
    if not a.varrer:
        for x in lotes[:8]:
            print(f"   {x['raiz']:9s} {x['pasta']:44s} {len(x['quadros']):4d} quadros")
        print("   ... (use --varrer para medir)")
        return 0

    mapa_video = mapear_videos()
    locais, ancoras = carregar_ancoras()
    print(f"  {len(mapa_video)} videos localizados em disco")
    print(f"  {len(locais)} locais, {len(ancoras)} ancoras herdadas do catalogo de 15/08")

    dir_thumb = RAIZ / a.thumbs
    slugs = mapa_de_slugs([x["pasta"] for x in lotes])
    tarefas, indice = [], []
    for lote in lotes:
        s = slugs[lote["pasta"]]
        for jpg in lote["quadros"]:
            th = None if a.sem_thumb else str(dir_thumb / s / (jpg.stem + ".jpg"))
            tarefas.append((str(jpg), th, a.thumb_px))
            indice.append((lote, jpg))
    if a.so:
        tarefas, indice = tarefas[: a.so], indice[: a.so]

    print(f"Medindo {len(tarefas)} quadros com {a.workers} processos...")
    medidas = []
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        for i, reg in enumerate(ex.map(medir, tarefas, chunksize=16), 1):
            medidas.append(reg)
            if i % 250 == 0 or i == len(tarefas):
                print(f"  {i}/{len(tarefas)}", flush=True)

    # ------------------------------------------------- montagem dos registros
    RE_Q = re.compile(r"^q(\d+)_(\d{2})-(\d{2})-(\d{2})$")
    por_video = {}
    erros = []
    for (lote, jpg), med in zip(indice, medidas):
        if "erro" in med:
            erros.append(med)
            continue
        m = RE_Q.match(jpg.stem)
        n = int(m.group(1)) if m else 0
        tc = (int(m.group(2)) * 3600 + int(m.group(3)) * 60 + int(m.group(4))) if m else 0
        pasta = lote["pasta"]
        reg = dict(med)
        reg.update({
            "id": f"{slugs[pasta]}__{jpg.stem}",
            "pasta": pasta,
            "raiz": lote["raiz"],
            "q": n,
            "tc_s": tc,
            "tc": hhmmss(tc),
            "arquivo": str(jpg),
            "thumb": f"thumbs/{slugs[pasta]}/{jpg.stem}.jpg",
            "video_arquivo": mapa_video.get(nome_limpo(pasta)),
        })
        por_video.setdefault(pasta, []).append(reg)

    pos_processar(por_video)

    n_anc, n_perto = classificar(por_video, ancoras)

    # ----------------------------------------------------------------- gravar
    todos = [r for regs in por_video.values() for r in regs]
    todos.sort(key=lambda r: (r["raiz"], r["pasta"], r["q"]))
    pastas = []
    for lote in lotes:
        regs = por_video.get(lote["pasta"], [])
        if not regs:
            continue
        pastas.append({
            "pasta": lote["pasta"],
            "raiz": lote["raiz"],
            "dir": str(lote["dir"]),
            "video_arquivo": mapa_video.get(nome_limpo(lote["pasta"])),
            "folhas_de_contato": lote["folhas"],
            "n_quadros": len(regs),
            "duracao_s": max(r["tc_s"] for r in regs),
            "periodo": regs[0]["periodo"],
            "hora_do_nome": regs[0].get("hora_do_nome"),
            "sequencias": len({r["seq"] for r in regs}),
            "bons": sum(1 for r in regs if r["tier"] == "bom"),
        })

    saida = {
        "_procedencia": "registro -- medido por pixel em 15/08/2026 por scripts/acervo_quadros.py",
        "_o_que_isto_e": [
            "O acervo INTEIRO de quadros extraidos das duas raizes que ele indicou,",
            "medido um por um. Substitui em cobertura o data/quadros-ia.json, que",
            "olhou 44 quadros escolhidos a mao -- e NAO o substitui em julgamento:",
            "aqueles 44 continuam sendo os unicos conferidos por olho, e entram aqui",
            "como ANCORA.",
        ],
        "_o_que_isto_nao_e": [
            "Nao e classificacao de local por conteudo. Nenhum quadro foi reconhecido",
            "por imagem. So' e' classificado quem cai perto de uma ancora do catalogo",
            "de 15/08 -- o resto sai 'nao_classificado', com sugestao de quais locais",
            "aquele MESMO voo toca em algum instante.",
            "Nao e descarte. 'fraco' e 'parecido' continuam no catalogo e na pagina.",
        ],
        "_criterio": {
            "medido": {
                "nitidez": "variancia do laplaciano sobre a imagem normalizada a 960 px de largura",
                "luma/std/estouro/escuro": "estatistica do canal de luminancia, 0-255",
                "dhash": "64 bits, comparacao de pixel com o vizinho da direita em 9x8",
                "hora_do_nome": "carimbo da camera no nome do arquivo -- so' os voos DJI_AAAAMMDD tem",
            },
            "receita_declarada": {
                "nota": "55*nitidez_pct + 20*exposicao + 15*contraste + 10*(1-estouro); "
                        "x0,45 se 'fraco', x0,80 se 'parecido'",
                "periodo": "mediana de luma do VIDEO: <45 noite, <90 crepusculo, senao dia",
                "por_que_o_periodo_e_do_video": "penalizar quadro escuro num voo noturno enterraria "
                                                "o material que ele pediu para o final (anoitecendo)",
                "limiar_parecido": LIMIAR_PARECIDO,
            },
        },
        "_raizes": {k: {"quadros": str(v["quadros"]), "rotulo": v["rotulo"]}
                    for k, v in RAIZES.items()},
        "_resumo": {
            "pastas": len(pastas),
            "quadros": len(todos),
            "bons": sum(1 for r in todos if r["tier"] == "bom"),
            "parecidos": sum(1 for r in todos if r["tier"] == "parecido"),
            "fracos": sum(1 for r in todos if r["tier"] == "fraco"),
            "ancoras": n_anc,
            "perto_da_ancora": n_perto,
            "nao_classificados": sum(1 for r in todos if r["classificacao"] == "nao_classificado"),
            "erros_de_leitura": len(erros),
            "por_periodo": {p: sum(1 for r in todos if r["periodo"] == p)
                            for p in PERIODOS},
            "em_pe": sum(1 for r in todos if r["h"] > r["w"]),
        },
        "locais": locais,
        "pastas": pastas,
        "quadros": todos,
        "erros": erros,
    }
    arq = RAIZ / a.saida
    arq.write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nGravado {arq}  ({arq.stat().st_size / 1e6:.1f} MB)")
    for k, v in saida["_resumo"].items():
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
