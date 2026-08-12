# SULL · AGENTE DE MAPA DE EVENTO
**Sub-skill de `SULL.md` — produção de vídeo de percurso para parques e recintos de eventos**

Ativa quando o trabalho envolve: planta baixa + vídeo de apresentação de espaço, feira, parque de exposições, recinto, ou qualquer peça que precise orientar espacialmente o espectador dentro de um local.

---

## 0. PRINCÍPIO OPERACIONAL

Este tipo de vídeo tem **duas camadas que nunca se misturam**:

| Camada | Origem | Nunca vem de |
|--------|--------|--------------|
| **Esqueleto** — o mapa, o percurso, a orientação espacial | Vetor da planta, extrudado ou animado em 2.5D | IA generativa |
| **Pele** — imagens de apoio, atmosfera, público, atividades | IA generativa ou footage | Planta baixa |

**Regra dura:** se um modelo de IA for solicitado a "gerar o parque a partir da planta", ele vai inventar arquitetura plausível que não corresponde ao local. Isso já queimou projeto antes. A IA nunca desenha o layout — a IA só preenche o que acontece dentro dele.

---

## 1. ESTADO DO PROJETO ATIVO

**Cliente:** Agroshow 2026 — Parque de Exposições, Dois Vizinhos / PR
**Entrega:** domingo
**Recursos:** mapa vetorial (PDF, confirmado vetor), gravações de drone do parque, geração por IA
**Mote:** *É daqui que sai o alimento que sustenta o mundo*
**Assinatura:** *Aqui será um grande balcão de negócios*

### Restrições imutáveis — violação = rejeição pelo cliente

1. **Arena de rodeio NÃO tem arquibancada.** Apenas pista, camarotes nos dois lados, palco de frente. Qualquer imagem gerada com arquibancada é descartada sem discussão.
2. **A palavra "Kids" é proibida.** O cliente rejeitou explicitamente por ser americanizada. Use **Fazendinha** como nome, "Área Infantil" apenas em descrição secundária.
3. **Fazendinha tem hierarquia própria:** nome grande, descrição pequena embaixo.
4. **Portal em conceito celeiro**, versão econômica. Não gerar portal monumental — o construído será simplificado.
5. **Ordem dos pavilhões de animais 4/5/6 está em disputa** entre o áudio do cliente e o mapa. Bloqueado até confirmação. Não animar essa seção antes da resposta.

---

## 2. DNA VISUAL — bloco obrigatório em todo prompt de imagem

Toda imagem gerada para este projeto carrega este bloco. Ele é o que impede 19 cenas de parecerem 19 projetos diferentes.

```
LOOK LOCK — colar em todo prompt:
southern Brazil agricultural fair, Paraná countryside,
late afternoon golden hour, warm low sun, long soft shadows,
overcast-free sky with high thin clouds,
shot on full-frame camera, 35mm lens, f/2.8, shallow but readable depth,
natural documentary color, slightly desaturated greens, warm skin tones,
no lens flare, no HDR look, no oversaturation,
photorealistic, grounded, unglamorous
```

**Por que golden hour:** casa com o material de drone (que deve ser gravado/selecionado no mesmo horário) e é o único horário que unifica cenas internas e externas sem parecer colagem.

### Bloco de rejeição — colar como negative prompt

```
NEGATIVE: stadium bleachers, grandstand seating, tiered seating,
american county fair, ferris wheel, carnival rides,
texas rodeo aesthetic, cowboy hats in american style,
neon lights, night club lighting, drone shot, aerial view,
cgi look, video game render, plastic skin, perfect teeth,
crowd faces in focus, identifiable faces, logos, brand names,
text, watermark, signage with readable letters
```

**"Crowd faces in focus / identifiable faces" é crítico:** rosto reconhecível gerado por IA num evento real é o que denuncia a peça. Público sempre em movimento, contraluz, ou fora de foco.

---

## 3. AS 19 CENAS — consolidadas em 12 blocos para o prazo

Com 4 dias, 19 cenas separadas não fecham. Consolidação obrigatória:

| Bloco | Cenas do roteiro | Precisa de imagem IA? | Prioridade |
|-------|-----------------|----------------------|-----------|
| B01 · Chegada | 00 estacionamento + 01 portal | Sim — portal celeiro | ALTA |
| B02 · Pavilhões 1 e 2 | 02 + 04 | Sim — 1 imagem serve os dois | MÉDIA |
| B03 · Alimentação coberta | 03 | Sim | MÉDIA |
| B04 · Pavilhão 3 | 05 + 06 + 07 | Sim — 2 imagens (mercado / café colonial) | **ALTA** (diferencial) |
| B05 · Bosque | 08 | Sim | BAIXA |
| B06 · Leilões | 09 | Sim | MÉDIA |
| B07 · Animais | 10 | Sim — 2 imagens | BLOQUEADO |
| B08 · Julgamento + externos | 11 + 12 | Sim — 1 imagem | BAIXA |
| B09 · Fazendinha | 13 | Sim — 2 imagens | **ALTA** (diferencial) |
| B10 · Máquinas e veículos | 14 + 15 | Sim | MÉDIA |
| B11 · Shows e rodeio | 16 + 17 + 18 | Sim — 2 imagens | **ALTA** (diferencial) |
| B12 · Assinatura | 19 | Não — drone + tipografia | ALTA |

**Ordem de execução:** ALTA primeiro. Se o prazo apertar, os blocos BAIXA viram apenas mapa + título, sem imagem de apoio. O vídeo continua funcionando.

---

## 4. PROMPTS BASE POR BLOCO

Cada prompt = descrição específica + LOOK LOCK + NEGATIVE.

**B01 — Portal celeiro**
`entrance gate of a rural fairground built to look like a traditional wooden barn, corrugated metal roof, simple economical construction, red-brown weathered wood, wide gravel road leading through it, cars parked in field beyond`

**B03 — Praça de alimentação coberta**
`covered food court at a rural agricultural fair, long metal roof structure, simple wooden tables and plastic chairs, food stalls along one side, smoke from a churrasco grill, families eating, people seen from behind and in movement`

**B04a — Mercado do produtor**
`indoor farmers market inside a large exhibition pavilion, small booths with wooden crates of vegetables, honey jars, cheese wheels, cured sausages, handwritten price cards without readable text, visitors browsing`

**B04b — Café colonial**
`southern Brazilian colonial afternoon tea table, long table covered with breads, cakes, jams, cold cuts, cheese, tea and coffee pots, homemade abundance, warm interior of a pavilion, families seated`

**B09a — Fazendinha, porteira**
`wooden farm gate entrance to a children's area at a rural fair, rustic timber posts, hay bales, small pens with sheep visible beyond, children walking through`

**B09b — Fazendinha, atividades**
`children riding ponies led by a handler at a rural fair, inflatable playground in the background, border collie herding a small group of sheep, parents watching from a fence line`

**B11a — Rodeio**
`bull riding arena at a rural Brazilian fair, dirt arena floor, wooden fence perimeter, elevated private boxes on both sides only, NO bleachers, NO grandstand, bull mid-buck with rider, dust in golden light`

**B11b — Show**
`country music concert stage at a rural fair seen from behind the crowd, large crowd of people from behind with raised arms, stage lights, dusk sky, silhouettes, no identifiable faces`

> Ao gerar B11a, verificar o resultado especificamente contra a restrição de arquibancada antes de aprovar. É o ponto de falha mais provável de todo o projeto.

---

## 5. PIPELINE DE 4 DIAS

**Dia 1 — esqueleto**
- PDF no Illustrator, separar camadas por cor da legenda (`Select > Same > Fill Color`)
- Exportar SVG por categoria
- Montar composição AE 2.5D: camadas de vetor distribuídas no eixo Z, câmera do AE
- Definir o caminho da câmera seguindo a ordem do roteiro
- Nenhuma imagem ainda. Só o percurso funcionando.

**Dia 2 — geração**
- Gerar todas as imagens dos blocos ALTA e MÉDIA
- Gerar em lote, mesmo seed/modelo, LOOK LOCK idêntico
- Filtro de aprovação: rejeitar qualquer imagem com arquibancada, rosto nítido, texto legível, ou estética de county fair americano
- Reservar tempo para 2 rodadas — a primeira rodada nunca fecha

**Dia 3 — montagem**
- Imagens entrando como "janelas" sobre o mapa, não em tela cheia
- Títulos em Remotion ou AE, tokens Sull: `#0A0A0A` / `#F4A800`, Anton display + Barlow body
- Drone na abertura e no fechamento
- Trilha e sonoplastia

**Dia 4 — fechamento**
- Revisão contra a lista de restrições imutáveis
- Correção de cor unificando drone real e imagens geradas
- Master ProRes 422 HQ → entregas H.264

---

## 6. TRATAMENTO DAS IMAGENS DE IA — o que separa aceitável de queimado

[Certo] Imagem gerada por IA em tela cheia, parada, num vídeo de evento real é onde a peça morre. Três mitigações, todas obrigatórias:

1. **Nunca em tela cheia.** As imagens entram como janelas, cards ou insertos sobre o mapa. O mapa é o herói, a imagem é apoio. Isso reduz o tempo de escrutínio do espectador.
2. **Sempre em movimento.** Push-in lento de 3-5% ou parallax leve. Imagem estática de IA denuncia; imagem com movimento sutil lê como fotografia.
3. **Grão e correção unificados.** Aplique o mesmo grão e a mesma LUT nas imagens geradas e no drone real. A diferença de textura entre real e gerado é o que o olho pega primeiro.

**Duração máxima em tela por imagem gerada: 2 segundos.** Acima disso o espectador começa a analisar detalhes e encontra os erros.

---

## 7. COMPORTAMENTO DO AGENTE

Ao ser acionado neste projeto:

- Verifique primeiro se a pendência dos pavilhões 4/5/6 foi resolvida. Se não, não produza essa seção.
- Ao gerar qualquer prompt de imagem, anexe LOOK LOCK e NEGATIVE sem exceção.
- Ao receber uma imagem gerada para revisão, cheque contra as cinco restrições imutáveis antes de qualquer comentário estético.
- Se o prazo estiver em risco, corte blocos de prioridade BAIXA — nunca corte tempo de revisão.
- Não sugira Blender, Cycles ou modelagem 3D neste prazo.
- Português brasileiro direto, marcadores de confiança, sem qualificação repetida.
