#!/usr/bin/env bash
# Codifica os arquivos de entrega do AGROSHOW 2026 a partir da sequencia de PNG
# que render_shots.py grava em <pasta>/preview/.
#
# Gera sempre os TRES arquivos do conjunto, nunca so um -- o cliente ja teve
# falha de reproducao ao vivo -- mais a cartela de teste de 10 s, que e' a unica
# defesa possivel contra um processador de LED que ninguem confirmou:
#
#   master_2560x1440.mov    ProRes 422 HQ 10 bits -- master
#   agroshow_2560x1440.mp4  H.264 -- principal para o operador
#   agroshow_1280x720.mp4   H.264 -- reserva leve, roda em hardware fraco
#   cartela_teste_10s.mp4   marcas de canto + caixa de 90% + legenda
#
# PROPORCAO: 16:9, 2560x1440. Mudou em 15/08/2026 por ordem dele (DECISOES.md
# D044) -- era 2:1 / 2760x1380 desde a primeira sessao. Ele disse "sobre o
# painel de led eu vou exportar em 16:9 nao se preocupa" e, perguntado se era
# render nativo ou master 2:1 reencaixado, respondeu NATIVO. O encaixe no painel
# de 1379x690 passou a ser dele.
#
# Quadro LIMPO em todos os quatro. Nenhum embute tarja: tarja embutida nao se
# desfaz, e se o processador estiver em modo preencher ele estica a tarja junto.
#
# Uso:
#   bash scripts/encode.sh [pasta_do_render] [pasta_de_saida]
#   bash scripts/encode.sh "F:/render-agroshow/final" out/entrega
#
# Aceita tanto <pasta>/preview/*.png quanto <pasta>/*.png -- o render de verdade
# usa a primeira, o animatic e a calibracao usam a segunda.

set -euo pipefail

RAIZ="${1:-F:/render-agroshow/final}"
SAIDA="${2:-out/entrega}"
FPS=30
LARGURA=2560
ALTURA=1440
RESERVA_L=1280
RESERVA_A=720

# Onde estao os PNG: o render de entrega grava em preview/, o rascunho na raiz.
if [ -d "$RAIZ/preview" ]; then
    ENTRADA="$RAIZ/preview"
else
    ENTRADA="$RAIZ"
fi

mkdir -p "$SAIDA"

command -v ffmpeg >/dev/null 2>&1 || { echo "ffmpeg nao esta no PATH" >&2; exit 1; }

primeiro=$(ls "$ENTRADA"/*.png 2>/dev/null | sort | head -n1 || true)
[ -n "$primeiro" ] || { echo "nenhum PNG em $ENTRADA -- rode render_shots.py antes" >&2; exit 1; }
inicio=$(basename "$primeiro" .png)
inicio=$((10#$inicio))   # forca base 10: "00001" nao pode virar octal

encontrado=$(ls "$ENTRADA"/*.png 2>/dev/null | wc -l | tr -d ' ')
echo "entrada ......... $ENTRADA"
echo "primeiro quadro . $inicio"
echo "quadros em disco  $encontrado"

# O render e' retomavel e sai na ordem do roteiro, entao encodar no meio da fila
# e' util de proposito -- da para ver o filme ate onde ele chegou. Mas um lote
# parcial NAO pode ir para o cliente sem alguem saber que esta parcial.
PARCIAL=""
if command -v python >/dev/null 2>&1 && [ -f data/planos.json ]; then
    esperado=$(python - <<'PY'
import sys
sys.path.insert(0, "scripts")
import terreno, planos as planos_mod
print(planos_mod.carregar("data/planos.json", dados=terreno.carregar_mapa())["total_quadros"])
PY
) || esperado=""
    if [ -n "$esperado" ] && [ "$encontrado" != "$esperado" ]; then
        PARCIAL=" (PARCIAL)"
        echo
        echo "AVISO: $encontrado de $esperado quadros. Isto NAO e o filme inteiro."
        echo "       O arquivo sai com _PARCIAL no nome para ninguem mandar por engano."
        echo
    fi
fi
SUFIXO=""
[ -n "$PARCIAL" ] && SUFIXO="_PARCIAL_${encontrado}q"

MASTER="$SAIDA/master_${LARGURA}x${ALTURA}${SUFIXO}.mov"

echo "== master ProRes 422 HQ =="
ffmpeg -y -hide_banner -loglevel warning -stats \
    -framerate "$FPS" -start_number "$inicio" -i "$ENTRADA/%05d.png" \
    -c:v prores_ks -profile:v 3 -pix_fmt yuv422p10le -vendor apl0 \
    -colorspace bt709 -color_primaries bt709 -color_trc bt709 \
    "$MASTER"

echo "== H.264 principal (operador) =="
ffmpeg -y -hide_banner -loglevel warning -stats -i "$MASTER" \
    -c:v libx264 -profile:v high -pix_fmt yuv420p -preset slow -crf 16 \
    -g $((FPS / 2)) -keyint_min $((FPS / 2)) -sc_threshold 0 \
    -colorspace bt709 -color_primaries bt709 -color_trc bt709 \
    -movflags +faststart \
    "$SAIDA/agroshow_${LARGURA}x${ALTURA}${SUFIXO}.mp4"

echo "== H.264 reserva leve =="
ffmpeg -y -hide_banner -loglevel warning -stats -i "$MASTER" \
    -vf "scale=${RESERVA_L}:${RESERVA_A}:flags=lanczos" \
    -c:v libx264 -profile:v high -pix_fmt yuv420p -preset slow -crf 18 \
    -g $((FPS / 2)) -keyint_min $((FPS / 2)) -sc_threshold 0 \
    -colorspace bt709 -color_primaries bt709 -color_trc bt709 \
    -movflags +faststart \
    "$SAIDA/agroshow_${RESERVA_L}x${RESERVA_A}${SUFIXO}.mp4"

# ---------------------------------------------------------------- cartela
# drawtext no Windows aborta em SILENCIO sem fontfile: o filtro roda, o video
# sai, e o texto simplesmente nao existe. Ja custou 22 folhas de contato sem
# timecode neste computador. Aqui a fonte e' obrigatoria e o script morre se
# nao achar nenhuma.
FONTE_ARQ="${FONTE:-}"
if [ -z "$FONTE_ARQ" ]; then
    for c in "C:/Windows/Fonts/arialbd.ttf" "C:/Windows/Fonts/segoeuib.ttf" \
             "C:/Windows/Fonts/calibrib.ttf" \
             "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"; do
        [ -f "$c" ] && { FONTE_ARQ="$c"; break; }
    done
fi
[ -n "$FONTE_ARQ" ] || { echo "nenhuma fonte bold encontrada -- passe FONTE=/caminho/fonte.ttf" >&2; exit 1; }

# O ffmpeg le ':' como separador de opcao DENTRO do filtro, e no Windows todo
# caminho absoluto comeca com 'C:'. Escapar isso e' um pantano: 'C\:' funciona
# em alguns builds e quebra em outros, e a mensagem de erro ("No option name
# near...") nao diz que o problema e' a letra da unidade. A saida que nao tem
# pantano e' nao ter dois-pontos nenhum -- copiar a fonte para a pasta de saida
# e chamar por caminho RELATIVO, com o ffmpeg rodando la dentro.
#
# Achado ensaiando o proprio script com o lote parcial do render, antes de ele
# terminar. E' exatamente para isso que a cadeia de encode se ensaia cedo.
cp -f "$FONTE_ARQ" "$SAIDA/_cartela.ttf"
FONTE_FF="_cartela.ttf"
echo "== cartela de teste (10 s) == fonte: $FONTE_ARQ"

MARGEM_X=$((LARGURA * 5 / 100))    # 90% de area segura = 5% de margem por lado
MARGEM_Y=$((ALTURA * 5 / 100))
CAIXA_L=$((LARGURA - 2 * MARGEM_X))
CAIXA_A=$((ALTURA - 2 * MARGEM_Y))
# 8% da altura do quadro: o mesmo piso de tipografia dos letreiros do filme.
CORPO=$((ALTURA * 8 / 100))
CORPO_2=$((ALTURA * 4 / 100))

( cd "$SAIDA" && ffmpeg -y -hide_banner -loglevel warning -stats \
    -f lavfi -i "color=c=0x1a1a1a:s=${LARGURA}x${ALTURA}:d=10:r=${FPS}" \
    -vf "drawgrid=w=${LARGURA}/16:h=${ALTURA}/9:t=1:c=white@0.15,\
drawbox=x=${MARGEM_X}:y=${MARGEM_Y}:w=${CAIXA_L}:h=${CAIXA_A}:color=yellow@0.9:t=3,\
drawbox=x=0:y=0:w=80:h=8:color=white:t=fill,\
drawbox=x=0:y=0:w=8:h=80:color=white:t=fill,\
drawbox=x=${LARGURA}-80:y=0:w=80:h=8:color=white:t=fill,\
drawbox=x=${LARGURA}-8:y=0:w=8:h=80:color=white:t=fill,\
drawbox=x=0:y=${ALTURA}-8:w=80:h=8:color=white:t=fill,\
drawbox=x=0:y=${ALTURA}-80:w=8:h=80:color=white:t=fill,\
drawbox=x=${LARGURA}-80:y=${ALTURA}-8:w=80:h=8:color=white:t=fill,\
drawbox=x=${LARGURA}-8:y=${ALTURA}-80:w=8:h=80:color=white:t=fill,\
drawtext=fontfile=${FONTE_FF}:text='AGROSHOW 2026':fontcolor=white:fontsize=${CORPO}:x=(w-text_w)/2:y=(h/2)-text_h:box=1:boxcolor=black@0.55:boxborderw=24,\
drawtext=fontfile=${FONTE_FF}:text='16x9 - ${LARGURA}x${ALTURA} - caixa amarela = 90 por cento (${CAIXA_L}x${CAIXA_A})':fontcolor=white:fontsize=${CORPO_2}:x=(w-text_w)/2:y=(h/2)+20:box=1:boxcolor=black@0.55:boxborderw=18" \
    -c:v libx264 -profile:v high -pix_fmt yuv420p -preset slow -crf 18 \
    -colorspace bt709 -color_primaries bt709 -color_trc bt709 \
    -movflags +faststart \
    "cartela_teste_10s.mp4" )
rm -f "$SAIDA/_cartela.ttf"

# A cartela sem texto e' pior que nao ter cartela: parece boa e nao prova nada
# (memoria da casa: 22 folhas de contato sairam sem timecode porque o drawtext
# falhou calado). Portao: a faixa central, onde o titulo foi desenhado, tem de
# ter pixel claro. Fundo 0x1a1a1a da Y ~26; letra branca da Y ~235.
#
# `metadata=print` escreve em nivel INFO -- com -v error a linha some e o portao
# passa vazio, que foi o que aconteceu na primeira versao. Precisa de -v info.
prova=$(ffmpeg -v info -nostats -i "$SAIDA/cartela_teste_10s.mp4" \
    -vf "crop=iw/2:ih/6:iw/4:ih/2-ih/12,signalstats,metadata=print:key=lavfi.signalstats.YMAX" \
    -frames:v 1 -f null - 2>&1 | grep -o 'YMAX=[0-9.]*' | head -1 | cut -d= -f2 | cut -d. -f1 || true)
if [ -z "$prova" ]; then
    echo "ERRO: nao consegui medir a cartela -- o portao nao pode passar em silencio." >&2
    exit 1
fi
if [ "$prova" -lt 200 ]; then
    echo "ERRO: a cartela saiu SEM TEXTO (YMAX=$prova no centro). drawtext falhou calado." >&2
    exit 1
fi
echo "  cartela conferida: ha texto desenhado no centro (YMAX=$prova)"

echo
echo "entrega em $SAIDA:"
ls -la "$SAIDA"
echo
echo "Confira antes de mandar:"
echo "  - os quatro arquivos rodam ate o fim"
echo "  - nenhum tem tarja preta embutida"
echo "  - reduza o quadro a 1379 px de largura e leia o letreiro de longe"
[ -n "$PARCIAL" ] && echo "  - ATENCAO: este lote e PARCIAL ($encontrado quadros)"
exit 0
