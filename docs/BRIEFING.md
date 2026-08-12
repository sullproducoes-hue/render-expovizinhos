# AGROSHOW 2026 — Briefing técnico

Render fotorrealista da Feira AGROSHOW 2026, no Parque de Exposições de
Dois Vizinhos, Paraná.

**Objetivo comercial:** o filme é ferramenta de venda de cota — estande,
camarote e patrocínio. Não é peça institucional decorativa. Toda decisão
técnica se subordina a isso.

---

## Especificações travadas

Vieram do cliente por escrito (`reference/Sobre_os_audios.txt`). Não altere sem
autorização.

| Item | Especificação |
|---|---|
| Proporção | **2:1** (telão de 4×2 m) — **não é 16:9** |
| Resolução de render | 3840×1920 |
| Orientação | Tudo horizontal. Sem verticais no filme mestre. |
| Formatos de entrega | `.mov` **e** `.mp4` — os dois, obrigatoriamente |
| `.mov` | ProRes 422 HQ (exibição em telão) |
| `.mp4` | H.264 alto bitrate (reserva) |
| Plano final | Câmera saindo pelo portal, replicando o fechamento do último vídeo aprovado |

**Sobre o formato duplo:** o cliente registrou que "pode dar erro na hora de
passar". Já houve falha de reprodução ao vivo. Redundância de formato é
requisito de segurança, não preferência estética.

**Pendência crítica de exibição:** confirmar se "telão 4×2" se refere a
**metros** ou a **contagem de painéis**, e qual a resolução nativa do painel.
Entregar em resolução incompatível com LED wall é a falha mais cara e mais
comum deste tipo de projeto. Resolver antes de qualquer render definitivo.

---

## O recinto

Fonte: `data/mapa_agroshow26.json`, extraído do PDF oficial da planta via
`scripts/extract_map.py`.

| | |
|---|---|
| Área locável cotada | 17.949 m² (1,79 ha) em 181 blocos |
| Estandes codificados | 134 — série A: 41, série C: 93 |
| Soma dos 134 estandes | 10.814 m² |
| Módulo dominante série C | 100 m² (10×10) — 39 unidades |
| Módulo dominante série A | 25 m² (5×5) — 35 unidades |
| Pavilhões de animais | 6 (5× 720 m² + 1× 560 m²) = 4.160 m² |
| Zonas nomeadas | 122 |

O emparelhamento código→área tem distância média de 3,2 pt e máxima de 26,9 pt
na prancha, o que é confiável.

**Consequência de modelagem:** 39 estandes de 10×10 e 35 de 5×5 são instâncias
de dois assets. Modele dois módulos, instancie 74 vezes com variação dirigida
de lona, sinalização e conteúdo. Não modele um a um.

### Zonas

Arena de Rodeio · Palco · Palco After · Camarotes Lado A e B · Pista de
Julgamentos · Pavilhões de Gado Leite, Gado Corte, Ovinos e Caprinos, Pequenos
Animais, Equinos e Núcleo Carra Branca · Praça de Alimentação Coberta e Aberta ·
Mercado do Produtor · Café Colonial e Cozinha Didática · Fazendinha / Área
Infantil · Arena do Conhecimento UTFPR · Recinto de Leilões · Espaço É
Churrasco · Portal de Entrada · estacionamentos · bosque e mata nativa.

### Limitação da planta

**O PDF não é vetor CAD.** O desenho é um bitmap de 1806×1383 px — cerca de
90 DPI sobre uma prancha de 508 mm — com camada de texto por cima. A página tem
apenas 2 primitivas vetoriais.

Consequências:
- Não há geometria importável. As coordenadas no JSON são da camada de texto,
  úteis para posicionar e conferir, não para extrair contorno.
- **Peça o DWG/DXF original.** Ele existe: o PDF saiu de um CAD. Com ele a
  planta entra no 3D como geometria exata e economiza dezenas de horas.
- Sem o DWG, o caminho é retraçado guiado pelo JSON somado a ortomosaico de
  drone para o terreno real.

---

## Referência de qualidade

O cliente aprovou como direção o vídeo da **EXPOJARA — Tapejara-PR 2026**
(2:13, 28 planos, feito em Lumion ou Twinmotion) e pediu o mesmo tipo de
narrativa, **mas fotorrealista**.

Decupagem da referência:

| Tempo | Conteúdo |
|---|---|
| 0–12s | Aéreo geral, exposições de animais |
| 12–21s | Portal, bilheteria, logo, grade de shows |
| 21–36s | Totem de boas-vindas, tendas, bovinos |
| 36–43s | Exposição de frota municipal |
| 43–67s | Praça de alimentação, interior das tendas |
| 67–75s | Parque de diversões, aéreo noturno |
| 75–100s | Arena de rodeio, fogos, camarote, bar |
| 100–119s | Palco, shows, DJ, camarote premium |
| 119–133s | Aéreos noturnos de fechamento |

### Por que a referência lê como maquete

Em ordem de gravidade — ataque nesta ordem:

1. **Pessoas.** Poses rígidas e repetidas, escala errada, sem peso, multidão
   clonada em bloco. É o denunciador número um.
2. **Luz.** Sem GI real. Cones de refletor chapados em vez de volumetria.
   Saturação de palco sem bounce no ambiente.
3. **Materiais.** Grama tileada visível, sem variação nem desgaste. Lona
   plástica, sem translucidez.
4. **Câmera.** Movimento perfeito demais, sem inércia, sem motion blur, sem
   imperfeição de lente.

Resolver 1 e 2 já entrega a maior parte do salto de realismo. Trocar de motor
de render sem resolver as pessoas não muda nada.

---

## Pendências abertas

| # | Pendência | Impacto |
|---|---|---|
| 1 | **Transcrever os 3 áudios do cliente** (7min43 de WhatsApp, ~Tega) | Alto — contêm a visão ponto a ponto |
| 2 | **DWG/DXF da planta** | Alto — dezenas de horas de retraçado |
| 3 | Data do evento e abertura da venda de cotas | Alto — define cronograma e prioridade de entregável |
| 4 | "Telão 4×2": metros ou painéis? Resolução nativa? | Alto — risco de entrega inutilizável |
| 5 | Acesso ao material de drone | Médio — necessário para ortomosaico do terreno |
| 6 | A cena Lumion da Expojara é do estúdio? | Médio — biblioteca reaproveitável |
| 7 | Identidade visual AGROSHOW 2026 em vetor | Médio — placas, totens, letreiros |

### Sobre a pendência 1

Os três áudios (4:43, 2:10 e 0:50) trazem a percepção do cliente ponto a ponto
e são o briefing criativo real. **Não foi possível transcrevê-los no ambiente
remoto:** todas as rotas de ASR estão bloqueadas pelo proxy de egresso —
HuggingFace e CDN da OpenAI (sem download de modelo Whisper), Alphacephei (sem
Vosk) e `at.adobe.com` (403 no CONNECT, sem upload para a Adobe).

Transcreva localmente antes de fechar o roteiro. Qualquer máquina com Whisper
resolve em minutos:

```bash
pip install faster-whisper
python3 -c "
from faster_whisper import WhisperModel
m = WhisperModel('medium', device='cpu', compute_type='int8')
for f in ['audio1.ogg','audio2.ogg','audio3.ogg']:
    segs, _ = m.transcribe(f, language='pt')
    print(f'--- {f}')
    for s in segs: print(f'[{s.start:.0f}s] {s.text}')
"
```

Cole o resultado em `docs/brief-audios.md` e revise este briefing à luz dele.
Enquanto isso, o roteiro é hipótese, não decisão.

---

## Estrutura do repositório

```
.claude/agents/render-agroshow.md   Agente diretor técnico
docs/BRIEFING.md                    Este arquivo
data/mapa_agroshow26.json           Planta extraída — fonte de verdade
scripts/extract_map.py              Extração reproduzível do PDF
reference/                          Planta original e material do cliente
```
