# ESTADO DO PROJETO — leia isto primeiro

**AGROSHOW 2026 · Parque de Exposições de Dois Vizinhos, PR**
Atualizado em 14/08/2026.

Este arquivo existe para retomar o trabalho em outra sessão sem perder contexto.
Leia daqui e siga para os documentos citados.

---

## Prazo e situação, hoje 14/08

**Domingo 16/08: tudo ajustado. Segunda 17/08 à tarde: renderizado e
exportado o `.mp4` para o cliente.** Três dias a contar de hoje para o que se
orça em 4 a 8 semanas de estúdio de archviz — ver `docs/PROPOSTA-3-DIAS.md`
para o cronograma completo, o portão de decisão e os riscos com saída.

Máquina de render: GPU de 8–12 GB de VRAM. Verba de asset: **zero** — só CC0 e
gratuito. Essas duas restrições decidiram o motor (ver abaixo).

### O achado que mudou o filme

O percurso antigo (16 pontos, uma curva bezier única, 128 s) foi medido contra
a planta: **1.152 m em 128 s dão 9,0 m/s — 32 km/h**, de 1,3 a 7× acima da
faixa cinematográfica de drone (1,3–2,2 m/s em órbita/push-in, 3,6–6,7 m/s em
sobrevoo). Nessa velocidade não se lê placa nem se reconhece área.

**A câmera virou dado.** `data/planos.json` declara 22 planos — alvo, lente,
altura, movimento, duração — cada um dentro da faixa cinematográfica, conferido
por `python3 scripts/planos.py --conferir`. Ver `docs/PLANOS.md`.

### Motor: dois planos, com portão de decisão

- **Plano A (ativo):** Blender gera a geometria e exporta FBX
  (`build_scene.py --export-fbx`); o **Twinmotion 2026** (gratuito, direito
  comercial abaixo de US$ 1 M de faturamento) veste — gente animada,
  vegetação, materiais, tudo que a verba zero não compra — e renderiza em
  tempo real.
- **Plano B (rede de segurança):** EEVEE Next no próprio Blender, mesma
  geometria, mesma decupagem, sem sair do repositório.
- **Portão: sábado 15/08, 12h.** Se o Twinmotion não segurar a cena inteira
  com fluidez (risco real: recomenda-se 12 GB+ de VRAM para site grande, a
  máquina tem 8–12), cai para o Plano B sem olhar para trás.
- **Calibração antes de prometer o domingo:** `render_shots.py --plano <ID>
  --quadros 24 --cronometrar` mede o tempo real por quadro do plano mais
  pesado e projeta o filme inteiro. Acima de ~11 h não cabe na noite de
  domingo.

Situação anterior (prazo original domingo 13/08, antecipado e depois
reaberto): a meta daquele momento era só a base navegável renderizando. Esse
momento passou; o que vale agora é o cronograma de 3 dias acima.

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
| Núcleo de terreno/bacia | `scripts/terreno.py` | Sem `bpy` — escala, bacia, leitura da planta. Fonte única para o gerador e a decupagem |
| Decupagem do filme | `data/planos.json` + `scripts/planos.py` | 22 planos, conferidos em velocidade — ver `docs/PLANOS.md` |
| Gerador da cena 3D | `scripts/build_scene.py` | Roda ponta a ponta em bpy 5.0.1. `--plano` corta por região, `--export-fbx` exporta para o Twinmotion |
| Render retomável | `scripts/render_shots.py` | Plano a plano, animatic, calibração de tempo (`--cronometrar`) |
| Entrega | `scripts/encode.sh` | Os 3 arquivos + cartela de teste, a partir da sequência de PNG |
| Transcrição dos áudios | `docs/brief-audios.md` | Fonte primária do roteiro |
| Briefing completo | `docs/BRIEFING.md` | Roteiro, restrições, entrega |
| Proposta de 3 dias | `docs/PROPOSTA-3-DIAS.md` | Cronograma, motor, portão de sábado, riscos |
| Referência do portal | `reference/PORTAL-referencia.md` | Descrição da fachada |
| Agente | `.claude/agents/render-agroshow.md` | Reescrito para 3D em 13/08/2026. Sistema próprio, fora do Cláudio. Texto 2.5D arquivado em `docs/AGENTE-2.5D-suspenso.md` |

Saída atual do gerador (filme completo, sem `--plano`):

```
escala .............. 0.5611 m/pt
extensao do terreno . 808 x 454 m
pavilhoes ........... 6
estandes ............ 74 instanciados + 60 proprios
planos ............... 22 de 22 (filme completo)
render .............. 2760x1380 (2:1)
duracao do filme ..... 4635 quadros (154 s a 30 fps)
patamares ........... arena 0 m -> shows 3.5 m -> anel 7.0 m -> plato 10.0 m
```

```bash
pip install bpy pymupdf ezdxf
python3 scripts/build_scene.py --out out/cena.blend                 # filme completo
python3 scripts/build_scene.py --plano P19 --out out/P19.blend      # so um plano, cabe em 8-12 GB
python3 scripts/build_scene.py --export-fbx out/cena.fbx            # para o Twinmotion (Plano A)
python3 scripts/planos.py --conferir                                # confere velocidades sem bpy
```

Renders de conferência: `docs/conferencia-layout.png` (topo),
`docs/conferencia-bacia.png` (patamares), `docs/conferencia-quadro.png`
(quadro da animação) — **desatualizado**, ainda mostra a câmera antiga de 16
pontos. Regenerar com a decupagem nova antes da próxima conferência visual.

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
6. **Plano final saindo pelo portal.**

Frases literais, não reescrever:
- Abertura: *É daqui que sai o alimento que sustenta o mundo*
- Fechamento: *Aqui será um grande balcão de negócios*

---

## Próximos passos, em ordem de valor

1. **Regenerar `docs/conferencia-quadro.png` com a decupagem nova** — a
   câmera antiga (16 pontos, 18° fixos) foi substituída por 22 planos com
   mira por constraint. Conferir se algum ainda vê telhado de estande.
2. **Exportar o FBX e testar no Twinmotion** (`--export-fbx`) — é o item que
   decide o portão de sábado 12h. Confira VRAM com a cena inteira vestida.
3. **HDRI no lugar do céu procedural.** `construir_ceu()` hoje é uma cor
   chapada. Um HDRI de fim de tarde do Poly Haven (CC0) muda o render inteiro.
4. **Sun Position** com −25,73144 / −53,07627 no lugar do sol fixo em
   `construir_luz()`.
5. **Materiais: variação macro primeiro** (ruído de baixa frequência sobre a
   cor base), textura PBR CC0 só onde a câmera desce.
6. **Vegetação e povoamento** com assets CC0 (Quaternius, Kenney, Poly Haven)
   no Plano B; *Populate* do Twinmotion no Plano A.
7. **Portal, palco e camarotes** modelados — hoje só existem como caixa ou nem
   isso. O portal é o primeiro e o último plano (P02 e P22).
8. Confirmar as alturas dos patamares com um quadro de drone.
9. **Confirmar a Fazendinha (P14/P15) com o cliente** — é a única posição do
   filme sem apoio na planta, só no áudio. Ver `docs/PLANOS.md`, âncora
   `estimada`.

Feito em 13/08/2026: o agente `.claude/agents/render-agroshow.md` foi reescrito
para o caminho 3D. Ele é **sistema próprio** — não responde ao Cláudio (o
diretor de montagem em `E:\I.A Edit\claudio`) e não herda a doutrina 2.5D, por
decisão do Natan.

Feito em 14/08/2026: a câmera deixou de ser uma curva única e virou decupagem
em `data/planos.json` (22 planos); o gerador ganhou corte por região
(`--plano`) e exportação para o Twinmotion (`--export-fbx`); e entrou o par
Plano A / Plano B com portão de decisão no sábado — ver
`docs/PROPOSTA-3-DIAS.md`.

---

## Pendências com o cliente

| # | Pendência | Impacto |
|---|---|---|
| 1 | Footage de edições anteriores — prometido, não chegou | Alto — vira textura e referência |
| 2 | Posição real da Fazendinha (P14/P15) — não existe na planta, só no áudio | Alto — é diferencial, e a câmera já está montada em cima da estimativa |
| 3 | Quadro de drone lateral da arena | Médio — trava as cotas dos patamares |
| 4 | Medida real de qualquer estrutura | Médio — confirma a escala |
| 5 | Identidade visual AGROSHOW 2026 em vetor | Médio — títulos e letreiros |

---

## Limitações do ambiente remoto

Registrado para não se repetir tentativa: o proxy de egresso bloqueia
`drive.google.com`, `at.adobe.com`, `portal.opentopography.org`,
`huggingface.co`, o CDN da OpenAI, `openstreetmap.org` e
`doisvizinhos.pr.gov.br`. Vídeo do Drive e transcrição de áudio precisam ser
feitos localmente e anexados no chat. GitHub, PyPI e o arquivo principal do
Ubuntu funcionam.
