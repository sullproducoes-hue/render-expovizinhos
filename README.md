# AGROSHOW 2026 — vídeo de apresentação do parque

Vídeo de percurso pelo Parque de Exposições de Dois Vizinhos (PR), na ordem
real de circulação do visitante, para exibição em telão.

**Caminho ativo: cena 3D em Blender**, gerada a partir da planta oficial, com
qualidade de jogo moderno. O material do caminho 2.5D anterior segue válido
para títulos, restrições e o LOOK LOCK das imagens de apoio.

## Comece por aqui

1. **`ESTADO.md`** — onde o projeto parou, o que foi descoberto, o que vem a seguir
2. `docs/PROPOSTA-3-DIAS.md` — cronograma, motor (Blender+Twinmotion com rede
   de segurança em EEVEE), portão de decisão, riscos
3. `docs/PLANOS.md` — a decupagem: 22 planos, cada um com alvo, lente, altura,
   movimento e duração, conferidos contra a faixa cinematográfica de drone
3b. **`docs/CENAS-IA.md`** — o **Plano A** operável: os planos viram clipes no
   Flow (ou Higgsfield), por quadro-para-vídeo. É o caminho ativo de finalização
4. `docs/brief-audios.md` — transcrição literal dos áudios do cliente (fonte primária)
5. `docs/BRIEFING.md` — roteiro, restrições e especificações de entrega
6. `.claude/agents/render-agroshow.md` — agente diretor técnico da cena 3D
   (`docs/AGENTE-2.5D-suspenso.md` guarda o texto antigo, do caminho 2.5D)

## Gerar a cena 3D

```bash
pip install bpy pymupdf ezdxf
python3 scripts/build_scene.py --out out/cena.blend                 # filme completo
python3 scripts/build_scene.py --plano P19 --out out/P19.blend      # so a regiao de um plano
python3 scripts/build_scene.py --export-fbx out/cena.fbx            # para o Twinmotion

python3 scripts/planos.py --conferir     # confere a decupagem, sem bpy
python3 scripts/tendas.py --conferir     # confere as famílias de tenda, sem bpy
python3 scripts/cenas_ia.py --conferir   # confere a grade do Flow, sem bpy
```

134 estandes **como tenda de lona nas posições medidas** (131 instanciados de 3
malhas — ver `data/tendas.json`), 8 pavilhões, bacia da arena em 3 patamares,
**22 planos** de câmera (não mais uma curva única — ver `docs/PLANOS.md`),
154 s a 30 fps, render em 2760×1380.

## Plano A — gerar as cenas no Flow (caminho ativo)

```bash
blender --background --python scripts/render_guias.py -- \
    --blend out/cena.blend --plataforma flow      # 51 quadros-guia, ~8 min
python3 scripts/cenas_ia.py --roteiro > out/cenas/roteiro-flow.md
```

**Nenhum clipe é texto-para-vídeo.** Cada clipe recebe o primeiro e o último
quadro renderizados da cena medida, e o prompt é proibido de descrever posição —
é isso que garante que o lugar seja este lugar, e não um parque genérico. Passo
a passo, regras de aspecto e o que conferir em cada clipe: **`docs/CENAS-IA.md`**.

## Plano B — renderizar tudo aqui e entregar

```bash
blender --background --python scripts/render_shots.py -- --blend out/cena.blend
bash scripts/encode.sh out/final out/entrega
```

`render_shots.py` renderiza plano a plano e é retomável — pula quadro já
existente em disco. `--animatic` gera rascunho rápido para aprovação;
`--plano <ID> --quadros 24 --cronometrar` calibra o tempo antes de prometer o
cronograma. `encode.sh` gera os três arquivos de entrega mais a cartela de
teste de 10 s.

```
> use o agente render-agroshow para revisar os prompts do bloco B11
```

## Restrições que causam rejeição

1. Arena de rodeio **sem arquibancada** — só pista, camarotes dos lados, palco de frente
2. A palavra **"Kids" é proibida** — use *Fazendinha*
3. Fazendinha: nome grande, descrição pequena embaixo
4. Portal em conceito **celeiro**, versão econômica
5. Quatro diferenciais com mais tela: Fazendinha, Rodeio, Café Colonial, Mercado do Produtor

## Entrega

Telão LED **P2,9 · 1379 × 690 px nativos · 4,00 × 2,00 m**. Proporção **2:1**.

Master em **2760 × 1380** (2× o nativo, dimensões pares), em `.mov` (ProRes
422 HQ) **e** `.mp4` (H.264), mais uma reserva leve em **1380 × 690**. Os três
arquivos, sempre — o cliente já teve falha de reprodução ao vivo. Gerados por
`scripts/encode.sh` a partir da sequência renderizada.

**Nunca masterize em 1379 × 690** — largura ímpar não codifica em H.264 4:2:0.

O painel tem 951.510 pixels para quatro metros de tela: tipografia fina some.
Título com no mínimo 8% da altura do quadro.

## O mapa não é vetor

PDF e DWG carregam o mesmo bitmap de 1806×1383 px. Zero geometria vetorial da
planta, e 4483 dos 4523 textos do DWG são caracteres soltos. Plano de "separar
camadas por cor no Illustrator" não funciona — ver `docs/BRIEFING.md`.

No caminho 3D ativo isso não bloqueia nada: `scripts/terreno.py` lê as
posições reais direto do JSON extraído (`data/mapa_agroshow26.json`), sem
precisar de contorno vetorial. Onde a planta não rotula um ponto que o áudio
descreve (o anel de máquinas, os expositores externos), a posição é derivada
da bacia ou marcada como estimada — ver as âncoras em `docs/PLANOS.md`. O
redesenho vetorial era necessário só para o mapa animado 2.5D, caminho
suspenso (`docs/AGENTE-2.5D-suspenso.md`).

## Reproduzir as extrações

```bash
pip install pymupdf ezdxf
python3 scripts/extract_map.py reference/Mapa_AGROSHOW26.pdf -o data/   # fonte de verdade
python3 scripts/extract_dwg.py reference/Mapa_AGROSHOW26.dxf -o data/   # auditoria
```

O DXF vem do DWG via LibreDWG: `dwg2dxf -o mapa.dxf mapa.dwg`
