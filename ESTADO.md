# ESTADO DO PROJETO — leia isto primeiro

**AGROSHOW 2026 · Parque de Exposições de Dois Vizinhos, PR**
Atualizado em 12/08/2026 (segunda passada do dia).

Este arquivo existe para retomar o trabalho em outra sessão sem perder contexto.
Leia daqui e siga para os documentos citados.

---

## Situação

Vídeo de apresentação do parque, para telão, com percurso pelo recinto na ordem
ditada pelo cliente. **Prazo original era domingo; o cliente antecipou para
amanhã (13/08)**, para sobrar tempo de lapidação antes da entrega.

Com essa antecipação, a meta de amanhã **não é o filme acabado** — é a **base
navegável e renderizando**, para lapidar por cima. Essa base existe: a cena
monta em segundos, o percurso cobre os 20 blocos do roteiro e a câmera enquadra
cada bloco pela frente.

### Duas abordagens conviveram nesta conversa

1. **Mapa animado 2.5D** com imagens de IA como janelas — veio de um chat
   anterior (`reference/SULL_MAPA_EVENTO.md`), documentado em `docs/BRIEFING.md`.
2. **Cena 3D real em Blender** — decisão do cliente, é o caminho ativo.
   Qualidade de jogo moderno é suficiente, não precisa fotorrealismo.

**O caminho ativo é o 2.** O material do caminho 1 segue válido para o LOOK LOCK
das imagens de apoio, os títulos e as restrições do cliente.

---

## O que já está pronto e testado

| Item | Onde | Estado |
|---|---|---|
| Planta extraída do PDF | `data/mapa_agroshow26.json` | 134 estandes com área, 181 blocos, 122 zonas |
| Auditoria do DWG | `data/dwg_agroshow26.json` | Confirma: não há vetor |
| Gerador da cena 3D | `scripts/build_scene.py` | Roda ponta a ponta em bpy 5.0.1 |
| Percurso dos 20 blocos | `PERCURSO` no gerador | 22 pontos, na ordem do roteiro |
| Portal, palco, camarotes | `construir_portal/palco/camarotes` | Modelados, leitura econômica |
| Galpões da faixa norte | `GALPOES` no gerador | **Dimensões supostas** — ver pendência 2 |
| Estacionamentos | `construir_estacionamentos` | Lajes de asfalto, dimensão aproximada |
| Quadros de conferência | `docs/conferencia/` | Um por bloco, 690×345 |
| Transcrição dos áudios | `docs/brief-audios.md` | Fonte primária do roteiro |
| Briefing completo | `docs/BRIEFING.md` | Roteiro, restrições, entrega |
| Referência do portal | `reference/PORTAL-referencia.md` | Descrição da fachada |
| Agente | `.claude/agents/render-agroshow.md` | Reescrito para o caminho 3D |

Saída atual do gerador:

```
escala .............. 0.5611 m/pt
extensao do terreno . 808 x 454 m
pavilhoes ........... 6
estandes ............ 74 instanciados + 60 proprios
estacionamentos ..... 8
galpoes da faixa norte 4
camarotes ........... 16 modulos, sem arquibancada
pontos do percurso .. 22 de 22
extensao do percurso  1937 m
trechos aereos ...... 9
camera .............. 30 mm, 4-52 m
render .............. 2760x1380 (2:1)
animacao ............ 4440 quadros (148 s a 30 fps)
sol ................. azimute 295°, elevacao 12°
patamares ........... arena 0 m -> shows 3.5 m -> anel 7.0 m -> plato 10.0 m
```

São 22 pontos para 20 blocos: o Bosque e a travessia do portal são nós de
passagem, sem título na tela.

```bash
pip install bpy pymupdf ezdxf
python3 scripts/build_scene.py --out cena.blend
python3 scripts/build_scene.py --conferencia docs/conferencia/
```

Conferência custa 10–20 s por quadro: Cycles em CPU, 25% da resolução, 32
amostras com denoise. **Não há GPU aqui** — EEVEE precisa de libEGL e quebra no
meio do render, por isso o padrão é Cycles. Em máquina com GPU, `--motor
BLENDER_EEVEE`.
Renders antigos do layout: `docs/conferencia-layout.png` (topo),
`docs/conferencia-bacia.png` (patamares).

---

## Descobertas que não podem ser perdidas

**Escala do mapa: 0,5611 m/pt.** Derivada dos 39 estandes de 100 m² da série C,
que ficam encostados em fileira — a mediana entre rótulos consecutivos é
17,82 pt. A série A não serve para o mesmo cálculo, há corredor entre módulos.
Resulta em terreno de 808 × 454 m. **Ainda não conferida com medida em campo.**

**Nem o PDF nem o DWG têm geometria vetorial.** Os dois carregam o mesmo bitmap
de 1806 × 1383 px. O DWG (AC1018) tem 4883 TEXT, 1 LINE, 1 SOLID, 2 HATCH e
zero polilinha — e 4483 dos textos são caracteres soltos, glifo a glifo.
Assinatura de PDF importado para CAD. Não insista em extrair contorno dele.

**DEM global não serve para o recinto.** SRTM, Copernicus, NASADEM e AW3D30 são
todos ~30 m. Um recorte de 2 × 2 km sai com **67 × 67 pixels** — o recinto
ocuparia uns 27. Os patamares somem. A bacia foi derivada da planta, e é mais
precisa. OpenTopography só vale para o entorno distante.

**A bacia veio de três fontes concordando:** os 93 estandes da série C se
agrupam em anéis a 72–90 m e 108–113 m do centro da arena; as 15 anotações de
"Talude" caem nas faixas de transição; e o áudio descreve três níveis. Os
**raios** são dado; as **alturas** (3,5 / 7 / 10 m) são estimadas por proporção.

**Ordem dos pavilhões de animais: não há divergência.** Um briefing anterior
travou o bloco alegando conflito entre áudio e planta. Ordenando os rótulos por
coordenada Y real, a sequência bate exatamente com a ditada. O bloco está
liberado.

**A câmera errava por três motivos, não um.** Voava a 12 m com inclinação fixa
e **parava em cima do assunto** — e de cima do assunto só se vê cobertura. As
três correções, que valem para qualquer bloco novo: altura por trecho (aéreo a
52 m nas transições, baixa nos pontos), **recuo** (a câmera para dezenas de
metros antes do assunto) e **mira em alvo animado** em vez de ângulo fixo.

**A planta não desenha os Pavilhões 1, 2 e 3.** Ela rotula e desenha os
estandes de dentro, mas não o contorno do galpão — e agrupar estandes por
proximidade não serve de envoltória (o grupo do Pavilhão 3 esparrama por
122 × 106 m, o do Pavilhão 1 junta quatro estandes). Os volumes atuais são
**supostos**, na leitura mais conservadora: como os pavilhões 2 e 3 distam
39 m, o lado comprido corre norte-sul. Seis blocos do roteiro acontecem neles.

**Recuo maior que o trecho gruda duas paradas no mesmo ponto** — e dois títulos
sobre o mesmo quadro. Acontece na faixa norte, onde os rótulos distam 55–68 m.
O gerador avisa na saída quando isso ocorre; a correção é baixar o `recuo` do
bloco. Mercado, Agroindústrias e Café Colonial dividem o Pavilhão 3 e por isso
têm recuo decrescente: a câmera avança pelo galpão enquanto o título muda.

**Cinco blocos do roteiro não têm rótulo na planta.** Expositores Externos,
Fazendinha, Máquinas, Veículos e Área de Shows. Quatro deles saem da geometria
da bacia — são anéis e patamares com raio conhecido. **A Fazendinha não sai:**
está posicionada em caráter provisório e o gerador imprime isso a cada rodada.

**Local:** -25,73144 / -53,07627 — R. Jorge Amado, Jardim Marcante, Dois
Vizinhos - PR, 85660-000.

---

## Especificações de entrega — não negociar

Telão LED **P2,9 · 1379 × 690 px nativos · 4,00 × 2,00 m**.

- Proporção **2:1**, master em **2760 × 1380**
- **Nunca masterizar em 1379 × 690** — largura ímpar não codifica em H.264 4:2:0
- **`.mov` (ProRes 422 HQ) e `.mp4` (H.264)** — os dois, sempre
- **2:1 limpo, jamais tarja embutida.** Tarja embutida não se desfaz, e se o
  processador estiver em modo preencher, estica a tarja junto
- **Área de segurança de 90%** — 2484 × 1242 centralizados
- Tipografia: o painel tem 951.510 pixels para 4 m de tela. Título com no mínimo
  8% da altura do quadro; apoio nunca abaixo de 4%
- Mandar junto uma **cartela de teste** de 10 s com marcas de canto

A resolução de entrada do processador não será confirmada — decisão do cliente.

---

## Restrições do cliente — violar é rejeição

1. **Arena de rodeio SEM arquibancada.** Só pista, camarotes nos dois lados,
   palco de frente.
2. **A palavra "Kids" é proibida.** Use *Fazendinha*; "Área Infantil" só em
   descrição secundária.
3. **Fazendinha:** nome grande, descrição pequena embaixo.
4. **O portal é o da foto** (`reference/PORTAL-referencia.md`). Na dúvida sobre
   um detalhe, escolha a leitura mais econômica.
5. **Quatro diferenciais** com mais tela: Fazendinha, Rodeio, Café Colonial,
   Mercado do Produtor.
6. **Plano final saindo pelo portal.** Já está na cena: o caminho atravessa o
   vão central a 3,5 m de altura, abaixo da verga.

Frases literais, não reescrever:
- Abertura: *É daqui que sai o alimento que sustenta o mundo*
- Fechamento: *Aqui será um grande balcão de negócios*

---

## Próximos passos, em ordem de valor

1. **Ajustar recuo, altura e mira bloco a bloco** pelos quadros em
   `docs/conferencia/`. Os parâmetros estão na lista `PERCURSO`, um dicionário
   por bloco — mexer é trocar um número, não remontar cena. Os blocos da faixa
   norte (02 a 07) são os que ainda leem como telhado branco sem assunto.
2. **Vegetação e povoamento** com assets CC0 (Quaternius, Kenney, Poly Haven).
   Gente é o que mais entrega maquete; ver `docs/CAMINHO-3D.md`.
3. **Texturas PBR** em vez da variação procedural de cor. Poly Haven e
   ambientCG, ambos CC0 — **os dois estão bloqueados pelo proxy do ambiente
   remoto**, precisam ser baixados localmente e anexados.
4. **HDRI real** no lugar do céu Nishita, pelo mesmo caminho.
5. **Render em passes** (beauty, depth, cryptomatte, motion vectors) antes de
   qualquer render longo. Sem os passes, refino vira re-render.
6. **Títulos e letreiros** sobre os quadros, na tipografia do telão.
7. Confirmar as alturas dos patamares com um quadro de drone.

---

## Pendências com o cliente

| # | Pendência | Impacto |
|---|---|---|
| 1 | Footage de edições anteriores — prometido, não chegou | Alto — vira textura e referência |
| 2 | **Dimensão dos Pavilhões 1, 2 e 3** — a planta não desenha o contorno | Alto — seis blocos do roteiro acontecem neles |
| 3 | **Onde fica a Fazendinha** — "ao lado da pista de tiro de laço", sem rótulo na planta | Alto — é diferencial, e a posição atual é chute |
| 4 | Quadro de drone lateral da arena | Médio — trava as cotas dos patamares |
| 5 | Medida real de qualquer estrutura | Médio — confirma a escala |
| 6 | Identidade visual AGROSHOW 2026 em vetor | Médio — títulos e letreiros |

---

## Limitações do ambiente remoto

Registrado para não se repetir tentativa: o proxy de egresso bloqueia
`drive.google.com`, `at.adobe.com`, `portal.opentopography.org`,
`huggingface.co`, o CDN da OpenAI, `openstreetmap.org`,
`doisvizinhos.pr.gov.br` e — testado nesta sessão — `polyhaven.com` e
`ambientcg.com`. Vídeo do Drive, transcrição de áudio, HDRI e textura PBR
precisam ser obtidos localmente e anexados no chat. GitHub, PyPI e o arquivo
principal do Ubuntu funcionam.

Não há GPU: o render roda em CPU, ~80 s por quadro a 25% da resolução. Render
final é trabalho de máquina local.
