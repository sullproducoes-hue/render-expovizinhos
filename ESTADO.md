# ESTADO DO PROJETO — leia isto primeiro

**AGROSHOW 2026 · Parque de Exposições de Dois Vizinhos, PR**
Atualizado em 14/08/2026.

Este arquivo existe para retomar o trabalho em outra sessão sem perder contexto.
Leia daqui e siga para os documentos citados.

---

## Situação

Vídeo de apresentação do parque, para telão, com percurso pelo recinto na ordem
ditada pelo cliente. **Prazo original era domingo; o cliente antecipou para
amanhã (13/08)**, para sobrar tempo de lapidação antes da entrega.

Com essa antecipação, a meta de amanhã **não é o filme acabado** — é a **base
navegável e renderizando**, para lapidar por cima.

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
| Transcrição dos áudios | `docs/brief-audios.md` | Fonte primária do roteiro |
| Briefing completo | `docs/BRIEFING.md` | Roteiro, restrições, entrega |
| Referência do portal | `reference/PORTAL-referencia.md` | Descrição da fachada |
| Agente | `.claude/agents/render-agroshow.md` | Reescrito para 3D em 13/08/2026. Sistema próprio, fora do Cláudio. Texto 2.5D arquivado em `docs/AGENTE-2.5D-suspenso.md` |

Saída atual do gerador:

```
escala .............. 0.5611 m/pt
extensao do terreno . 808 x 454 m
pavilhoes ........... 6
estandes ............ 74 instanciados + 60 proprios
pontos do percurso .. 16 de 16
render .............. 2760x1380 (2:1)
animacao ............ 3840 quadros (128 s a 30 fps)
patamares ........... arena 0 m -> shows 3.5 m -> anel 7.0 m -> plato 10.0 m
```

```bash
pip install bpy pymupdf ezdxf
python3 scripts/build_scene.py --out cena.blend
```

Renders de conferência: `docs/conferencia-layout.png` (topo),
`docs/conferencia-bacia.png` (patamares), `docs/conferencia-quadro.png`
(quadro da animação).

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

1. **Câmera está baixa demais** — e agora existe o número certo, medido.
   A telemetria dos 62 voos do próprio Natan neste recinto dá:
   **altura mediana 24,0 m** (quartis 18,2 / 44,7; máxima 122,3) e
   **gimbal pitch mediano −18,8°** (quartis −28,8 / −12,4).
   Ele **quase não usa nadir**: 0,7% dos quadros abaixo de −80°, 51% acima de
   −20°. A linguagem dele é percurso oblíquo baixo, não mapa visto de cima —
   o que confirma a escolha do cliente pelo percurso 3D.
   Ajuste `ALTURA_CAMERA` e `INCLINACAO_CAM` para esses valores medidos, e faça
   variar por trecho. Dados em `_triagem\telemetria\camera-real.json`.
2. **HDRI no lugar do céu procedural.** `construir_ceu()` hoje é uma cor chapada.
   A **temperatura de cor medida** nos voos vai de 3318 K a 8061 K, mediana
   5206 K. O footage sustenta bem dois momentos: sol duro de meio-dia com
   cumulus, e golden hour de fim de tarde — e a maior parte do material bom de
   material está no segundo. Ver a seção de luz no dossiê.
3. **Texturas PBR** em vez das cores base — **as referências já estão
   escolhidas**, com vídeo, timecode e quadro de prova em resolução nativa:
   `docs/MATERIAIS-referencia.md`. Poly Haven e ambientCG, ambos CC0.
4. **Vegetação e povoamento** com assets CC0 (Quaternius, Kenney, Poly Haven).
5. **Portal, palco e camarotes** modelados — hoje só existem como caixa ou nem
   isso. O portal é o primeiro e o último plano. **Os três têm referência
   agora**, e vale saber de onde vem cada uma:
   - **Portal:** não aparece em nenhuma das 173 folhas. A referência é a foto
     que o cliente mandou, e ela estava solta fora do repositório —
     `E:\Projetos todos\Mapa - agroshow\WhatsApp Image 2026-08-12 at 13.15.32.jpeg`.
     É a foto que o `reference/PORTAL-referencia.md` descreve.
   - **Palco:** vários, o melhor em `DJI_20251127184447_0110_D` 00:00:02 —
     montado e vazio, com treliça, cobertura tensionada, telões e deck.
   - **Camarotes:** `DJI_20251128224305_0163_D` 00:00:09 — deck elevado de
     madeira, módulos separados por gradil branco de tubo, e **sem
     arquibancada**, o que confirma a restrição 1 por imagem do próprio recinto.
6. Confirmar as alturas dos patamares com um quadro de drone — **continua
   aberto**, e a telemetria não resolve (ver o dossiê: o barômetro da DJI não
   recalibra entre decolagens da mesma sessão).

Feito em 13/08/2026: o agente `.claude/agents/render-agroshow.md` foi reescrito
para o caminho 3D. Ele é **sistema próprio** — não responde ao Cláudio (o
diretor de montagem em `E:\I.A Edit\claudio`) e não herda a doutrina 2.5D, por
decisão do Natan.

---

## Pendências com o cliente

| # | Pendência | Impacto |
|---|---|---|
| ~~1~~ | ~~Footage de edições anteriores~~ — **chegou em 13/08/2026** | Resolvida — ver abaixo |
| 2 | Quadro de drone **lateral** da arena | Médio — trava as cotas dos patamares |
| 3 | Medida real de qualquer estrutura | Médio — confirma a escala |
| 4 | Identidade visual AGROSHOW 2026 em vetor | Médio — títulos e letreiros |

A pendência 2 **continua aberta e ficou mais estreita**: das 173 folhas triadas,
nenhuma traz perfil lateral da arena com elemento de cota conhecida. Os melhores
candidatos (`DJI_20251126155259_0053_D` 00:02:11, `DJI_20251128150656_0136_D`
00:00:15, `DJI_20251126120722_0045_D_stabilized` 00:00:00) provam que o degrau
existe e que **não há arquibancada**, mas são oblíquos altos: dão a forma do
talude, não a altura. O que falta é um voo lateral rasante, com o drone à altura
do patamar intermediário.

---

## O footage chegou — 137 GB, 173 vídeos

Em `E:\Projetos todos\Mapa - agroshow\Brutos Expo`. **Não está neste repositório
e não deve entrar**: é material de cliente e o `origin` é público. O que sobe
para cá é o dossiê e o caminho absoluto de cada prova.

Triagem completa em 14/08/2026 — 173 folhas de contato, 10 quadros por vídeo com
timecode gravado no quadro, mais a análise de todas elas por classe de material.
As escolhas estão em **`docs/MATERIAIS-referencia.md`**.

Ferramentas, em `E:\Projetos todos\Mapa - agroshow\Comandos\`:

| script | o que faz |
|---|---|
| `extrair_quadros.py` | folhas de contato e passada densa (decode em CUDA, tonemap de HLG) |
| `extrair_telemetria.py` | telemetria de voo dos streams `djmd` via exiftool |
| `cotas_do_terreno.py` | tentativa de cotar os patamares pelo barômetro — **não funciona**, ver dossiê |
| `camera_real.py` | altura de voo, gimbal e luz medidos dos 62 voos |
| `extrair_provas.py` | rajadas em resolução nativa dos materiais escolhidos |

**Registro de material sondado que não está no disco:** há 17 `.ffprobe.json` em
`_triagem\metadados\` de arquivos `dji_fly_20260813_*` que não existem mais na
pasta. Vieram de um zip que falhou na descompactação de 13/08 e foi apagado
depois de extraído. Não é perda conhecida — é uma ausência que ninguém decidiu.
Decisão do Natan.

---

## Limitações do ambiente remoto

Registrado para não se repetir tentativa: o proxy de egresso bloqueia
`drive.google.com`, `at.adobe.com`, `portal.opentopography.org`,
`huggingface.co`, o CDN da OpenAI, `openstreetmap.org` e
`doisvizinhos.pr.gov.br`. Vídeo do Drive e transcrição de áudio precisam ser
feitos localmente e anexados no chat. GitHub, PyPI e o arquivo principal do
Ubuntu funcionam.
