> # ⚠ CORRIGIDO EM 16/08/2026 — ESTE DOCUMENTO ESTAVA ERRADO
>
> **A fotogrametria FECHOU. As seis tentativas sempre tinham fechado.**
>
> O erro foi de leitura, não de reconstrução: o COLMAP escreve VÁRIOS
> submodelos, e o `0` é quase sempre o descarte de duas imagens. A reconstrução
> boa é o `1`. Conferido no cabeçalho binário (`images.bin` e `points3D.bin`,
> uint64 little-endian nos 8 primeiros bytes) e por `model_analyzer`:
>
> | modelo | imagens | pontos 3D | erro de reprojeção | trilha |
> |---|---|---|---|---|
> | `montagem/sparse/1` | 100/100 | 42.090 | 0,797 px | 5,67 |
> | `montagem/sparse311/1` | 100/100 | 42.300 | 0,796 px | 5,65 |
> | `montagem/sparse4/1` | 100/100 | 42.199 | 0,886 px | 5,75 |
> | `montagem/sparsec/2` | 100/100 | 42.020 | 0,794 px | 5,67 |
> | `fazendinha/sparse/1` | 150/150 | 37.730 | 0,602 px | 10,35 |
> | `fazendinha/sparse3/0` | 150/150 | 37.945 | 0,616 px | 10,31 |
>
> Os próprios logs já diziam `num_reg_frames=99` e `Keeping successful
> reconstruction`. **Todos ≤ 1,5 px → a nuvem entra como GABARITO DE MEDIDA.**
>
> **Três consequências.** (1) Cai a hipótese de *textura repetitiva*: o conjunto
> de telhado reconstruiu com 42 mil pontos. (2) Inverte-se a conclusão sobre
> focal: as rodadas que fecharam partiram de 3.225,6 e a bundle adjustment
> convergiu sozinha para ≈2.511 — declarar 1792 não ajudou. (3) A `sw_1792` não
> falhou: **foi morta em andamento**, com 27 imagens e subindo, enquanto outro
> mapper rodava em paralelo.
>
> **Mas o número não diz o conteúdo** (D073). A `fazendinha` tem o melhor erro do
> lote e reconstruiu o **evento à noite, com a arena tomada de gente** — erro
> baixo e trilha dobrada vêm de multidão e luz darem feature demais. Ela
> reconstruiu um mar de pessoas, e é inútil como geometria de prédio. A nuvem que
> presta é a **`montagem`**: dia, montagem do evento, prédio redondo poligonal,
> galpões de telha, pátio de saibro.
>
> **Delta de método, e é o que mais economiza tempo depois:** eu declarei seis
> fracassos **sem abrir um único arquivo de modelo**. Ler a pasta não é ler o
> dado. Registro completo em `DECISOES.md` **D072** e **D073**.
>
> *Nada abaixo foi apagado — a leitura errada fica registrada, como manda a casa.*

---

# Fotogrametria a partir do footage — o que o material aguenta

**Procedência: registro.** Levantado em 15/08/2026 à noite, depois de ele
perguntar: *"é possível criar um mapa 3d só usando as imagem que tenho no
extrator para com esse 3d melhorar esse render?"*

Resposta curta: **sim, mas não do jeito que se imagina.** Não dá para fazer o
mapa do recinto inteiro. Dá para reconstruir **lugar por lugar**, e um deles
vale muito.

---

## O que foi medido, e como

A telemetria dos voos já estava extraída desde 14/08 em
`Brutos Expo\_triagem\telemetria` — **62 CSVs**, com latitude, longitude,
altitude, pitch e yaw do gimbal amostra a amostra, do stream `djmd` do próprio
MP4. Nenhum voo precisou ser reprocessado.

De cada traçado eu medi a **forma do voo**: centróide, raio médio e quanto o
voo circulou em torno do próprio centro (varredura angular).

## O achado que muda o plano: não existe voo de mapeamento

| pitch do gimbal | voos | o que é |
|---|---|---|
| ≤ −60° (nadir) | **0** | o que ortofoto e modelo digital de terreno exigem |
| −60° a −35° | 5 | oblíquo alto, ajuda mas não basta |
| acima de −35° | 57 | oblíquo baixo e horizonte — footage cinematográfico |

**Ortofoto e malha de terreno do recinto inteiro estão fora.** Isso não é
limitação de ferramenta: é que ninguém voou grade nadir aqui. O material é
filmagem de cinema, não levantamento.

## O que está dentro: 32 órbitas

Órbita é a melhor entrada que existe para reconstruir **um assunto** — para
geometria de prédio e textura de fachada ela ganha da grade nadir. Há 32 voos
dentro do recinto com 120° ou mais de varredura, e vários dão a volta completa:

| voo | varredura | raio | pitch | centro (x, y) | o que cerca |
|---|---|---|---|---|---|
| `DJI_20251130103519_0172_D` | 526° | 69 m | −26,5° | (−158, −18) | **Fazendinha** (rótulo em −164, −19) |
| `DJI_20251128224107_0156_D` | 611° | 29 m | −32,3° | (−131, −70) | sul da Fazendinha |
| `DJI_20251126231950_0100_D` | 228° | 65 m | −42,9° | (−121, −11) | **arena de rodeio** |
| `DJI_20251127211437_0124_D` | 187° | 130 m | −17,2° | (−114, −11) | arena, raio maior |
| `DJI_20251129182606_0171_D` | 196° | 129 m | −14,6° | (−97, −20) | arena, terceiro anel |
| `DJI_20251126210242_0009_D` | 456° | 53 m | −7,5° | (−318, −161) | pavilhões de animais |
| `DJI_20251128150656_0136_D` | 231° | 24 m | −32,5° | (−330, −92) | pavilhões de animais |
| `DJI_20251127184025_0104_D` | 294° | 56 m | −12,2° | (43, −49) | entrada / portal |

## Por onde começar, e por quê

**A arena de rodeio**, com os três anéis de órbita — 228°, 187° e 196°, em
raios de 65, 130 e 129 m. Três alturas e três distâncias em volta do mesmo
assunto é justamente o que uma reconstrução pede.

E é onde o retorno é maior, porque a arena carrega as duas pendências abertas
do projeto: as **cotas dos patamares**, que seguem estimadas esperando o
cliente, e a **escala de 0,5611 m/pt**, que nunca foi conferida com medida em
campo. Uma nuvem de pontos medida fecha as duas sem depender de ninguém.

## As armadilhas deste material

**1. Os quadros extraídos não têm EXIF.** Medido: zero tags. Sem GPS, sem
modelo de câmera, sem distância focal. A georreferência tem de vir do CSV de
telemetria, casada por timecode.

**2. Metade das pastas é export estabilizado.** 58 das 157 têm `_stabilized` no
nome. Estabilização deforma a imagem quadro a quadro e destrói o modelo de
câmera — para fotogrametria elas são veneno. Só os originais servem.

**3. O que estava montado em 2025 entra na malha.** Tenda, público, palco e
brinquedo vêm colados. Servem de referência visual; não servem de geometria
para o layout de 2026, que é outro.

**4. Interior de galpão não sai.** O drone não entra. Os planos que agora
passam por dentro continuam dependendo do modelo feito à mão.

## O que ainda não foi decidido

A ferramenta. Nada de fotogrametria está instalado nesta máquina — só o
exiftool e o OpenCV. As três gratuitas e sem cadastro são **COLMAP**,
**Meshroom** e **OpenDroneMap**; a última precisa de Docker, que também não
está instalado. Instalar é decisão dele.

---

# Primeira rodada — 15/08/2026, noite. Não reconstruiu.

COLMAP 4.1.1 com CUDA instalado em `.ferramentas/colmap` (359 MB, release
oficial do GitHub, autorizado por ele). Roda, vê a RTX 4060.

## Um erro meu, e vale mais que o resultado

Eu ranqueei os voos por **hora no nome do arquivo** e propus a arena de rodeio
como primeiro alvo. Fui olhar os quadros: `DJI_20251130103519_0172_D`, que o
nome diz 10h35, é **show noturno com multidão e fogos**. O carimbo do nome não
é hora de captura confiável.

Refiz a triagem medindo **luminância no pixel** — 156 pastas, três quadros cada.
87 são de dia. Cruzado com órbita e telemetria, sobraram 15 candidatos de
verdade. É essa a lista que vale; a anterior está errada e fica aqui só para
ninguém repetir o caminho.

## As quatro tentativas

| # | conjunto | imagens | intrínseca | resultado |
|---|---|---|---|---|
| 1 | Fazendinha (noturno) | 150 | OPENCV, focal 2304 (chute do COLMAP) | **2 registradas** |
| 2 | Fazendinha (noturno) | 150 | SIMPLE_RADIAL, focal 1280 declarada | **2 registradas** |
| 3 | Fazendinha (noturno) | 150 | idem + **pose prior GPS** por quadro | **0 — nem inicializou** |
| 4 | Montagem (dia, rígido) | 100 | SIMPLE_RADIAL + limiares de PnP soltos | **2 registradas** |

## O que está medido, e é bom

O casamento de imagens **funciona**: 9.432 features por quadro, 2.089 pares
verificados, mediana de 457 inliers. E o conjunto de dia é geometricamente são
— só **3,4%** dos pares saem `PLANAR_OR_PANORAMIC`, contra **42%** do noturno.
O material de dia tem paralaxe e é rígido. O problema não é ele.

## Onde trava

Sempre no mesmo ponto: o par inicial entra, e **toda** imagem seguinte falha o
PnP mesmo enxergando 500 correspondências. Muda o conjunto, muda a intrínseca,
solta `abs_pose_min_num_inliers` e `abs_pose_max_error` — e o número final é
**exatamente 2** todas as vezes. Falha marginal varia; esta não varia.

Suspeita, não confirmada: o modelo novo de `rigs`/`frames` do COLMAP 4.x. O log
conta `Frames: 150 · Registered frames: 2`, e esse esquema de dados é recente.

## Próximo passo, quando ele mandar

Trocar de motor antes de mexer em mais parâmetro:

1. **COLMAP 3.11** (o último da linha anterior, sem `rigs`/`frames`), no mesmo
   conjunto `out/fotogrametria/montagem`. É o teste que isola a suspeita.
2. Se reconstruir, seguir para denso e malha.
3. Se também falhar, então é o material, e aí o caminho é **Meshroom**.

Os dois conjuntos ficam prontos em `out/fotogrametria/`, com banco, features e
casamentos já calculados — trocar de motor não repete esse custo.

---

# Segunda rodada — mesma noite. Ainda não reconstruiu, e a suspeita anterior caiu.

**COLMAP 3.11.1 falha igual ao 4.1.1.** Duas linhas maiores, mesmo resultado.
A suspeita do modelo `rigs`/`frames` do 4.x **está descartada**.

## O que o metadado do vídeo entregou

`exiftool` no MP4 original: **`model_name:FC8282`, `dvtm_Air3`** — é um **DJI
Air 3**. E o vídeo é nativamente **2688×1512 landscape**, girado na extração
(os JPG saem 1512×2688). O Air 3 tem duas câmeras, 24 mm e 70 mm equivalentes,
o que dá focais muito diferentes: ~1792 px e ~5227 px.

## A varredura de focal

Trocando só o parâmetro da câmera no banco e remapeando:

| focal | resultado |
|---|---|
| **1792 px** (24 mm equiv.) | 2 modelos, **9 e 13 imagens**, e chegou a 27 num pico |
| 2400 / 3226 / 5227 px | não terminaram dentro do tempo da rodada |

1792 é a faixa certa — é a única que sai do lugar. Mas os modelos saem
**degenerados**: 13 imagens registradas com **2 pontos 3D**. Imagem registrada
sem ponto não é reconstrução fraca, é reconstrução inválida.

## O que está descartado, por medida

- **Não é o material estar corrompido.** 100 arquivos distintos, 8.232 a 18.804
  keypoints por imagem, 2.097 pares com mediana de 214 inliers.
- **Não é a versão do COLMAP.** 3.11.1 e 4.1.1 falham igual.
- **Não é a cena ser não-rígida.** O conjunto de montagem é de dia, quase sem
  gente, e só 3,4% dos pares saem degenerados.
- **Não é limiar de PnP.** Soltar `abs_pose_min_num_inliers` e
  `abs_pose_max_error` não mudou o desfecho.

## A hipótese que sobra, e não testei

**Textura repetitiva.** Boa parte do quadro nesse voo é **telha metálica
ondulada** e chão de saibro — padrão periódico, que produz muito casamento que
passa no RANSAC como plano e não triangula. Isso explica o que nenhuma das
outras explica: par com centenas de "inliers" e reconstrução com dois pontos.

## Próximo passo, e é decisão dele

1. **Trocar de assunto antes de trocar de ferramenta.** Um voo sobre bosque e
   terreno variado, não sobre telhado. Da lista de 15 candidatos de dia, o
   `DJI_20251129182345_0168_D` (189°, 100 quadros, feira montada com barracas e
   árvores) tem textura muito mais variada.
2. Se também falhar, então é a ferramenta, e aí vale o **Meshroom**.
3. Custo até aqui: duas ferramentas baixadas (513 MB somados), 1,4 GB de
   conjunto preparado, nenhuma GPU-hora desperdiçada em render.
