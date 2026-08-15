#!/usr/bin/env bash
# Codifica os arquivos de entrega do AGROSHOW 2026 a partir da sequencia de
# PNG renderizada por render_shots.py em out/final/ (ou na pasta passada como
# primeiro argumento).
#
# Gera os tres arquivos do conjunto de entrega -- sempre os tres, nunca so um,
# porque o cliente ja teve falha de reproducao ao vivo -- mais a cartela de
# teste de 10 s. E a unica defesa possivel contra um processador de LED que
# ninguem confirmou:
#
#   master_2760x1380.mov   ProRes 422 HQ, 10 bits -- master, qualidade maxima
#   agroshow_2760x1380.mp4 H.264 -- principal para o operador
#   agroshow_1380x690.mp4  H.264 -- reserva leve, quase 1:1 com o painel
#   cartela_teste_10s.mp4  marcas de canto + caixa de seguranca de 90% + legenda
#
# 2:1 limpo em todos os quatro. Nenhum embute tarja -- tarja embutida nao se
# desfaz, e se o processador estiver em modo preencher, estica a tarja junto.
#
# Uso:
#   bash scripts/encode.sh [pasta_com_png] [pasta_de_saida]
#   bash scripts/encode.sh out/final out/entrega
#
# Fonte do texto da cartela: se drawtext reclamar de fonte, aponte uma:
#   FONTE=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf bash scripts/encode.sh

set -euo pipefail

ENTRADA="${1:-out/final}"
SAIDA="${2:-out/entrega}"
FPS=30
LARGURA=2760
ALTURA=1380

mkdir -p "$SAIDA"

if ! command -v ffmpeg >/dev/null 2>&1; then
    echo "ffmpeg nao encontrado no PATH" >&2
    exit 1
fi

# A entrada vem de um dos dois caminhos, e o script aceita os dois:
#
#   Plano B -- uma PASTA com a sequencia de PNG de scripts/render_shots.py
#   Plano A -- um ARQUIVO de video, a montagem dos clipes do Flow que sai de
#              scripts/montar_flow.sh
#
# O que vem depois do master e identico nos dois. A especificacao de entrega
# mora aqui e em nenhum outro lugar -- duplicar os quatro ffmpeg no montar_flow
# seria duas verdades sobre o que o cliente recebe.
MASTER="$SAIDA/master_${LARGURA}x${ALTURA}.mov"

if [ -f "$ENTRADA" ]; then
    echo "entrada: video (Plano A) -- $ENTRADA"
    dur=$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$ENTRADA")
    dim=$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height \
          -of csv=p=0:s=x "$ENTRADA")
    echo "  $dim · ${dur}s"
    if [ "$dim" != "${LARGURA}x${ALTURA}" ]; then
        echo "AVISO: a montagem esta em $dim e a entrega e ${LARGURA}x${ALTURA}." >&2
        echo "       Vai ser reescalada. Confira se o corte 2:1 foi feito." >&2
    fi
    echo "== master ProRes 422 HQ =="
    ffmpeg -y -i "$ENTRADA" \
        -vf "scale=${LARGURA}:${ALTURA}:flags=lanczos,setsar=1" \
        -c:v prores_ks -profile:v 3 -pix_fmt yuv422p10le -vendor apl0 \
        -colorspace bt709 -color_primaries bt709 -color_trc bt709 \
        "$MASTER"
else
    primeiro=$(ls "$ENTRADA"/*.png 2>/dev/null | sort | head -n1 || true)
    if [ -z "$primeiro" ]; then
        echo "nem video nem PNG em $ENTRADA." >&2
        echo "  Plano A: bash scripts/montar_flow.sh   -> passe o .mov dele aqui" >&2
        echo "  Plano B: blender ... render_shots.py   -> passe a pasta out/final" >&2
        exit 1
    fi
    inicio=$(basename "$primeiro" .png)
    inicio=$((10#$inicio))   # forca base 10: "00001" nao pode virar octal
    echo "entrada: sequencia de PNG (Plano B) -- primeiro quadro $inicio ($primeiro)"

    # Confere contra a decupagem: um lote parcial (calibracao, corte por --plano)
    # nao deve ir para o cliente sem que alguem saiba que esta parcial.
    if command -v python3 >/dev/null 2>&1 && [ -f data/planos.json ]; then
        esperado=$(python3 - <<'PY'
import sys
sys.path.insert(0, "scripts")
import terreno, planos as planos_mod
dados = terreno.carregar_mapa()
pacote = planos_mod.carregar("data/planos.json", dados=dados)
print(pacote["total_quadros"])
PY
)
        encontrado=$(ls "$ENTRADA"/*.png 2>/dev/null | wc -l | tr -d ' ')
        if [ "$encontrado" != "$esperado" ]; then
            echo "AVISO: $encontrado quadros em $ENTRADA, esperado $esperado (filme completo)." >&2
            echo "       Confira se e um lote parcial de proposito antes de mandar." >&2
        fi
    fi

    echo "== master ProRes 422 HQ =="
    ffmpeg -y -framerate "$FPS" -start_number "$inicio" -i "$ENTRADA/%05d.png" \
        -c:v prores_ks -profile:v 3 -pix_fmt yuv422p10le -vendor apl0 \
        -colorspace bt709 -color_primaries bt709 -color_trc bt709 \
        "$MASTER"
fi

echo "== H.264 principal (operador) =="
ffmpeg -y -i "$SAIDA/master_${LARGURA}x${ALTURA}.mov" \
    -c:v libx264 -profile:v high -pix_fmt yuv420p -preset slow -crf 16 \
    -g $((FPS / 2)) -keyint_min $((FPS / 2)) -sc_threshold 0 \
    -movflags +faststart \
    "$SAIDA/agroshow_${LARGURA}x${ALTURA}.mp4"

echo "== H.264 reserva leve =="
ffmpeg -y -i "$SAIDA/master_${LARGURA}x${ALTURA}.mov" \
    -vf "scale=1380:690:flags=lanczos" \
    -c:v libx264 -profile:v high -pix_fmt yuv420p -preset slow -crf 18 \
    -g $((FPS / 2)) -keyint_min $((FPS / 2)) -sc_threshold 0 \
    -movflags +faststart \
    "$SAIDA/agroshow_1380x690.mp4"

echo "== cartela de teste (10 s) =="
MARGEM_X=$((LARGURA * 5 / 100))
MARGEM_Y=$((ALTURA * 5 / 100))
CAIXA_L=$((LARGURA - 2 * MARGEM_X))
CAIXA_A=$((ALTURA - 2 * MARGEM_Y))

FONTE_OPT=""
if [ -n "${FONTE:-}" ]; then
    FONTE_OPT=":fontfile=${FONTE}"
fi

ffmpeg -y -f lavfi -i "color=c=0x1a1a1a:s=${LARGURA}x${ALTURA}:d=10:r=${FPS}" \
    -vf "
        drawgrid=w=${LARGURA}/12:h=${ALTURA}/6:t=1:c=white@0.15,
        drawbox=x=${MARGEM_X}:y=${MARGEM_Y}:w=${CAIXA_L}:h=${CAIXA_A}:color=yellow@0.9:t=3,
        drawbox=x=0:y=0:w=60:h=6:color=white:t=fill,
        drawbox=x=0:y=0:w=6:h=60:color=white:t=fill,
        drawbox=x=${LARGURA}-60:y=0:w=60:h=6:color=white:t=fill,
        drawbox=x=${LARGURA}-6:y=0:w=6:h=60:color=white:t=fill,
        drawbox=x=0:y=${ALTURA}-6:w=60:h=6:color=white:t=fill,
        drawbox=x=0:y=${ALTURA}-60:w=6:h=60:color=white:t=fill,
        drawbox=x=${LARGURA}-60:y=${ALTURA}-6:w=60:h=6:color=white:t=fill,
        drawbox=x=${LARGURA}-6:y=${ALTURA}-60:w=6:h=60:color=white:t=fill,
        drawtext=text='AGROSHOW 2026 · 2\\:1 · ${LARGURA}x${ALTURA}'${FONTE_OPT}:fontcolor=white:fontsize=48:x=(w-text_w)/2:y=(h-text_h)/2:box=1:boxcolor=black@0.5:boxborderw=20
    " \
    -c:v libx264 -profile:v high -pix_fmt yuv420p -preset slow -crf 18 \
    -movflags +faststart \
    "$SAIDA/cartela_teste_10s.mp4"

echo
echo "entrega em $SAIDA:"
ls -la "$SAIDA"
echo
echo "confira antes de mandar: area de seguranca de 90%, sem tarja embutida,"
echo "titulo legivel a 1379 px de largura, os quatro arquivos rodando ate o fim."
