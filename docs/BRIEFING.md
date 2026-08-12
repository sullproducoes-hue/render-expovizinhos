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

O telão é um painel de LED **P2,9 com 1379 × 690 px nativos**. Conferindo:
1379 × 2,9 mm = 3,999 m e 690 × 2,9 mm = 2,001 m — confirma o "4×2 m" que
tinha sido informado antes, agora com a resolução real.

| Item | Especificação |
|---|---|
| Painel | LED P2,9 · 1379 × 690 px nativos · 4,00 × 2,00 m |
| Aspecto | 1,99855 — trate como **2:1**. Não é 16:9 |
| Master | **2760 × 1380** (2× o nativo, 2:1 exato, dimensões pares) |
| Reserva | 1920 × 960 (2:1, pares) |
| Orientação | Tudo horizontal |
| Entrega | `.mov` (ProRes 422 HQ) **e** `.mp4` (H.264) — os dois |
| Mote de abertura | *É daqui que sai o alimento que sustenta o mundo* |
| Assinatura final | *Aqui será um grande balcão de negócios* |

O formato duplo é requisito de segurança: o cliente registrou que "pode dar erro
na hora de passar" e já teve falha de reprodução ao vivo.

### Armadilha: 1379 é ímpar

**Não masterize em 1379 × 690.** H.264 com subamostragem 4:2:0 exige largura e
altura pares — largura ímpar não codifica. Se alguém tentar exportar no nativo
exato, o encode falha ou o player corrige sozinho e desalinha o mapeamento de
pixel.

Masterize em **2760 × 1380** e deixe o processador de LED fazer o downscale
para o painel. Se o processador só aceitar 1080p, o 2:1 entra letterboxed em
1920 × 1080, com conteúdo de 1920 × 960 e tarja de 60 px em cima e embaixo.

**Confirme com o operador do telão qual resolução o processador aceita na
entrada.** O alvo real da entrega é o processador, não o painel.

### Consequência para tipografia — a mais importante

O painel tem **951.510 pixels**. Menos da metade de um 1080p, espalhados por
quatro metros de largura.

Isso é um canvas pequeno para uma tela grande, e este vídeo é feito de títulos.
Tipografia fina, caixa alta apertada ou texto secundário pequeno **somem** no
P2,9 visto a distância. Regra prática: título principal ocupando pelo menos 8%
da altura do quadro, peso bold ou heavier, e nada de texto de apoio abaixo de
4% da altura. Teste cada letreiro reduzindo o quadro a 1379 px de largura e
olhando de longe antes de aprovar.

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
4. **Portal em conceito celeiro, econômico.** A foto enviada pelo cliente é a
   referência de forma, material e identidade — descrita em
   `reference/PORTAL-referencia.md`. A versão construída será **mais simples**
   que a referência, nunca mais ornamentada: *"vamos dar um jeito dele, fazer
   mais barato."*
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
   Este é o motivo real do redesenho: sem camadas separadas não há animação de
   mapa, e sem vetor não há camadas.
2. Resolução deixou de ser o problema. Com o painel real em 1379 px de largura
   e master em 2760, o bitmap de 1806 px cobre o nativo e chega perto do master.
   Aguenta como base de traçado e até como fundo estático — o que ele não faz é
   separar em camadas nem escalar em push-in.
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
| 1 | Resolução que o **processador** do telão aceita na entrada | Alto — alvo real da entrega |
| 2 | No portal, reproduzir a estrutura da foto ou acrescentar elemento à frente? | Médio — fecha o bloco B01 |
| 3 | Drone é do parque vazio, fora de evento? | Médio — limita o que vai na abertura |
| 4 | Arquivo nativo do mapa | Médio — pode poupar o redesenho |
| 5 | Identidade visual AGROSHOW 2026 em vetor | Médio — títulos e letreiros |

**Resolvidas:**

- Transcrição dos áudios — em `docs/brief-audios.md`
- Ordem dos pavilhões de animais — não havia divergência, B07 liberado
- DWG da planta — recebido e auditado, não contém vetor
- Especificação do telão — LED P2,9, 1379 × 690 px, 4,00 × 2,00 m
- Referência do portal-celeiro — foto recebida, descrita em
  `reference/PORTAL-referencia.md`
- Footage de edições anteriores — existe, o cliente vai enviar

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
