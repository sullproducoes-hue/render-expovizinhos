# AGROSHOW 2026 — vídeo de apresentação do parque

Vídeo de percurso pelo Parque de Exposições de Dois Vizinhos (PR), na ordem
real de circulação do visitante, para exibição em telão.

**Caminho ativo: cena 3D em Blender**, gerada a partir da planta oficial, com
qualidade de jogo moderno. O material do caminho 2.5D anterior segue válido
para títulos, restrições e o LOOK LOCK das imagens de apoio.

## Comece por aqui

1. **`ESTADO.md`** — onde o projeto parou, o que foi descoberto, o que vem a seguir
2. `docs/brief-audios.md` — transcrição literal dos áudios do cliente (fonte primária)
3. `docs/BRIEFING.md` — roteiro, restrições e especificações de entrega
4. `.claude/agents/render-agroshow.md` — agente diretor técnico da cena 3D
   (`docs/AGENTE-2.5D-suspenso.md` guarda o texto antigo, do caminho 2.5D)

## Gerar a cena 3D

```bash
pip install bpy pymupdf ezdxf
python3 scripts/build_scene.py --out cena.blend
```

134 estandes, 6 pavilhões, bacia da arena em 3 patamares, percurso de 16 pontos
animado em 128 s, render em 2760×1380.

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
422 HQ) **e** `.mp4` (H.264). Os dois formatos, sempre.

**Nunca masterize em 1379 × 690** — largura ímpar não codifica em H.264 4:2:0.

O painel tem 951.510 pixels para quatro metros de tela: tipografia fina some.
Título com no mínimo 8% da altura do quadro.

## O mapa não é vetor

PDF e DWG carregam o mesmo bitmap de 1806×1383 px. Zero geometria vetorial da
planta, e 4483 dos 4523 textos do DWG são caracteres soltos. Plano de "separar
camadas por cor no Illustrator" não funciona — ver `docs/BRIEFING.md`.

O caminho é redesenhar como vetor por cima do raster. O motivo não é resolução
(1806 px cobre o painel de 1379): é que sem vetor não há camadas separadas, e
sem camadas não há animação de mapa.

## Reproduzir as extrações

```bash
pip install pymupdf ezdxf
python3 scripts/extract_map.py reference/Mapa_AGROSHOW26.pdf -o data/   # fonte de verdade
python3 scripts/extract_dwg.py reference/Mapa_AGROSHOW26.dxf -o data/   # auditoria
```

O DXF vem do DWG via LibreDWG: `dwg2dxf -o mapa.dxf mapa.dwg`
