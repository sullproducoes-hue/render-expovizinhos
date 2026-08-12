# AGROSHOW 2026 — vídeo de apresentação do parque

Mapa navegável animado em 2.5D do Parque de Exposições de Dois Vizinhos (PR),
percorrendo o recinto na ordem real de circulação do visitante, com imagens de
apoio geradas por IA entrando como janelas sobre o mapa.

**Prazo: domingo.** Não é render 3D fotorrealista — esse caminho está em
`docs/CAMINHO-3D.md`, como projeto futuro.

## Comece por aqui

1. `docs/brief-audios.md` — transcrição literal dos áudios do cliente (fonte primária)
2. `docs/BRIEFING.md` — roteiro, restrições, blocos de execução e pendências
3. `.claude/agents/render-agroshow.md` — o agente diretor técnico

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

Proporção **2:1** (telão 4×2 m), render 3840×1920, em `.mov` (ProRes 422 HQ)
**e** `.mp4` (H.264). Os dois formatos, sempre.

## O mapa não é vetor

PDF e DWG carregam o mesmo bitmap de 1806×1383 px. Zero geometria vetorial da
planta. Plano de "separar camadas por cor no Illustrator" não funciona — ver
`docs/BRIEFING.md`. O caminho é redesenhar como vetor por cima do raster.

## Reproduzir as extrações

```bash
pip install pymupdf ezdxf
python3 scripts/extract_map.py reference/Mapa_AGROSHOW26.pdf -o data/   # fonte de verdade
python3 scripts/extract_dwg.py reference/Mapa_AGROSHOW26.dxf -o data/   # auditoria
```

O DXF vem do DWG via LibreDWG: `dwg2dxf -o mapa.dxf mapa.dwg`
