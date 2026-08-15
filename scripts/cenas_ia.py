#!/usr/bin/env python3
"""O Plano A: os 22 planos viram clipes de IA geradora (Flow ou Higgsfield).

Ordem do Natan em 15/08: *"preciso gerar as cenas no flow para posteriormente
animar, ou no flow ou no higgsfield mas nao posso cometer erros o lugar tem que
ser exatamente o lugar onde sera o agroshow"*.

## A regra que garante o lugar

**Nenhum clipe e texto-para-video.** Todo clipe e **quadro-para-video**, com os
DOIS extremos -- primeiro e ultimo quadro -- renderizados da cena medida.

Texto-para-video inventa um parque generico: e o modo de falha exato que ele
nomeou. Travando os dois extremos com render da planta medida, a IA nao escolhe
onde ficam as coisas. Ela preenche o movimento entre dois quadros que ja **sao**
o lugar certo -- poe pele nas figuras, pelo no gado, poeira e vento na lona. A
posicao nao esta em disputa em momento nenhum.

E a decupagem ja entrega isso de graca: cada plano de `data/planos.json` declara
camera de inicio e de fim. Primeiro e ultimo quadro e exatamente o que o
"Frames to Video" do Flow pede.

## O que isso custa de render, e e o argumento do Plano A

O filme inteiro sao 4.635 quadros a 10,0 s -> 12,9 h. Os quadros-guia sao a
soma de (clipes + 1) por plano -- algumas dezenas. O `--conferir` imprime o
numero medido, nao estimado.

## A grade de duracao, que e onde se erra feio

Flow faz clipe de 4, 6 ou 8 s. Higgsfield faz 5 ou 10. Os planos duram de 5,0 a
11,0 s. Entao cada plano e quebrado em clipes que somem o mais perto possivel da
duracao dele -- e quando a soma nao fecha exato, a **velocidade da camera muda**,
porque o caminho e o mesmo e o tempo mudou. Isso nao pode passar em silencio: a
faixa cinematografica de drone (1,3-2,2 m/s em orbita e push-in, 3,6-6,7 em
sobrevoo) e o motivo de a decupagem existir. O conferidor remede a velocidade
**depois** do encaixe na grade e acusa quem sair.

    python3 scripts/cenas_ia.py --conferir
    python3 scripts/cenas_ia.py --plataforma higgsfield --conferir
    python3 scripts/cenas_ia.py --roteiro > out/cenas/roteiro-flow.md
    python3 scripts/cenas_ia.py --quadros
"""

import argparse
import itertools
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import planos as planos_mod
from terreno import carregar_mapa

RAIZ = Path(__file__).resolve().parent.parent
CONTRATO = RAIZ / "data" / "cenas-ia.json"

# Ate quantos clipes um plano pode ser quebrado. Cada emenda e um lugar onde a
# IA pode discordar de si mesma entre um clipe e o outro, entao menos e melhor;
# 4 cobre o plano mais longo (11 s) nas duas grades com folga.
MAX_CLIPES = 4


def carregar_contrato(caminho=None):
    p = Path(caminho) if caminho else CONTRATO
    return json.loads(p.read_text(encoding="utf-8"))


def encaixar(duracao_s, grade, aceita=None, max_clipes=MAX_CLIPES):
    """A combinacao de clipes da grade que melhor cobre `duracao_s`.

    Criterio, nesta ordem: **cabe na regra** (o `aceita`); menor erro de
    duracao; menos clipes; clipes mais longos. "Menos clipes" vem antes de
    "clipes mais longos" porque cada emenda custa continuidade, e continuidade e
    o que a IA tem de mais fragil.

    A regra vem primeiro, e nao por elegancia -- foi medido. Sem ela, um plano
    de 9,0 s encaixava em 8,0 s (erro 1,0 s, um clipe) em vez de 4+6 (erro 1,0 s,
    dois clipes), porque o desempate era "menos clipes". Os dois erram 1 s de
    duracao, mas **encurtar acelera a camera** e alongar desacelera: os 8 s
    jogavam o push-in a 2,35 m/s, fora da faixa cinematografica, e os 10 s o
    deixavam em 1,88, dentro. Empate em duracao nao e empate em cinema.

    Devolve (lista de duracoes, erro em segundos com sinal).
    """
    candidatos = []
    for n in range(1, max_clipes + 1):
        for combo in itertools.combinations_with_replacement(sorted(grade), n):
            soma = sum(combo)
            recusado = False if aceita is None else not aceita(soma)
            candidatos.append((recusado, round(abs(soma - duracao_s), 6), n,
                               -min(combo), list(combo), soma))
    candidatos.sort(key=lambda c: c[:4])
    _, _, _, _, combo, soma = candidatos[0]
    return combo, soma - duracao_s


def quebrar(plano, grade, fps, centro, max_clipes=MAX_CLIPES):
    """Um plano -> a lista de clipes, com os quadros-guia de cada um.

    O caminho da camera nao muda: o que muda e o tempo que se leva para
    percorre-lo. Por isso a velocidade nova e a velha vezes (dur_velha/dur_nova),
    uniforme -- o movimento e linear em t dentro do plano.

    O quadro de emenda e o MESMO objeto nos dois clipes: ultimo do clipe k e
    primeiro do clipe k+1. Renderizado uma vez, usado duas. E o que faz o corte
    entre clipes cair sobre geometria identica.
    """
    lo, hi = planos_mod.FAIXAS[plano["movimento"]]
    v_pico, dur = plano["_v_pico"], plano["duracao_s"]
    diferencial = plano["peso"] == "diferencial"

    def aceita(soma):
        # A velocidade e inversamente proporcional ao tempo: mesmo caminho, mais
        # segundos, mais devagar. E os quatro diferenciais tem piso de 8 s de
        # tela, que e pedido do cliente e nao preferencia de montagem.
        if not lo <= v_pico * dur / soma <= hi:
            return False
        return not (diferencial and soma < 8.0)

    duracoes, erro = encaixar(dur, grade, aceita, max_clipes)
    total_novo = sum(duracoes)
    fator = plano["duracao_s"] / total_novo          # <1 acelera, >1 desacelera

    q_ini, q_fim = plano["_quadro_ini"], plano["_quadro_fim"]
    vao = q_fim - q_ini

    clipes, acumulado = [], 0.0
    for i, d in enumerate(duracoes):
        t0 = acumulado / total_novo
        t1 = (acumulado + d) / total_novo
        acumulado += d

        c0, m0 = planos_mod.amostra(plano, t0, centro)
        c1, m1 = planos_mod.amostra(plano, t1, centro)
        trecho_m = math.dist(c0, c1)

        clipes.append({
            "id": f"{plano['id']}-{i + 1}" if len(duracoes) > 1 else plano["id"],
            "plano": plano["id"],
            "ordem": i + 1,
            "de_quantos": len(duracoes),
            "duracao_s": d,
            "t_ini": round(t0, 6),
            "t_fim": round(t1, 6),
            "quadro_ini": q_ini + int(round(t0 * vao)),
            "quadro_fim": q_ini + int(round(t1 * vao)),
            "corda_m": round(trecho_m, 1),
            "v_corda": round(trecho_m / d, 2),
        })

    return {
        "id": plano["id"],
        "titulo": plano["titulo"],
        "peso": plano["peso"],
        "movimento": plano["movimento"],
        "lente_mm": plano["lente_mm"],
        "duracao_original_s": plano["duracao_s"],
        "duracao_na_grade_s": total_novo,
        "erro_s": round(erro, 2),
        "fator_de_tempo": round(fator, 4),
        "v_pico_original": round(plano["_v_pico"], 2),
        "v_pico_na_grade": round(plano["_v_pico"] * fator, 2),
        "comprimento_m": round(plano["_comprimento_m"], 1),
        "clipes": clipes,
    }


def montar(pacote, contrato, plataforma):
    """Todos os planos quebrados, mais os numeros do lote."""
    plat = contrato["plataformas"][plataforma]
    grade = plat["duracoes_s"]
    centro, fps = pacote["centro"], pacote["fps"]

    quebrados = [quebrar(p, grade, fps, centro) for p in pacote["planos"]]

    clipes = sum(len(q["clipes"]) for q in quebrados)
    # Um quadro-guia por ponta de clipe, MENOS as emendas, que sao o mesmo
    # quadro servindo aos dois lados. Por plano: clipes + 1.
    quadros = sum(len(q["clipes"]) + 1 for q in quebrados)

    return {
        "plataforma": plataforma,
        "grade_s": grade,
        "planos": quebrados,
        "clipes": clipes,
        "quadros_guia": quadros,
        "duracao_original_s": round(sum(q["duracao_original_s"] for q in quebrados), 1),
        "duracao_na_grade_s": round(sum(q["duracao_na_grade_s"] for q in quebrados), 1),
    }


# --------------------------------------------------------------------------
# O prompt

def prompt_de(clipe, plano_q, contrato, idioma="en"):
    """O prompt de um clipe. Movimento, materia e vida -- nunca posicao.

    O que este texto NAO tem, e e de proposito: onde ficam as coisas. O quadro
    ja diz isso, com medida. Repetir em palavra e convidar a IA a discordar do
    quadro que ela recebeu -- e quando ela discorda, quem ganha e o texto.
    """
    p = contrato["planos"][plano_q["id"]]
    look = contrato["look_lock"]
    proib = contrato["proibicoes_duras"]
    mov = contrato["movimento_em_ingles"][plano_q["movimento"]]

    continuidade = ""
    if clipe["de_quantos"] > 1:
        continuidade = (
            f" This is part {clipe['ordem']} of {clipe['de_quantos']} of one "
            f"continuous move; keep exposure, color and crowd density identical "
            f"across the parts.")

    # A negativa da arquibancada so entra onde ha publico assistindo. Citar
    # "grandstand" num plano de estacionamento nao protege nada e ainda puxa o
    # conceito para dentro do quadro -- modelo generativo carrega a palavra da
    # negativa. A lista esta no contrato, revisavel.
    arq = proib["arquibancada"]
    com_arquibancada = plano_q["id"] in arq.get("vale_em", [])

    if idioma == "pt":
        proibido = ([arq["pt"]] if com_arquibancada else []) + [
            proib["texto_no_quadro"]["pt"]]
        return (
            f"Cena fotorrealista de uma feira agropecuaria brasileira, fim de "
            f"tarde. Camera: {plano_q['movimento']}, equivalente a "
            f"{plano_q['lente_mm']} mm, lenta e constante. "
            f"Animar: {p['acao_pt']}. "
            f"Manter exatamente como esta nos quadros o traçado, as edificacoes, "
            f"as tendas brancas e as posicoes de tudo -- nao acrescentar, mover "
            f"nem remover estrutura nenhuma. "
            f"Luz: {look['hora']}, sombras longas e suaves, leve neblina ao longe. "
            f"Proibido: {'; '.join(proibido)}.")

    negativas = ([arq["en"]] if com_arquibancada else []) + [
        proib["texto_no_quadro"]["en"], proib["deriva_de_camera"]["en"]]
    return (
        f"Photorealistic aerial-cinema shot of a Brazilian agricultural fair. "
        f"Camera: {mov}, {plano_q['lente_mm']}mm equivalent, slow and steady at "
        f"constant speed.{continuidade} "
        f"Animate: {p['acao_en']}. "
        f"Keep the ground plan, the buildings, the white peaked tents and every "
        f"position exactly as given in the frames -- do not add, move, resize or "
        f"remove any structure. "
        f"Light: {look['en']}. "
        f"Look: {look['camera_en']}. "
        f"Negative: {'; '.join(negativas)}.")


# --------------------------------------------------------------------------
# Saidas

def conferir(lote, pacote, contrato):
    """Mede o encaixe na grade e acusa quem saiu da faixa. Sem bpy, sem GPU."""
    problemas = []
    plat = contrato["plataformas"][lote["plataforma"]]

    print("=" * 100)
    print(f"  CENAS PARA IA -- plataforma {lote['plataforma'].upper()} "
          f"· grade {lote['grade_s']} s · aspecto {plat['aspectos'][0]}")
    print("=" * 100)
    print(f"{'id':5} {'mov':11} {'orig':>5} {'grade':>6} {'erro':>6} "
          f"{'clipes':>7} {'v.pico':>7} {'->':>2} {'v.nova':>7} {'faixa':>10}  titulo")
    print("-" * 100)

    for q in lote["planos"]:
        lo, hi = planos_mod.FAIXAS[q["movimento"]]
        fora = not (lo <= q["v_pico_na_grade"] <= hi)
        marca = "  FORA" if fora else ""
        durs = "+".join(str(int(c["duracao_s"])) for c in q["clipes"])
        print(f"{q['id']:5} {q['movimento']:11} {q['duracao_original_s']:5.1f} "
              f"{q['duracao_na_grade_s']:6.1f} {q['erro_s']:+6.1f} "
              f"{durs:>7} {q['v_pico_original']:7.2f} {'->':>2} "
              f"{q['v_pico_na_grade']:7.2f} {lo:4.1f}-{hi:<4.1f}  "
              f"{(q['titulo'] or '—')[:28]}{marca}")

        if fora:
            # O conserto NAO e mexer na duracao -- ela ja esta encostada na
            # grade da plataforma, que nao se negocia. E encurtar (ou alongar) o
            # CAMINHO da camera, e o quanto sai de conta: velocidade de pico e
            # linear no comprimento do percurso.
            alvo = hi if q["v_pico_na_grade"] > hi else lo
            fator = alvo / q["v_pico_na_grade"]
            verbo = "encurtar" if fator < 1 else "alongar"
            problemas.append(
                f"{q['id']}: na grade de {q['duracao_na_grade_s']:.0f} s a "
                f"velocidade vai a {q['v_pico_na_grade']:.2f} m/s, fora de "
                f"{lo}-{hi}. A grade nao se negocia, entao o conserto e o "
                f"caminho: {verbo} o percurso para {fator * 100:.0f}% "
                f"({q['comprimento_m']:.1f} m -> {q['comprimento_m'] * fator:.1f} m), "
                f"em dist_ini_m/dist_fim_m de {q['id']} em data/planos.json")
        if q["peso"] == "diferencial" and q["duracao_na_grade_s"] < 8.0:
            problemas.append(
                f"{q['id']}: diferencial cai para {q['duracao_na_grade_s']:.0f}s "
                f"na grade -- o cliente pediu mais tela para os quatro")

    print("-" * 100)
    deriva = lote["duracao_na_grade_s"] - lote["duracao_original_s"]
    print(f"  clipes a gerar ........ {lote['clipes']}")
    print(f"  quadros-guia .......... {lote['quadros_guia']} "
          f"(emenda e um quadro so, servindo aos dois clipes)")
    print(f"  filme ................. {lote['duracao_original_s']:.0f} s -> "
          f"{lote['duracao_na_grade_s']:.0f} s ({deriva:+.0f} s)")

    total_quadros = pacote["total_quadros"]
    print(f"  render do Plano A ..... {lote['quadros_guia']} quadros contra os "
          f"{total_quadros} do filme inteiro "
          f"({lote['quadros_guia'] / total_quadros * 100:.1f}%)")
    print(f"  a 10,0 s/quadro ....... {lote['quadros_guia'] * 10.0 / 60:.0f} min "
          f"contra as 12,9 h do Plano B")

    letras = carregar_letreiros()
    p_let = conferir_letreiros(lote, letras)
    problemas += p_let
    lt = linha_do_tempo(lote, letras)
    print(f"  letreiros ............. {len(lt['letreiros'])} na linha de tempo, "
          f"{'casando com o plano que nomeiam' if not p_let else 'COM PROBLEMA'}")

    print()
    if problemas:
        print(f"  {len(problemas)} PROBLEMA(S):")
        for x in problemas:
            print(f"    - {x}")
    else:
        print("  encaixe limpo: toda velocidade continua na faixa "
              "cinematografica depois da grade, e todo letreiro esta no seu plano.")
    print("=" * 100)
    return problemas


def roteiro(lote, contrato):
    """O caderno para colar na plataforma, clipe a clipe."""
    plat = contrato["plataformas"][lote["plataforma"]]
    asp = contrato["aspecto_a_conta_que_nao_pode_errar"]
    L = []
    a = L.append

    a(f"# Cenas para IA — {lote['plataforma'].upper()}")
    a("")
    a(f"**{lote['clipes']} clipes · {lote['quadros_guia']} quadros-guia · "
      f"{lote['duracao_na_grade_s']:.0f} s de filme**")
    a("")
    a(f"Modo: **{plat['modo']}**. Aspecto: **{plat['aspectos'][0]}** — "
      f"a entrega é 2:1 e se faz cortando a faixa central "
      f"({asp['corta_de_cada_lado_px']} px de cada lado no guia de "
      f"{asp['quadro_guia_px'][0]}×{asp['quadro_guia_px'][1]}). Nunca esticar.")
    a("")
    a("**Os dois quadros de cada clipe são render da cena medida.** O prompt não "
      "descreve onde as coisas estão — o quadro já diz, com medida. Nenhum clipe "
      "é texto-para-vídeo.")
    a("")
    a("**Os letreiros não entram aqui.** Modelo generativo destrói tipografia. "
      "O texto entra na montagem, por cima do clipe pronto.")
    a("")

    for q in lote["planos"]:
        p = contrato["planos"][q["id"]]
        a("---")
        a("")
        titulo = q["titulo"] or "(continuação)"
        marca = " · **DIFERENCIAL**" if q["peso"] == "diferencial" else ""
        a(f"## {q['id']} — {titulo}{marca}")
        a("")
        a(f"`{q['movimento']}` · {q['lente_mm']} mm · "
          f"{q['duracao_na_grade_s']:.0f} s em {len(q['clipes'])} clipe(s) · "
          f"{q['v_pico_na_grade']:.2f} m/s")
        a("")
        a(f"Áudio: {p['audio']}")
        if p.get("cuidado"):
            a("")
            a(f"> **Cuidado:** {p['cuidado']}")
        a("")
        for c in q["clipes"]:
            a(f"### {c['id']} — {c['duracao_s']:.0f} s")
            a("")
            a(f"- primeiro quadro: `{c['quadro_ini']:05d}.png`")
            a(f"- último quadro: `{c['quadro_fim']:05d}.png`")
            a("")
            a("```")
            a(prompt_de(c, q, contrato, "en"))
            a("```")
            a("")
            a("<details><summary>o mesmo, em português, para conferir</summary>")
            a("")
            a("```")
            a(prompt_de(c, q, contrato, "pt"))
            a("```")
            a("</details>")
            a("")
    return "\n".join(L)


def carregar_letreiros(caminho=None):
    p = Path(caminho) if caminho else RAIZ / "data" / "letreiros.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def linha_do_tempo(lote, letras, altura_master=1380):
    """A montagem: cada clipe e cada letreiro com entrada e saida em segundos.

    E aqui que o filme vira ordem de edicao. Sem isto, montar 29 clipes na mao
    e apostar que a ordem saiu certa -- e a ordem do percurso e o produto: o
    cliente comprou reconhecer o parque dele na sequencia em que se anda nele.

    **O letreiro entra como texto 2D, e nao como o objeto 3D da cena.** No Plano
    B ele e geometria: billboard plantado no mundo, que a camera atravessa e que
    muda de tamanho durante o plano. No Plano A isso deixa de servir, e o motivo
    e que o clipe da IA **nao segue o caminho da camera quadro a quadro** -- ela
    interpola entre os dois extremos travados do jeito dela. Um letreiro
    renderizado do nosso percurso exato ia deslizar contra a imagem. Como texto
    2D, ele nao tem com o que brigar, e a regra de 8%/4% passa a ser conta
    direta sobre a altura do master.
    """
    escala = letras.get("escala_por_nivel", {})
    por_plano = {x["plano"]: x for x in letras.get("letreiros", [])}

    t, clipes, sobreposicoes = 0.0, [], []
    for q in lote["planos"]:
        t_plano = t
        for c in q["clipes"]:
            clipes.append({
                "id": c["id"], "plano": q["id"],
                "arquivo": f"{c['id']}.mp4",
                "entra_s": round(t, 3),
                "sai_s": round(t + c["duracao_s"], 3),
                "duracao_s": c["duracao_s"],
                "quadro_ini": c["quadro_ini"], "quadro_fim": c["quadro_fim"],
            })
            t += c["duracao_s"]

        item = por_plano.get(q["id"])
        if item:
            nivel = item["nivel"]
            frac = escala.get(nivel, {}).get("fracao_da_altura", 0.08)
            # Meio segundo de folga em cada ponta: letreiro que nasce e morre
            # junto com o corte pisca. E o de baixo (o apoio) e sempre menor,
            # com o minimo de 4% da regra de entrega.
            sobreposicoes.append({
                "plano": q["id"],
                "texto": item["texto"],
                "apoio": item.get("apoio"),
                "nivel": nivel,
                "entra_s": round(t_plano + 0.5, 3),
                "sai_s": round(t - 0.5, 3),
                "altura_px": int(round(frac * altura_master)),
                "altura_apoio_px": int(round(
                    escala.get("apoio", {}).get("fracao_da_altura", 0.042)
                    * altura_master)),
                "fracao": frac,
            })

    return {"total_s": round(t, 3), "clipes": clipes, "letreiros": sobreposicoes}


def conferir_letreiros(lote, letras):
    """O letreiro esta no plano que ele nomeia? E cabe na regra de 8%/4%?

    Existe por causa de um defeito que quase foi para a entrega: **5 dos 17
    letreiros estavam amarrados ao plano errado** -- "Pista de Julgamentos" no
    plano das maquinas, a frase de assinatura na saida pelo portal. Nada
    acusava, porque `letreiros.json` e `planos.json` so se falam pelo `id`, e id
    errado e id valido. Agora se falam pelo TEXTO tambem.
    """
    import unicodedata

    def norm(s):
        s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
        return "".join(c for c in s.lower() if c.isalnum() or c == " ").strip()

    def parece(a, b):
        a, b = norm(a), norm(b)
        if not a or not b:
            return False
        if a in b or b in a:
            return True
        return len(set(a.split()) & set(b.split())) >= 2

    titulos = {q["id"]: q["titulo"] for q in lote["planos"]}
    problemas = []
    vistos = set()

    for item in letras.get("letreiros", []):
        pid = item["plano"]
        if pid in vistos:
            problemas.append(f"letreiro: {pid} tem mais de um letreiro")
        vistos.add(pid)
        if pid not in titulos:
            problemas.append(f"letreiro {item['texto']!r}: plano {pid} nao existe")
            continue
        tit = titulos[pid]
        # Divergencia DECLARADA passa. Ha dois casos legitimos em que o letreiro
        # usa outra palavra que a decupagem -- "Pavilhao 3" para o plano das
        # Agroindustrias, "Alimentacao no Bosque" para a Praca Aberta --, e nos
        # dois o texto e a palavra do cliente. Declarar caso a caso e o que
        # deixa a checagem apertada: afrouxar o comparador para engoli-los
        # deixaria passar tambem os cinco que estavam de fato no plano errado.
        if item.get("texto_difere_do_titulo"):
            continue
        if tit and not parece(item["texto"], tit):
            onde = [k for k, v in titulos.items() if parece(item["texto"], v)]
            problemas.append(
                f"letreiro {item['texto']!r} esta em {pid} (que se chama "
                f"{tit!r})" + (f" -- o texto bate com {onde}" if onde else ""))

    for q in lote["planos"]:
        if q["titulo"] and q["id"] not in vistos:
            problemas.append(f"{q['id']} tem titulo {q['titulo'][:30]!r} na "
                             f"decupagem e NENHUM letreiro")
    return problemas


def lista_de_quadros(lote):
    """Os quadros-guia, sem repetir a emenda. E o que o render precisa."""
    q = set()
    for pl in lote["planos"]:
        for c in pl["clipes"]:
            q.add(c["quadro_ini"])
            q.add(c["quadro_fim"])
    return sorted(q)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--plataforma", default="flow", choices=("flow", "higgsfield"))
    ap.add_argument("--planos-json", dest="planos_json", default="data/planos.json")
    ap.add_argument("--conferir", action="store_true")
    ap.add_argument("--roteiro", action="store_true",
                    help="o caderno de prompts, em markdown, para o stdout")
    ap.add_argument("--quadros", action="store_true",
                    help="so a lista de quadros-guia, um por linha")
    ap.add_argument("--timeline", action="store_true",
                    help="a linha de tempo da montagem em json: ordem dos "
                         "clipes e entrada/saida de cada letreiro. E o que o "
                         "scripts/montar_flow.sh consome")
    ap.add_argument("--json", action="store_true",
                    help="o lote inteiro em json, para outro script consumir")
    args = ap.parse_args()

    contrato = carregar_contrato()
    pacote = planos_mod.carregar(args.planos_json, dados=carregar_mapa())
    lote = montar(pacote, contrato, args.plataforma)

    if args.roteiro:
        print(roteiro(lote, contrato))
        return
    if args.quadros:
        for n in lista_de_quadros(lote):
            print(n)
        return
    if args.timeline:
        lt = linha_do_tempo(lote, carregar_letreiros())
        lt["plataforma"] = lote["plataforma"]
        lt["tipografia"] = carregar_letreiros().get("tipografia", {})
        lt["cor_do_texto"] = carregar_letreiros().get("cor", {})
        print(json.dumps(lt, ensure_ascii=False, indent=1))
        return
    if args.json:
        print(json.dumps(lote, ensure_ascii=False, indent=1))
        return

    if conferir(lote, pacote, contrato):
        sys.exit(1)


if __name__ == "__main__":
    main()
