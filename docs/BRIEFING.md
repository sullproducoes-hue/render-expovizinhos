# AGROSHOW 2026 — Briefing técnico

Vídeo de apresentação do Parque de Exposições de Dois Vizinhos, Paraná, para a
Feira AGROSHOW 2026.

**O que é:** um mapa navegável animado em 2.5D, percorrendo o parque na ordem
real de circulação do visitante, com títulos a cada área e imagens de apoio
geradas por IA entrando como janelas sobre o mapa.

**O que não é:** render arquitetônico fotorrealista. Existe esse caminho e ele
está em `docs/CAMINHO-3D.md`, como projeto futuro. Não cabe neste prazo.

**Prazo: domingo.**

Fonte primária: `docs/brief-audios.md` — transcrição literal dos três áudios do
cliente. Em qualquer divergência, a transcrição vence este documento.

---

## Especificações travadas

| Item | Especificação |
|---|---|
| Proporção | **2:1** (telão 4×2 m) — **não é 16:9** |
| Resolução | 3840×1920 |
| Orientação | Tudo horizontal |
| Entrega | `.mov` (ProRes 422 HQ) **e** `.mp4` (H.264) — os dois |
| Mote de abertura | *É daqui que sai o alimento que sustenta o mundo* |
| Assinatura final | *Aqui será um grande balcão de negócios* |

O formato duplo é requisito de segurança: o cliente registrou que "pode dar erro
na hora de passar" e já teve falha de reprodução ao vivo.

**Pendência de exibição:** confirmar se "telão 4×2" é metros ou contagem de
painéis, e a resolução nativa do painel. Resolver antes do master.

---

## Roteiro — ordem ditada pelo cliente

| # | Área | Título na tela | Observação |
|---|---|---|---|
| 00 | Estacionamentos | *Estacionamento* | Dois, em frente ao parque. Ponto de vista de quem chega |
| 01 | **Portal de Entrada** | *É daqui que sai o alimento que sustenta o mundo* | Conceito celeiro, versão econômica |
| 02 | Pavilhão 1 | *Pavilhão 1 — Indústria, Comércio e Prestação de Serviços* | Logo à direita de quem entra |
| 03 | Área coberta ao fundo | *Praça de Alimentação Coberta* | Mesas, cadeiras, guichês, lado da churrasqueira |
| 04 | Pavilhão 2 | *Pavilhão 2 — Indústria, Comércio e Prestação de Serviços* | — |
| 05 | Pavilhão 3, entrada | *Mercado do Produtor* | Diferencial |
| 06 | Pavilhão 3, 1ª metade | *Agroindústrias* | Guichês dos expositores |
| 07 | Pavilhão 3, fundos | *Café Colonial* + *Cozinha Didática* | Divisão de meia-parede. Cozinha de um lado, cozinha didática do outro. Diferencial |
| 08 | Bosque | *Praça de Alimentação Aberta* | Percurso passa por dentro do bosque |
| 09 | Sociedade Rural | *Recinto de Leilões* | Leilão acontecendo |
| 10 | Pavilhões de Animais | *Exposição de Animais* | 6 pavilhões — ver abaixo |
| 11 | Pista de Julgamento | *Pista de Julgamentos* | Área de pasto verde |
| 12 | Expositores Externos | *Expositores Externos* | — |
| 13 | **Fazendinha** | *Fazendinha* (grande) + descrição menor | Ao lado da pista de tiro de laço, porteira de destaque. Diferencial |
| 14 | 1º anel | *Máquinas, Equipamentos e Implementos Agrícolas* | — |
| 15 | 1º anel, continuação | *Veículos e Motos Náuticas* | Depois das máquinas, na volta do anel |
| 16 | 2º patamar descendo | *Área de Shows* | — |
| 17 | Frente ao palco | *Arena de Rodeio* | Diferencial |
| 18 | Palco | *Palco Principal* | Artista cantando, público lotado |
| 19 | Assinatura | *Aqui será um grande balcão de negócios* | — |

Conteúdo da Fazendinha: brinquedos infláveis, passeio a cavalo, pônei,
apresentação de Border Collie com ovelhas.

---

## Pavilhões de animais — divergência resolvida

Um briefing anterior (`reference/BRIEFING_chat_anterior.md`) marcou este bloco
como **BLOQUEADO**, alegando que as posições 4, 5 e 6 estavam trocadas entre o
áudio do cliente e a planta.

**Não estão.** Ordenando os rótulos da planta pela coordenada Y real, de norte
para sul, a sequência física é:

| # | Pavilhão | y |
|---|---|---|
| 1 | Gado Leite | 507,6 |
| 2 | Núcleo Cara Branca | 546,5 |
| 3 | Gado Corte | 585,4 |
| 4 | Ovinos e Caprinos | 624,9 |
| 5 | Pequenos Animais | 663,2 |
| 6 | Equinos | 699,7 |

O cliente ditou: gado de leite, núcleo cara branca, diversas raças, ovinos e
caprinos, pequenos animais, equinos. **Bate exatamente.** O briefing anterior
leu os rótulos na ordem de extração do texto, não na ordem espacial.

A única diferença é o ponto 3: o cliente disse "diversas raças, pode usar
Nelore, o gado branco", e a planta diz "Gado de Corte" — que é a mesma coisa
descrita por dentro. Não é conflito.

**O bloco de animais está liberado.** Não há o que perguntar ao cliente aqui.

Referências de raça ditadas no áudio, para os prompts: pavilhão 2 é cara branca
(corpo vermelho, cabeça branca — Hereford/Braford); pavilhão 3 pode usar Nelore,
branco.

---

## Restrições imutáveis

1. **Arena de rodeio SEM arquibancada.** Só pista, camarotes nos dois lados e
   palco de frente. Modelo de IA tende a gerar arquibancada em cena de rodeio —
   é o ponto de falha mais provável do projeto.
2. **A palavra "Kids" é proibida.** Use *Fazendinha*; "Área Infantil" só em
   descrição secundária.
3. **Fazendinha:** nome grande, descrição pequena embaixo.
4. **Portal em conceito celeiro, econômico.** A foto em `reference/` é o portal
   que existe hoje, não o que será construído.
5. **Quatro diferenciais** com mais tela e peso: Fazendinha, Rodeio, Café
   Colonial, Mercado do Produtor.

---

## Blocos de execução

19 cenas não fecham em quatro dias. Consolidação:

| Bloco | Cenas | Imagens IA | Prioridade |
|---|---|---|---|
| B01 · Chegada | 00 + 01 | 1 (portal celeiro) | ALTA |
| B02 · Pavilhões 1 e 2 | 02 + 04 | 1 serve os dois | MÉDIA |
| B03 · Alimentação coberta | 03 | 1 | MÉDIA |
| B04 · Pavilhão 3 | 05 + 06 + 07 | 2 | **ALTA** |
| B05 · Bosque | 08 | 1 | BAIXA |
| B06 · Leilões | 09 | 1 | MÉDIA |
| B07 · Animais | 10 | 2 | **LIBERADO** |
| B08 · Julgamento + externos | 11 + 12 | 1 | BAIXA |
| B09 · Fazendinha | 13 | 2 | **ALTA** |
| B10 · Máquinas e veículos | 14 + 15 | 1 | MÉDIA |
| B11 · Shows e rodeio | 16 + 17 + 18 | 2 | **ALTA** |
| B12 · Assinatura | 19 | — (drone + tipografia) | ALTA |

ALTA primeiro. Blocos BAIXA, se o prazo apertar, viram mapa e título sem
imagem. Nunca corte tempo de revisão.

---

## O mapa não é vetor

Os dois arquivos entregues foram auditados:

| Arquivo | Conteúdo real |
|---|---|
| `Mapa_AGROSHOW26.pdf` | 2 primitivas vetoriais + bitmap 1806×1383 px (~90 DPI) + camada de texto |
| `Mapa_AGROSHOW26.dwg` (AC1018) | Mesmo bitmap + 4883 TEXT + 1 LINE + 1 SOLID + 2 HATCH. Zero polilinha, zero arco |

E 4483 dos 4523 textos do DWG são **caracteres soltos**, gravados glifo a
glifo — assinatura de PDF importado para CAD. Só 40 são rótulos legíveis.

**Consequências:**

1. Qualquer plano de abrir no Illustrator e separar camadas por cor da legenda
   (`Select > Same > Fill Color`) **falha** — não há preenchimento vetorial.
2. 1806 px de largura não preenchem um quadro de 3840 px.
3. O DWG não desbloqueou nada. A extração do PDF continua sendo a melhor fonte,
   porque o PDF preserva as palavras montadas.

**Caminho:** redesenhar o mapa como vetor limpo por cima do raster, com as
categorias da legenda em camadas separadas. Para mapa animado isso é o certo de
qualquer forma — você quer arte de marca, legível em movimento e separável, não
a prancha do engenheiro. Orce 4 a 8 horas, tarefa do Dia 1.

Em paralelo, peça o arquivo nativo a quem desenhou o mapa.

---

## Dados do recinto

Fonte: `data/mapa_agroshow26.json` (via `scripts/extract_map.py`).

| | |
|---|---|
| Área locável cotada | 17.949 m² (1,79 ha) em 181 blocos |
| Estandes codificados | 134 — série A: 41, série C: 93 |
| Soma dos 134 estandes | 10.814 m² |
| Módulo dominante série C | 100 m² (10×10) — 39 unidades |
| Módulo dominante série A | 25 m² (5×5) — 35 unidades |
| Pavilhões de animais | 6 (5× 720 m² + 1× 560 m²) |
| Zonas nomeadas | 122 |

Emparelhamento código→área com distância média de 3,2 pt. Confiável.

`data/dwg_agroshow26.json` é auditoria do DWG, não fonte de dados.

---

## Pendências abertas

| # | Pendência | Impacto |
|---|---|---|
| 1 | Existe footage de edições anteriores? (rodeio, show, público, leilão) | Alto — define se apoio é real ou gerado |
| 2 | O portal-celeiro já tem projeto da arquiteta? | Alto — evita desenhar o que não será construído |
| 3 | "Telão 4×2": metros ou painéis? Resolução nativa? | Alto — risco de master inutilizável |
| 4 | Drone é do parque vazio, fora de evento? | Médio — limita o que vai na abertura |
| 5 | Arquivo nativo do mapa | Médio — pode poupar o redesenho |
| 6 | Identidade visual AGROSHOW 2026 em vetor | Médio — títulos e letreiros |

**Resolvidas:** transcrição dos áudios (feita, em `docs/brief-audios.md`); ordem
dos pavilhões de animais (não havia divergência); DWG da planta (recebido e
auditado — não contém vetor).

---

## Estrutura do repositório

```
.claude/agents/render-agroshow.md   Agente diretor técnico
docs/BRIEFING.md                    Este arquivo
docs/brief-audios.md                Transcrição literal dos áudios — fonte primária
docs/CAMINHO-3D.md                  Caminho fotorrealista, projeto futuro
data/mapa_agroshow26.json           Planta extraída do PDF — fonte de verdade
data/dwg_agroshow26.json            Auditoria do DWG
scripts/extract_map.py              Extração do PDF
scripts/extract_dwg.py              Auditoria do DWG
reference/                          Originais do cliente e briefings anteriores
```
