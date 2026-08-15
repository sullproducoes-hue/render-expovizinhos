#!/usr/bin/env python3
"""Mede o footprint de cada zona da planta no proprio desenho.

Por que existe: a planta so declara area em texto para os pavilhoes de animais
(720 m², colada no rotulo) e para os estandes. Para as outras ~100 zonas --
Praca de Alimentacao, Recinto de Leiloes, Mangueiras, Saguao Aberto, PAVILHAO
1/2/3 -- nao ha cota nenhuma. Sem isto, construir "tudo que a planta descreve"
viraria inventar tamanho.

Metodo v1 (`--metodo hachura`, o de 14/08): renderiza a prancha, separa o cinza
das EDIFICACOES do resto, e para cada rotulo acha a mancha que o contem ou esta
mais perto. De cada mancha sai `cv2.minAreaRect`.

O v1 media 104 de 113 e tinha tres modos de falha conhecidos -- bloco fundido,
mancha vazada e casamento a distancia. **A raiz dos tres e a mesma e so
apareceu ao olhar o desenho: a ancora de cada zona E O CENTRO DA CAIXA DE TEXTO
DO ROTULO, e a letra e desenhada por cima do mapa.** Entao a tinta do proprio
rotulo entra na mascara, cola predios vizinhos, e qualquer metodo semeado por
pixel acaba medindo a mancha da letra em vez do predio.

Metodo v2 (padrao), o que este arquivo passou a fazer:

1. **Tira o texto.** As caixas vem do PDF (`page.get_text`), nao de heuristica:
   o centro de cada span bate com o (x,y) da zona ate a primeira decimal.
2. **Junta fragmento de rotulo.** "Praca de Alimentacao" + "Coberta" sao duas
   linhas de UM nome; "CASA DO" + "MEDICO" + "VETERINARIO" idem. Ancoras da
   mesma categoria a menos de `--fragmento` pt viram uma zona so, e os rotulos
   originais ficam gravados em `rotulos`.
3. **Semeia pela CAIXA, nao pelo ponto.** A zona fica com a mancha de maior
   sobreposicao com o retangulo do rotulo dilatado -- o rotulo e desenhado
   dentro do que ele nomeia. Acaba o casamento com mancha a 172 px.
4. **Bloco fundido -> watershed.** Quando duas zonas caem na mesma mancha, ela
   e repartida com os rotulos como marcadores e o desenho como relevo: o corte
   cai na parede interna onde ela existe, e vira divisa por proximidade onde
   nao existe. Sai `particao: "watershed"`.
5. **Classe de cor que faltava.** O bloco do Mercado do Produtor / Cafe
   Colonial / Cozinha Didatica e laranja, nao cinza, e caia fora da mascara --
   eram 4 das 9 zonas perdidas. Fill saturado entrou como segunda classe.
6. **E recusa o que nao da para medir.** Ver abaixo.

**O achado que muda o plano, e ele e ruim:** metade das 104 medidas do v1 era a
tinta da propria palavra. A mascara pega o cinza antisserrilhado da fonte (V
120..242) e NAO pega o preenchimento do predio (247), entao onde nao ha predio
desenhado ela devolve o retangulo do texto -- eram os `Talude` de 3 m², os
`Bosque` de 12 m², os `ESTACIONAMENTO` de 13 m². `area_fora_do_rotulo_m2`
reprova esses, e o extrator passa a dizer **"esta zona nao tem footprint
desenhado"** em vez de inventar um.

Tres primitivos foram testados para recuperar o que sobrou, e os TRES foram
recusados pelo numero -- ficam escritos para nao voltarem:

- **casco convexo por raio** (para a grade das MANGUEIRAS): a medida crescia
  junto com o raio (31 m a raio 30 pt, 89 m a raio 80 pt). Parametro virando
  resposta nao e medida.
- **densidade de traco**: a mesma grade dava de 3.000 a 50.000 m² conforme
  janela e limiar, e a densidade dentro do pavilhao cotado dava 0,000 --
  porque o preenchimento nao e traco. Funcao mantida em `mascara_densidade`,
  fora do caminho de decisao.
- **regiao fechada** (inundar o branco a partir da borda): o recinto inteiro
  vira UMA regiao de 591 x 441 m. O contorno externo fecha, os internos vazam:
  o desenho e um bitmap de 1806x1383 reamostrado, e linha fina nao sobrevive.

Nada disso e cota: continua **medido do desenho**. Cada item sai com `metodo`,
`confianca` e os sinais que motivaram a desconfianca, para o gerador nao tratar
palpite como dado.

Roda no venv (pymupdf + cv2 + numpy).

Uso:
    .venv/Scripts/python.exe scripts/extrair_footprints.py
    .venv/Scripts/python.exe scripts/extrair_footprints.py --diagnostico
    .venv/Scripts/python.exe scripts/extrair_footprints.py --debug out/footprints.png
    .venv/Scripts/python.exe scripts/extrair_footprints.py --metodo hachura
"""

import argparse
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np
import pymupdf

RAIZ = Path(__file__).resolve().parent.parent
PDF = RAIZ / "reference" / "Mapa_AGROSHOW26.pdf"

# 2,5 px por ponto: acima do bitmap embutido (1806x1383 para 1440x810 pt, ou
# ~1,25 px/pt), com folga para o contorno nao virar serrilha na hora de medir.
PX_POR_PT = 2.5

# Limiares do v2, todos medidos na prancha e nao chutados -- ver --diagnostico.
FRAGMENTO_PT = 12.0      # ancoras mais perto que isto sao linhas do mesmo nome
SEMENTE_PT = 6.0         # quanto a caixa do rotulo cresce para pegar a mancha
SOBREPOSICAO_MIN = 50    # px de encontro caixa x mancha para valer semente
ENCOSTO_MIN = 250        # abaixo disto o rotulo so raspa a mancha: e palpite
AREA_MIN_M2 = 25.0       # abaixo disto a medida e suspeita
RAZAO_MAX = 8.0          # comprido/estreito demais e suspeito
PREENCHIMENTO_MIN = 0.30 # mancha que ocupa pouco do proprio retangulo = vazada
FORA_E_ROTULO_M2 = 20.0  # sobra fora da caixa do rotulo: abaixo disto E a palavra
FORA_DUVIDOSO_M2 = 60.0  # entre os dois, mede-se algo, mas nao se constroi
DENS_JANELA = 31         # px, janela da densidade de traco (recusada, ver abaixo)
DENS_TAU = 0.12

# Categorias que este extrator nao mede, e nao e limitacao dele: Talude, Bosque,
# Mata Nativa, Trilha e as ruas nao sao edificacao e nao tem footprint no
# desenho. Talude ja e geometria em `terreno.PATAMARES`, vegetacao e o passo 3
# do ESTADO, e o tracado das vias sai do bitmap em outro caminho. Sem esta
# lista, "Talude Talude" apareceu medindo 23,4 x 12,3 m -- que e um estande
# vizinho que o rotulo alcancou.
FORA_DO_ALCANCE = {"paisagem", "vias"}


# --------------------------------------------------------------------------
# Prancha

def renderizar(pdf=PDF, escala=PX_POR_PT):
    doc = pymupdf.open(str(pdf))
    pag = doc[0]
    pix = pag.get_pixmap(matrix=pymupdf.Matrix(escala, escala))
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.n == 4:
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
    else:
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    return img, pag.rect.width, pag.rect.height


def spans_de_texto(pdf=PDF):
    """Caixa de cada pedaco de texto da prancha, em PONTOS de PDF.

    Vem do PDF e nao de OCR nem de heuristica de cor. O centro de cada caixa
    bate com o (x,y) das zonas do mapa -- foi assim que as zonas nasceram.
    """
    doc = pymupdf.open(str(pdf))
    d = doc[0].get_text("dict")
    return [s for b in d["blocks"] if b["type"] == 0
            for l in b["lines"] for s in l["spans"]]


def mascara_texto(spans, escala, forma, folga_px=2):
    m = np.zeros(forma, np.uint8)
    for s in spans:
        x0, y0, x1, y1 = s["bbox"]
        cv2.rectangle(m,
                      (int(x0 * escala) - folga_px, int(y0 * escala) - folga_px),
                      (int(x1 * escala) + folga_px, int(y1 * escala) + folga_px),
                      255, -1)
    return m


# --------------------------------------------------------------------------
# Mascaras de area construida

def mascara_edificacao(img):
    """Cinza de EDIFICACOES: saturacao baixa e luminosidade media.

    O branco do fundo fica de fora por cima e o traco preto por baixo. Cortar
    por saturacao antes e o que separa o cinza tecnico do estande pintado --
    a mesma licao que o extrator de vias ja tinha aprendido.

    Atencao ao que ela de fato pega: o PREENCHIMENTO dos predios e 247/248, ou
    seja, esta ACIMA da faixa. O que entra na mascara e o HACHURADO de dentro,
    e o fechamento junta o resto. Por isso ela depende da densidade da hachura
    -- e por isso a grade das MANGUEIRAS escapa dela.
    """
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    m = cv2.inRange(hsv, (0, 0, 120), (180, 45, 242))
    nucleo = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, nucleo)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, nucleo)
    return m


def mascara_fill_colorido(img):
    """Segunda classe de fill: os blocos pintados, nao cinzas.

    O bloco do Mercado do Produtor / Cafe Colonial / Cozinha Didatica e laranja
    (S de 77 a 106) e o v1 o descartava junto com o rosa dos estandes. Sem esta
    classe, quatro zonas do norte nunca teriam mancha nenhuma.
    """
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    m = cv2.inRange(hsv, (0, 50, 150), (180, 255, 255))
    nucleo = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, nucleo)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, nucleo)
    return m


def preencher(mascara):
    """Fecha a mancha no contorno externo dela.

    A mascara e HACHURA, e isso tem uma consequencia que so apareceu ao olhar a
    particao desenhada: repartir a mancha crua repartia as LISTRAS. As celulas
    do watershed saiam como faixas diagonais atravessando o bloco inteiro, e o
    `minAreaRect` de um punhado de listras devolve um retangulo girado -- era
    dai que vinham rumos de 138° num predio que corre a 108°.

    Preenchendo o contorno externo, o que se mede e o poligono desenhado, que e
    o que se queria desde o inicio.
    """
    cont, _ = cv2.findContours(mascara, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cheio = np.zeros_like(mascara)
    cv2.drawContours(cheio, cont, -1, 255, -1)
    return cheio


def manchas(img):
    """Componentes da area construida: hachura cinza + fill colorido.

    **Sem cortar o texto, e o motivo vale ficar escrito**, porque foram duas
    tentativas erradas antes de chegar aqui. O rotulo e desenhado POR CIMA do
    predio que ele nomeia. Tirar a caixa de texto da mascara parece limpeza --
    e corta o predio ao meio: o PAVILHAO - GADO CORTE, cotado em 720 m², caiu
    para 251. Costurar o buraco de volta por watershed tambem nao resolve,
    porque as duas metades ja nasceram como componentes diferentes e o buraco
    so se reparte entre elas (358 m², -50%).

    A licao: **o texto nao e o que cola predio vizinho neste desenho.** O bloco
    do norte e continuo no proprio desenho -- ele foi conferido no recorte, nao
    deduzido. Quem separa comodo la dentro e a parede interna, e quem trata
    disso e `repartir()`, depois, por mancha e com os rotulos como marcadores.

    O texto continua servindo para duas coisas: marcar onde semear, e sair do
    calculo de densidade em `mascara_densidade` -- la a letra ATRAPALHA, porque
    letra e traco denso e vira mancha sozinha.
    """
    fill = cv2.bitwise_or(mascara_edificacao(img), mascara_fill_colorido(img))
    n, rotulacao, _, _ = cv2.connectedComponentsWithStats(fill, 8)
    # cada componente vira o proprio poligono cheio -- ver `preencher`
    rot = np.zeros_like(rotulacao)
    for i in range(1, n):
        cheio = preencher((rotulacao == i).astype(np.uint8) * 255)
        rot[cheio > 0] = i
    return rot, n, fill


def mascara_densidade(img, texto, janela=DENS_JANELA, tau=DENS_TAU):
    """Regiao por DENSIDADE de traco. RECUSADA -- fora do caminho de decisao.

    A ideia era pegar o que e desenhado vazado, como a grade de currais das
    MANGUEIRAS, que a mascara de fill reduz a um filete de 25 m². Nao funciona,
    e os numeros estao aqui para ninguem tentar de novo:

      janela 31 tau 0.04 -> 6.899 m²      janela 51 tau 0.04 -> 35.557 m²
      janela 31 tau 0.08 -> 3.782 m²      janela 71 tau 0.04 -> 49.916 m²

    e a densidade DENTRO do PAVILHAO - GADO CORTE, que a planta cota em 720 m²,
    da 0,000 -- porque o preenchimento do predio nao e traco, e 247 liso.

    Fica no arquivo porque o teste custou uma rodada e o resultado negativo e
    informacao. Nao chame no caminho de medida.
    """
    cinza = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    tinta = (((cinza < 235) | (hsv[:, :, 1] > 40)) & (texto == 0)).astype(np.float32)
    dens = cv2.boxFilter(tinta, -1, (janela, janela), normalize=True)
    m = (dens > tau).astype(np.uint8) * 255
    return cv2.morphologyEx(m, cv2.MORPH_CLOSE,
                            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))


# --------------------------------------------------------------------------
# Zonas: juntar fragmento de rotulo

def _caixa_do_rotulo(z, spans, tol=1.5):
    """Caixa de texto do span que deu origem a esta zona, em pt."""
    melhor, dmelhor = None, float("inf")
    for s in spans:
        x0, y0, x1, y1 = s["bbox"]
        cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        d = math.hypot(cx - z["x"], cy - z["y"])
        if d < dmelhor:
            melhor, dmelhor = (x0, y0, x1, y1), d
    if melhor is None or dmelhor > tol:
        # sem span correspondente: caixa sintetica minima em volta da ancora
        return (z["x"] - 3, z["y"] - 3, z["x"] + 3, z["y"] + 3), False
    return melhor, True


def agrupar_fragmentos(zonas, spans, limite=FRAGMENTO_PT):
    """Linhas do mesmo nome viram uma zona so.

    A planta quebra nome comprido em duas ou tres linhas, e o extrator do mapa
    gravou cada linha como uma zona. Sem juntar, o watershed reparte um predio
    entre "Praca de Alimentacao" e "Coberta" -- que sao a mesma coisa.

    Regra conservadora: mesma categoria e menos de `limite` pt (6,7 m) de
    distancia. BANHEIROS FEM./MASC. ficam a 13,3 pt e continuam separados de
    proposito -- sao dois blocos no desenho.
    """
    itens = []
    for z in zonas:
        caixa, achou = _caixa_do_rotulo(z, spans)
        itens.append({"zona": z, "caixa": caixa, "span": achou})

    pai = list(range(len(itens)))

    def raiz(i):
        while pai[i] != i:
            pai[i] = pai[pai[i]]
            i = pai[i]
        return i

    for i in range(len(itens)):
        for j in range(i + 1, len(itens)):
            a, b = itens[i]["zona"], itens[j]["zona"]
            if a["categoria"] != b["categoria"]:
                continue
            if math.hypot(a["x"] - b["x"], a["y"] - b["y"]) <= limite:
                pai[raiz(i)] = raiz(j)

    grupos = {}
    for i, it in enumerate(itens):
        grupos.setdefault(raiz(i), []).append(it)

    zonas_juntas = []
    for membros in grupos.values():
        membros.sort(key=lambda m: (round(m["zona"]["y"], 1), m["zona"]["x"]))
        rotulos = [m["zona"]["rotulo"] for m in membros]
        caixas = [m["caixa"] for m in membros]
        zonas_juntas.append({
            "rotulo": " ".join(rotulos),
            "rotulos": rotulos,
            "categoria": membros[0]["zona"]["categoria"],
            "x": sum(m["zona"]["x"] for m in membros) / len(membros),
            "y": sum(m["zona"]["y"] for m in membros) / len(membros),
            "caixa": (min(c[0] for c in caixas), min(c[1] for c in caixas),
                      max(c[2] for c in caixas), max(c[3] for c in caixas)),
            "com_span": all(m["span"] for m in membros),
        })
    zonas_juntas.sort(key=lambda z: (z["categoria"], z["rotulo"]))
    return zonas_juntas


# --------------------------------------------------------------------------
# Semear pela caixa e medir

def _retangulo_px(caixa, escala, cresce_px, forma):
    x0, y0, x1, y1 = caixa
    a = max(0, int(x0 * escala) - cresce_px)
    b = max(0, int(y0 * escala) - cresce_px)
    c = min(forma[1], int(x1 * escala) + cresce_px + 1)
    d = min(forma[0], int(y1 * escala) + cresce_px + 1)
    return a, b, c, d


def semear(rot, caixa, escala, forma, cresce_max_px, passo_px):
    """Componente de maior encontro com a caixa do rotulo, crescendo aos poucos.

    Devolve (id, sobreposicao_px, cresceu_px) ou (0,0,0). Crescer aos poucos e o
    que impede o "casou com mancha a 172 px": a mancha vizinha so entra na
    conta depois que a de baixo do rotulo ja nao existe.
    """
    cresce = int(SEMENTE_PT * escala)
    while cresce <= cresce_max_px:
        a, b, c, d = _retangulo_px(caixa, escala, cresce, forma)
        janela = rot[b:d, a:c]
        if janela.size:
            contas = np.bincount(janela.ravel())
            if len(contas) > 1:
                contas[0] = 0
                i = int(contas.argmax())
                if contas[i] >= SOBREPOSICAO_MIN:
                    return i, int(contas[i]), cresce
        cresce += passo_px
    return 0, 0, 0


def medir_pontos(xs, ys, escala, escala_m):
    """largura, profundidade, rumo, area e preenchimento de um conjunto de px."""
    pts = np.column_stack([xs, ys]).astype(np.float32)
    caixa = cv2.minAreaRect(pts)
    (_, _), (w, h), _ang = caixa
    if w < h:
        w, h = h, w

    # O RUMO SAI DOS CANTOS, nao do angulo do minAreaRect.
    #
    # A versao anterior convertia `ang` por formula, e a formula pressupunha a
    # convencao antiga do OpenCV (angulo em [-90,0)). O cv2 5.0 devolve [0,90),
    # e o resultado saia ESPELHADO em 90 graus: um predio a 70 era gravado como
    # 110, um a 108 como 72. Provado com retangulo sintetico de rumo conhecido
    # -- 70->110, 108->72, 20->160, e 90 e 0 passando porque sao os dois pontos
    # fixos do espelho, que e' o que fazia o erro parecer inexistente.
    #
    # Foi isto que deixou os seis pavilhoes de animais girados ~37 graus na
    # cena, cruzando os retangulos desenhados. Tres fontes concordam com o valor
    # novo: a medicao por Hough direto no bitmap (71,5), a perpendicular da
    # fileira dos centros (70,3) e a sobreposicao.
    #
    # Medir pelos cantos nao depende de convencao nenhuma e sobrevive a proxima
    # troca de versao -- que ja mordeu este projeto uma vez (armadilha 10).
    cantos = cv2.boxPoints(caixa)
    lados = [(cantos[(i + 1) % 4] - cantos[i]) for i in range(4)]
    dx, dy = max(lados, key=lambda v: float(np.hypot(v[0], v[1])))
    # y do raster cresce para BAIXO; azimute cresce de norte para leste
    rumo = math.degrees(math.atan2(float(dx), float(-dy))) % 180.0

    npx = float(len(xs))
    return {
        "largura_m": round(w / escala * escala_m, 2),
        "profundidade_m": round(h / escala * escala_m, 2),
        "area_m2": round(npx / (escala ** 2) * escala_m ** 2, 1),
        "rumo_graus": round(rumo, 1),
        "preenchimento": round(npx / max(w * h, 1.0), 3),
    }


def area_fora_do_rotulo(xs, ys, caixa, escala, forma, escala_m):
    """Quanto da mancha sobra FORA da caixa de texto do rotulo, em m².

    Este e o teste que sustenta o resto, e ele so ficou obvio depois de medir:
    a mascara de edificacao inclui a tinta da propria letra (o cinza
    antisserrilhado da fonte cai na faixa V 120..242, e o preenchimento do
    predio, 247, nao cai). Entao para metade das zonas a "mancha" achada e a
    palavra escrita no mapa -- e foi isso que o v1 mediu e chamou de footprint.

    Usar so a fracao dentro da caixa nao serve: `PAVILHAO - NUCLEO CARRA
    BRANCA` e um nome comprido sobre um predio pequeno, e 65% da mancha real
    cai dentro da caixa. O que separa e a area ABSOLUTA que sobra fora --
    letra nao deixa sobra, predio deixa.
    """
    a, b, c, d = _retangulo_px(caixa, escala, 2, forma)
    fora = ~((xs >= a) & (xs < c) & (ys >= b) & (ys < d))
    return round(int(fora.sum()) / (escala ** 2) * escala_m ** 2, 1)


def suspeitas(m, fora_m2=None):
    """Sinais de que a medida nao vale. Vazio = medida plausivel."""
    s = []
    if fora_m2 is not None:
        if fora_m2 < FORA_E_ROTULO_M2:
            s.append("a mancha e a propria palavra")
        elif fora_m2 < FORA_DUVIDOSO_M2:
            s.append("quase toda a mancha e a palavra")
    if m["area_m2"] < AREA_MIN_M2:
        s.append("area minuscula")
    if m["profundidade_m"] > 0 and m["largura_m"] / m["profundidade_m"] > RAZAO_MAX:
        s.append("filete")
    if m["preenchimento"] < PREENCHIMENTO_MIN:
        s.append("mancha vazada")
    return s


# --------------------------------------------------------------------------
# Bloco fundido: watershed com os rotulos como marcadores

def repartir(img, rot, comp, membros, escala):
    """Reparte UMA mancha entre as zonas que caem dentro dela.

    O relevo e o proprio desenho: onde ha parede interna, a linha escura e uma
    crista e o corte cai nela; onde nao ha, a divisa fica no meio do caminho
    entre os rotulos. Isso e melhor que Voronoi puro, que ignora o desenho, e
    honesto quando o desenho nao diz nada.

    Devolve {indice_do_membro: (xs, ys)}.
    """
    mancha = (rot == comp).astype(np.uint8)
    ys, xs = np.nonzero(mancha)
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    sub = img[y0:y1, x0:x1]
    submancha = mancha[y0:y1, x0:x1]

    marcadores = np.zeros(submancha.shape, np.int32)
    marcadores[submancha == 0] = 1                     # fundo: fora da mancha
    for k, (idx, z) in enumerate(membros, start=2):
        a, b, c, d = _retangulo_px(z["caixa"], escala, 1, img.shape[:2])
        a, b = max(a - x0, 0), max(b - y0, 0)
        c, d = min(c - x0, submancha.shape[1]), min(d - y0, submancha.shape[0])
        if c > a and d > b:
            marcadores[b:d, a:c] = k

    cv2.watershed(np.ascontiguousarray(sub), marcadores)

    saida = {}
    for k, (idx, _z) in enumerate(membros, start=2):
        yy, xx = np.nonzero((marcadores == k) & (submancha > 0))
        if len(xx):
            saida[idx] = (xx + x0, yy + y0)
    return saida


# --------------------------------------------------------------------------
# v2

def extrair_v2(img, larg_pt, mapa, spans, raio_pt, escala_m, diagnostico=False):
    escala = img.shape[1] / larg_pt
    forma = img.shape[:2]

    texto = mascara_texto(spans, escala, forma)
    rot, n, fill = manchas(img)
    zonas = agrupar_fragmentos([z for z in mapa["zonas"] if z["categoria"] != "legenda"],
                               spans)

    cresce_max = int(raio_pt * escala)
    passo = max(2, int(2 * escala))

    # 1a passada: cada zona pega sua mancha, e a mancha que e a PROPRIA PALAVRA
    # sai do caminho aqui -- se ela seguisse, disputaria bloco com predio de
    # verdade e o watershed repartiria area real para um rotulo que nao tem
    # desenho nenhum embaixo.
    donos, sem_mancha, so_rotulo = {}, [], {}
    for i, z in enumerate(zonas):
        if z["categoria"] in FORA_DO_ALCANCE:
            continue
        comp, sobrep, cresceu = semear(rot, z["caixa"], escala, forma, cresce_max, passo)
        if comp == 0:
            sem_mancha.append(i)
            continue
        yy, xx = np.nonzero(rot == comp)
        fora = area_fora_do_rotulo(xx, yy, z["caixa"], escala, forma, escala_m)
        if fora < FORA_E_ROTULO_M2:
            so_rotulo[i] = fora
            continue
        donos[i] = {"comp": comp, "sobreposicao": sobrep, "cresceu_px": cresceu,
                    "fora_m2": fora}

    # 2a passada: manchas disputadas viram watershed
    por_comp = {}
    for i, d in donos.items():
        por_comp.setdefault(d["comp"], []).append(i)

    pixels, particao, rumo_bloco = {}, {}, {}
    for comp, idxs in por_comp.items():
        if len(idxs) == 1:
            i = idxs[0]
            yy, xx = np.nonzero(rot == comp)
            pixels[i] = (xx, yy)
            particao[i] = "inteira"
        else:
            membros = [(i, zonas[i]) for i in idxs]
            # o rumo de uma FATIA nao vale nada: a celula do watershed tem
            # contorno irregular e o minAreaRect gira com ela. Quem tem rumo e
            # o bloco -- comodo de fita segue a orientacao do predio.
            yy, xx = np.nonzero(rot == comp)
            r = medir_pontos(xx, yy, escala, escala_m)["rumo_graus"]
            fatias = repartir(img, rot, comp, membros, escala)
            for i in idxs:
                if i in fatias:
                    pixels[i] = fatias[i]
                    particao[i] = "watershed"
                    rumo_bloco[i] = r
                else:
                    sem_mancha.append(i)

    # 3a passada: medida
    saida = []
    for i, z in enumerate(zonas):
        registro = {
            "rotulo": z["rotulo"],
            "rotulos": z["rotulos"],
            "categoria": z["categoria"],
            "x_pt": round(z["x"], 2),
            "y_pt": round(z["y"], 2),
        }
        if z["categoria"] in FORA_DO_ALCANCE:
            registro.update({
                "metodo": "fora do alcance",
                "confianca": "nenhuma",
                "suspeitas": ["categoria sem edificacao: nao se mede footprint "
                              "de talude, bosque, trilha ou rua neste desenho"],
            })
            saida.append(registro)
            continue
        if i in so_rotulo:
            registro.update({
                "metodo": "so o rotulo",
                "confianca": "nenhuma",
                "area_fora_do_rotulo_m2": so_rotulo[i],
                "suspeitas": ["a unica mancha sob o rotulo e a tinta da propria "
                              "palavra: esta zona nao tem footprint desenhado"],
            })
            saida.append(registro)
            continue
        if i not in pixels:
            registro.update({"metodo": "sem mancha", "confianca": "nenhuma",
                             "suspeitas": ["nenhuma mancha encontrada"]})
            saida.append(registro)
            continue

        xs, ys = pixels[i]
        m = medir_pontos(xs, ys, escala, escala_m)
        d = donos.get(i, {})
        fora = area_fora_do_rotulo(xs, ys, z["caixa"], escala, forma, escala_m)
        sus = suspeitas(m, fora)
        # Associacao a distancia: com o rotulo em cima do que ele nomeia, a
        # mancha aparece ja no primeiro passo de busca. Das 19 aceitas, 18 tem
        # busca de 6 pt e encosto de 343 px ou mais; a excecao foi um `Bar` que
        # cresceu ate 14 pt e encostou em 96 px para abocanhar uma mancha de
        # 893 m² -- que nao e um bar.
        if d.get("cresceu_px", 0) > SEMENTE_PT * escala:
            sus.append("o rotulo nao encosta na mancha")
        elif d.get("sobreposicao", 0) < ENCOSTO_MIN:
            sus.append("encosto minimo entre rotulo e mancha")

        registro.update(m)
        registro.update({
            "metodo": "fill",
            "particao": particao.get(i, "inteira"),
            "sobreposicao_px": d.get("sobreposicao", 0),
            "busca_px": d.get("cresceu_px", 0),
            "area_fora_do_rotulo_m2": fora,
            "rumo_do_bloco": rumo_bloco.get(i),
            "rumo_confiavel": i not in rumo_bloco,
            "suspeitas": sus,
            "confianca": "baixa" if sus else (
                "media" if particao.get(i) == "watershed"
                or d.get("cresceu_px", 0) > SEMENTE_PT * escala * 2 else "alta"),
            "fonte": "medido do desenho da prancha, nao cotado em texto",
        })
        saida.append(registro)

    if diagnostico:
        print(f"\nzonas apos juntar fragmento: {len(zonas)} "
              f"(de {len([z for z in mapa['zonas'] if z['categoria'] != 'legenda'])} rotulos)")
        juntadas = [z for z in zonas if len(z["rotulos"]) > 1]
        print(f"nomes remontados: {len(juntadas)}")
        for z in juntadas:
            print(f"   {' + '.join(z['rotulos'])}")
        disputadas = {c: v for c, v in por_comp.items() if len(v) > 1}
        print(f"\nmanchas disputadas (repartidas por watershed): {len(disputadas)}")
        for c, idxs in disputadas.items():
            print(f"   mancha #{c}: " + " | ".join(zonas[i]["rotulo"][:28] for i in idxs))

    return saida, fill, texto


# --------------------------------------------------------------------------
# v1, preservado

def medir(mascara, px, py, raio_busca_px):
    """v1: mancha que contem (px,py), ou a mais proxima dentro do raio."""
    n, rot, stats, cent = cv2.connectedComponentsWithStats(mascara, 8)
    if n < 2:
        return None

    alvo = None
    if 0 <= int(py) < rot.shape[0] and 0 <= int(px) < rot.shape[1]:
        i = int(rot[int(py), int(px)])
        if i > 0:
            alvo, dist = i, 0.0

    if alvo is None:
        melhor, dmelhor = None, float("inf")
        for i in range(1, n):
            if stats[i, cv2.CC_STAT_AREA] < 400:
                continue
            d = math.hypot(cent[i][0] - px, cent[i][1] - py)
            if d < dmelhor:
                melhor, dmelhor = i, d
        if melhor is None or dmelhor > raio_busca_px:
            return None
        alvo, dist = melhor, dmelhor

    ys, xs = np.nonzero(rot == alvo)
    pts = np.column_stack([xs, ys]).astype(np.float32)
    (_, _), (w, h), ang = cv2.minAreaRect(pts)
    if w < h:
        w, h = h, w
        ang += 90.0
    return w, h, ang, float(len(xs)), dist


def extrair_v1(img, larg_pt, mapa, raio_pt, escala_m):
    escala = img.shape[1] / larg_pt
    masc = mascara_edificacao(img)
    saida = []
    for z in mapa["zonas"]:
        if z["categoria"] == "legenda":
            continue
        r = medir(masc, z["x"] * escala, z["y"] * escala, raio_pt * escala)
        if r is None:
            saida.append({"rotulo": z["rotulo"], "categoria": z["categoria"],
                          "metodo": "sem mancha"})
            continue
        w_px, h_px, ang, area_px, dist = r
        rumo = math.degrees(math.atan2(math.cos(math.radians(-ang)),
                                       -math.sin(math.radians(-ang)))) % 180.0
        saida.append({
            "rotulo": z["rotulo"],
            "categoria": z["categoria"],
            "largura_m": round(w_px / escala * escala_m, 2),
            "profundidade_m": round(h_px / escala * escala_m, 2),
            "area_m2": round(area_px / (escala ** 2) * escala_m ** 2, 1),
            "rumo_graus": round(rumo, 1),
            "dist_do_rotulo_px": round(dist, 1),
            "metodo": "hachura",
            "fonte": "medido do desenho da prancha, nao cotado em texto",
        })
    return saida, masc


# --------------------------------------------------------------------------

def cotas_do_pdf(spans, raio_pt=8.0):
    """As areas que a planta ESCREVE, casadas com o rotulo que elas cotam.

    Antes isto era uma tabela digitada a mao, e a tabela estava errada: dizia
    560 m² para o `PAVILHAO - PEQUENOS ANIMAIS` porque o teste original era
    `"EQU" in rotulo`, e **PEQUENOS contem EQU**. A planta escreve 720,00 m² ali,
    a 5,2 pt do rotulo. Um pavilhao inteiro ficou 28% menor por causa de um
    casamento de substring.

    Agora a cota vem do PDF: cada span no formato `720,00 m²` vai para o rotulo
    mais proximo. E a unica cota em texto que existe fora dos estandes, e e a
    regua contra a qual o desenho medido se confere.
    """
    numeros, rotulos = [], []
    for s in spans:
        t = s["text"].strip()
        b = s["bbox"]
        centro = ((b[0] + b[2]) / 2.0, (b[1] + b[3]) / 2.0)
        if t.endswith("m²") and any(c.isdigit() for c in t):
            try:
                numeros.append((float(t[:-2].strip().replace(".", "").replace(",", ".")),
                                centro))
            except ValueError:
                pass
        elif t:
            rotulos.append((t, centro))

    cotas = {}
    for valor, (nx, ny) in numeros:
        melhor, dmelhor = None, float("inf")
        for t, (rx, ry) in rotulos:
            d = math.hypot(rx - nx, ry - ny)
            if d < dmelhor:
                melhor, dmelhor = t, d
        if melhor is not None and dmelhor <= raio_pt:
            cotas[melhor] = valor
    return cotas


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pdf", default=str(PDF))
    ap.add_argument("--metodo", choices=["v2", "hachura"], default="v2")
    ap.add_argument("--raio", type=float, default=45.0,
                    help="raio maximo de busca em PONTOS de PDF")
    ap.add_argument("--fragmento", type=float, default=FRAGMENTO_PT,
                    help="distancia em pt para juntar linha do mesmo rotulo")
    ap.add_argument("--diagnostico", action="store_true")
    ap.add_argument("--debug")
    ap.add_argument("--saida", default="data/footprints.json")
    args = ap.parse_args()

    sys.path.insert(0, str(RAIZ / "scripts"))
    import terreno

    img, larg_pt, alt_pt = renderizar(Path(args.pdf))
    escala = img.shape[1] / larg_pt
    print(f"prancha {larg_pt:.0f}x{alt_pt:.0f} pt -> {img.shape[1]}x{img.shape[0]} px "
          f"({escala:.2f} px/pt)   metodo {args.metodo}")

    mapa = json.loads((RAIZ / "data" / "mapa_agroshow26.json").read_text(encoding="utf-8"))
    spans = spans_de_texto(Path(args.pdf))
    cotas = cotas_do_pdf(spans)
    print(f"spans de texto no PDF: {len(spans)}   cotas em texto: {len(cotas)}")

    if args.metodo == "v2":
        globals()["FRAGMENTO_PT"] = args.fragmento
        itens, masc, texto = extrair_v2(img, larg_pt, mapa, spans, args.raio,
                                        terreno.ESCALA, args.diagnostico)
    else:
        itens, masc = extrair_v1(img, larg_pt, mapa, args.raio, terreno.ESCALA)
        texto = None

    # a cota da planta entra em cada item: e a unica medida declarada por quem
    # desenhou, e vale mais que o pixel para AREA. Ver a conferencia abaixo.
    for it in itens:
        for nome in it.get("rotulos", [it["rotulo"]]):
            if nome in cotas:
                it["area_cotada_m2"] = cotas[nome]
                break

    perdidos = [i for i in itens if i.get("metodo") == "sem mancha"]
    rotulo_so = [i for i in itens if i.get("metodo") == "so o rotulo"]
    medidos = [i for i in itens if i.get("metodo") in ("fill", "hachura")]
    baixa = [i for i in medidos if i.get("confianca") == "baixa"]
    servem = [i for i in medidos if i.get("confianca") in ("alta", "media")]

    alvo = RAIZ / args.saida
    alvo.write_text(json.dumps({
        "aviso": ("MEDIDO DO DESENHO, nao de cota. A planta so cota area dos "
                  "pavilhoes de animais e dos estandes. Confira antes de tratar "
                  "como dado. Item com confianca 'baixa' nao vai para geometria "
                  "sem olhar o desenho."),
        "metodo": args.metodo,
        "escala_m_por_pt": terreno.ESCALA,
        "px_por_pt": round(escala, 3),
        "itens": itens,
    }, indent=1, ensure_ascii=False), encoding="utf-8")

    if args.metodo == "v2":
        print(f"\nzonas: {len(itens)}")
        print(f"  com footprint que serve  : {len(servem)}")
        print(f"  medido mas duvidoso      : {len(baixa)}")
        print(f"  so o rotulo (sem desenho): {len(rotulo_so)}")
        print(f"  fora do alcance          : "
              f"{len([i for i in itens if i.get('metodo') == 'fora do alcance'])}")
        print(f"  sem mancha nenhuma       : {len(perdidos)}")
    else:
        print(f"\nmedidos: {len(medidos)}   sem mancha: {len(perdidos)}")
    print(f"gravado: {alvo}\n")

    print("CONFERENCIA contra as cotas em texto (lidas do PDF):")
    for it in itens:
        if "area_cotada_m2" in it and "area_m2" in it:
            esperado = it["area_cotada_m2"]
            erro = (it["area_m2"] - esperado) / esperado * 100
            print(f"  {it['rotulo'][:32]:34s} medido {it['area_m2']:7.1f} m2  "
                  f"cotado {esperado:.0f}  erro {erro:+.0f}%  "
                  f"{it['largura_m']:.1f} x {it['profundidade_m']:.1f} m  "
                  f"rumo {it['rumo_graus']:.0f}")

    if args.metodo == "v2" and args.diagnostico:
        print("\nZONAS DE INTERESSE (as que o RETOMAR nomeia):")
        for it in itens:
            r = it["rotulo"].upper()
            if any(k in r for k in ("MANGUEIRA", "PAVILHÃO 1", "PAVILHÃO 2", "PAVILHÃO 3",
                                    "PRAÇA", "SAGUÃO", "LEILÕES", "AUDITÓRIO",
                                    "MERCADO", "ALIMENTAÇÃO")):
                if "area_m2" in it:
                    print(f"  {it['rotulo'][:40]:42s} {it['largura_m']:6.1f} x "
                          f"{it['profundidade_m']:5.1f} m  {it['area_m2']:8.1f} m2  "
                          f"{it['metodo']:10s} {it['particao']:10s} {it['confianca']:6s} "
                          + (";".join(it["suspeitas"]) if it["suspeitas"] else ""))
                else:
                    print(f"  {it['rotulo'][:40]:42s} SEM MANCHA")

    if args.metodo == "v2":
        print(f"\nFOOTPRINT QUE SERVE ({len(servem)}) -- so estes viram geometria:")
        for it in sorted(servem, key=lambda i: -i["area_m2"]):
            rumo = (f"rumo {it['rumo_graus']:5.1f}" if it["rumo_confiavel"]
                    else f"rumo {it['rumo_do_bloco']:5.1f} (do bloco)")
            print(f"  {it['rotulo'][:38]:40s} {it['largura_m']:6.1f} x "
                  f"{it['profundidade_m']:5.1f} m  {it['area_m2']:8.1f} m2  "
                  f"{rumo:20s} {it['particao']:10s} {it['confianca']}")

        print(f"\nSEM FOOTPRINT NO DESENHO ({len(rotulo_so) + len(perdidos)}) -- "
              "estas zonas precisam de decisao, nao de mais processamento:")
        for it in rotulo_so + perdidos:
            print(f"  {it['rotulo'][:44]:46s} {it['categoria']}")

    if baixa:
        print(f"\nMEDIDO MAS DUVIDOSO ({len(baixa)}) -- nao construir sem olhar:")
        for it in baixa:
            print(f"  {it['rotulo'][:38]:40s} {it['area_m2']:8.1f} m2  "
                  f"{'; '.join(it['suspeitas'])}")

    if args.debug:
        vis = img.copy()
        vis[masc > 0] = (0.5 * vis[masc > 0] + 0.5 * np.array([0, 0, 255])).astype(np.uint8)
        if texto is not None:
            vis[texto > 0] = (0.7 * vis[texto > 0] + 0.3 * np.array([0, 255, 0])).astype(np.uint8)
        cv2.imwrite(str(RAIZ / args.debug), vis)
        print(f"\ndebug: {args.debug}")


if __name__ == "__main__":
    main()
