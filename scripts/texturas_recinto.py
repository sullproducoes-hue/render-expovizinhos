#!/usr/bin/env python3
"""Mapas PBR DEILUMINADOS a partir das provas de material do PROPRIO recinto.

Este script substitui, classe por classe, as texturas CC0 de biblioteca por
recorte do footage do Parque de Exposicoes de Dois Vizinhos. O que muda nao e
gosto: e PROCEDENCIA. Uma grama da Africa do Sul e um ferro enferrujado da
Europa trazem a sombra, o sol e o balanco de branco de outro lugar; o recorte
do recinto traz os do recinto.

O pipeline nao se negocia, e a ordem dele e a razao de ele funcionar:

  1. RECORTE plano e frontal da imagem;
  2. RETIFICACAO -- chao visto em obliquo esta comprimido na vertical. A
     compressao e MEDIDA na propria imagem (razao entre a energia do gradiente
     vertical e a do horizontal), nao arbitrada: textura de chao e isotropica,
     entao gradiente que sobra num eixo e perspectiva, nao material;
  3. DEILUMINACAO -- divide pela propria versao desfocada (gaussiana com sigma
     = 1/8 do menor lado). Sombra assada na textura e o que mais denuncia 3D:
     a mesma parede fica escura no sol e clara na sombra, e nenhuma luz de
     render conserta isso porque a sombra ja esta pintada;
  4. TILEAVEL -- costura por cross-fade das bandas opostas. Recorta-se uma
     imagem de lado N+f e devolve-se N, com a faixa de f pixels da esquerda
     misturada com a da direita. A coluna 0 da saida passa a ser a continuacao
     da coluna N-1, que e a definicao de tileavel;
  5. Os mapas.

O que sai, por material:

  <slug>_Diffuse_2k.jpg   VARIACAO DE LUMINANCIA, **neutra**. E o que
                          scripts/texturas.py:aplicar() consome. Neutra de
                          proposito: o no do Blender multiplica a cor medida
                          por este mapa, e um mapa colorido multiplicaria a
                          cor DUAS vezes -- com forca 0,3 o desvio medido foi
                          de +10% no vermelho do MAT_ARENA. Mapa neutro deixa
                          a media do multiplicador em 1,0 por canal, que e o
                          que `a_regra_que_nao_se_quebra` promete.
  <slug>_Albedo_2k.jpg    o albedo COLORIDO de verdade, com media linear por
                          canal igual a cor medida em data/materiais-medidos.json.
                          Nao entra no shader; e a PROVA da deiluminacao e a
                          fonte para quem quiser a cor sem passar pelo no.
  <slug>_Rough_2k.jpg     luminancia deiluminada, invertida e comprimida.
  <slug>_nor_gl_2k.jpg    normal from-height, convencao OpenGL.

nor_gl e nao nor_dx: o Blender le OpenGL. DirectX inverte o verde e o relevo
sai com a luz vindo do lado errado -- erro que nao da erro, so fica estranho.

Uso:
    python scripts/texturas_recinto.py            # gera tudo
    python scripts/texturas_recinto.py --so telha # gera um so
    python scripts/texturas_recinto.py --amostra  # so a folha de prova
"""

import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "assets" / "textura"
PROVAS = Path(r"E:\Projetos todos\Mapa - agroshow\Brutos Expo\_triagem\provas-materiais")
FOTO_CLIENTE = Path(r"E:\Projetos todos\Mapa - agroshow\WhatsApp Image 2026-08-12 at 13.15.32.jpeg")
LADO = 2048
FEATHER = 256
TRABALHO = Path(r"F:\trabalho-materiais-1608")


# --------------------------------------------------------------------------
# O contrato deste script: de onde sai cada material, e para que cor ele vai.

RECEITAS = [
    {
        "chave": "madeira",
        "slug": "recinto_madeira_portal",
        "material": "MAT_MADEIRA",
        "origem": "FOTO_CLIENTE",
        "fonte": str(FOTO_CLIENTE),
        # dois panos de tabua da ala direita, um de cada lado da luminaria.
        # Emendar dois campos de tabua VERTICAL na horizontal e legitimo: a
        # emenda cai onde ja cairia uma junta de tabua.
        "recortes": [(1094, 508, 1180, 580), (1256, 522, 1336, 580)],
        "isotropico": False,          # tabua e anisotropica de proposito
        "eixo_vertical": True,
        "estica_y": 1.0,
        "cor_alvo": [0.21, 0.11, 0.055],
        "cor_procedencia": "DECLARADA em scripts/build_scene.py (MAT_MADEIRA). "
                           "NAO ha madeira em data/materiais-medidos.json nem em "
                           "materiais-quinta.json -- o portal nao aparece em "
                           "video nenhum.",
        "lado_m": 2.1,
        "lado_m_como": "contei ~15 tabuas nos dois panos somados (166 px, "
                       "11,1 px por tabua); tabua de fachada de celeiro tem "
                       "~0,14 m. 15 x 0,14 = 2,10 m. E a escala mais confiavel "
                       "do conjunto, porque nao depende de perspectiva: e "
                       "contagem de pecas numa parede frontal.",
        "forca_normal": 0.6,
        "forca_variacao": 0.35,
        "mapas": ["nor_gl", "Rough", "Diffuse"],
    },
    {
        "chave": "telha",
        "slug": "recinto_telha_metalica",
        "material": "MAT_TELHA",
        "origem": "PROVA_RECINTO",
        "pasta": "telha-metalica",
        "quadro": 6,
        "recorte": (880, 90, 1420, 500),
        "isotropico": False,
        "eixo_vertical": True,
        "endireita_ondas": True,      # gira ate a onda ficar vertical
        "cor_alvo": None,             # NAO se mede: ver data/estouro-telhado.json
        "cor_procedencia": "sem albedo por decisao ja registrada -- a medicao "
                           "estourou em 97% dos quadros claros. Fica o cinza "
                           "galvanizado 0,62/0,63/0,64 com metallic 0,55.",
        "onda_m": 0.076,              # chapa ondulada brasileira: onda de 76 mm
        "forca_normal": 1.0,
        "forca_variacao": None,
        "mapas": ["nor_gl", "Rough"],
    },
    {
        "chave": "terra",
        "slug": "recinto_terra_pista",
        "material": "MAT_ARENA",
        "origem": "PROVA_RECINTO",
        "pasta": "terra-pista-arena",
        "quadro": 30,
        "recorte": (900, 1300, 3000, 1950),
        "isotropico": True,
        "cor_alvo": [0.2659, 0.1875, 0.1548],
        "cor_procedencia": "MEDIDA -- data/materiais-medidos.json > terra "
                           "(chao batido da alameda, golden hour).",
        "lado_m": 8.0,
        "lado_m_como": "ESTIMADA. O palco do bosque tem ~12 m de frente e ocupa "
                       "936 px na linha dele; propagando pela perspectiva ate o "
                       "centro do recorte da ~6 mm/px, e o quadrado retificado "
                       "tem ~1300 px. Erro provavel de +-40%.",
        "forca_normal": 0.7,
        "forca_variacao": 0.30,
        "mapas": ["nor_gl", "Rough", "Diffuse"],
    },
    {
        "chave": "brita",
        "slug": "recinto_brita_piso",
        "material": "MAT_SAIBRO",
        "origem": "PROVA_RECINTO",
        "pasta": "brita-piso-asfalto",
        "quadro": 6,
        "recorte": (150, 1560, 2000, 2150),
        "isotropico": True,
        "cor_alvo": [0.1362, 0.0978, 0.0704],
        "cor_procedencia": "MEDIDA -- data/materiais-medidos.json > brita "
                           "(piso solto da area de maquinas).",
        "lado_m": 2.2,
        "lado_m_como": "ESTIMADA pelo tambor de 200 L junto a cerca (0,88 m "
                       "deitado, 220 px), propagado pela perspectiva. Bate com "
                       "os 2,0 m que o contrato ja usava para via de brita.",
        "forca_normal": 0.8,
        "forca_variacao": 0.35,
        "mapas": ["nor_gl", "Rough", "Diffuse"],
    },
    {
        "chave": "grama",
        "slug": "recinto_grama_sa",
        "material": "MAT_TERRENO",
        "origem": "PROVA_RECINTO",
        "pasta": "grama-sa",
        "quadro": 32,
        "recorte": (200, 1500, 1450, 2500),
        "isotropico": True,
        "cor_alvo": [0.1286, 0.1239, 0.0369],
        "cor_procedencia": "MEDIDA -- data/materiais-medidos.json > grama "
                           "(faixa preservada entre a alameda e o bosque).",
        "lado_m": 4.5,
        "lado_m_como": "ESTIMADA pela camiseta das criancas no mesmo quadro "
                       "(~0,36 m em 94 px = 3,8 mm/px), corrigida para a linha "
                       "do recorte. Erro provavel de +-40%.",
        "forca_normal": 0.45,
        "forca_variacao": 0.30,
        "mapas": ["nor_gl", "Rough"],
    },
    {
        "chave": "grama-desgastada",
        "slug": "recinto_grama_desgastada",
        "material": None,             # nao ha material para esta classe hoje
        "origem": "PROVA_RECINTO",
        "pasta": "grama-desgastada",
        "quadro": 20,
        "recorte": (200, 1400, 3600, 2100),
        "isotropico": True,
        "cor_alvo": [0.2775, 0.2351, 0.1078],
        "cor_procedencia": "MEDIDA -- data/materiais-medidos.json > grama_pisada "
                           "(a grama do desgaste, a que deixou a cena com cara "
                           "de deserto quando foi usada chapada).",
        "lado_m": 4.5,
        "lado_m_como": "ESTIMADA, mesma familia do recorte de grama sa.",
        "forca_normal": 0.45,
        "forca_variacao": 0.30,
        "mapas": ["nor_gl", "Rough", "Diffuse"],
    },
    {
        "chave": "concreto",
        "slug": "recinto_concreto_pavilhao",
        "material": "MAT_CONCRETO",
        "origem": "PROVA_RECINTO",
        "pasta": "telha-metalica",
        "quadro": 61,
        "recorte": (1000, 1450, 2800, 2150),
        "isotropico": True,
        "cor_alvo": [0.25, 0.25, 0.25],
        "cor_procedencia": "DECLARADA POR ELE em 15/08 (concreto envelhecido, "
                           "0,25). Nas mangueiras nao ha ceu medivel.",
        "lado_m": 2.0,
        "lado_m_como": "ESTIMADA pelo contentor de 1000 L (1,37 m de frente, "
                       "265 px), propagado pela perspectiva. Erro provavel de "
                       "+-50%: e a estimativa mais fraca do conjunto.",
        "forca_normal": 0.5,
        "forca_variacao": 0.25,
        "mapas": ["nor_gl", "Rough", "Diffuse"],
        "aviso": "NAO veio de arena-lateral-patamares. Aquela pasta nao tem "
                 "concreto nenhum -- ver o relatorio.",
    },
]


# --------------------------------------------------------------------------
# Leitura / escrita

def ler(caminho):
    """cv2.imread nao abre caminho com acento no Windows. Este projeto mora em
    'E:\\I.A Edit' e as provas em 'Projetos todos'; imdecode e o caminho seguro."""
    dados = np.fromfile(str(caminho), dtype=np.uint8)
    img = cv2.imdecode(dados, cv2.IMREAD_COLOR)
    if img is None:
        raise SystemExit(f"nao abriu: {caminho}")
    return img


def gravar(caminho, img8):
    ok, buf = cv2.imencode(".jpg", img8, [cv2.IMWRITE_JPEG_QUALITY, 95])
    if not ok:
        raise SystemExit(f"nao codificou: {caminho}")
    buf.tofile(str(caminho))


def srgb_para_linear(v):
    """A conversao de verdade, com o trecho reto perto do zero. A aproximacao
    v**2.2 erra ate 4% nos tons escuros -- e tom escuro e onde este projeto
    vive: a grama medida tem albedo 0,129."""
    return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)


def linear_para_srgb(v):
    v = np.clip(v, 0.0, 1.0)
    return np.where(v <= 0.0031308, v * 12.92, 1.055 * v ** (1 / 2.4) - 0.055)


def luminancia(lin_bgr):
    """BT.709 sobre canais LINEARES. Luminancia calculada sobre sRGB nao e
    luminancia -- e um numero sem nome."""
    return (0.0722 * lin_bgr[..., 0] + 0.7152 * lin_bgr[..., 1]
            + 0.2126 * lin_bgr[..., 2])


# --------------------------------------------------------------------------
# Os passos

def medir_anisotropia(lin):
    """Quanto o chao esta comprimido na vertical, MEDIDO na propria imagem.

    Textura de chao (brita, terra, grama) e isotropica: no mundo, o gradiente
    nao tem eixo preferido. Se a imagem devolve mais gradiente na vertical do
    que na horizontal, a diferenca e o angulo da camera, nao o material. A
    razao dos desvios-padrao dos gradientes e o fator que devolve a isotropia.
    """
    lum = luminancia(lin).astype(np.float32)
    lum = cv2.GaussianBlur(lum, (0, 0), 1.0)
    gx = cv2.Sobel(lum, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(lum, cv2.CV_32F, 0, 1, ksize=3)
    k = float(gy.std() / max(gx.std(), 1e-9))
    return float(np.clip(k, 1.0, 4.0)), k


def angulo_da_onda(lin):
    """Angulo das ondas da telha, pelo tensor de estrutura.

    A telha e o unico material do conjunto com direcao propria, e ela precisa
    sair vertical no mapa: onda diagonal num tile quadrado nao fecha na costura
    e, pior, entra torta no BOX projection do Blender.
    """
    lum = luminancia(lin).astype(np.float32)
    lum = cv2.GaussianBlur(lum, (0, 0), 1.2)
    gx = cv2.Sobel(lum, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(lum, cv2.CV_32F, 0, 1, ksize=3)
    jxx, jyy, jxy = (gx * gx).mean(), (gy * gy).mean(), (gx * gy).mean()
    # direcao dominante do GRADIENTE; a onda corre perpendicular a ela
    ang = 0.5 * np.arctan2(2 * jxy, jxx - jyy)
    return float(np.degrees(ang))


def _crista_vertical(lin):
    """True se a crista da onda ja esta na vertical.

    Crista vertical => variacao ao longo das COLUNAS e alta e ao longo das
    LINHAS e baixa. Comparar os dois desvios responde sem ambiguidade, e essa
    ambiguidade e real: o tensor de estrutura nao distingue a direcao da onda
    da perpendicular dela.
    """
    lum = luminancia(lin)
    return lum.mean(axis=0).std() > lum.mean(axis=1).std()


def periodo_horizontal(lin):
    """Passo da onda em px, por autocorrelacao da media das colunas."""
    lum = luminancia(lin).astype(np.float64)
    perfil = lum.mean(axis=0)
    perfil = perfil - perfil.mean()
    ac = np.correlate(perfil, perfil, mode="full")[len(perfil) - 1:]
    ac /= ac[0]
    # o primeiro maximo local depois do primeiro cruzamento por zero
    i = 1
    while i < len(ac) and ac[i] > 0:
        i += 1
    melhor, valor = None, -1.0
    for j in range(i, min(len(ac) - 1, 120)):
        if ac[j] > ac[j - 1] and ac[j] >= ac[j + 1] and ac[j] > valor:
            melhor, valor = j, ac[j]
    return melhor, valor


def deiluminar(lin, divisor=8.0):
    """Divide pela propria versao desfocada. Devolve a razao e o campo de luz.

    sigma = menor lado / 8: grande o bastante para nao comer o material (a
    pedra da brita, a tabua da madeira), pequeno o bastante para pegar o
    gradiente de sol e a sombra grande. Esse e o unico numero do passo e ele
    esta escrito no contrato da noite.
    """
    h, w = lin.shape[:2]
    sigma = min(h, w) / divisor
    campo = cv2.GaussianBlur(lin, (0, 0), sigma, borderType=cv2.BORDER_REFLECT)
    campo = np.maximum(campo, 1e-5)
    razao = lin / campo
    return razao, campo


def tilear(img, feather=FEATHER):
    """Costura por cross-fade das bandas opostas.

    Entra uma imagem de lado N+f, sai uma de lado N. A faixa de f px da
    esquerda da saida vira a mistura da faixa esquerda com a faixa que comeca
    na coluna N -- e como a coluna N e vizinha da N-1 na origem, a coluna 0 da
    saida passa a ser a continuacao natural da coluna N-1. Isso e tileavel de
    verdade, e nao espelhamento: espelho deixa simetria, e simetria repetida
    405 vezes num terreno de 800 m le como grade tanto quanto a costura.
    """
    n = img.shape[0] - feather
    saida = img[:n, :n].copy().astype(np.float64)
    a = np.linspace(0.0, 1.0, feather)
    if saida.ndim == 3:
        ax = a[None, :, None]
        ay = a[:, None, None]
    else:
        ax = a[None, :]
        ay = a[:, None]
    saida[:, :feather] = (saida[:, :feather] * ax
                          + img[:n, n:n + feather] * (1 - ax))
    saida[:feather, :] = (saida[:feather, :] * ay
                          + saida_vertical(img, n, feather) * (1 - ay))
    return saida


def saida_vertical(img, n, feather):
    """A faixa de baixo, ja com a costura horizontal aplicada, para a costura
    vertical usar o mesmo criterio."""
    faixa = img[n:n + feather, :n].copy().astype(np.float64)
    a = np.linspace(0.0, 1.0, feather)
    ax = a[None, :, None] if faixa.ndim == 3 else a[None, :]
    faixa[:, :feather] = (faixa[:, :feather] * ax
                          + img[n:n + feather, n:n + feather] * (1 - ax))
    return faixa


def normalizar_percentil(x, lo=2.0, hi=98.0):
    a, b = np.percentile(x, lo), np.percentile(x, hi)
    if b - a < 1e-9:
        return np.zeros_like(x)
    return np.clip((x - a) / (b - a), 0.0, 1.0)


def normal_de_altura(altura, forca=1.0):
    """Normal from-height, convencao OpenGL (nor_gl).

    Conferencia da convencao: acima de uma saliencia, a altura cresce descendo
    as linhas, entao gy > 0; em OpenGL o Y aponta para CIMA na textura, e a
    normal ali tem que apontar para cima -- ny > 0. Logo ny = +gy. Em DirectX
    seria -gy, e o relevo sairia com a luz do lado errado.
    """
    h = cv2.GaussianBlur(altura.astype(np.float32), (0, 0), 1.0)
    gx = cv2.Sobel(h, cv2.CV_32F, 1, 0, ksize=3) * forca
    gy = cv2.Sobel(h, cv2.CV_32F, 0, 1, ksize=3) * forca
    nx, ny, nz = -gx, gy, np.ones_like(gx)
    norma = np.sqrt(nx * nx + ny * ny + nz * nz)
    nx, ny, nz = nx / norma, ny / norma, nz / norma
    rgb = np.stack([nx, ny, nz], axis=-1) * 0.5 + 0.5
    return rgb  # ordem RGB


# --------------------------------------------------------------------------

def quadro_da_receita(r):
    if r["origem"] == "FOTO_CLIENTE":
        return ler(r["fonte"]), Path(r["fonte"]).name
    pasta = PROVAS / r["pasta"]
    arquivos = sorted(pasta.glob("*.jpg"))
    alvo = arquivos[r["quadro"]]
    return ler(alvo), alvo.name


def produzir(r, guardar_prova=True):
    bruto, nome_quadro = quadro_da_receita(r)
    if "recortes" in r:
        pedacos = []
        for (x0, y0, x1, y1) in r["recortes"]:
            pedacos.append(bruto[y0:y1, x0:x1])
        # iguala pela MAIOR altura em vez de cortar pela menor: os dois panos
        # estao a distancias parecidas e a tabua e vertical, entao esticar um
        # pouco no comprimento nao muda a largura da tabua -- e largura de
        # tabua e o que o olho le. Cortar pela menor jogaria fora 20% do pouco
        # que a foto do cliente tem.
        altura = max(p.shape[0] for p in pedacos)
        pedacos = [cv2.resize(p, (p.shape[1], altura), interpolation=cv2.INTER_CUBIC)
                   for p in pedacos]
        corte = np.hstack(pedacos).astype(np.float64) / 255.0
        recorte_px = [list(c) for c in r["recortes"]]
    else:
        x0, y0, x1, y1 = r["recorte"]
        corte = bruto[y0:y1, x0:x1].astype(np.float64) / 255.0
        recorte_px = list(r["recorte"])
    lin = srgb_para_linear(corte)
    registro = {
        "slug": r["slug"],
        "material": r["material"],
        "origem": r["origem"],
        "quadro": nome_quadro,
        "recorte_px": recorte_px,
        "recorte_tamanho_px": [corte.shape[1], corte.shape[0]],
    }

    # 2. retificacao
    if r["isotropico"]:
        k, k_bruto = medir_anisotropia(lin)
        lin = cv2.resize(lin, (lin.shape[1], int(round(lin.shape[0] * k))),
                         interpolation=cv2.INTER_CUBIC)
        registro["retificacao_vertical"] = round(k, 3)
        registro["retificacao_medida_bruta"] = round(k_bruto, 3)
        registro["retificacao_como"] = ("razao entre o desvio do gradiente "
                                        "vertical e o do horizontal; chao e "
                                        "isotropico, o que sobra e perspectiva")
    elif r.get("endireita_ondas"):
        # O tensor de estrutura devolve a direcao do GRADIENTE, que e
        # perpendicular a crista. Girar por -ang deixa o gradiente horizontal e
        # a CRISTA vertical -- que e o que se quer: com a crista vertical, a
        # costura de cima e trivial e a de lado so pede numero inteiro de ondas.
        ang = angulo_da_onda(lin)
        h, w = lin.shape[:2]
        m = cv2.getRotationMatrix2D((w / 2, h / 2), -ang, 1.0)
        lin = cv2.warpAffine(lin, m, (w, h), flags=cv2.INTER_CUBIC,
                             borderMode=cv2.BORDER_REFLECT)
        lado = int(min(h, w) / np.sqrt(2))
        cy, cx = h // 2, w // 2
        lin = lin[cy - lado // 2:cy + lado // 2, cx - lado // 2:cx + lado // 2]
        # se sobrou crista HORIZONTAL, gira um quarto de volta
        if not _crista_vertical(lin):
            lin = np.rot90(lin).copy()
            ang -= 90.0
        registro["giro_graus"] = round(-ang, 2)
        passo, forca_ac = periodo_horizontal(lin)
        registro["onda_passo_px"] = passo
        registro["onda_autocorrelacao"] = round(float(forca_ac), 3) if passo else None
        if passo:
            # recorta um numero INTEIRO de ondas, mais a faixa de costura
            n = max(4, int(min(lin.shape[:2]) / (passo * (1 + FEATHER / LADO))))
            preciso = int(round(n * passo * (1 + FEATHER / LADO)))
            if preciso <= lin.shape[1] and preciso <= lin.shape[0]:
                c = lin.shape[1] // 2, lin.shape[0] // 2
                meia = preciso // 2
                lin = lin[c[1] - meia:c[1] - meia + preciso,
                          c[0] - meia:c[0] - meia + preciso]
                registro["ondas_no_tile"] = n
                registro["lado_m_calculado"] = round(n * r["onda_m"], 3)
                r["lado_m"] = round(n * r["onda_m"], 3)
                r["lado_m_como"] = (
                    f"MEDIDA: {n} ondas no tile x {r['onda_m']} m de passo da "
                    f"chapa ondulada. O passo em pixel ({passo} px) saiu da "
                    f"autocorrelacao do perfil de colunas depois do giro.")
    else:
        e = r.get("estica_y", 1.0)
        if e != 1.0:
            lin = cv2.resize(lin, (lin.shape[1], int(round(lin.shape[0] * e))),
                             interpolation=cv2.INTER_CUBIC)
            registro["estica_y"] = e

    # Quadrado. Material com EIXO (tabua vertical, onda de telha) pode ser
    # esticado ao longo do eixo em vez de recortado: esticar uma tabua no
    # comprimento nao muda a largura da tabua, e largura da tabua e a leitura.
    # Chao isotropico, nao: ali esticar seria inventar direcao.
    h, w = lin.shape[:2]
    if r.get("eixo_vertical") and w != h:
        lado = max(h, w)
        lin = cv2.resize(lin, (lado, lado), interpolation=cv2.INTER_CUBIC)
        registro["esticado_no_eixo"] = round(max(h, w) / min(h, w), 3)
    else:
        lado = min(h, w)
        lin = lin[(h - lado) // 2:(h - lado) // 2 + lado,
                  (w - lado) // 2:(w - lado) // 2 + lado]
    registro["quadrado_nativo_px"] = lado

    # 3. deiluminacao
    antes = lin.copy()          # ja retificado e quadrado: compara mesma coisa
    razao, campo = deiluminar(lin)
    lum_campo = luminancia(campo)
    registro["campo_de_luz_min_max"] = [round(float(lum_campo.min()), 5),
                                        round(float(lum_campo.max()), 5)]
    registro["campo_de_luz_amplitude"] = round(
        float(lum_campo.max() / max(lum_campo.min(), 1e-6)), 3)

    # 4. tileavel  (sobe para LADO+FEATHER e costura)
    alvo = LADO + FEATHER
    razao_g = cv2.resize(razao, (alvo, alvo), interpolation=cv2.INTER_CUBIC)
    tile = tilear(razao_g)
    tile = np.maximum(tile, 1e-5)
    registro["ampliacao"] = round(alvo / lado, 3)

    # 5. os mapas
    lum = luminancia(tile)
    lum_norm = lum / max(lum.mean(), 1e-9)

    saidas = {}

    # Diffuse -- variacao de luminancia NEUTRA
    if "Diffuse" in r["mapas"]:
        # media linear em 0,214 (cinza sRGB 0,5): melhor uso dos 8 bits
        d_lin = np.clip(lum_norm * 0.2140, 0.0, 1.0)
        d = linear_para_srgb(np.repeat(d_lin[..., None], 3, axis=2))
        p = SAIDA / f"{r['slug']}_Diffuse_2k.jpg"
        gravar(p, np.round(d * 255).astype(np.uint8))
        saidas["Diffuse"] = p.name
        registro["diffuse_media_linear"] = round(float(d_lin.mean()), 6)
        registro["diffuse_e_neutro"] = True

    # Albedo -- colorido, media linear por canal = cor medida
    if r["cor_alvo"] is not None:
        alvo_bgr = np.array(r["cor_alvo"][::-1], dtype=np.float64)  # cv2 e BGR
        medias = tile.reshape(-1, 3).mean(axis=0)
        alb_lin = tile * (alvo_bgr / np.maximum(medias, 1e-9))
        registro["albedo_media_antes_bgr"] = [round(float(v), 5) for v in medias]
        # Se a variacao levar algum pixel acima de 1,0, o corte tira luz e a
        # media cai abaixo da cor medida -- o erro apareceu em -2,9% no
        # vermelho da grama desgastada, que e a classe mais clara do conjunto.
        # Ponto fixo: reescala ate a media DEPOIS do corte bater no alvo.
        for _ in range(6):
            m = np.clip(alb_lin, 0.0, 1.0).reshape(-1, 3).mean(axis=0)
            erro = alvo_bgr / np.maximum(m, 1e-9)
            if np.all(np.abs(erro - 1.0) < 2e-4):
                break
            alb_lin = alb_lin * erro
        alb_clip = np.clip(alb_lin, 0.0, 1.0)
        registro["albedo_estourou_fracao"] = round(
            float((alb_lin > 1.0).mean()), 6)
        alb = linear_para_srgb(alb_clip)
        alb8 = np.round(alb * 255).astype(np.uint8)
        p = SAIDA / f"{r['slug']}_Albedo_2k.jpg"
        gravar(p, alb8)
        saidas["Albedo"] = p.name
        # prova: reabre o JPG gravado e mede
        relido = srgb_para_linear(ler(p).astype(np.float64) / 255.0)
        m = relido.reshape(-1, 3).mean(axis=0)
        registro["albedo_alvo_rgb"] = r["cor_alvo"]
        registro["albedo_medido_no_arquivo_rgb"] = [round(float(m[2]), 5),
                                                    round(float(m[1]), 5),
                                                    round(float(m[0]), 5)]
        registro["albedo_erro_relativo_pct"] = [
            round(float(100 * (m[2 - i] - r["cor_alvo"][i]) / max(r["cor_alvo"][i], 1e-9)), 2)
            for i in range(3)]

    # Roughness
    if "Rough" in r["mapas"]:
        rough = 1.0 - normalizar_percentil(lum)
        rough = 0.5 + (rough - 0.5) * 0.85   # comprime; o no do Blender aperta mais
        p = SAIDA / f"{r['slug']}_Rough_2k.jpg"
        gravar(p, np.round(np.clip(rough, 0, 1) * 255).astype(np.uint8))
        saidas["Rough"] = p.name
        registro["rough_media"] = round(float(rough.mean()), 4)
        registro["rough_p05_p95"] = [round(float(np.percentile(rough, 5)), 4),
                                     round(float(np.percentile(rough, 95)), 4)]

    # Normal
    if "nor_gl" in r["mapas"]:
        altura = normalizar_percentil(lum)
        n = normal_de_altura(altura, forca=r.get("forca_altura", 3.0))
        p = SAIDA / f"{r['slug']}_nor_gl_2k.jpg"
        gravar(p, np.round(n[..., ::-1] * 255).astype(np.uint8))  # RGB -> BGR
        saidas["nor_gl"] = p.name
        registro["normal_convencao"] = "OpenGL (nor_gl)"
        registro["normal_verde_medio"] = round(float(n[..., 1].mean()), 4)
        registro["normal_azul_minimo"] = round(float(n[..., 2].min()), 4)

    registro["arquivos"] = saidas

    if guardar_prova:
        TRABALHO.mkdir(parents=True, exist_ok=True)
        # a media POR CANAL do campo de luz, e nao a luminancia dele: devolver
        # so a luminancia deixaria o "depois" cinza e faria a deiluminacao
        # parecer que lavou a cor, que e exatamente o que ela nao faz.
        media_canal = campo.reshape(-1, 3).mean(axis=0)
        depois = np.clip(razao * media_canal, 0, 1)
        final = SAIDA / f"{r['slug']}_Albedo_2k.jpg"
        if not final.exists():
            final = SAIDA / f"{r['slug']}_Rough_2k.jpg"
        prova = np.hstack([
            _mini(linear_para_srgb(antes)),
            _mini(linear_para_srgb(depois)),
            _mini(ler(final).astype(np.float64) / 255.0),
        ])
        gravar(TRABALHO / f"prova-{r['chave']}.jpg",
               np.round(prova * 255).astype(np.uint8))

    return registro


def _mini(img, lado=512):
    return cv2.resize(img, (lado, lado), interpolation=cv2.INTER_AREA)


# --------------------------------------------------------------------------

def folha_de_amostra(registros):
    """A grade antes/depois da deiluminacao, para o olho e nao para o log."""
    linhas = []
    for r in RECEITAS:
        p = TRABALHO / f"prova-{r['chave']}.jpg"
        if not p.exists():
            continue
        par = ler(p)
        rotulo = np.zeros((44, par.shape[1], 3), np.uint8)
        reg = next((x for x in registros if x["slug"] == r["slug"]), {})
        amp = reg.get("campo_de_luz_amplitude", "?")
        cv2.putText(rotulo, f"{r['chave']}  ({r['origem']})  campo de luz {amp}x",
                    (8, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        linhas.append(np.vstack([rotulo, par]))
    if not linhas:
        return None
    largura = max(l.shape[1] for l in linhas)
    linhas = [cv2.copyMakeBorder(l, 0, 0, 0, largura - l.shape[1],
                                 cv2.BORDER_CONSTANT, value=(0, 0, 0))
              for l in linhas]
    grade = np.vstack(linhas)
    cab = np.zeros((56, largura, 3), np.uint8)
    cv2.putText(cab, "recorte cru  |  deiluminado  |  o mapa que foi para o disco",
                (10, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
    grade = np.vstack([cab, grade])
    destino = RAIZ / "out" / "heroi" / "_materiais-amostra.jpg"
    destino.parent.mkdir(parents=True, exist_ok=True)
    gravar(destino, grade)
    return destino


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--so", action="append", default=None,
                    help="produz so estas chaves")
    ap.add_argument("--amostra", action="store_true",
                    help="so remonta a folha de amostra")
    args = ap.parse_args()

    SAIDA.mkdir(parents=True, exist_ok=True)
    TRABALHO.mkdir(parents=True, exist_ok=True)
    diario = TRABALHO / "registro.json"

    if args.amostra and diario.exists():
        registros = json.loads(diario.read_text(encoding="utf-8"))
        print("folha:", folha_de_amostra(registros))
        return 0

    registros = []
    for r in RECEITAS:
        if args.so and r["chave"] not in args.so:
            continue
        print(f"\n=== {r['chave']}  ({r['slug']})")
        reg = produzir(r)
        registros.append(reg)
        for k, v in reg.items():
            if k != "arquivos":
                print(f"   {k}: {v}")
        print(f"   arquivos: {list(reg['arquivos'].values())}")

    diario.write_text(json.dumps(registros, indent=1, ensure_ascii=False),
                      encoding="utf-8")
    print("\nfolha:", folha_de_amostra(registros))
    return 0


if __name__ == "__main__":
    sys.exit(main())
