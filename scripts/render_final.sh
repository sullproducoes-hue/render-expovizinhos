#!/usr/bin/env bash
# Render final do video de percurso da AGROSHOW 2026 e os arquivos de entrega.
#
# RODE ISTO NUMA MAQUINA COM GPU. No ambiente remoto do projeto nao ha placa:
# Cycles em CPU leva de 2 a 4 minutos por quadro em 2760x1380, e sao 4440
# quadros -- entre 6 e 12 dias. Com GPU e EEVEE, o mesmo filme sai em torno de
# uma hora.
#
# Uso:
#   bash scripts/render_final.sh                 # filme inteiro
#   bash scripts/render_final.sh 1 300           # so os 10 primeiros segundos
set -euo pipefail

INICIO="${1:-}"
FIM="${2:-}"
SAIDA="${SAIDA:-entrega}"
QUADROS="$SAIDA/quadros"
NOME="AGROSHOW2026_percurso"
FPS=30

mkdir -p "$QUADROS"

# ---------------------------------------------------------------------------
# 1. Cena. Reconstroi do zero a partir da planta -- nunca edite o .blend a mao.
echo "== montando a cena =="
python3 scripts/build_scene.py --out "$SAIDA/cena.blend"

# Conferencia de posicao antes de gastar horas de render.
python3 scripts/overlay_check.py --out "$SAIDA/conferencia-planta.png"
echo "confira $SAIDA/conferencia-planta.png antes de seguir"

# ---------------------------------------------------------------------------
# 2. Quadros. EEVEE com GPU; troque para CYCLES se quiser luz indireta melhor
#    e tiver tempo de maquina.
echo "== renderizando quadros =="
FAIXA=()
if [ -n "$INICIO" ]; then FAIXA=(--frame-start "$INICIO" --frame-end "${FIM:-$INICIO}"); fi

blender --background "$SAIDA/cena.blend" \
  --engine BLENDER_EEVEE_NEXT \
  --render-output "$QUADROS/q_" \
  --render-format PNG \
  "${FAIXA[@]}" \
  --render-anim

# ---------------------------------------------------------------------------
# 3. Entrega. Os tres arquivos combinados com o cliente, sempre os tres.
#    2:1 limpo, jamais com tarja embutida: tarja embutida nao se desfaz, e num
#    processador em modo preencher ela estica junto com a imagem.
echo "== codificando =="

# ProRes 422 HQ -- master
ffmpeg -y -framerate $FPS -i "$QUADROS/q_%04d.png" \
  -c:v prores_ks -profile:v 3 -pix_fmt yuv422p10le \
  "$SAIDA/${NOME}_2760x1380.mov"

# H.264 alto bitrate -- reproducao
ffmpeg -y -framerate $FPS -i "$QUADROS/q_%04d.png" \
  -c:v libx264 -preset slow -crf 14 -pix_fmt yuv420p \
  -movflags +faststart \
  "$SAIDA/${NOME}_2760x1380.mp4"

# Reserva leve, para processador que nao aguentar o master.
# 1380x690 e par nos dois lados; 1379x690 NAO codifica em 4:2:0.
ffmpeg -y -framerate $FPS -i "$QUADROS/q_%04d.png" \
  -vf scale=1380:690 \
  -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p \
  -movflags +faststart \
  "$SAIDA/${NOME}_1380x690.mp4"

echo
echo "entregar:"
ls -lh "$SAIDA"/*.mov "$SAIDA"/*.mp4
echo
echo "falta ainda a cartela de teste de 10 s com marcas de canto e a caixa de"
echo "90% (2484x1242) desenhada -- o operador confere o recorte com ela antes"
echo "de rodar o filme, e e a unica defesa contra um processador nao checado."
