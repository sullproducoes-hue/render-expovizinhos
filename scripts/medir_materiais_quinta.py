#!/usr/bin/env python3
"""Mede a cor-base das classes que o PARQUE tem e a CENA ainda nao tem.

    .venv/Scripts/python.exe scripts/medir_materiais_quinta.py --debug

O `medir_materiais.py` de 14/08 mediu sete classes num quadro de golden hour de
29/11: lona, telha, grama, terra, brita, copa, campo. Ele continua valendo e NAO
e refeito aqui. O que falta sao as classes que o Natan filmou em 13/08 e que o
parque de verdade tem: **tijolo vermelho, coluna azul, chapa azul, telha clara,
terra batida, concreto, grade** e o piso dos currais.


## Por que a ancora de 14/08 nao serve aqui, e o que entra no lugar

Em 14/08 a ancora foi a lona branca com albedo de mercado 0,75. Tentei repetir
isso aqui e o numero denunciou na hora: com a telha clara declarada em 0,70, o
tijolo saiu com **albedo 1,000 no vermelho** -- ou seja, a parede refletiria
mais vermelho do que o branco reflete. Isso nao existe, e a causa e fisica:

**Em dia encoberto a irradiancia depende da ORIENTACAO da superficie.** A agua
de telhado ve o hemisferio de ceu inteiro; a parede vertical ve metade dele. Uma
ancora no telhado mede uma luz que a parede nao recebe, e todo albedo de parede
sai inflado. A doutrina de 14/08 ja avisava disso em uma linha -- *"superficie de
ancora tem que estar iluminada como as que se quer medir"* -- e a lona daquele
quadro estava virada para o sol junto com o resto. Aqui nao ha essa sorte.

**O conserto nao e escolher outra ancora de albedo chutado: e usar o ceu.** Sob
ceu encoberto o proprio ceu no quadro e o fotometro, e ele esta medido:

    E_horizontal = pi * L_ceu                       (ceu uniforme)
    E_vertical   = pi * L_ceu * FATOR_VISTA[orientacao]
    albedo       = pi * L_superficie / E_superficie

`FATOR_VISTA` esta declarado abaixo, valor por valor, com o motivo de cada um.
Isto e um MODELO, nao uma carta de cor -- mas e um modelo derivavel, conferivel
e escrito, e nao um numero que eu escolhi porque a imagem "parecia" branca.

**E ele e conferido contra medida independente.** As classes `copa` e `terra`
ja foram medidas em 14/08, noutro quadro e noutra luz. Elas entram aqui como
CONTROLE: se a inversao pelo ceu devolver a mata com o dobro do albedo que a
outra medicao deu, quem esta errado e o modelo, e o script diz isso na cara.


## As tres travas do material

1. **Linear de verdade.** Entrada e o PNG 16 bits de `extracao/linear/`. Divisao
   so vale em linear; em sRGB a conta roda e devolve numero errado que passa no
   teste (armadilha 32).
2. **So regiao grande e chapada.** 4:2:0, e as duas classes mais criticas --
   vermelho e azul saturados -- sao o pior caso de croma. Caixa menor que
   `AREA_MINIMA_PX` e recusada.
3. **Nada de pixel estourado.** `1 (17)__0037s` tem 8,7% do quadro em 1,0. Amostra
   com mais de `ESTOURO_MAXIMO` de pixels no teto vira mediana de um valor que a
   camera nao viu. Recusada, e com o numero impresso.

Sai em `data/materiais-quinta.json`. Roda no venv (cv2 + numpy).
"""

import argparse
import json
from pathlib import Path

import cv2
import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
LINEAR = Path(r"E:\Projetos todos\Mapa - agroshow\Brutos Expo"
              r"\agroshow extrator somente\extracao\linear")

AREA_MINIMA_PX = 20000
"""Piso de area da amostra, em pixel do quadro original (3840x2160).

~140x140. Abaixo disso o croma 4:2:0 de uma regiao com borda perto contamina a
mediana, e o numero fica bonito e errado."""

ESTOURO_MAXIMO = 0.005
"""Fracao maxima de pixels no teto (>= 65000/65535) dentro da amostra."""

FATOR_VISTA = {
    "horizontal": 1.00,
    "vertical_aberta": 0.54,
    "vertical_sob_beiral": 0.32,
    "telhado_baixa_inclinacao": 0.96,
}
"""Quanto da irradiancia horizontal chega em cada orientacao, sob ceu encoberto.

- `horizontal` = 1,00 por definicao: e a referencia, E = pi*L.
- `vertical_aberta` = 0,54. Parede em pe ve **metade** do hemisferio de ceu, o
  que da 0,50; o chao na frente devolve mais um pouco, e com albedo de solo de
  ~0,15 e fator de vista 0,5 isso soma ~0,075 -> 0,54 arredondado para baixo.
- `vertical_sob_beiral` = 0,32. Parede coberta por avanco de telhado perde a
  parte alta do ceu, que sob ceu encoberto CIE e a mais luminosa. 0,32 e a conta
  para um beiral que corta ~40% do hemisferio visivel.
- `telhado_baixa_inclinacao` = 0,96. Agua de pouca inclinacao ve quase tudo.

Estes numeros carregam a incerteza do metodo, e ela e declarada no JSON: a
diferenca entre 0,50 e 0,54 e de 8%, e e menor que a diferenca entre medir na
parede e medir no telhado, que e de 85%. **Sao eles que o controle testa.**"""

# Medido em 14/08 noutro quadro e noutra luz, `data/materiais-medidos.json`.
# Entra aqui so como CONTROLE.
CONTROLE_14_08 = {
    "copa": [0.1324, 0.1538, 0.0455],
    "terra": [0.2659, 0.1875, 0.1548],
    "brita": [0.1362, 0.0978, 0.0704],
}


def cx(x0, y0, x1, y1):
    return (x0, y0, x1, y1)


QUADROS = {
    "1 (17)__0006s": {
        "por_que": ("o quadro-chave do conjunto: fachada de tijolo, chapa azul, "
                    "estrada de brita, mata e **ceu NAO estourado** (99,9% em "
                    "0,957, so 0,06% dos pixels no teto). E o unico que permite "
                    "medir o iluminante em vez de arbitrar."),
        "ceu": {
            "caixa": cx(1520, 40, 2160, 280),
            "onde": "vao de ceu encoberto acima da linha de arvores, ao centro-alto",
        },
        "amostras": {
            "tijolo_vermelho": {
                "caixa": cx(2940, 460, 3220, 980),
                "orientacao": "vertical_aberta",
                "onde": ("pano cheio de alvenaria vermelha do galpao, a direita do "
                         "vao. A primeira caixa caiu 200 px a esquerda, em cima da "
                         "GRADE de ventilacao escura, e devolveu albedo 0,013 -- "
                         "tijolo mais escuro que a mata, que nao existe"),
                "material": "MAT_TIJOLO",
            },
            "chapa_azul": {
                "caixa": cx(2320, 220, 2720, 480),
                "orientacao": "telhado_baixa_inclinacao",
                "onde": ("faixa de chapa azul da agua do telhado, seguindo a "
                         "diagonal. A primeira caixa era um retangulo grande sobre "
                         "uma faixa inclinada e pegava parede no canto de baixo"),
                "material": "MAT_CHAPA_AZUL",
            },
            "brita_estrada": {
                "caixa": cx(1400, 1560, 3400, 1980),
                "orientacao": "horizontal",
                "onde": "estrada de brita e saibro no primeiro plano, grande e chapada",
                "material": "MAT_SAIBRO",
            },
            "chao_batido": {
                "caixa": cx(1320, 1032, 1880, 1140),
                "orientacao": "horizontal",
                "onde": ("faixa de chao batido entre a alameda e a estrada. "
                         "**Estava rotulada `grama` e nao e.** Saiu 0,339/0,240/"
                         "0,159, que e bege, e o debug mostrou terra pisada entre "
                         "as arvores. Renomeada em vez de forcada: rotulo errado "
                         "sobre medida certa e pior que medida faltando. Vira o "
                         "SEGUNDO controle -- bate com a classe `terra` de 14/08"),
                "material": None,
                "controle": "terra",
            },
            "copa_controle": {
                "caixa": cx(800, 320, 2000, 960),
                "orientacao": "vertical_aberta",
                "onde": ("massa fechada de mata no centro do quadro. CONTROLE: a "
                         "mata e perene e ja foi medida em 14/08 (0,132/0,154/"
                         "0,046). Se sair longe disso, o modelo de ceu esta errado"),
                "material": None,
                "controle": "copa",
            },
        },
    },

    # -------------------------------------------------------------------------
    # Este quadro NAO tem ceu -- a fachada preenche o enquadramento inteiro, e
    # 8,7% dos pixels estao no teto. Entao ele nao mede iluminante sozinho: ele
    # ENTRA PELO TIJOLO. E a mesma alvenaria pintada do mesmo galpao, na mesma
    # orientacao vertical aberta, filmada no mesmo dia e na mesma luz. O que a
    # cadeia transporta e o iluminante; o que ela mede aqui e o que so existe
    # aqui -- a coluna azul larga e o portao de chapa.
    "1 (17)__0037s": {
        "por_que": ("de perto, a mesma fachada: e o unico quadro com a pilastra "
                    "azul grande e chapada o bastante para sobreviver ao 4:2:0, "
                    "e com o portao de chapa inteiro."),
        "ancora_transferida": {
            "classe_aqui": "tijolo_vermelho",
            "de_quadro": "1 (17)__0006s",
            "de_classe": "tijolo_vermelho",
            "canais_limpos": [1, 2],
            "por_que": (
                "Mesma parede, mesmo galpao, mesmo dia -- mas neste plano fechado a "
                "camera expos para o interior escuro do vao e **41% dos pixels do "
                "tijolo estao no teto do VERMELHO**. O verde e o azul continuam "
                "limpos. Entao a cadeia carrega so o NIVEL, medido em G e B, e "
                "reusa a COR do iluminante do quadro aberto -- que e o mesmo dia, "
                "o mesmo ceu encoberto e o mesmo balanco de branco da camera. "
                "Ancorar no canal saturado transportaria um valor que a camera "
                "nao viu; ancorar so nos limpos transporta o que ela viu."),
        },
        "amostras": {
            "tijolo_vermelho": {
                "caixa": cx(730, 1000, 1120, 1310),
                "orientacao": "vertical_aberta",
                "canais_limpos": [1, 2],
                "onde": ("pano de alvenaria vermelha a direita da pilastra azul. "
                         "So os canais G e B desta amostra entram na cadeia -- o "
                         "R esta estourado em 41% dos pixels, e esta dito"),
                "material": None,
            },
            "coluna_azul": {
                "caixa": cx(3140, 300, 3290, 1200),
                "orientacao": "vertical_aberta",
                "onde": "pilastra azul larga a direita do vao -- a mais chapada do conjunto",
                "material": "MAT_COLUNA_AZUL",
            },
            "portao_chapa": {
                "caixa": cx(1400, 500, 1820, 1500),
                "orientacao": "vertical_sob_beiral",
                "onde": ("portao de chapa ondulada azul-ardosia, fechado, no "
                         "centro. Fica recuado sob o avanco do telhado -- por "
                         "isso a orientacao dele nao e a mesma da fachada"),
                "material": "MAT_CHAPA_PORTAO",
            },
            "terra_batida": {
                "caixa": cx(2100, 1450, 2800, 1650),
                "orientacao": "vertical_sob_beiral",
                "onde": ("piso de terra batida avermelhada DENTRO do vao. Chao "
                         "coberto ve pouco ceu: entra como sob beiral, nao como "
                         "horizontal aberto"),
                "material": "MAT_TERRA_BATIDA",
            },
        },
    },

    # -------------------------------------------------------------------------
    # MANGUEIRAS. Aqui NAO ha fotometro: o galpao e aberto dos lados e todo o
    # fundo claro que aparece pelos vaos esta ESTOURADO (1,3% a 2,6% do quadro
    # no teto, em todos os dez quadros extraidos). Sem ceu medivel nao ha como
    # inverter para albedo absoluto, e nao ha superficie de albedo conhecido no
    # quadro.
    #
    # O que se faz entao NAO e escolher um numero: e entregar o que esta medido
    # e dizer o que nao esta. O iluminante daquele dia tem COR conhecida (R/B
    # 0,80, medida no ceu do 1 (17)), entao a CROMATICIDADE de cada material sai
    # correta. O que falta e o NIVEL, e ele vira pendencia declarada.
    "1 (14)__0011s": {
        "modo": "relativo",
        "referencia": "grade_cinza",
        "por_que": ("MANGUEIRAS por dentro: coluna de concreto, estrutura de "
                    "telhado vermelha e grade de manejo. E o unico quadro do "
                    "conjunto com concreto estrutural grande e chapado -- e o "
                    "unico sem nenhum fotometro."),
        "amostras": {
            "concreto_coluna": {
                "caixa": cx(3620, 700, 3740, 1560),
                "orientacao": "vertical_sob_beiral",
                "_atencao": ("esta coluna esta no FUNDO COBERTO e le 3x mais escura "
                             "que as grades do primeiro plano. A diferenca NAO e "
                             "albedo, e iluminacao: as grades recebem ceu pelo vao "
                             "aberto e ela nao. Por isso ela deixou de ser a "
                             "referencia deste quadro"),
                "onde": ("coluna de concreto do vao direito, a mais proxima, de cima a "
                         "baixo. A primeira caixa ficava 700 px a esquerda e "
                         "metade dela era MATA ao fundo, pelo vao aberto. E a "
                         "REFERENCIA deste quadro"),
                "material": "MAT_CONCRETO",
            },
            # `estrutura_vermelha` SAIU daqui, e o motivo e a propria trava.
            # A unica pintura vermelha deste galpao aparece em terca e em rufo --
            # pecas de 20 a 40 px de largura no quadro. Em 4:2:0 o croma de peca
            # fina e mistura inventada pelo decodificador, e a primeira caixa que
            # tentei ainda vinha com 1,25% de pixel no teto. Nao ha medida boa
            # aqui: vira pendencia, nao numero.
            "grade_cinza": {
                "caixa": cx(200, 1700, 1400, 2050),
                "orientacao": "vertical_sob_beiral",
                "onde": "grade de manejo pintada de cinza, primeiro plano",
                "material": "MAT_GRADE",
            },
            "piso_curral": {
                "caixa": cx(1720, 1720, 2080, 1880),
                "orientacao": "horizontal",
                "onde": ("piso do curral entre as grades. A decupagem de 15/08 "
                         "escreveu 'piso de brita'; o quadro mostra terra com "
                         "MARAVALHA. A cor sai daqui, nao do rotulo"),
                "material": "MAT_PISO_CURRAL",
            },
        },
    },
}


def linear_para_srgb(c):
    c = np.clip(np.asarray(c, dtype=np.float64), 0.0, 1.0)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def achar_png(nome):
    p = LINEAR / nome.split("__")[0] / f"{nome}.png"
    if not p.exists():
        raise SystemExit(f"quadro linear ausente: {p}\n"
                         "rode extrair_linear.py --todos --por-video 4")
    return p


def amostrar(bruto16, caixa, rotulo, canais=None):
    """Mediana linear RGB do recorte, com trava de estouro.

    `canais` e uma lista de indices em RGB (0=R, 1=G, 2=B). Quando dada, a trava
    de estouro so olha esses canais -- e o caso do tijolo no plano fechado, em
    que o vermelho saturou e o verde e o azul nao."""
    x0, y0, x1, y1 = caixa
    r = bruto16[y0:y1, x0:x1]
    if r.size == 0:
        raise SystemExit(f"{rotulo}: recorte vazio {caixa}")
    olhar = r if canais is None else r[:, :, [2 - i for i in canais]]  # RGB -> BGR
    estouro = float((olhar >= 65000).any(axis=2).mean())
    if estouro > ESTOURO_MAXIMO:
        raise SystemExit(
            f"{rotulo}: {estouro*100:.2f}% de pixel no teto (max {ESTOURO_MAXIMO*100:.1f}%). "
            "Mediana de valor estourado e mediana de coisa que a camera nao viu.")
    lin = r.astype(np.float64) / 65535.0
    bgr = np.median(lin.reshape(-1, 3), axis=0)
    return bgr[::-1], estouro


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--saida", default="data/materiais-quinta.json")
    ap.add_argument("--debug", action="store_true")
    args = ap.parse_args()

    saida = {
        "_procedencia": ("registro -- medicao. Cor-base das classes que o parque "
                         "tem e a cena nao tinha, do footage de 13/08, em linear "
                         "16 bits, com o iluminante MEDIDO no ceu do proprio quadro."),
        "_metodo": ("ceu encoberto como fotometro. E_h = pi*L_ceu; a orientacao "
                    "de cada superficie entra por FATOR_VISTA; albedo = "
                    "pi*L_superficie / E_superficie."),
        "_por_que_nao_a_ancora_de_14_08": (
            "ancora no telhado mede luz que a parede vertical nao recebe. Com a "
            "telha declarada em 0,70 o tijolo saiu com albedo 1,000 no vermelho, "
            "que e mais vermelho do que o branco reflete. O erro foi de "
            "ORIENTACAO, nao de caixa."),
        "_fator_vista": FATOR_VISTA,
        "_area_minima_px": AREA_MINIMA_PX,
        "_estouro_maximo": ESTOURO_MAXIMO,
        "quadros": {},
    }

    for nome, q in QUADROS.items():
        png = achar_png(nome)
        bruto = cv2.imdecode(np.fromfile(str(png), dtype=np.uint8), cv2.IMREAD_UNCHANGED)
        if bruto is None:
            raise SystemExit(f"nao decodifiquei {png}")
        if bruto.dtype != np.uint16:
            raise SystemExit(f"{png.name} nao e 16 bits ({bruto.dtype}). "
                             "Medir em 8 bits com gama e o erro que passa no teste.")

        print("=" * 78)
        print(f"{nome}   {bruto.shape[1]}x{bruto.shape[0]}  linear 16 bits")
        print(f"  {q['por_que']}\n")

        for cls, a in q["amostras"].items():
            x0, y0, x1, y1 = a["caixa"]
            area = (x1 - x0) * (y1 - y0)
            if area < AREA_MINIMA_PX:
                raise SystemExit(f"{nome}/{cls}: caixa de {area} px < {AREA_MINIMA_PX}.")

        if q.get("modo") == "relativo":
            # Sem fotometro: nao se inventa nivel. Entrega-se a COR (que o
            # iluminante MEDIDO daquele dia permite corrigir) e a razao de
            # reflectancia contra a referencia declarada. O nivel absoluto vira
            # pendencia, escrita no JSON.
            branco = np.array(saida["quadros"]["1 (17)__0006s"]["E_horizontal"])
            branco = branco / branco[1]
            l_ref, _ = amostrar(bruto, q["amostras"][q["referencia"]]["caixa"],
                                f"{nome}/{q['referencia']}")
            print("  MODO RELATIVO -- nao ha ceu medivel neste quadro.")
            print(f"  referencia: {q['referencia']}; cor do iluminante reusada "
                  f"do 1 (17)__0006s (R/B 0,80)\n")
            print(f"  {'classe':22s} {'razao vs referencia':>22s}  {'hex balanceado':>15s}")
            itens = {}
            for cls, a in q["amostras"].items():
                x0, y0, x1, y1 = a["caixa"]
                if (x1 - x0) * (y1 - y0) < AREA_MINIMA_PX:
                    raise SystemExit(f"{nome}/{cls}: caixa pequena demais")
                lin, est = amostrar(bruto, a["caixa"], f"{nome}/{cls}")
                razao = lin / np.maximum(l_ref, 1e-9)
                bal = lin / branco
                bal = bal / max(bal.max(), 1e-9)   # so a cor, nao o nivel
                srgb = linear_para_srgb(bal)
                hexa = "#" + "".join(f"{int(round(v*255)):02x}" for v in srgb)
                print(f"  {cls:22s} {razao[0]:6.3f} {razao[1]:6.3f} {razao[2]:6.3f}  {hexa:>15s}")
                itens[cls] = {
                    "material": a["material"],
                    "onde": a["onde"],
                    "caixa_px": list(a["caixa"]),
                    "orientacao": a["orientacao"],
                    "razao_vs_referencia": [round(float(v), 4) for v in razao],
                    "cor_balanceada_normalizada": [round(float(v), 4) for v in bal],
                    "hex_balanceado": hexa,
                    "albedo_linear": None,
                    "estouro_na_amostra": round(est, 5),
                }
            saida["quadros"][nome] = {
                "arquivo": str(png),
                "modo": "relativo",
                "por_que": q["por_que"],
                "referencia": q["referencia"],
                "_a_razao_NAO_e_reflectancia_entre_regimes": (
                    "dentro deste galpao a luz nao e uniforme: o primeiro plano "
                    "recebe ceu pelos vaos abertos e o fundo coberto nao. Grade e "
                    "piso estao no mesmo regime e sao comparaveis entre si; a "
                    "coluna esta noutro e le 3x mais escura POR ILUMINACAO. "
                    "Comparar as duas familias como se fossem albedo e o erro que "
                    "este campo existe para impedir."),
                "_o_que_falta": (
                    "o NIVEL. O galpao e aberto e todo o fundo claro que aparece "
                    "pelos vaos esta estourado nos dez quadros extraidos, entao nao "
                    "ha ceu para inverter e nao ha superficie de albedo conhecido "
                    "no quadro. A COR esta medida (o iluminante daquele dia tem "
                    "R/B 0,80, medido no 1 (17)); o albedo absoluto NAO. Nao "
                    "arbitrei um valor: vira pendencia."),
                "_como_fechar": (
                    "duas saidas baratas: (a) o Natan diz o albedo do concreto "
                    "daquela coluna -- concreto envelhecido de mercado fica entre "
                    "0,20 e 0,30, e uma palavra dele fecha o quadro inteiro; ou "
                    "(b) um quadro do mesmo dia com a coluna e o ceu nao "
                    "estourado juntos."),
                "itens": itens,
            }
            if args.debug:
                vis = (linear_para_srgb(bruto.astype(np.float64) / 65535.0) * 255).astype(np.uint8)
                for cls, a in q["amostras"].items():
                    x0, y0, x1, y1 = a["caixa"]
                    cor = (0, 255, 255) if cls == q["referencia"] else (0, 0, 255)
                    cv2.rectangle(vis, (x0, y0), (x1, y1), cor, 8)
                    cv2.putText(vis, cls, (x0 + 10, max(y0 - 14, 40)),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.7, cor, 5)
                d = RAIZ / "out" / "amostras-quinta" / f"{nome}.jpg"
                d.parent.mkdir(parents=True, exist_ok=True)
                cv2.imwrite(str(d), cv2.resize(vis, None, fx=0.25, fy=0.25),
                            [cv2.IMWRITE_JPEG_QUALITY, 92])
                print(f"\n  debug: {d.relative_to(RAIZ)}")
            continue

        if "ceu" in q:
            l_ceu, est_ceu = amostrar(bruto, q["ceu"]["caixa"], f"{nome}/ceu")
            e_h = np.pi * l_ceu
            print(f"  ceu (radiancia linear RGB): {l_ceu[0]:.4f} {l_ceu[1]:.4f} {l_ceu[2]:.4f}"
                  f"   estouro {est_ceu*100:.3f}%")
            print(f"  E_horizontal = pi*L: {e_h[0]:.4f} {e_h[1]:.4f} {e_h[2]:.4f}"
                  f"   R/B = {e_h[0]/max(e_h[2],1e-9):.2f}  (ceu encoberto puxa para o azul)\n")
        else:
            t = q["ancora_transferida"]
            qref = saida["quadros"][t["de_quadro"]]
            ref = qref["itens"][t["de_classe"]]
            albedo_ref = np.array(ref["albedo_linear"])
            e_h_ref = np.array(qref["E_horizontal"])
            a_aqui = q["amostras"][t["classe_aqui"]]
            l_anc, est_anc = amostrar(bruto, a_aqui["caixa"], f"{nome}/{t['classe_aqui']}",
                                      canais=t.get("canais_limpos"))
            # E_h que explicaria esta leitura, canal a canal
            e_h_bruta = (np.pi * l_anc) / (albedo_ref * FATOR_VISTA[a_aqui["orientacao"]])
            canais = t.get("canais_limpos")
            if canais:
                # so o NIVEL vem daqui; a COR do iluminante vem do quadro aberto,
                # que e o mesmo dia, o mesmo ceu e o mesmo balanco de branco.
                k = float(np.mean(e_h_bruta[canais] / e_h_ref[canais]))
                e_h = e_h_ref * k
                print(f"  ancora TRANSFERIDA de {t['de_quadro']}/{t['de_classe']}"
                      f"  (so canais {canais}: R esta estourado)")
                print(f"  fator de nivel k = {k:.3f}  sobre a cor do iluminante do quadro aberto")
            else:
                e_h = e_h_bruta
                print(f"  ancora TRANSFERIDA de {t['de_quadro']}/{t['de_classe']} "
                      f"albedo {albedo_ref.round(3)}")
            print(f"  E_horizontal implicita: {e_h[0]:.4f} {e_h[1]:.4f} {e_h[2]:.4f}"
                  f"   R/B = {e_h[0]/max(e_h[2],1e-9):.2f}\n")

        itens, alertas = {}, []
        print(f"  {'classe':20s} {'orientacao':26s} {'albedo linear':>21s}  {'hex':>8s}")
        for cls, a in q["amostras"].items():
            lin, est = amostrar(bruto, a["caixa"], f"{nome}/{cls}",
                                canais=a.get("canais_limpos"))
            fator = FATOR_VISTA[a["orientacao"]]
            albedo = np.clip((np.pi * lin) / (e_h * fator), 0.0, 1.0)
            srgb = linear_para_srgb(albedo)
            hexa = "#" + "".join(f"{int(round(v*255)):02x}" for v in srgb)
            lum = float(0.2126*albedo[0] + 0.7152*albedo[1] + 0.0722*albedo[2])
            print(f"  {cls:20s} {a['orientacao']:26s} "
                  f"{albedo[0]:6.3f} {albedo[1]:6.3f} {albedo[2]:6.3f}  {hexa}")

            item = {
                "material": a["material"],
                "onde": a["onde"],
                "caixa_px": list(a["caixa"]),
                "orientacao": a["orientacao"],
                "fator_vista": fator,
                "albedo_linear": [round(float(v), 4) for v in albedo],
                "hex_aproximado": hexa,
                "luminancia": round(lum, 4),
                "estouro_na_amostra": round(est, 5),
            }

            if a.get("controle"):
                ref = np.array(CONTROLE_14_08[a["controle"]])
                razao = albedo / np.maximum(ref, 1e-6)
                lum_r = float(0.2126*ref[0] + 0.7152*ref[1] + 0.0722*ref[2])
                fator_lum = lum / max(lum_r, 1e-9)
                item["controle_contra_14_08"] = {
                    "referencia": [round(float(v), 4) for v in ref],
                    "razao_por_canal": [round(float(v), 3) for v in razao],
                    "razao_de_luminancia": round(fator_lum, 3),
                }
                veredito = ("PASSA" if 0.7 <= fator_lum <= 1.45 else "NAO PASSA")
                print(f"       -> CONTROLE contra 14/08 ({a['controle']}): "
                      f"luminancia {fator_lum:.2f}x  {veredito}")
                item["controle_contra_14_08"]["veredito"] = veredito
                if veredito == "NAO PASSA":
                    alertas.append(f"{cls}: {fator_lum:.2f}x a medicao de 14/08")

            itens[cls] = item

        saida["quadros"][nome] = {
            "arquivo": str(png),
            "por_que": q["por_que"],
            "ceu": ({**q["ceu"], "radiancia_linear_rgb": [round(float(v), 5) for v in l_ceu]}
                    if "ceu" in q else None),
            "ancora_transferida": q.get("ancora_transferida"),
            "E_horizontal": [round(float(v), 5) for v in e_h],
            "itens": itens,
            "alertas": alertas,
        }
        if alertas:
            print("\n  ALERTAS: " + "; ".join(alertas))

        if args.debug:
            vis = (linear_para_srgb(bruto.astype(np.float64)/65535.0)*255).astype(np.uint8)
            todas = dict(q["amostras"])
            if "ceu" in q:
                todas = {"CEU": q["ceu"], **todas}
            for cls, a in todas.items():
                x0, y0, x1, y1 = a["caixa"]
                cor = (0, 255, 255) if cls == "CEU" else (0, 0, 255)
                cv2.rectangle(vis, (x0, y0), (x1, y1), cor, 8)
                cv2.putText(vis, cls, (x0+10, max(y0-14, 40)),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.7, cor, 5)
            d = RAIZ / "out" / "amostras-quinta" / f"{nome}.jpg"
            d.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(d), cv2.resize(vis, None, fx=0.25, fy=0.25),
                        [cv2.IMWRITE_JPEG_QUALITY, 92])
            print(f"\n  debug: {d.relative_to(RAIZ)}")

    alvo = RAIZ / args.saida
    alvo.write_text(json.dumps(saida, indent=1, ensure_ascii=False), encoding="utf-8")
    print("=" * 78)
    print(f"gravado: {alvo}")


if __name__ == "__main__":
    main()
