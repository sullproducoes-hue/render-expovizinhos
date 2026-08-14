# ESTADO DO PROJETO — leia isto primeiro

**AGROSHOW 2026 · Parque de Exposições de Dois Vizinhos, PR**
Atualizado em 13/08/2026.

Este arquivo existe para retomar o trabalho em outra sessão sem perder contexto.
Leia daqui e siga para os documentos citados.

---

## Resumo e objetivo final

**O que estamos fazendo.** Reconstruindo o Parque de Exposições de Dois
Vizinhos em 3D, por script, a partir da planta oficial — e passeando por ele com
uma câmera na ordem que o cliente ditou no áudio, com título a cada área.

**Para onde vai.** Um vídeo de percurso de ~2,5 min, 2:1, exibido no telão LED
P2,9 de 4 × 2 m da feira. Quem assiste tem que reconhecer o parque, entender o
caminho e ler os títulos de longe. Abre com *É daqui que sai o alimento que
sustenta o mundo* e fecha saindo pelo portal, com *Aqui será um grande balcão
de negócios*.

**Por que 3D e não montagem de imagens.** Porque o parque recebe mais de um
evento por ano. A camada permanente — terreno, taludes, pavilhões, arena — não
muda; a camada do evento — estandes, palco, portal, sinalização — troca a cada
edição. Construído assim, o modelo se paga na segunda temporada, e a AGROSHOW
vira a primeira cliente de um ativo, não um vídeo descartável.

**Como termina.** Render final em **Cycles**, com o máximo de realismo, na
máquina do cliente (GPU NVIDIA, OptiX). Este ambiente remoto não tem GPU e
serve só para gerar a cena e conferir enquadramento.

**O que falta para o realismo, em ordem:** gente na cena, referência real do
lugar (o footage de drone, em triagem), vegetação e texturas com arquivo.

---

## Situação

Vídeo de apresentação do parque, para telão, com percurso pelo recinto na ordem
ditada pelo cliente. O prazo foi antecipado para hoje (13/08), para sobrar tempo
de lapidação antes da entrega.

Com essa antecipação, a meta de hoje **não é o filme acabado** — é a **base
navegável e renderizando**, para lapidar por cima. **Essa base está fechada.**

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
| Gerador da cena 3D | `scripts/build_scene.py` | Roda ponta a ponta em bpy 5.0.1, com perfil de prévia e de entrega |
| Conferência de quadros | `scripts/render_conferencia.py` | Cycles CPU, quadro isolado, sem GPU |
| Extração do footage | `scripts/extrair_quadros.py` | Roda na máquina do cliente; metadados, triagem e passada densa |
| Triagem do drone | `docs/triagem-drone.md` | Método fechado, aguardando as folhas de contato |
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
portal .............. modelado
palco / camarotes ... 1 palco, 2 lados de camarote (sem arquibancada)
pontos do percurso .. 16 de 16
render .............. 2760x1380 (2:1)
animacao ............ 4591 quadros (153 s a 30 fps)
patamares ........... arena 0 m -> shows 3.5 m -> anel 7.0 m -> plato 10.0 m
```

```bash
pip install bpy pymupdf ezdxf
python3 scripts/build_scene.py --out cena.blend                 # previa
python3 scripts/build_scene.py --perfil final --out cena.blend  # entrega
python3 scripts/render_conferencia.py cena.blend --quadros 1,316,3886,4231,4591 \
    --saida docs --escala 35 --amostras 64
```

**Perfil de entrega (`--perfil final`).** Decisão do cliente: render final em
Cycles, na máquina dele, com GPU NVIDIA. **O perfil exige GPU por padrão — se
não achar OptiX/CUDA, o script para com código de saída 1, imprime o que
conferir (driver, Preferences > System > Cycles Render Devices) e não salva a
cena.** Ele não cai para CPU em silêncio: são 4.591 quadros, e um render de
dias rodando no lugar errado por engano é pior do que o script recusar a
sair. Só continua em CPU se `--permitir-cpu` for passado explicitamente — use
isso só para conferir a cena num ambiente sem GPU, nunca para a entrega. Uma
vez com a GPU confirmada: 512 amostras adaptativas com denoise, 12 bounces,
motion blur de obturador 180° e saída em **EXR multicamada com passes** —
combined, z, vetor, normal e cryptomatte de objeto e material. Os passes não
são luxo: sem cryptomatte não há máscara para
compor placa, totem e letreiro, e o texto é o que vende o vídeo — ele é
composto, nunca gerado.

O gerador imprime a tabela de pontos com quadro, tempo e altura de cada um, e
deixa um marcador de timeline por ponto do roteiro — é assim que se acha o
quadro de cada área sem contar na mão.

Renders de conferência: `docs/conferencia-layout.png` (topo),
`docs/conferencia-bacia.png` (patamares) e um por ponto do percurso
(`docs/conferencia-01-portal-de-entrada.png` e seguintes).

---

## O que entrou nesta sessão

**Câmera em duas curvas.** Uma curva para o voo, outra para o olhar. A câmera
mira um alvo na altura de quem caminha, então a inclinação sai da geometria em
vez de ser um ângulo fixo. Cada ponto tem altura, permanência e recuo próprios.
Três defeitos que isso resolveu, todos vistos em quadro e não no código:

- 12 m fixos com 18° enquadravam telhado de estande;
- passar por cima do assunto entregava o ponto em nadir — daí o recuo, que é
  190 m na arena e 45 m no portal;
- a saída pelo portal atravessava o frontão a 14 m de altura. O último ponto
  agora voa a 3,6 m e **para 5 m antes do plano do portal**, sob o vão. Passar
  do plano joga o portal para trás da nuca e o último quadro vira campo vazio.

**Céu Nishita** no lugar da cor chapada, com sol e céu no mesmo azimute. Na 5.0
o tipo passou a se chamar `MULTIPLE_SCATTERING` e `dust_density` virou
`aerosol_density`; o código aceita os dois nomes. `--hdri` continua disponível
para quando a máquina tiver acesso ao Poly Haven.

**Materiais procedurais** com ruído em escala métrica, cor e relevo — no lugar
das cores chapadas. Sol forte com céu fraco (`FORCA_SOL` / `FORCA_CEU`): céu
forte lava a cena inteira.

**Portal, palco e camarotes como geometria.** O portal segue a foto: frontão em
duas águas, treliça em V invertido, três vãos, letreiro em relevo, alas com
beiral, janelas e luminárias. Palco e camarotes ficam na **borda** da pista, não
onde caem os rótulos: rótulo de planta é âncora de texto, e o de `PALCO` cai a
16 m do centro, dentro da pista. O azimute do rótulo é que manda de que lado
cada um está. Camarotes são módulos fechados de dois pavimentos — **não é
arquibancada**, e essa é a restrição mais fácil de violar sem perceber.

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

**A Fazendinha não existe na planta.** Não há rótulo de "Fazendinha" nem de
"tiro de laço" em `data/mapa_agroshow26.json` — o áudio só diz "ao lado da pista
de tiro de laço". Por isso ela **não está no percurso**, apesar de ser um dos
quatro diferenciais. É pendência de cliente, não decisão de projeto: sem
coordenada, arbitrar posição de área é inventar material de venda de espaço.

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

1. **Gente.** É o que tira a cara de maquete, antes de qualquer outra coisa —
   e hoje não há uma única figura humana na cena. Humanos fotoscaneados, escala
   conferida, nunca a mesma pose duas vezes no mesmo quadro.
2. **Vegetação e povoamento** com assets CC0 (Quaternius, Kenney, Poly Haven):
   bosque, mata nativa, veículos no estacionamento, gado nos pavilhões.
3. **Texturas PBR com arquivo**, ligadas nos mesmos slots dos materiais
   procedurais. Precisa ser feito em máquina com acesso — o proxy bloqueia
   Poly Haven e ambientCG.
4. **HDRI real** no lugar do céu Nishita, pelo mesmo motivo (`--hdri` já existe).
5. **Fazendinha no percurso**, assim que o cliente disser onde ela fica.
6. **Estandes com cara de estande** — hoje são caixas de lona. Toldo, testeira e
   frente aberta resolvem a leitura a 20 m de câmera.
7. **Confirmar as alturas dos patamares** com um quadro de drone.
8. **Entorno**: fora do recinto o terreno é campo vazio, e o plano final olha
   justamente para lá. Estacionamento, via e cerca fecham o quadro.

---

## Pendências com o cliente

| # | Pendência | Impacto |
|---|---|---|
| 1 | **Onde fica a Fazendinha** — não há rótulo na planta | Alto — é um dos quatro diferenciais e está fora do percurso |
| 2 | Folhas de contato da triagem do drone | Alto — é o que destrava cotas, escala e materiais |
| 3 | Identidade visual AGROSHOW 2026 em vetor | Médio — títulos e letreiros |

O footage de drone **chegou** (13/08): envio por rclone de 186 arquivos,
~168 GiB, para a pasta `MAPA AGROSHOW`. Era a pendência nº 1 e saiu da lista.
O método de triagem está em `docs/triagem-drone.md`; o que falta é rodar
`scripts/extrair_quadros.py` na máquina do cliente e anexar as folhas.

As pendências de quadro lateral da arena e de medida real de estrutura também
saíram da lista: o footage responde as duas, desde que a triagem ache os
quadros certos.

---

## Limitações do ambiente remoto

Registrado para não se repetir tentativa: o proxy de egresso bloqueia
`drive.google.com`, `at.adobe.com`, `portal.opentopography.org`,
`huggingface.co`, o CDN da OpenAI, `openstreetmap.org`, `doisvizinhos.pr.gov.br`
e **`dl.polyhaven.org`** (por tabela, ambientCG também deve cair). GitHub, PyPI
e o arquivo principal do Ubuntu funcionam.

**Correção sobre o Drive:** o conector do Drive *funciona* e lê metadados —
nomes, tamanhos, datas, e arquivos de texto pequenos, como o log do rclone. É
assim que dá para acompanhar o envio de longe. O que não passa é o **binário**:
o domínio de download está bloqueado, e `download_file_content` devolveria
base64 de 3 GB por vídeo, o que não cabe em contexto nenhum. Por isso a extração
de quadros roda na máquina do cliente e volta anexada no chat. Transcrição de
áudio segue na mesma regra.

Não há GPU: render em Cycles CPU. Um quadro de conferência a 35% da resolução de
entrega com 64 amostras leva cerca de 45 s em 4 núcleos — o suficiente para
conferir enquadramento, longe do necessário para animação.
