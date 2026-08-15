#!/usr/bin/env python3
"""Transforma o rabisco do Natan em coordenada de mundo.

Em 15/08 ele marcou por cima de `out/conferencia/sobreposto-planta.png`, na
tela: **laranja** = onde o portal de entrada REALMENTE fica; **azul** = por onde
passa a estrada de asfalto. Marca em tela e' ordem, mas nao e' numero -- este
script faz virar numero.

Metodo, e ele nao depende de eu adivinhar onde ele clicou:

1. o print dele contem a nossa propria imagem, entao da' para RECUPERAR a
   transformacao entre os dois por casamento de imagem (ECC em escala de cinza,
   modelo euclidiano: so' escala e deslocamento -- print nao gira);
2. as marcas saem por COR no espaco HSV, nao por posicao;
3. o pixel volta para ponto de PDF e para metro pela mesma cadeia que gerou a
   imagem (`terreno.ESCALA`, origem no centro da prancha), entao a ida e a volta
   usam a mesma regua.

O que sai: `data/correcao-posicao-1508.json`, com a posicao velha guardada ao
lado da nova -- `nada se apaga` -- e a polilinha da estrada em metros.

Uso:
    .venv/Scripts/python.exe scripts/digitalizar_marcas.py --print "C:\\caminho\\print.png"
"""

import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import terreno

RAIZ = Path(__file__).resolve().parent.parent
BASE = RAIZ / "out" / "conferencia" / "sobreposto-planta.png"
SAIDA = RAIZ / "data" / "correcao-posicao-1508.json"

# Faixas HSV das duas canetas. Laranja e azul foram escolhidos por ele e nao
# existem no desenho da planta (que e' preto, cinza e pastel) nem na nossa
# marcacao (vermelho puro e azul-marinho da legenda) -- por isso separam.
LARANJA = ((5, 120, 120), (28, 255, 255))
AZUL = ((90, 120, 120), (115, 255, 255))


def ler(caminho):
    """cv2.imread nao abre caminho com acento no Windows -- armadilha 9."""
    dados = np.fromfile(str(caminho), dtype=np.uint8)
    img = cv2.imdecode(dados, cv2.IMREAD_COLOR)
    if img is None:
        raise SystemExit(f"nao consegui abrir {caminho}")
    return img


def alinhar(print_dele, base):
    """Devolve a matriz 2x3 que leva pixel do PRINT para pixel da BASE.

    Casamento por pontos-chave (AKAZE), nao por template: o print dele nao e' a
    imagem inteira reduzida, e' um RECORTE com zoom dentro do visualizador --
    template multiescala falha nisso (casamento 0,10 na primeira tentativa).
    Features toleram corte, zoom e a barra da janela em volta.

    O modelo e' similaridade (escala + translacao + giro residual), estimado por
    RANSAC: print nao deforma perspectiva.
    """
    g_print = cv2.cvtColor(print_dele, cv2.COLOR_BGR2GRAY)
    g_base = cv2.cvtColor(base, cv2.COLOR_BGR2GRAY)
    hb, wb = g_base.shape

    # Casamento por TEMPLATE do MIOLO da base, varrendo escala.
    #
    # Duas tentativas anteriores falharam, e o motivo de cada uma esta aqui para
    # nao se repetir:
    #  - template da base INTEIRA: o print corta o rodape da imagem, e
    #    matchTemplate exige o template inteiro dentro do quadro -> 0,10;
    #  - ORB + RANSAC: o desenho tem fileiras de estandes IDENTICOS, e padrao
    #    repetido produz consenso falso -- 2784 "inliers" numa transformacao
    #    visivelmente errada. Casamento denso nao cai nessa.
    # O template e' PEQUENO (18% e 28% do lado, centrado) e a varredura de
    # escala e' larga. Com miolo de 50% o casamento nao passava de 0,22: o print
    # e' um ZOOM cortado, e template grande demais nao cabe no que sobrou. A
    # 18% o pico e' 0,945, e as duas fracoes concordam na mesma escala -- que e'
    # o que distingue pico de verdade de maximo de ruido.
    melhor = None
    for frac in (0.18, 0.28):
        y0c = int(hb * (0.5 - frac / 2))
        x0c = int(wb * (0.5 - frac / 2))
        tpl0 = g_base[y0c:int(hb * (0.5 + frac / 2)),
                      x0c:int(wb * (0.5 + frac / 2))]
        for s in np.arange(0.25, 1.60, 0.01):   # base * s = tamanho no print
            alvo = cv2.resize(tpl0, None, fx=s, fy=s,
                              interpolation=cv2.INTER_AREA)
            if (alvo.shape[0] >= g_print.shape[0]
                    or alvo.shape[1] >= g_print.shape[1]
                    or min(alvo.shape) < 40):
                continue
            r = cv2.matchTemplate(g_print, alvo, cv2.TM_CCOEFF_NORMED)
            _, val, _, loc = cv2.minMaxLoc(r)
            if melhor is None or val > melhor[0]:
                melhor = (val, float(s), loc, (x0c, y0c), frac)

    if melhor is None or melhor[0] < 0.60:
        raise SystemExit(
            f"nao reconheci a sobreposicao dentro do print "
            f"(melhor casamento {melhor[0] if melhor else 0:.2f})")

    val, s, (px, py), (x0c, y0c), frac = melhor
    # o template comeca em (x0c,y0c) na base e caiu em (px,py) no print:
    #   pixel_print = s * (pixel_base - (x0c,y0c)) + (px,py)
    #   pixel_base  = (pixel_print - (px,py)) / s + (x0c,y0c)
    M = np.array([[1.0 / s, 0.0, x0c - px / s],
                  [0.0, 1.0 / s, y0c - py / s]], dtype=np.float64)
    print(f"alinhamento .. casamento {val:.3f} (template {frac:.0%}), "
          f"a base aparece a {s*100:.1f}% no print")
    return M


def conferir_alinhamento(print_dele, base, M, limite=18.0):
    """Portao: reprojeta o print sobre a base e mede se de fato coincide.

    Sem isto um alinhamento errado vira coordenada errada em silencio -- foi
    exatamente o que o ORB entregou. O numero e' o erro absoluto medio de
    luminancia na area coberta: imagem igual da' baixo, imagem deslocada da' alto.
    """
    hb, wb = base.shape[:2]
    warp = cv2.warpAffine(print_dele, M.astype(np.float32), (wb, hb),
                          borderValue=(255, 255, 255))
    cobertura = cv2.warpAffine(np.full(print_dele.shape[:2], 255, np.uint8),
                               M.astype(np.float32), (wb, hb))
    g1 = cv2.cvtColor(warp, cv2.COLOR_BGR2GRAY).astype(np.float32)
    g2 = cv2.cvtColor(base, cv2.COLOR_BGR2GRAY).astype(np.float32)
    # So' onde o print mostra a IMAGEM. A barra de titulo, a barra de tarefas e
    # o "Ativar o Windows" sao escuros e entram na area coberta: incluidos, eles
    # sozinhos levaram a media a 28,5 com um alinhamento de casamento 0,945 --
    # o portao reprovava o alinhamento certo pelo motivo errado.
    sel = (cobertura > 0) & (g1 > 60)
    erro = float(np.abs(g1[sel] - g2[sel]).mean())
    print(f"conferencia .. cobre {100*sel.mean():.0f}% da base (so' area de "
          f"imagem), erro medio {erro:.1f} (limite {limite:.0f})")
    if erro > limite:
        raise SystemExit(
            f"ABORTADO: o print nao casa com a base (erro {erro:.1f}). "
            "Coordenada tirada de alinhamento errado e' pior que nenhuma.")
    return erro


def para_base(pt, M):
    v = M @ np.array([pt[0], pt[1], 1.0])
    return float(v[0]), float(v[1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--print", dest="print_", required=True,
                    help="o arquivo do print marcado")
    ap.add_argument("--base", default=str(BASE))
    ap.add_argument("--debug", default="out/conferencia/marcas-lidas.png")
    args = ap.parse_args()

    print_dele = ler(args.print_)
    base = ler(args.base)
    print(f"print .. {print_dele.shape[1]}x{print_dele.shape[0]}   "
          f"base .. {base.shape[1]}x{base.shape[0]}")

    M = alinhar(print_dele, base)
    erro_alinhamento = conferir_alinhamento(print_dele, base, M)

    # `corrigir=False` de proposito: a partir de agora `carregar_mapa` ja aplica
    # esta correcao, e sem isto o "antigo" impresso aqui seria o NOVO -- o
    # desvio apareceria como 0,0 m na segunda execucao e ninguem entenderia.
    dados = terreno.carregar_mapa(RAIZ / terreno.MAPA_PADRAO, corrigir=False)
    origem = dados["_origem"]
    # a base foi rasterizada com zoom 2.5 sobre a prancha
    kx = base.shape[1] / dados["prancha"]["largura_pt"]
    ky = base.shape[0] / dados["prancha"]["altura_pt"]

    def px_para_mundo(px, py):
        x_pt, y_pt = px / kx, py / ky
        return terreno.para_mundo(x_pt, y_pt, origem)

    hsv = cv2.cvtColor(print_dele, cv2.COLOR_BGR2HSV)
    m_lar = cv2.inRange(hsv, *[np.array(c) for c in LARANJA])
    m_azu = cv2.inRange(hsv, *[np.array(c) for c in AZUL])
    # a caneta e' grossa: fecha buracos antes de medir
    k = np.ones((5, 5), np.uint8)
    m_lar = cv2.morphologyEx(m_lar, cv2.MORPH_CLOSE, k)
    m_azu = cv2.morphologyEx(m_azu, cv2.MORPH_CLOSE, k)

    saida = {
        "fonte": "marca em tela do Natan, 15/08/2026",
        "ordem": ("aqui ta em laranja a localizacao do portal e em azul onde "
                  "tem que ter a estrada de asfalto"),
        "print": str(Path(args.print_).resolve()),
        "alinhamento": {
            "matriz_print_para_base": [[round(float(v), 6) for v in linha]
                                       for linha in M],
            "erro_medio_de_reprojecao": round(erro_alinhamento, 2),
        },
    }
    dbg = print_dele.copy()

    # ---- portal: centro da mancha laranja ------------------------------
    cnts, _ = cv2.findContours(m_lar, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = [c for c in cnts if cv2.contourArea(c) > 200]
    if not cnts:
        print("AVISO: nenhuma marca laranja encontrada")
    else:
        c = max(cnts, key=cv2.contourArea)
        mom = cv2.moments(c)
        cx, cy = mom["m10"] / mom["m00"], mom["m01"] / mom["m00"]
        bx, by = para_base((cx, cy), M)
        mx, my = px_para_mundo(bx, by)

        antigo = terreno.ponto_da_zona(dados, "Portal de Entrada")
        d = float(np.hypot(mx - antigo[0], my - antigo[1])) if antigo else None
        saida["portal"] = {
            "novo_m": [round(mx, 2), round(my, 2)],
            "antigo_m": [round(antigo[0], 2), round(antigo[1], 2)] if antigo else None,
            "desvio_m": round(d, 1) if d else None,
            "raio_marca_m": round(float(np.sqrt(cv2.contourArea(c) / np.pi))
                                  * float(M[0, 0]) / kx * terreno.ESCALA, 1),
        }
        cv2.drawContours(dbg, [c], -1, (0, 255, 255), 3)
        cv2.drawMarker(dbg, (int(cx), int(cy)), (0, 0, 255), cv2.MARKER_CROSS, 30, 3)
        print(f"\nPORTAL")
        print(f"  marcado por ele .. ({mx:8.1f}, {my:8.1f}) m")
        if antigo:
            print(f"  esta hoje em ..... ({antigo[0]:8.1f}, {antigo[1]:8.1f}) m")
            print(f"  desvio ........... {d:.1f} m")

    # ---- estrada: esqueleto da mancha azul, virado em polilinha --------
    cnts, _ = cv2.findContours(m_azu, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = [c for c in cnts if cv2.contourArea(c) > 500]
    if not cnts:
        print("AVISO: nenhuma marca azul encontrada")
    else:
        c = max(cnts, key=cv2.contourArea)
        # o traco e' um rabisco grosso: o eixo sai do afinamento da mascara
        mask = np.zeros(m_azu.shape, np.uint8)
        cv2.drawContours(mask, [c], -1, 255, -1)
        fino = cv2.ximgproc.thinning(mask) if hasattr(cv2, "ximgproc") else None
        if fino is None:
            # sem opencv-contrib: aproxima o eixo pelo contorno simplificado
            eps = 0.002 * cv2.arcLength(c, False)
            pts = cv2.approxPolyDP(c, eps, False).reshape(-1, 2)
            # o contorno vai e volta pelos dois lados do traco: fica a metade
            pts = pts[:len(pts) // 2]
        else:
            ys, xs = np.nonzero(fino)
            pts = np.stack([xs, ys], axis=1)
            pts = pts[np.argsort(pts[:, 0])]
            pts = pts[::max(1, len(pts) // 60)]

        mundo = []
        for px, py in pts:
            bx, by = para_base((float(px), float(py)), M)
            mx, my = px_para_mundo(bx, by)
            mundo.append([round(mx, 2), round(my, 2)])

        comp = sum(float(np.hypot(mundo[i + 1][0] - mundo[i][0],
                                  mundo[i + 1][1] - mundo[i][1]))
                   for i in range(len(mundo) - 1))
        saida["estrada_asfalto"] = {
            "pontos_m": mundo,
            "vertices": len(mundo),
            "comprimento_m": round(comp, 1),
            "largura_m": 8.0,
            "material": "MAT_ASFALTO",
            "conferido_pelo_natan": True,
        }
        cv2.drawContours(dbg, [c], -1, (255, 255, 0), 2)
        print(f"\nESTRADA DE ASFALTO")
        print(f"  vertices ......... {len(mundo)}")
        print(f"  comprimento ...... {comp:.0f} m")

    SAIDA.write_text(json.dumps(saida, indent=2, ensure_ascii=False),
                     encoding="utf-8")
    cv2.imwrite(str(RAIZ / args.debug), dbg)
    print(f"\ngravado: {SAIDA}")
    print(f"gravado: {RAIZ / args.debug}")


if __name__ == "__main__":
    main()
