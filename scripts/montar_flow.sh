#!/usr/bin/env bash
# Monta o filme do AGROSHOW 2026 a partir dos clipes gerados no Google Flow.
#
# E o passo 6 do Plano A (docs/CENAS-IA.md): os 29 clipes baixados do Flow
# viram um master 2:1 de 2760x1380, com os letreiros por cima, pronto para o
# scripts/encode.sh gerar a entrega.
#
# Uso:
#   bash scripts/montar_flow.sh [pasta_com_os_clipes] [pasta_de_saida]
#   bash scripts/montar_flow.sh out/cenas/flow/clipes out/cenas/flow
#
# Os clipes tem que estar nomeados como a linha de tempo manda -- P01.mp4,
# P02-1.mp4, P02-2.mp4 ... --, e e o roteiro que diz o nome de cada um:
#   python3 scripts/cenas_ia.py --roteiro
#
# ============================================================================
# AS TRES COISAS QUE ESTE SCRIPT EXISTE PARA IMPEDIR
#
# 1. ESTICAR EM VEZ DE CORTAR. O Flow entrega 16:9 e a entrega e 2:1. Esticar
#    16:9 para 2:1 achata todo mundo em 11% e ninguem percebe olhando sozinho
#    -- percebe no telao, com a cara do artista no palco. Aqui e `crop` da
#    faixa central e depois `scale`, nessa ordem, e a conta esta escrita.
#
# 2. MONTAR FORA DE ORDEM. O produto e o percurso: o cliente comprou
#    reconhecer o parque dele na sequencia em que se anda nele. A ordem sai da
#    linha de tempo medida (`cenas_ia.py --timeline`), nao do `ls`.
#
# 3. ACEITAR CLIPE ERRADO CALADO. Antes de montar, cada arquivo e conferido
#    contra o que a linha de tempo espera: existe, tem a duracao certa e tem
#    proporcao 16:9. Clipe faltando ou com duracao errada PARA a montagem --
#    descobrir isso depois de exportar custa a exportacao inteira.
# ============================================================================

set -euo pipefail

CLIPES="${1:-out/cenas/flow/clipes}"
SAIDA="${2:-out/cenas/flow}"
LARGURA=2760
ALTURA=1380
FPS=30
TOLERANCIA_S=0.35     # o encoder da plataforma nao entrega duracao exata

TRAB="$SAIDA/_trabalho"
mkdir -p "$TRAB"

for prog in ffmpeg ffprobe python3; do
    command -v "$prog" >/dev/null 2>&1 || { echo "$prog nao encontrado no PATH" >&2; exit 1; }
done

echo "== linha de tempo =="
python3 scripts/cenas_ia.py --timeline > "$TRAB/timeline.json"
python3 - "$TRAB/timeline.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
print(f"  {len(d['clipes'])} clipes · {len(d['letreiros'])} letreiros · "
      f"{d['total_s']:.0f} s")
PY

# ---------------------------------------------------------------------------
echo
echo "== conferindo os clipes =="
FALTOU=0
while IFS=$'\t' read -r arquivo dur_esperada; do
    caminho="$CLIPES/$arquivo"
    if [ ! -f "$caminho" ]; then
        echo "  FALTA      $arquivo" >&2
        FALTOU=1
        continue
    fi
    leitura=$(ffprobe -v error -select_streams v:0 \
        -show_entries stream=width,height -show_entries format=duration \
        -of default=nw=1:nk=1 "$caminho")
    larg=$(echo "$leitura" | sed -n 1p)
    alt=$(echo "$leitura" | sed -n 2p)
    dur=$(echo "$leitura" | sed -n 3p)

    aviso=$(python3 - "$larg" "$alt" "$dur" "$dur_esperada" "$TOLERANCIA_S" <<'PY'
import sys
larg, alt, dur, esperada, tol = (float(x) for x in sys.argv[1:6])
saida = []
if abs(dur - esperada) > tol:
    saida.append(f"duracao {dur:.2f}s, esperada {esperada:.0f}s")
prop = larg / alt
if abs(prop - 16 / 9) > 0.02:
    saida.append(f"proporcao {prop:.3f}, esperada 1.778 (16:9)")
if alt < 720:
    saida.append(f"altura {alt:.0f}px -- gere em 1080p ou 4K, nao em 720p")
print(" · ".join(saida))
PY
)
    if [ -n "$aviso" ]; then
        echo "  PROBLEMA   $arquivo: $aviso" >&2
        FALTOU=1
    else
        printf "  ok         %-12s %sx%s  %.1fs\n" "$arquivo" "$larg" "$alt" "$dur"
    fi
done < <(python3 - "$TRAB/timeline.json" <<'PY'
import json, sys
for c in json.load(open(sys.argv[1], encoding="utf-8"))["clipes"]:
    print(f"{c['arquivo']}\t{c['duracao_s']}")
PY
)

if [ "$FALTOU" != "0" ]; then
    echo >&2
    echo "montagem interrompida: conserte os clipes acima e rode de novo." >&2
    echo "O roteiro diz o nome e a duracao de cada um:" >&2
    echo "  python3 scripts/cenas_ia.py --roteiro" >&2
    exit 1
fi

# ---------------------------------------------------------------------------
echo
echo "== corte 2:1 e conformacao =="
# A conta do corte, e ela e o coracao do script: de um quadro 16:9 de altura A,
# a faixa 2:1 tem altura A/2*... nao -- tem a MESMA largura e altura L/2. Em
# fracao da altura: (L/2)/A = (L/2)/(L*9/16) = 8/9. Sobram 1/9 da altura, meio
# em cima e meio embaixo. `crop=iw:iw/2` diz exatamente isso sem constante
# magica, e vale para 1080p, 4K ou o que a plataforma entregar.
: > "$TRAB/lista.txt"
while IFS=$'\t' read -r arquivo _; do
    destino="$TRAB/conf_${arquivo}"
    ffmpeg -y -v error -i "$CLIPES/$arquivo" \
        -vf "crop=iw:iw/2,scale=${LARGURA}:${ALTURA}:flags=lanczos,fps=${FPS},setsar=1" \
        -c:v prores_ks -profile:v 3 -pix_fmt yuv422p10le -vendor apl0 \
        -colorspace bt709 -color_primaries bt709 -color_trc bt709 \
        -an "$destino"
    echo "file '$(basename "$destino")'" >> "$TRAB/lista.txt"
    echo "  $arquivo -> 2:1"
done < <(python3 - "$TRAB/timeline.json" <<'PY'
import json, sys
for c in json.load(open(sys.argv[1], encoding="utf-8"))["clipes"]:
    print(f"{c['arquivo']}\t{c['duracao_s']}")
PY
)

echo
echo "== emenda na ordem do percurso =="
ffmpeg -y -v error -f concat -safe 0 -i "$TRAB/lista.txt" \
    -c copy "$TRAB/filme_sem_letreiro.mov"
echo "  $(python3 -c "import json;print(len(json.load(open('$TRAB/timeline.json',encoding='utf-8'))['clipes']))") clipes emendados"

# ---------------------------------------------------------------------------
echo
echo "== letreiros =="
# O letreiro entra aqui como TEXTO 2D, e nao como o objeto 3D da cena. No Plano
# B ele e geometria plantada no mundo; no Plano A isso deixa de servir, porque
# o clipe da IA nao segue o caminho da camera quadro a quadro -- ela interpola
# entre os dois extremos travados do jeito dela, e um letreiro renderizado do
# nosso percurso exato ia DESLIZAR contra a imagem. Como texto 2D ele nao tem
# com o que brigar, e a regra de 8%/4% vira conta direta sobre os 1380 px.
FONTE_ARQ="${FONTE:-}"
if [ -z "$FONTE_ARQ" ]; then
    FONTE_ARQ=$(python3 -c "
import json
print(json.load(open('$TRAB/timeline.json', encoding='utf-8')).get('tipografia', {}).get('arquivo', ''))
")
fi

if [ -n "$FONTE_ARQ" ] && [ -f "$FONTE_ARQ" ]; then
    echo "  fonte: $FONTE_ARQ"
    python3 - "$TRAB/timeline.json" "$FONTE_ARQ" "$TRAB" > "$TRAB/letreiros.txt" <<'PY'
import json, pathlib, sys

d = json.load(open(sys.argv[1], encoding="utf-8"))
trab = pathlib.Path(sys.argv[3])
fonte = sys.argv[2].replace("\\", "/").replace(":", r"\:")
cor = d.get("cor_do_texto", {}).get("texto", [0.92, 0.90, 0.86])
hexa = "".join(f"{int(max(0.0, min(1.0, c)) * 255):02x}" for c in cor)

# O TEXTO VAI EM ARQUIVO, e nao dentro do filtro. Motivo medido: "Dois, em
# frente ao parque" tem VIRGULA, e virgula e o separador de filtros do ffmpeg.
# Escapar virgula dentro de aspas simples e ambiguo -- as aspas do ffmpeg
# protegem o conteudo, entao um `\,` ali dentro sai literalmente como `\,` na
# tela. Com `textfile=` a string e lida verbatim e a classe inteira de bug
# desaparece: virgula, dois-pontos, apostrofo, porcento e acento passam iguais.
# `expansion=none` completa o servico -- sem ele, `%` e `{}` ainda seriam
# interpretados como diretiva de texto.
filtros = []
for i, l in enumerate(d["letreiros"]):
    # Caixa de seguranca de 90%: o rodape do bloco nao passa de 5% da base.
    base = int(1380 * 0.86)
    campos = [("t", l["texto"], l["altura_px"], base - l["altura_px"])]
    if l.get("apoio"):
        campos.append(("a", l["apoio"], l["altura_apoio_px"],
                       base + int(l["altura_apoio_px"] * 0.35)))
    for marca, txt, tam, y in campos:
        arq = trab / f"txt_{i:02d}{marca}.txt"
        arq.write_text(txt, encoding="utf-8")
        filtros.append(
            f"drawtext=fontfile='{fonte}'"
            f":textfile='{arq.as_posix()}':expansion=none"
            f":fontcolor=0x{hexa}:fontsize={tam}"
            f":x=(w-text_w)/2:y={y}"
            f":shadowcolor=black@0.55:shadowx=3:shadowy=3"
            f":enable='between(t,{l['entra_s']},{l['sai_s']})'")
print(",".join(filtros))
PY
    ffmpeg -y -v error -i "$TRAB/filme_sem_letreiro.mov" \
        -filter_complex_script "$TRAB/letreiros.txt" \
        -c:v prores_ks -profile:v 3 -pix_fmt yuv422p10le -vendor apl0 \
        -colorspace bt709 -color_primaries bt709 -color_trc bt709 \
        "$SAIDA/montagem_${LARGURA}x${ALTURA}.mov"
    echo "  $(python3 -c "import json;print(len(json.load(open('$TRAB/timeline.json',encoding='utf-8'))['letreiros']))") letreiros gravados"
else
    echo "  AVISO: fonte nao encontrada em '${FONTE_ARQ:-<vazio>}'." >&2
    echo "         O filme sai SEM LETREIRO. Aponte uma com:" >&2
    echo "           FONTE=/caminho/ArchivoNarrow-Bold.ttf bash scripts/montar_flow.sh" >&2
    echo "         Tipografia errada num telao de 4 m e visivel; e melhor sair sem." >&2
    cp "$TRAB/filme_sem_letreiro.mov" "$SAIDA/montagem_${LARGURA}x${ALTURA}.mov"
fi

echo
echo "=============================================================="
echo "  montagem: $SAIDA/montagem_${LARGURA}x${ALTURA}.mov"
ffprobe -v error -select_streams v:0 \
    -show_entries stream=width,height,r_frame_rate \
    -show_entries format=duration -of default=nw=1 \
    "$SAIDA/montagem_${LARGURA}x${ALTURA}.mov" | sed 's/^/  /'
echo
echo "  agora a entrega:"
echo "    bash scripts/encode.sh $SAIDA/montagem_${LARGURA}x${ALTURA}.mov out/entrega"
echo "=============================================================="
