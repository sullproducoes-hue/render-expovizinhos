# Render AGROSHOW 2026

Render fotorrealista da Feira AGROSHOW 2026, no Parque de Exposições de
Dois Vizinhos, Paraná.

O filme é ferramenta de venda de cota — estande, camarote e patrocínio.
Precisa parecer filmagem real, não maquete.

## Comece por aqui

1. `docs/BRIEFING.md` — brief, especificações travadas e pendências abertas
2. `data/mapa_agroshow26.json` — a planta extraída, fonte de verdade geométrica
3. `.claude/agents/render-agroshow.md` — o agente diretor técnico

## O agente

```
> use o agente render-agroshow para montar a base do terreno
```

Ele conhece o recinto, as quatro regras de realismo, as especificações de
entrega e o pipeline em seis fases.

## Especificações que não se negociam

- Proporção **2:1** (telão 4×2 m), render em 3840×1920 — não é 16:9
- Entrega em `.mov` (ProRes 422 HQ) **e** `.mp4` (H.264) — os dois
- Plano final saindo pelo portal

## Reproduzir a extração da planta

```bash
pip install pymupdf
python3 scripts/extract_map.py reference/Mapa_AGROSHOW26.pdf -o data/
```
