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

# RETOMAR — fotogrametria a partir do footage (16/08/2026, madrugada)

**AGROSHOW 2026 · Parque de Exposições de Dois Vizinhos, PR**

> Handoff de **uma frente só**: reconstruir 3D a partir dos quadros do
> extrator. Não toca em render, decupagem nem letreiro — para essas, o handoff
> é `RETOMAR-1508-RENDER.md` e o `ESTADO.md`.
>
> Decisão: `DECISOES.md` **D071**. Levantamento e log completo:
> **`docs/FOTOGRAMETRIA.md`**.

---

## De onde veio

Pergunta dele, 15/08 à noite: *"é possível criar um mapa 3d só usando as imagem
que tenho no extrator para com esse 3d melhorar esse render?"* Respondi que sim
com ressalvas, ele mandou seguir, autorizou baixar a ferramenta, e mandou
continuar mais uma vez. **Não terminou.**

## Estado em uma linha

**Não reconstruiu.** O melhor resultado foi um modelo degenerado — 13 imagens
registradas com 2 pontos 3D. A causa está cercada, mas não confirmada.

## O que ficou provado, e vale para sempre

**1. Não existe voo de mapeamento neste acervo.** Medi o pitch do gimbal nos 62
voos com telemetria: **zero em nadir** (≤ −60°), 5 entre −60° e −35°, e **57
oblíquos ou de horizonte**. Ortofoto e modelo de terreno do recinto inteiro
estão fora — não por ferramenta, mas porque ninguém voou grade aqui.

**2. Existem 32 órbitas.** Órbita é ótima entrada para reconstruir *um assunto*.
Várias dão volta completa. É por aí que este caminho continua, se continuar.

**3. Os quadros extraídos não têm EXIF.** Zero tags: sem GPS, sem focal. A
georreferência tem de vir dos CSVs de telemetria
(`Brutos Expo\_triagem\telemetria`, 62 arquivos, do stream `djmd`), casada por
timecode. Já fiz isso funcionar: `pose_priors` gravados no banco do COLMAP.

**4. A câmera é um DJI Air 3 (`FC8282`)**, e o vídeo é nativamente 2688×1512
landscape, girado na extração. Focal ~**1792 px** para a wide de 24 mm —
confirmado pela varredura: é a única faixa em que a reconstrução sai do lugar.

**5. Metade das pastas é export estabilizado** (58 de 157). Estabilização
destrói o modelo de câmera. Só originais servem.

## O erro que eu cometi, e que custou uma rodada inteira

Ranqueei os voos pela **hora no nome do arquivo** e propus a arena de rodeio.
Fui olhar os quadros: o voo que o nome diz 10h35 é **show noturno, com multidão
e fogos**. O carimbo do nome não é hora de captura.

Refiz medindo **luminância no pixel** — 156 pastas, três quadros cada. 87 são de
dia. Cruzado com órbita e telemetria, sobraram **15 candidatos reais**.

**Regra que fica:** neste acervo, triagem se faz no pixel, nunca no nome.

## As seis tentativas

| # | conjunto | intrínseca | resultado |
|---|---|---|---|
| 1 | Fazendinha (noturno, 150 img) | OPENCV, focal automática 2304 | 2 registradas |
| 2 | idem | SIMPLE_RADIAL, focal 1280 | 2 registradas |
| 3 | idem | + pose prior GPS por quadro | 0 — nem inicializou |
| 4 | Montagem (dia, rígido, 100 img) | SIMPLE_RADIAL automática | 2 registradas |
| 5 | idem, **COLMAP 3.11.1** | idem | 2 registradas |
| 6 | idem, **focal 1792 declarada** | SIMPLE_RADIAL | **9 e 13 registradas, pico de 27** — mas 0 e 2 pontos |

## O que está descartado por medida

- **Material corrompido**: não. 100 arquivos distintos, 8.232 a 18.804 keypoints
  por imagem, 2.097 pares com mediana de 214 inliers.
- **Versão do COLMAP**: não. 3.11.1 e 4.1.1 falham igual — a suspeita do modelo
  `rigs`/`frames` do 4.x caiu.
- **Cena não-rígida**: não. O conjunto de montagem é de dia, quase sem gente, e
  só **3,4%** dos pares saem degenerados, contra **42%** do noturno.
- **Limiar de PnP**: não. Soltar `abs_pose_min_num_inliers` e
  `abs_pose_max_error` não mudou o desfecho.

## A hipótese que sobra, e que NÃO testei

**Textura repetitiva.** Boa parte do quadro do voo de montagem é **telha
metálica ondulada** e chão de saibro — padrão periódico gera casamento que passa
no RANSAC como plano e não triangula. É a única explicação que cobre o sintoma
esquisito: par com centenas de inliers e reconstrução com dois pontos.

## Próximo passo, na ordem

1. **Trocar de assunto antes de trocar de ferramenta.** Rodar
   `DJI_20251129182345_0168_D` — 189° de órbita, 100 quadros, feira montada com
   árvores e barracas coloridas, luminância 121. Textura muito mais variada que
   telhado. Uns 10 minutos de máquina.
2. Se falhar igual, aí é a ferramenta: **Meshroom** (~2 GB, grátis, sem
   cadastro, usa a NVIDIA).
3. Se reconstruir, seguir para `patch_match_stereo` + `stereo_fusion` e trazer a
   nuvem para o Blender.

## Onde está tudo

| o quê | onde |
|---|---|
| levantamento e log completo | `docs/FOTOGRAMETRIA.md` |
| COLMAP 4.1.1 CUDA | `.ferramentas/colmap/bin/colmap.exe` |
| COLMAP 3.11.1 CUDA | `.ferramentas/colmap311/bin/colmap.exe` |
| conjunto Fazendinha (noturno, descartado) | `out/fotogrametria/fazendinha/` — 1,1 GB |
| conjunto Montagem (dia, o bom) | `out/fotogrametria/montagem/` — 274 MB |
| telemetria dos 62 voos | `E:\Projetos todos\Mapa - agroshow\Brutos Expo\_triagem\telemetria` |

Os bancos já têm features e casamentos calculados: trocar de motor ou de
parâmetro **não repete esse custo**.

## Comando que chegou mais longe

```bash
cd "E:\I.A Edit\render-expovizinhos\out\fotogrametria\montagem" && "..\..\..\.ferramentas\colmap\bin\colmap.exe" mapper --database_path sw_1792.db --image_path images --output_path sw_1792 --Mapper.ba_refine_focal_length 1
```

## O que este caminho NÃO resolve, mesmo se der certo

Interior de galpão (o drone não entra), o layout de 2026 (o que está no footage
é a montagem de 2025), e o recinto inteiro (sem voo nadir). O que ele entrega é
**um lugar por vez**: geometria e textura medidas de um assunto que o drone
circulou.
