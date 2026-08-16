#!/usr/bin/env bash
# Vigia o render e fecha a entrega sozinho.
#
# Existe por causa de uma ordem com hora marcada: "Eu vou sair 4h00 tome todas
# as medidas necessarias pra finalizar hoje". O render sao ~13,3 h e ninguem vai
# estar acordado quando ele terminar. Este script faz as tres coisas que uma
# pessoa faria de madrugada:
#
#   1. conta os quadros de tempos em tempos;
#   2. se o render MORREU (a contagem parou de crescer) e ainda falta quadro,
#      RELANCA -- render_shots.py pula o que ja existe, entao retomar e' de
#      graca e nao ha risco de refazer trabalho;
#   3. quando fecha os 5.280, roda scripts/encode.sh e deixa os tres arquivos
#      de entrega mais a cartela prontos em out/entrega/.
#
# Ele nao decide nada. So repete o que ja esta escrito.
#
#   bash scripts/fechar_entrega.sh
#   bash scripts/fechar_entrega.sh 5280 "F:/render-agroshow/final" out/entrega

set -uo pipefail

# O total NAO pode ser constante no script. Em 15/08 ele ficou 5280 aqui e a
# decupagem passou para 5475 sem ninguem perceber: o vigia teria encodado 195
# quadros antes do fim e encerrado o laco -- entregando filme cortado e nunca
# mais voltando. Quem sabe o total e data/planos.json, e e' dele que se pergunta.
if [ $# -ge 1 ]; then
    ESPERADO="$1"
else
    ESPERADO=$(.venv/Scripts/python.exe -c "
import sys; sys.path.insert(0, 'scripts')
import terreno, planos as pm
print(pm.carregar('data/planos.json', dados=terreno.carregar_mapa())['total_quadros'])
" 2>/dev/null) || ESPERADO=""
    [ -n "$ESPERADO" ] || { echo 'nao consegui ler o total de data/planos.json' >&2; exit 1; }
fi
RENDER="${2:-F:/render-agroshow/final}"
SAIDA="${3:-out/entrega}"
BLEND="out/cena.blend"
BLENDER="C:/Program Files/Blender Foundation/Blender 5.2/blender.exe"
INTERVALO=300          # 5 min entre contagens
PACIENCIA=2            # 2 contagens paradas (10 min) ja acende a luz
MUDO_MAX=420           # 7 min sem NENHUMA escrita no log = morreu ou travou
LOG="out/fechar-entrega.log"

diz() { echo "[$(date '+%d/%m %H:%M:%S')] $*" | tee -a "$LOG"; }

# Trava de instancia unica. Sem ela, chamar o script duas vezes poe dois vigias
# no mesmo log -- e, pior, DOIS encodes disputando o mesmo arquivo de saida no
# fim. Aconteceu em 15/08: tres vigias vivos ao mesmo tempo, achados por `ps`,
# nao pelo log (o log so ficava com o dobro de linhas e parecia normal).
TRAVA="out/.fechar-entrega.pid"
if [ -f "$TRAVA" ] && kill -0 "$(cat "$TRAVA")" 2>/dev/null; then
    echo "ja existe um vigia rodando (pid $(cat "$TRAVA")). Saindo." >&2
    exit 0
fi
echo $$ > "$TRAVA"
trap 'rm -f "$TRAVA"' EXIT

conta() { ls "$RENDER/preview"/*.png 2>/dev/null | wc -l | tr -d ' '; }

diz "vigia iniciado -- esperando $ESPERADO quadros em $RENDER/preview"

# -1 de proposito: na primeira volta a contagem sempre empataria com ela mesma
# e o vigia acusaria um falso "parado" antes de ter qualquer historico.
anterior=-1
parado=0

while true; do
    atual=$(conta)
    if [ "$atual" -ge "$ESPERADO" ]; then
        diz "render completo: $atual/$ESPERADO quadros"
        break
    fi

    if [ "$atual" -le "$anterior" ]; then
        parado=$((parado + 1))
        diz "parado em $atual quadros ($parado de $PACIENCIA)"
        if [ "$parado" -ge "$PACIENCIA" ]; then
            # Contagem parada NAO e' prova de que o render morreu -- pode ser um
            # plano pesado, ou o disco engasgando na gravacao do EXR. Relancar
            # com o Blender ainda TRABALHANDO poe dois processos disputando a
            # mesma GPU e a mesma pasta.
            #
            # Mas "existe um blender.exe" tambem NAO e' prova de que ele esta
            # trabalhando: em 15/08 sobrou um blender.exe vivo e mudo depois que
            # o processo pai foi encerrado, e a checagem por processo travou o
            # vigia num impasse -- ele nao relancava porque via o zumbi. Quem
            # decide e' o RELOGIO DO LOG: se o render escreve, ele esta vivo.
            idade=$(( $(date +%s) - $(stat -c %Y out/render-final.log 2>/dev/null || echo 0) ))
            if [ "$idade" -lt "$MUDO_MAX" ]; then
                diz "contagem parada, mas o log escreveu ha ${idade}s -- ainda trabalhando"
                parado=0
            else
                diz "o log esta mudo ha ${idade}s: o render morreu ou travou"
                taskkill //F //IM blender.exe >/dev/null 2>&1
                sleep 5
                diz "relancando -- render_shots.py pula os $atual quadros que ja existem"
                # `nohup ... &` a partir DESTE processo, que e' quem sobrevive.
                # Testado em 15/08: um `blender.exe` lancado por uma sessao de
                # shell efemera morre junto com ela (foi assim que o render caiu
                # no quadro 238), mas um lancado por este vigia vive enquanto o
                # vigia viver. `cmd //c start` e `schtasks` foram tentados e sao
                # piores: os dois travam a chamada ou disparam duas vezes.
                #
                # NOTA: cada sessao do Blender 5.2 aparece como DOIS `blender.exe`
                # no tasklist, com poucos segundos de diferenca. Isso e' normal --
                # dois processos NAO querem dizer dois renders. Quem conta sessao
                # e' o numero de linhas "Read blend" em out/render-final.log.
                nohup "$BLENDER" --background --python scripts/render_shots.py -- \
                    --blend "$BLEND" --saida "$RENDER" >> out/render-final.log 2>&1 &
                parado=0
            fi
        fi
    else
        falta=$((ESPERADO - atual))
        # 9,1 s/quadro medido em regime nesta maquina, 15/08
        horas=$(awk "BEGIN{printf \"%.1f\", $falta * 9.1 / 3600}")
        diz "$atual/$ESPERADO quadros · faltam $falta · ~${horas} h"
        parado=0
    fi
    anterior=$atual
    sleep "$INTERVALO"
done

diz "codificando a entrega"
if bash scripts/encode.sh "$RENDER" "$SAIDA" >> "$LOG" 2>&1; then
    diz "ENTREGA PRONTA em $SAIDA"
    ls -la "$SAIDA" | tee -a "$LOG"
else
    diz "ERRO no encode -- ver $LOG. Os quadros estao intactos em $RENDER/preview,"
    diz "e da para rodar de novo: bash scripts/encode.sh \"$RENDER\" \"$SAIDA\""
    exit 1
fi
