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
4. `docs/brief-audios.md` — transcrição literal dos áudios do cliente (fonte primária)
5. `docs/BRIEFING.md` — roteiro, restrições e especificações de entrega
6. `.claude/agents/render-agroshow.md` — agente diretor técnico da cena 3D
   (`docs/AGENTE-2.5D-suspenso.md` guarda o texto antigo, do caminho 2.5D)

## Caminho B — quadros gerados por IA a partir do footage

Esteira paralela à cena 3D: o quadro real do acervo entra numa IA geradora de
imagem, a imagem aprovada entra numa IA de vídeo, e o clipe entra na edição.

```bash
python3 scripts/plano_b.py --criar-pastas
```

Escreve `PLANO-B.md` (o runbook, na ordem de trabalho), `data/plano-b.json` e
**`out/plano-b/PLANO-B.html`** — a página que resolve o "não acho o quadro que
eu quero": um cartão por plano, na ordem do filme, com a placa em disco pelo
**caminho absoluto**, os prompts de imagem e de movimento prontos para copiar,
e a pasta onde salvar o que voltar.

`out/` não versiona, então a página e as pastas nascem localmente — e é o certo:
os caminhos são de `F:` e `E:`, e as miniaturas vêm de `out/acervo/thumbs/`.
**As 46 placas resolvem para arquivo em disco**; P17, que não tinha imagem
nenhuma, usa a das máquinas do P16 como placa emprestada, por ordem dele.

`docs/ONDE-GERAR.md` diz **onde** gerar: o estado de cada conta, o custo por
geração, a saída grátis pelo Google AI Studio, a regra de prompt
imagem-para-imagem e os cinco itens a conferir antes de animar.

## Gerar a cena 3D

```bash
pip install bpy pymupdf ezdxf
python3 scripts/build_scene.py --out out/cena.blend                 # filme completo
python3 scripts/build_scene.py --plano P19 --out out/P19.blend      # so a regiao de um plano
python3 scripts/build_scene.py --export-fbx out/cena.fbx            # para o Twinmotion

python3 scripts/planos.py --conferir     # confere a decupagem, sem bpy
```

134 estandes, 6 pavilhões, bacia da arena em 3 patamares, **22 planos** de
câmera (não mais uma curva única — ver `docs/PLANOS.md`), **176 s a 30 fps**
(5.280 quadros), render em **2560×1440**.

## Renderizar e entregar

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

Telão LED **P2,9 · 1379 × 690 px nativos · 4,00 × 2,00 m**.

> **A proporção mudou em 15/08/2026, por ordem dele** (`DECISOES.md` D044):
> *"sobre o painel de led eu vou exportar em 16:9 não se preocupa"*, e,
> perguntado se era render nativo ou master 2:1 reencaixado, **nativo**. O
> encaixe no painel passou a ser dele. Era 2:1 / 2760×1380 até então.

Master em **2560 × 1440 (16:9)**, em `.mov` (ProRes 422 HQ) **e** `.mp4`
(H.264), mais uma reserva leve em **1280 × 720**. Os três arquivos, sempre — o
cliente já teve falha de reprodução ao vivo. Gerados por `scripts/encode.sh` a
partir da sequência renderizada, mais uma cartela de teste de 10 s.

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
