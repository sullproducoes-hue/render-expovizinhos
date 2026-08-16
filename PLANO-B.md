# PLANO B — a esteira, plano a plano

> Gerado por `scripts/plano_b.py`. Não editar à mão — editar a fonte e regerar.

**22 planos · 182.5 s de filme · 44 de 44 placas resolvem para arquivo em disco.**

10 prontos · 11 prontos com ressalva · 1 sem placa utilizável.


## O ciclo, por plano — sempre os mesmos cinco passos

| # | passo | onde |
|---|---|---|
| 1 | abrir a **placa** (o quadro real do footage) | caminho absoluto, na página ou neste arquivo |
| 2 | colar o **prompt de imagem** + a placa no gerador | prompt abaixo, por plano |
| 3 | baixar o que voltar | `out/plano-b/PXX/gerado/` |
| 4 | colar a imagem aprovada + o **prompt de movimento** no Seedance | prompt abaixo |
| 5 | baixar o clipe | `out/plano-b/PXX/video/` |

**A imagem gerada é a placa do plano seguinte quando os dois olham o mesmo lugar** (P14→P15, P19→P20, P02→P22). Isso é o que segura a continuidade do filme.


## Ordem de trabalho — não é a ordem do filme

O filme roda P01→P22. O **trabalho** não: começa pelo que tem mais tela e pelo que pode travar.


### Onda 1 — os quatro diferenciais

*mais tempo de tela, e os três com material mais fino. Se algo falhar, falha aqui.*

| plano | local | dur. | estado |
|---|---|---|---|
| **P06** | Mercado do Produtor | 17.5 s | PRONTO COM RESSALVA |
| **P08** | Cafe Colonial | 13.5 s | PRONTO COM RESSALVA |
| **P14** | Fazendinha | 18.5 s | PRONTO COM RESSALVA |
| **P15** | Fazendinha (continuacao, orbita) | 7.0 s | PRONTO COM RESSALVA |
| **P19** | Arena de Rodeio | 12.0 s | PRONTO COM RESSALVA |

### Onda 2 — abertura e fechamento

*o portal abre e fecha o filme; a mesma imagem serve nos dois, espelhada.*

| plano | local | dur. | estado |
|---|---|---|---|
| **P01** | Estacionamento | 7.0 s | PRONTO |
| **P02** | Portal -- 'E daqui que sai o alimento que sustenta o mundo' | 9.0 s | PRONTO COM RESSALVA |
| **P21** | 'Aqui sera um grande balcao de negocios' -- subida final | 7.0 s | PRONTO |
| **P22** | Saida pelo portal | 6.0 s | PRONTO COM RESSALVA |

### Onda 3 — o corpo do percurso

*planos de 5 a 11 s, o miolo. Rodam em série, sem decisão nova.*

| plano | local | dur. | estado |
|---|---|---|---|
| **P03** | Pavilhao 1 -- Industria, Comercio e Prestacao de Servicos | 6.0 s | PRONTO |
| **P04** | Praca de Alimentacao Coberta | 7.0 s | PRONTO COM RESSALVA |
| **P05** | Pavilhao 2 -- Industria, Comercio e Prestacao de Servicos | 5.0 s | PRONTO |
| **P07** | Agroindustrias | 5.0 s | PRONTO COM RESSALVA |
| **P09** | Praca de Alimentacao Aberta | 9.0 s | PRONTO |
| **P10** | Recinto de Leiloes | 8.0 s | PRONTO |
| **P11** | Exposicao de Animais | 11.0 s | PRONTO |
| **P12** | Pista de Julgamentos | 5.0 s | PRONTO COM RESSALVA |
| **P13** | Expositores Externos | 5.5 s | PRONTO |
| **P16** | Maquinas, Equipamentos e Implementos Agricolas | 6.0 s | PRONTO |
| **P18** | Area de Shows | 5.5 s | PRONTO |
| **P20** | Palco Principal | 7.0 s | PRONTO COM RESSALVA |

### Onda 4 — o que não tem placa

*só entra depois que as três primeiras fecharem: gera sem referência, ou sai do filme.*

| plano | local | dur. | estado |
|---|---|---|---|
| **P17** | Veiculos e Motos Nauticas | 5.0 s | SEM PLACA |

---

## Os planos, na ordem do filme


### P01 — Estacionamento

`PRONTO` · 7.0 s · 24 mm · subida · câmera a 24.0 m


**Placas** (abrir estas):


- `F:\Extração quadros expo 2025\DJI_20251127184025_0104_D\quadros\q020_00-00-40.jpg`  
  placa-base · confirmado · fim de tarde · nota 96.2 · **EM PÉ, o filme é deitado**  
  *asfalto com vaga pintada virando saibro vermelho, sol a ~5 graus. E a hora do filme.*

- `E:\Projetos todos\Mapa - agroshow\Brutos Expo\agroshow extrator somente\extracao\1 _15_\quadros\q007_00-00-02.jpg`  
  placa-base · confirmado · dia · nota 48.6  
  *entrada do Recinto de Leiloes com estacionamento e cerca, com sol -- uma das tres folhas de sol do lote 01.*

- `F:\Extração quadros expo 2025\IMG_9131-004\quadros\q002_00-00-11.jpg`  
  apoio · confirmado · dia · nota 50.7  
  *parque VAZIO de manha: via asfaltica com terra vermelha arrastada por cima. Placa limpa, sem nada para a IA apagar.*


**Prompt de imagem:**

```
Ultra-photorealistic photograph, not a 3D render and not an illustration. Southern Brazil agricultural fairground in Dois Vizinhos, Parana. Shot on a full-frame camera, natural colour, real atmospheric haze, believable depth of field, no CGI look, no plastic surfaces, no oversaturation, no HDR halo. wide gravel parking field full of parked pickup trucks and cars, families walking toward the entrance gate, tree-lined access avenue. white peaked event marquees and tents pitched across the grounds, guy ropes and steel poles visible. late-afternoon golden hour, 18:15 on 27 November, sun low at ~10 degrees above the horizon, long warm raking shadows, clear sky with soft high cloud. 24 mm lens from a drone about 24 m above the ground, roughly 122 m from the subject, looking down at a shallow angle — the ground plane still reads, this is not a top-down map view. 16:9 horizontal frame, 2560x1440.
```

**Negativo:**

```
cartoon, illustration, 3D render, videogame, CGI, plastic skin, distorted faces, extra limbs, warped text, unreadable signage, watermark, logo overlay, oversaturated colours, fisheye distortion, grandstand bleachers around the rodeo arena
```

**Prompt de movimento (Seedance):**

```
slow vertical crane-up, camera rising steadily while holding the subject centred. Duration 7.0 seconds. The camera moves slowly and deliberately at a constant speed — this is a drone shot, not a fast fly-through. Everything in the frame stays physically consistent: people walk, flags and banners move in a light breeze, animals shift naturally, the light does not change. No morphing, no warping architecture, no drifting text, no zoom.
```

**Salvar em:** `out/plano-b/P01/gerado/` e `out/plano-b/P01/video/`


### P02 — Portal -- 'E daqui que sai o alimento que sustenta o mundo'

`PRONTO COM RESSALVA` · 9.0 s · 35 mm · push-in · câmera a 6.5 m

**Letreiro na tela:** É daqui que sai o alimento que sustenta o mundo — *entra na edição, nunca no prompt.*


> **Bloqueio:** Duas entradas ou uma? A foto de 12/08 e o portico azul do 0126_D tem o mesmo letreiro PARQUE DE EXPOSICOES. Qual dos dois abre e fecha o filme e pergunta para ele. Registrado em lideres.md e nao arbitrado aqui.


**Placas** (abrir estas):


- `E:\Projetos todos\Mapa - agroshow\WhatsApp Image 2026-08-12 at 13.15.32.jpeg`  
  forma · confirmado · foto do cliente, nao e footage · nota None  
  *a UNICA imagem do portal celeiro que existe. Frontal, unica vista. Referencia obrigatoria do primeiro e do ultimo plano.*

- `F:\Extração quadros expo 2025\DJI_20251127211702_0126_D\quadros\q023_00-00-16.jpg`  
  forma · confirmado · noite · nota 51.0 · **EM PÉ, o filme é deitado**  
  *o portico ATUAL do parque -- metalico, azul, com esferas e telao. NOTURNO (o arquivo e de 21:17): serve de FORMA e de leitura de sinalizacao, nao de luz. Nao e o celeiro; entra porque a duvida das duas entradas esta aberta.*

- `E:\Projetos todos\Mapa - agroshow\Brutos Expo\agroshow extrator somente\extracao\1 _15_\quadros\q048_00-00-12.jpg`  
  placa-base · confirmado · dia · nota 69.4  
  *a alameda de entrada com arvores em fileira e postes: o corredor por onde o plano de abertura passa.*

- `F:\Extração quadros expo 2025\DJI_20251127211745_0128_D\quadros\q001_00-00-00.jpg`  
  forma · confirmado · noite · nota 73.9 · **EM PÉ, o filme é deitado**  
  *duas casas de madeira ja construidas no recinto: tabuado vertical, telha ceramica, varanda. E a leitura ECONOMICA do celeiro, que e a que o cliente pediu. NOTURNO (21:17) -- vale a forma e o detalhe de madeira, nao a cor.*


**Prompt de imagem:**

```
Ultra-photorealistic photograph, not a 3D render and not an illustration. Southern Brazil agricultural fairground in Dois Vizinhos, Parana. Shot on a full-frame camera, natural colour, real atmospheric haze, believable depth of field, no CGI look, no plastic surfaces, no oversaturation, no HDR halo. large rustic timber entrance portal in barn style — vertical board cladding, ceramic tile roof, economical construction, a hanging wooden sign across the opening, visitors walking through. white peaked event marquees and tents pitched across the grounds, guy ropes and steel poles visible. late-afternoon golden hour, 18:15 on 27 November, sun low at ~10 degrees above the horizon, long warm raking shadows, clear sky with soft high cloud. 35 mm lens from a low drone, camera about 6 m above the ground, roughly 54 m from the subject, slight downward tilt. 16:9 horizontal frame, 2560x1440.
```

**Negativo:**

```
cartoon, illustration, 3D render, videogame, CGI, plastic skin, distorted faces, extra limbs, warped text, unreadable signage, watermark, logo overlay, oversaturated colours, fisheye distortion, grandstand bleachers around the rodeo arena
```

**Prompt de movimento (Seedance):**

```
slow steady push-in, camera advancing straight toward the subject at constant speed. Duration 9.0 seconds. The camera moves slowly and deliberately at a constant speed — this is a drone shot, not a fast fly-through. Everything in the frame stays physically consistent: people walk, flags and banners move in a light breeze, animals shift naturally, the light does not change. No morphing, no warping architecture, no drifting text, no zoom.
```

**Salvar em:** `out/plano-b/P02/gerado/` e `out/plano-b/P02/video/`


### P03 — Pavilhao 1 -- Industria, Comercio e Prestacao de Servicos

`PRONTO` · 6.0 s · 24 mm · push-in · câmera a 46.0 m

**Letreiro na tela:** Pavilhão 1 — *entra na edição, nunca no prompt.*


**Placas** (abrir estas):


- `E:\Projetos todos\Mapa - agroshow\Brutos Expo\agroshow extrator somente\extracao\1 _16_\quadros\q076_00-01-49.jpg`  
  forma · confirmado · dia · nota 81.4  
  *coluna azul, alvenaria de tijolo vermelho, estrutura de telhado vermelha, e uma pessoa em pe dando escala. E a paleta do parque em um quadro.*

- `F:\Extração quadros expo 2025\IMG_9131-004\quadros\q017_00-02-56.jpg`  
  forma · confirmado · dia · nota 60.2  
  *cobertura POR DENTRO: telha ondulada, tesoura vermelha, terca, pilar azul, piso de cimento gasto. Parque vazio.*

- `E:\Projetos todos\Mapa - agroshow\Brutos Expo\agroshow extrator somente\extracao\1 _1_\quadros\q032_00-00-08.jpg`  
  placa-base · confirmado · fim de tarde · nota 70.0  
  *interior de pavilhao VAZIO -- o vao livre pronto para a IA montar estande dentro.*


**Prompt de imagem:**

```
Ultra-photorealistic photograph, not a 3D render and not an illustration. Southern Brazil agricultural fairground in Dois Vizinhos, Parana. Shot on a full-frame camera, natural colour, real atmospheric haze, believable depth of field, no CGI look, no plastic surfaces, no oversaturation, no HDR halo. long exhibition pavilion with brick walls and corrugated metal roof, commercial trade booths under the roof, banners, visitors browsing. white peaked event marquees and tents pitched across the grounds, guy ropes and steel poles visible. roughly 80 visitors. late-afternoon golden hour, 18:15 on 27 November, sun low at ~10 degrees above the horizon, long warm raking shadows, clear sky with soft high cloud. 24 mm lens from a drone about 46 m above the ground, roughly 23 m from the subject, looking down at a shallow angle — the ground plane still reads, this is not a top-down map view. 16:9 horizontal frame, 2560x1440.
```

**Negativo:**

```
cartoon, illustration, 3D render, videogame, CGI, plastic skin, distorted faces, extra limbs, warped text, unreadable signage, watermark, logo overlay, oversaturated colours, fisheye distortion, grandstand bleachers around the rodeo arena
```

**Prompt de movimento (Seedance):**

```
slow steady push-in, camera advancing straight toward the subject at constant speed. Duration 6.0 seconds. The camera moves slowly and deliberately at a constant speed — this is a drone shot, not a fast fly-through. Everything in the frame stays physically consistent: people walk, flags and banners move in a light breeze, animals shift naturally, the light does not change. No morphing, no warping architecture, no drifting text, no zoom.
```

**Salvar em:** `out/plano-b/P03/gerado/` e `out/plano-b/P03/video/`


### P04 — Praca de Alimentacao Coberta

`PRONTO COM RESSALVA` · 7.0 s · 24 mm · push-in · câmera a 11.0 m

**Letreiro na tela:** Praça de Alimentação — *entra na edição, nunca no prompt.*


> **Bloqueio:** Nenhum quadro do acervo confirma a Praca de Alimentacao Coberta por placa. O candidato entra como tipologia, nao como local.


**Placas** (abrir estas):


- `F:\Extração quadros expo 2025\DJI_0935_stabilized_1\quadros\q008_00-00-05.jpg`  
  apoio · nao_confirmado · fim de tarde · nota 62.7  
  *rua dos food stands ao nivel do chao. Nenhuma placa confirma que seja esta praca.*


**Prompt de imagem:**

```
Ultra-photorealistic photograph, not a 3D render and not an illustration. Southern Brazil agricultural fairground in Dois Vizinhos, Parana. Shot on a full-frame camera, natural colour, real atmospheric haze, believable depth of field, no CGI look, no plastic surfaces, no oversaturation, no HDR halo. covered food court with long rows of tables and chairs, food service counters along one side, families eating, overhead roof structure. white peaked event marquees and tents pitched across the grounds, guy ropes and steel poles visible. roughly 120 visitors. late-afternoon golden hour, 18:15 on 27 November, sun low at ~10 degrees above the horizon, long warm raking shadows, clear sky with soft high cloud. 24 mm lens from a low drone, camera about 11 m above the ground, roughly 52 m from the subject, slight downward tilt. 16:9 horizontal frame, 2560x1440.
```

**Negativo:**

```
cartoon, illustration, 3D render, videogame, CGI, plastic skin, distorted faces, extra limbs, warped text, unreadable signage, watermark, logo overlay, oversaturated colours, fisheye distortion, grandstand bleachers around the rodeo arena
```

**Prompt de movimento (Seedance):**

```
slow steady push-in, camera advancing straight toward the subject at constant speed. Duration 7.0 seconds. The camera moves slowly and deliberately at a constant speed — this is a drone shot, not a fast fly-through. Everything in the frame stays physically consistent: people walk, flags and banners move in a light breeze, animals shift naturally, the light does not change. No morphing, no warping architecture, no drifting text, no zoom.
```

**Salvar em:** `out/plano-b/P04/gerado/` e `out/plano-b/P04/video/`


### P05 — Pavilhao 2 -- Industria, Comercio e Prestacao de Servicos

`PRONTO` · 5.0 s · 24 mm · push-in · câmera a 14.0 m

**Letreiro na tela:** Pavilhão 2 — *entra na edição, nunca no prompt.*


**Placas** (abrir estas):


- `E:\Projetos todos\Mapa - agroshow\Brutos Expo\agroshow extrator somente\extracao\1 _17_\quadros\q008_00-00-04.jpg`  
  forma · confirmado · dia · nota 82.5  
  *galpao VERMELHO com portas AZUIS -- confirma vermelho+azul como identidade construida do parque.*

- `E:\Projetos todos\Mapa - agroshow\Brutos Expo\agroshow extrator somente\extracao\1 _16_\quadros\q021_00-00-29.jpg`  
  forma · confirmado · dia · nota 55.8  
  *ritmo dos vaos e beiral do mesmo tipo de pavilhao, por fora.*


**Prompt de imagem:**

```
Ultra-photorealistic photograph, not a 3D render and not an illustration. Southern Brazil agricultural fairground in Dois Vizinhos, Parana. Shot on a full-frame camera, natural colour, real atmospheric haze, believable depth of field, no CGI look, no plastic surfaces, no oversaturation, no HDR halo. second exhibition pavilion, same construction as the first, trade stands and machinery displays, visitors walking the central aisle. white peaked event marquees and tents pitched across the grounds, guy ropes and steel poles visible. roughly 80 visitors. late-afternoon golden hour, 18:15 on 27 November, sun low at ~10 degrees above the horizon, long warm raking shadows, clear sky with soft high cloud. 24 mm lens from a low drone, camera about 14 m above the ground, roughly 22 m from the subject, slight downward tilt. 16:9 horizontal frame, 2560x1440.
```

**Negativo:**

```
cartoon, illustration, 3D render, videogame, CGI, plastic skin, distorted faces, extra limbs, warped text, unreadable signage, watermark, logo overlay, oversaturated colours, fisheye distortion, grandstand bleachers around the rodeo arena
```

**Prompt de movimento (Seedance):**

```
slow steady push-in, camera advancing straight toward the subject at constant speed. Duration 5.0 seconds. The camera moves slowly and deliberately at a constant speed — this is a drone shot, not a fast fly-through. Everything in the frame stays physically consistent: people walk, flags and banners move in a light breeze, animals shift naturally, the light does not change. No morphing, no warping architecture, no drifting text, no zoom.
```

**Salvar em:** `out/plano-b/P05/gerado/` e `out/plano-b/P05/video/`


### P06 — Mercado do Produtor ·diferencial·

`PRONTO COM RESSALVA` · 17.5 s · 24 mm · push-in · câmera a 15.0 m

**Letreiro na tela:** Mercado do Produtor — *entra na edição, nunca no prompt.*


> **Bloqueio:** Um dos quatro diferenciais e nao existe um unico quadro do acervo com o Mercado do Produtor confirmado por placa. Posicao vem da planta; aparencia nao vem de lugar nenhum.


**Placas** (abrir estas):


- `E:\Projetos todos\Mapa - agroshow\Brutos Expo\agroshow extrator somente\extracao\1 _16_\quadros\q042_00-01-00.jpg`  
  placa-base · nao_confirmado · dia · nota 65.6  
  *o lote 01 registrou que este pavilhao vazio de pilar azul e alvenaria vermelha e a coisa mais parecida com o Mercado do Produtor montado que o acervo tem -- e esta VAZIO, sem banca nenhuma. Placa perfeita para a IA montar as bancas; nome nao confirmado.*


**Prompt de imagem:**

```
Ultra-photorealistic photograph, not a 3D render and not an illustration. Southern Brazil agricultural fairground in Dois Vizinhos, Parana. Shot on a full-frame camera, natural colour, real atmospheric haze, believable depth of field, no CGI look, no plastic surfaces, no oversaturation, no HDR halo. producer's market — open-sided stalls with wooden crates of fresh produce, cheeses, preserves and cured meats, farmers behind the counters talking to buyers. white peaked event marquees and tents pitched across the grounds, guy ropes and steel poles visible. late-afternoon golden hour, 18:15 on 27 November, sun low at ~10 degrees above the horizon, long warm raking shadows, clear sky with soft high cloud. 24 mm lens from a low drone, camera about 15 m above the ground, roughly 45 m from the subject, slight downward tilt. 16:9 horizontal frame, 2560x1440.
```

**Negativo:**

```
cartoon, illustration, 3D render, videogame, CGI, plastic skin, distorted faces, extra limbs, warped text, unreadable signage, watermark, logo overlay, oversaturated colours, fisheye distortion, grandstand bleachers around the rodeo arena
```

**Prompt de movimento (Seedance):**

```
slow steady push-in, camera advancing straight toward the subject at constant speed. Duration 17.5 seconds. The camera moves slowly and deliberately at a constant speed — this is a drone shot, not a fast fly-through. Everything in the frame stays physically consistent: people walk, flags and banners move in a light breeze, animals shift naturally, the light does not change. No morphing, no warping architecture, no drifting text, no zoom.
```

**Salvar em:** `out/plano-b/P06/gerado/` e `out/plano-b/P06/video/`


### P07 — Agroindustrias

`PRONTO COM RESSALVA` · 5.0 s · 24 mm · push-in · câmera a 46.0 m

**Letreiro na tela:** Pavilhão 3 — *entra na edição, nunca no prompt.*


> **Bloqueio:** Sem confirmacao nominal no acervo.


**Placas** (abrir estas):


- `E:\Projetos todos\Mapa - agroshow\Brutos Expo\agroshow extrator somente\extracao\1 _17_\quadros\q061_00-00-30.jpg`  
  apoio · nao_confirmado · dia · nota 70.8  
  *galpao e estrada de terra do mesmo setor. Tipologia, nao nome.*


**Prompt de imagem:**

```
Ultra-photorealistic photograph, not a 3D render and not an illustration. Southern Brazil agricultural fairground in Dois Vizinhos, Parana. Shot on a full-frame camera, natural colour, real atmospheric haze, believable depth of field, no CGI look, no plastic surfaces, no oversaturation, no HDR halo. agro-industry stands: small-scale food processing displays, stainless equipment, tasting counters, branded booths. white peaked event marquees and tents pitched across the grounds, guy ropes and steel poles visible. late-afternoon golden hour, 18:15 on 27 November, sun low at ~10 degrees above the horizon, long warm raking shadows, clear sky with soft high cloud. 24 mm lens from a drone about 46 m above the ground, roughly 20 m from the subject, looking down at a shallow angle — the ground plane still reads, this is not a top-down map view. 16:9 horizontal frame, 2560x1440.
```

**Negativo:**

```
cartoon, illustration, 3D render, videogame, CGI, plastic skin, distorted faces, extra limbs, warped text, unreadable signage, watermark, logo overlay, oversaturated colours, fisheye distortion, grandstand bleachers around the rodeo arena
```

**Prompt de movimento (Seedance):**

```
slow steady push-in, camera advancing straight toward the subject at constant speed. Duration 5.0 seconds. The camera moves slowly and deliberately at a constant speed — this is a drone shot, not a fast fly-through. Everything in the frame stays physically consistent: people walk, flags and banners move in a light breeze, animals shift naturally, the light does not change. No morphing, no warping architecture, no drifting text, no zoom.
```

**Salvar em:** `out/plano-b/P07/gerado/` e `out/plano-b/P07/video/`


### P08 — Cafe Colonial ·diferencial·

`PRONTO COM RESSALVA` · 13.5 s · 24 mm · push-in · câmera a 5.0 m

**Letreiro na tela:** Café Colonial — *entra na edição, nunca no prompt.*


> **Bloqueio:** Um dos quatro diferenciais, sem quadro nominalmente confirmado. O lote 03 tambem achou um salao com mesas e escreveu, literal, que SUPOE ser Centro de Convivencia ou Cafe Colonial. Suposicao nao vira referencia de area: e material de venda de espaco fisico.


**Placas** (abrir estas):


- `F:\Extração quadros expo 2025\DJI_0964_stabilized_1\quadros\q007_00-00-05.jpg`  
  apoio · nao_confirmado · fim de tarde · nota 75.6  
  *fogo de chao com costelas e gradil metalico -- material de gastronomia do proprio recinto. O lote 04 registrou como Cafe Colonial POSSIVEL, sem placa.*


**Prompt de imagem:**

```
Ultra-photorealistic photograph, not a 3D render and not an illustration. Southern Brazil agricultural fairground in Dois Vizinhos, Parana. Shot on a full-frame camera, natural colour, real atmospheric haze, believable depth of field, no CGI look, no plastic surfaces, no oversaturation, no HDR halo. colonial café — long tables laid with breads, cakes, cured meats, cheese and coffee, warm hanging lights, families seated eating. white peaked event marquees and tents pitched across the grounds, guy ropes and steel poles visible. late-afternoon golden hour, 18:15 on 27 November, sun low at ~10 degrees above the horizon, long warm raking shadows, clear sky with soft high cloud. 24 mm lens from a low drone, camera about 5 m above the ground, roughly 60 m from the subject, slight downward tilt. 16:9 horizontal frame, 2560x1440.
```

**Negativo:**

```
cartoon, illustration, 3D render, videogame, CGI, plastic skin, distorted faces, extra limbs, warped text, unreadable signage, watermark, logo overlay, oversaturated colours, fisheye distortion, grandstand bleachers around the rodeo arena
```

**Prompt de movimento (Seedance):**

```
slow steady push-in, camera advancing straight toward the subject at constant speed. Duration 13.5 seconds. The camera moves slowly and deliberately at a constant speed — this is a drone shot, not a fast fly-through. Everything in the frame stays physically consistent: people walk, flags and banners move in a light breeze, animals shift naturally, the light does not change. No morphing, no warping architecture, no drifting text, no zoom.
```

**Salvar em:** `out/plano-b/P08/gerado/` e `out/plano-b/P08/video/`


### P09 — Praca de Alimentacao Aberta

`PRONTO` · 9.0 s · 35 mm · sobrevoo · câmera a 31.0 m

**Letreiro na tela:** Alimentação no Bosque — *entra na edição, nunca no prompt.*


**Placas** (abrir estas):


- `F:\Extração quadros expo 2025\DJI_20251128150932_0138_D\quadros\q008_00-00-06.jpg`  
  forma · confirmado · dia · nota 50.3 · **EM PÉ, o filme é deitado**  
  *fechamento de lona branca com dobra, vinco e translucidez -- a tenda como ela e montada aqui. Serve de gabarito para a IA nao inventar tenda de outro lugar.*

- `F:\Extração quadros expo 2025\DJI_0935_stabilized_1\quadros\q005_00-00-03.jpg`  
  apoio · nao_confirmado · fim de tarde · nota 45.0  
  *rua de food stands em operacao.*


**Prompt de imagem:**

```
Ultra-photorealistic photograph, not a 3D render and not an illustration. Southern Brazil agricultural fairground in Dois Vizinhos, Parana. Shot on a full-frame camera, natural colour, real atmospheric haze, believable depth of field, no CGI look, no plastic surfaces, no oversaturation, no HDR halo. open-air food court in a grove of trees, food trucks and stalls around the edge, picnic tables in dappled shade, people queuing. white peaked event marquees and tents pitched across the grounds, guy ropes and steel poles visible. roughly 70 visitors. late-afternoon golden hour, 18:15 on 27 November, sun low at ~10 degrees above the horizon, long warm raking shadows, clear sky with soft high cloud. 35 mm lens from a drone about 31 m above the ground, roughly 139 m from the subject, looking down at a shallow angle — the ground plane still reads, this is not a top-down map view. 16:9 horizontal frame, 2560x1440.
```

**Negativo:**

```
cartoon, illustration, 3D render, videogame, CGI, plastic skin, distorted faces, extra limbs, warped text, unreadable signage, watermark, logo overlay, oversaturated colours, fisheye distortion, grandstand bleachers around the rodeo arena
```

**Prompt de movimento (Seedance):**

```
smooth aerial fly-over, camera advancing forward above the ground. Duration 9.0 seconds. The camera moves slowly and deliberately at a constant speed — this is a drone shot, not a fast fly-through. Everything in the frame stays physically consistent: people walk, flags and banners move in a light breeze, animals shift naturally, the light does not change. No morphing, no warping architecture, no drifting text, no zoom.
```

**Salvar em:** `out/plano-b/P09/gerado/` e `out/plano-b/P09/video/`


### P10 — Recinto de Leiloes

`PRONTO` · 8.0 s · 35 mm · push-in · câmera a 5.0 m

**Letreiro na tela:** Recinto de Leilões — *entra na edição, nunca no prompt.*


**Placas** (abrir estas):


- `F:\Extração quadros expo 2025\DJI_20251126155259_0053_D\quadros\q035_00-00-46.jpg`  
  forma · confirmado · dia · nota 96.7 · **EM PÉ, o filme é deitado**  
  *top-down do predio de telhado radial com a fachada dizendo RECINTO DE LEILOES ERVELINO COLETTI -- lido em recorte ampliado. E a unica confirmacao nominal por placa deste local no acervo inteiro.*

- `E:\Projetos todos\Mapa - agroshow\Brutos Expo\agroshow extrator somente\extracao\1 _10_\quadros\q052_00-00-20.jpg`  
  forma · confirmado · dia · nota 48.8  
  *orbita COMPLETA do predio redondo: numero de faces, ritmo de pilar, geometria do telhado. A melhor prova de forma que este projeto tem.*

- `E:\Projetos todos\Mapa - agroshow\Brutos Expo\agroshow extrator somente\extracao\1 _12_\quadros\q039_00-00-20.jpg`  
  forma · confirmado · fim de tarde · nota 92.5  
  *salao de leiloes POR DENTRO: forro de madeira ripada em curva, luminaria embutida, cadeira preta, balcao. O audio [02:18] pede o leilao acontecendo.*

- `E:\Projetos todos\Mapa - agroshow\Brutos Expo\agroshow extrator somente\extracao\1 _13_\quadros\q043_00-00-04.jpg`  
  forma · confirmado · fim de tarde · nota 49.9  
  *o pulpito do leiloeiro e as grades azuis do ringue -- o audio nomeia o pulpito.*


**Prompt de imagem:**

```
Ultra-photorealistic photograph, not a 3D render and not an illustration. Southern Brazil agricultural fairground in Dois Vizinhos, Parana. Shot on a full-frame camera, natural colour, real atmospheric haze, believable depth of field, no CGI look, no plastic surfaces, no oversaturation, no HDR halo. livestock auction ring — circular sale ring with a raised auctioneer's booth, tiered seating facing the ring, buyers seated with catalogues, a single animal in the ring. white peaked event marquees and tents pitched across the grounds, guy ropes and steel poles visible. roughly 70 visitors. late-afternoon golden hour, 18:15 on 27 November, sun low at ~10 degrees above the horizon, long warm raking shadows, clear sky with soft high cloud. 35 mm lens from a low drone, camera about 5 m above the ground, roughly 53 m from the subject, slight downward tilt. 16:9 horizontal frame, 2560x1440.
```

**Negativo:**

```
cartoon, illustration, 3D render, videogame, CGI, plastic skin, distorted faces, extra limbs, warped text, unreadable signage, watermark, logo overlay, oversaturated colours, fisheye distortion, grandstand bleachers around the rodeo arena
```

**Prompt de movimento (Seedance):**

```
slow steady push-in, camera advancing straight toward the subject at constant speed. Duration 8.0 seconds. The camera moves slowly and deliberately at a constant speed — this is a drone shot, not a fast fly-through. Everything in the frame stays physically consistent: people walk, flags and banners move in a light breeze, animals shift naturally, the light does not change. No morphing, no warping architecture, no drifting text, no zoom.
```

**Salvar em:** `out/plano-b/P10/gerado/` e `out/plano-b/P10/video/`


### P11 — Exposicao de Animais

`PRONTO` · 11.0 s · 35 mm · sobrevoo · câmera a 14.0 m

**Letreiro na tela:** Pavilhões de Animais — *entra na edição, nunca no prompt.*


**Placas** (abrir estas):


- `F:\Extração quadros expo 2025\DJI_20251126185721_0082_D\quadros\q023_00-00-16.jpg`  
  placa-base · confirmado · fim de tarde · nota 86.5  
  *os SEIS pavilhoes em fila sob sol rasante, com a pista de julgamento gramada ao lado. O quadro mais completo da camada BASE em todo o acervo, e na hora do filme.*

- `F:\Extração quadros expo 2025\DJI_20251126185022_0065_D\quadros\q002_00-00-01.jpg`  
  forma · confirmado · fim de tarde · nota 88.6 · **EM PÉ, o filme é deitado**  
  *a placa diz EXPO VIZINHOS . GADO DE LEITE -- confirmacao nominal do pavilhao. No mesmo quadro, a telha vista de baixo e a brita ao nivel do chao.*

- `E:\Projetos todos\Mapa - agroshow\Brutos Expo\agroshow extrator somente\extracao\1 _14_\quadros\q024_00-00-06.jpg`  
  forma · confirmado · dia · nota 62.3  
  *MANGUEIRAS / currais: grade metalica em serie sobre brita, com cobertura. A planta so tinha o rotulo -- 14,1 x 2,4 m era o tamanho da PALAVRA.*


**Prompt de imagem:**

```
Ultra-photorealistic photograph, not a 3D render and not an illustration. Southern Brazil agricultural fairground in Dois Vizinhos, Parana. Shot on a full-frame camera, natural colour, real atmospheric haze, believable depth of field, no CGI look, no plastic surfaces, no oversaturation, no HDR halo. row of open livestock barns, animals in individual pens with straw bedding, handlers grooming them, feed and water troughs. white peaked event marquees and tents pitched across the grounds, guy ropes and steel poles visible. 34 dairy cattle, 34 Hereford and Braford cattle, 34 Nelore beef cattle, roughly 48 sheep and goats, 22 horses. late-afternoon golden hour, 18:15 on 27 November, sun low at ~10 degrees above the horizon, long warm raking shadows, clear sky with soft high cloud. 35 mm lens from a low drone, camera about 14 m above the ground, roughly 86 m from the subject, slight downward tilt. 16:9 horizontal frame, 2560x1440.
```

**Negativo:**

```
cartoon, illustration, 3D render, videogame, CGI, plastic skin, distorted faces, extra limbs, warped text, unreadable signage, watermark, logo overlay, oversaturated colours, fisheye distortion, grandstand bleachers around the rodeo arena
```

**Prompt de movimento (Seedance):**

```
smooth aerial fly-over, camera advancing forward above the ground. Duration 11.0 seconds. The camera moves slowly and deliberately at a constant speed — this is a drone shot, not a fast fly-through. Everything in the frame stays physically consistent: people walk, flags and banners move in a light breeze, animals shift naturally, the light does not change. No morphing, no warping architecture, no drifting text, no zoom.
```

**Salvar em:** `out/plano-b/P11/gerado/` e `out/plano-b/P11/video/`


### P12 — Pista de Julgamentos

`PRONTO COM RESSALVA` · 5.0 s · 35 mm · orbita · câmera a 23.0 m

**Letreiro na tela:** Pista de Julgamentos — *entra na edição, nunca no prompt.*


> **Bloqueio:** O lote 05 achou outra pista gramada cercada por tapume branco COM CAVALOS e escreveu que supoe ser julgamento e nao arena. Duas candidatas, nenhuma com placa.


**Placas** (abrir estas):


- `F:\Extração quadros expo 2025\DJI_20251126185721_0082_D\quadros\q029_00-00-20.jpg`  
  placa-base · provavel · fim de tarde · nota 61.5  
  *pista de julgamento gramada e cercada, verde uniforme, com arvore isolada dentro e sombra longa atravessando. Duas gramas distintas no mesmo quadro.*


**Prompt de imagem:**

```
Ultra-photorealistic photograph, not a 3D render and not an illustration. Southern Brazil agricultural fairground in Dois Vizinhos, Parana. Shot on a full-frame camera, natural colour, real atmospheric haze, believable depth of field, no CGI look, no plastic surfaces, no oversaturation, no HDR halo. grass judging arena, cattle led on halters by handlers in a line, judges in the centre, spectators along the rail. white peaked event marquees and tents pitched across the grounds, guy ropes and steel poles visible. 8 Hereford and Braford cattle, roughly 40 visitors. late-afternoon golden hour, 18:15 on 27 November, sun low at ~10 degrees above the horizon, long warm raking shadows, clear sky with soft high cloud. 35 mm lens from a drone about 23 m above the ground, roughly 44 m from the subject, looking down at a shallow angle — the ground plane still reads, this is not a top-down map view. 16:9 horizontal frame, 2560x1440.
```

**Negativo:**

```
cartoon, illustration, 3D render, videogame, CGI, plastic skin, distorted faces, extra limbs, warped text, unreadable signage, watermark, logo overlay, oversaturated colours, fisheye distortion, grandstand bleachers around the rodeo arena
```

**Prompt de movimento (Seedance):**

```
slow orbital arc around the subject, camera holding distance and height. Duration 5.0 seconds. The camera moves slowly and deliberately at a constant speed — this is a drone shot, not a fast fly-through. Everything in the frame stays physically consistent: people walk, flags and banners move in a light breeze, animals shift naturally, the light does not change. No morphing, no warping architecture, no drifting text, no zoom.
```

**Salvar em:** `out/plano-b/P12/gerado/` e `out/plano-b/P12/video/`


### P13 — Expositores Externos

`PRONTO` · 5.5 s · 35 mm · sobrevoo · câmera a 13.0 m

**Letreiro na tela:** Expositores Externos — *entra na edição, nunca no prompt.*


**Placas** (abrir estas):


- `F:\Extração quadros expo 2025\DJI_20251128150932_0138_D\quadros\q019_00-00-16.jpg`  
  placa-base · provavel · dia · nota 69.1 · **EM PÉ, o filme é deitado**  
  *brita e saibro com pedra solta, placa de concreto rente ao chao -- o chao onde o estande externo pousa.*


**Prompt de imagem:**

```
Ultra-photorealistic photograph, not a 3D render and not an illustration. Southern Brazil agricultural fairground in Dois Vizinhos, Parana. Shot on a full-frame camera, natural colour, real atmospheric haze, believable depth of field, no CGI look, no plastic surfaces, no oversaturation, no HDR halo. outdoor exhibitor area on grass, open stands and marquees, equipment displayed on the ground, visitors walking between them. white peaked event marquees and tents pitched across the grounds, guy ropes and steel poles visible. roughly 50 visitors. late-afternoon golden hour, 18:15 on 27 November, sun low at ~10 degrees above the horizon, long warm raking shadows, clear sky with soft high cloud. 35 mm lens from a low drone, camera about 13 m above the ground, roughly 48 m from the subject, slight downward tilt. 16:9 horizontal frame, 2560x1440.
```

**Negativo:**

```
cartoon, illustration, 3D render, videogame, CGI, plastic skin, distorted faces, extra limbs, warped text, unreadable signage, watermark, logo overlay, oversaturated colours, fisheye distortion, grandstand bleachers around the rodeo arena
```

**Prompt de movimento (Seedance):**

```
smooth aerial fly-over, camera advancing forward above the ground. Duration 5.5 seconds. The camera moves slowly and deliberately at a constant speed — this is a drone shot, not a fast fly-through. Everything in the frame stays physically consistent: people walk, flags and banners move in a light breeze, animals shift naturally, the light does not change. No morphing, no warping architecture, no drifting text, no zoom.
```

**Salvar em:** `out/plano-b/P13/gerado/` e `out/plano-b/P13/video/`


### P14 — Fazendinha ·diferencial·

`PRONTO COM RESSALVA` · 18.5 s · 24 mm · sobrevoo · câmera a 14.0 m

**Letreiro na tela:** Fazendinha — *entra na edição, nunca no prompt.*


> **Bloqueio:** Um dos quatro diferenciais. Nenhum quadro confirma a Fazendinha por placa. A posicao ja e dele (mapa, 14/08); a APARENCIA continua sem fonte no acervo.


**Placas** (abrir estas):


- `F:\Extração quadros expo 2025\DJI_20251127211745_0128_D\quadros\q001_00-00-00.jpg`  
  forma · confirmado · noite · nota 73.9 · **EM PÉ, o filme é deitado**  
  *casas de madeira construidas no recinto: tabuado vertical, telha ceramica, varanda, cerca de mourao. O lote 10 aponta este quadro como vocabulario da Fazendinha e do portal ao mesmo tempo. NOTURNO (21:17) -- forma sim, cor nao.*

- `F:\Extração quadros expo 2025\DJI_20251128151108_0140_D\quadros\q015_00-00-04.jpg`  
  apoio · provavel · dia · nota 48.6 · **EM PÉ, o filme é deitado**  
  *area infantil EM USO: painel pintado, cones, animadores, criancas. Referencia de como a area funciona na pratica -- sem usar a palavra proibida.*

- `F:\Extração quadros expo 2025\DJI_0962_stabilized\quadros\q004_00-00-04.jpg`  
  apoio · nao_confirmado · fim de tarde · nota 77.8  
  *conjunto de casinhas de madeira com cara de tema rural. O lote 04 escreveu, literal, que NAO tem certeza de que seja a Fazendinha.*


**Prompt de imagem:**

```
Ultra-photorealistic photograph, not a 3D render and not an illustration. Southern Brazil agricultural fairground in Dois Vizinhos, Parana. Shot on a full-frame camera, natural colour, real atmospheric haze, believable depth of field, no CGI look, no plastic surfaces, no oversaturation, no HDR halo. children's farm area — small rustic barn, pony rides, pens with sheep and goats, a border collie herding demonstration, families with small children watching. white peaked event marquees and tents pitched across the grounds, guy ropes and steel poles visible. roughly 55 visitors, 4 horses, 9 sheep and goats, 2 border collie dogs. late-afternoon golden hour, 18:15 on 27 November, sun low at ~10 degrees above the horizon, long warm raking shadows, clear sky with soft high cloud. 24 mm lens from a low drone, camera about 14 m above the ground, roughly 38 m from the subject, slight downward tilt. 16:9 horizontal frame, 2560x1440.
```

**Negativo:**

```
cartoon, illustration, 3D render, videogame, CGI, plastic skin, distorted faces, extra limbs, warped text, unreadable signage, watermark, logo overlay, oversaturated colours, fisheye distortion, grandstand bleachers around the rodeo arena
```

**Prompt de movimento (Seedance):**

```
smooth aerial fly-over, camera advancing forward above the ground. Duration 18.5 seconds. The camera moves slowly and deliberately at a constant speed — this is a drone shot, not a fast fly-through. Everything in the frame stays physically consistent: people walk, flags and banners move in a light breeze, animals shift naturally, the light does not change. No morphing, no warping architecture, no drifting text, no zoom.
```

**Salvar em:** `out/plano-b/P14/gerado/` e `out/plano-b/P14/video/`


### P15 — Fazendinha (continuacao, orbita) ·diferencial·

`PRONTO COM RESSALVA` · 7.0 s · 50 mm · orbita · câmera a 37.0 m


> **Bloqueio:** O mesmo do P14.


**Placas** (abrir estas):


- `F:\Extração quadros expo 2025\DJI_20251128151108_0140_D\quadros\q025_00-00-07.jpg`  
  apoio · provavel · dia · nota 73.4 · **EM PÉ, o filme é deitado**  
  *segundo angulo da mesma area infantil, para a IA nao repetir o mesmo enquadramento no par de planos.*


**Prompt de imagem:**

```
Ultra-photorealistic photograph, not a 3D render and not an illustration. Southern Brazil agricultural fairground in Dois Vizinhos, Parana. Shot on a full-frame camera, natural colour, real atmospheric haze, believable depth of field, no CGI look, no plastic surfaces, no oversaturation, no HDR halo. the same children's farm area seen closer: the pony ring and the animal pens, children feeding the animals over a low wooden fence. white peaked event marquees and tents pitched across the grounds, guy ropes and steel poles visible. roughly 55 visitors, 4 horses, 9 sheep and goats, 2 border collie dogs. late-afternoon golden hour, 18:15 on 27 November, sun low at ~10 degrees above the horizon, long warm raking shadows, clear sky with soft high cloud. 50 mm lens from a drone about 37 m above the ground, roughly 31 m from the subject, looking down at a shallow angle — the ground plane still reads, this is not a top-down map view. 16:9 horizontal frame, 2560x1440.
```

**Negativo:**

```
cartoon, illustration, 3D render, videogame, CGI, plastic skin, distorted faces, extra limbs, warped text, unreadable signage, watermark, logo overlay, oversaturated colours, fisheye distortion, grandstand bleachers around the rodeo arena
```

**Prompt de movimento (Seedance):**

```
slow orbital arc around the subject, camera holding distance and height. Duration 7.0 seconds. The camera moves slowly and deliberately at a constant speed — this is a drone shot, not a fast fly-through. Everything in the frame stays physically consistent: people walk, flags and banners move in a light breeze, animals shift naturally, the light does not change. No morphing, no warping architecture, no drifting text, no zoom.
```

**Salvar em:** `out/plano-b/P15/gerado/` e `out/plano-b/P15/video/`


### P16 — Maquinas, Equipamentos e Implementos Agricolas

`PRONTO` · 6.0 s · 35 mm · sobrevoo · câmera a 9.0 m

**Letreiro na tela:** Máquinas e Implementos — *entra na edição, nunca no prompt.*


**Placas** (abrir estas):


- `F:\Extração quadros expo 2025\DJI_0937_stabilized\quadros\q013_00-00-06.jpg`  
  placa-base · provavel · fim de tarde · nota 74.6  
  *alameda de tratores -- exatamente o setor, com a implantacao real dos equipamentos em fila sob arvore.*

- `F:\Extração quadros expo 2025\DJI_0935_stabilized_2\quadros\q005_00-00-02.jpg`  
  apoio · provavel · fim de tarde · nota 45.0  
  *alameda de maquinas sob as arvores, outro angulo e outra hora.*


**Prompt de imagem:**

```
Ultra-photorealistic photograph, not a 3D render and not an illustration. Southern Brazil agricultural fairground in Dois Vizinhos, Parana. Shot on a full-frame camera, natural colour, real atmospheric haze, believable depth of field, no CGI look, no plastic surfaces, no oversaturation, no HDR halo. agricultural machinery exhibition — tractors, combine harvesters, seeders and implements lined up on gravel, buyers inspecting them, manufacturer flags. white peaked event marquees and tents pitched across the grounds, guy ropes and steel poles visible. roughly 90 visitors. late-afternoon golden hour, 18:15 on 27 November, sun low at ~10 degrees above the horizon, long warm raking shadows, clear sky with soft high cloud. 35 mm lens from a low drone, camera about 9 m above the ground, roughly 68 m from the subject, slight downward tilt. 16:9 horizontal frame, 2560x1440.
```

**Negativo:**

```
cartoon, illustration, 3D render, videogame, CGI, plastic skin, distorted faces, extra limbs, warped text, unreadable signage, watermark, logo overlay, oversaturated colours, fisheye distortion, grandstand bleachers around the rodeo arena
```

**Prompt de movimento (Seedance):**

```
smooth aerial fly-over, camera advancing forward above the ground. Duration 6.0 seconds. The camera moves slowly and deliberately at a constant speed — this is a drone shot, not a fast fly-through. Everything in the frame stays physically consistent: people walk, flags and banners move in a light breeze, animals shift naturally, the light does not change. No morphing, no warping architecture, no drifting text, no zoom.
```

**Salvar em:** `out/plano-b/P16/gerado/` e `out/plano-b/P16/video/`


### P17 — Veiculos e Motos Nauticas

`SEM PLACA` · 5.0 s · 24 mm · travelling · câmera a 21.0 m


> **Bloqueio:** Nenhum quadro do acervo mostra o setor de veiculos e motos nauticas identificado. A separacao entre maquinas e veiculos so existe pela COR com que a planta pinta o estande -- ver scripts/classificar_estandes.py.


**Placas** (abrir estas):


*Nenhuma. Este plano não tem imagem de referência no projeto.*



**Prompt de imagem:**

```
Ultra-photorealistic photograph, not a 3D render and not an illustration. Southern Brazil agricultural fairground in Dois Vizinhos, Parana. Shot on a full-frame camera, natural colour, real atmospheric haze, believable depth of field, no CGI look, no plastic surfaces, no oversaturation, no HDR halo. vehicle and nautical display area — pickup trucks and boats on trailers, dealer stands, buyers walking the line. white peaked event marquees and tents pitched across the grounds, guy ropes and steel poles visible. late-afternoon golden hour, 18:15 on 27 November, sun low at ~10 degrees above the horizon, long warm raking shadows, clear sky with soft high cloud. 24 mm lens from a drone about 21 m above the ground, roughly 37 m from the subject, looking down at a shallow angle — the ground plane still reads, this is not a top-down map view. 16:9 horizontal frame, 2560x1440.
```

**Negativo:**

```
cartoon, illustration, 3D render, videogame, CGI, plastic skin, distorted faces, extra limbs, warped text, unreadable signage, watermark, logo overlay, oversaturated colours, fisheye distortion, grandstand bleachers around the rodeo arena
```

**Prompt de movimento (Seedance):**

```
slow lateral tracking move, camera sliding sideways at constant speed. Duration 5.0 seconds. The camera moves slowly and deliberately at a constant speed — this is a drone shot, not a fast fly-through. Everything in the frame stays physically consistent: people walk, flags and banners move in a light breeze, animals shift naturally, the light does not change. No morphing, no warping architecture, no drifting text, no zoom.
```

**Salvar em:** `out/plano-b/P17/gerado/` e `out/plano-b/P17/video/`


### P18 — Area de Shows

`PRONTO` · 5.5 s · 35 mm · sobrevoo · câmera a 16.0 m

**Letreiro na tela:** Área de Shows — *entra na edição, nunca no prompt.*


**Placas** (abrir estas):


- `F:\Extração quadros expo 2025\DJI_0937_stabilized_1\quadros\q013_00-00-06.jpg`  
  placa-base · provavel · fim de tarde · nota 75.2  
  *area de shows com o palco montado, de dia.*

- `F:\Extração quadros expo 2025\DJI_0961_stabilized\quadros\q015_00-00-11.jpg`  
  placa-base · confirmado · fim de tarde · nota 84.8  
  *a bacia inteira num quadro: anel de saibro, talude gramado descendo, esplanada rebaixada com deck e palco ao fundo. Conferido: NAO HA ARQUIBANCADA.*


**Prompt de imagem:**

```
Ultra-photorealistic photograph, not a 3D render and not an illustration. Southern Brazil agricultural fairground in Dois Vizinhos, Parana. Shot on a full-frame camera, natural colour, real atmospheric haze, believable depth of field, no CGI look, no plastic surfaces, no oversaturation, no HDR halo. large open show ground filling with a crowd at dusk, stage lighting towers, sound system, the crowd facing the stage. white peaked event marquees and tents pitched across the grounds, guy ropes and steel poles visible. a dense crowd of several hundred visitors, 4 visitors. late-afternoon golden hour, 18:15 on 27 November, sun low at ~10 degrees above the horizon, long warm raking shadows, clear sky with soft high cloud. 35 mm lens from a low drone, camera about 16 m above the ground, roughly 84 m from the subject, slight downward tilt. 16:9 horizontal frame, 2560x1440.
```

**Negativo:**

```
cartoon, illustration, 3D render, videogame, CGI, plastic skin, distorted faces, extra limbs, warped text, unreadable signage, watermark, logo overlay, oversaturated colours, fisheye distortion, grandstand bleachers around the rodeo arena
```

**Prompt de movimento (Seedance):**

```
smooth aerial fly-over, camera advancing forward above the ground. Duration 5.5 seconds. The camera moves slowly and deliberately at a constant speed — this is a drone shot, not a fast fly-through. Everything in the frame stays physically consistent: people walk, flags and banners move in a light breeze, animals shift naturally, the light does not change. No morphing, no warping architecture, no drifting text, no zoom.
```

**Salvar em:** `out/plano-b/P18/gerado/` e `out/plano-b/P18/video/`


### P19 — Arena de Rodeio ·diferencial·

`PRONTO COM RESSALVA` · 12.0 s · 35 mm · orbita · câmera a 26.0 m

**Letreiro na tela:** Arena de Rodeio — *entra na edição, nunca no prompt.*


> **Bloqueio:** Onze dos doze lotes usam 'bacia' com ressalva: a placa que aparece diz ARENA DE EVENTOS, nao arena de rodeio. E o acervo NAO TEM arena de rodeio montada -- zero quadros de brete, porteira de partida ou prova. Como o rodeio fica configurado nao vem do footage.


**Placas** (abrir estas):


- `E:\Projetos todos\Mapa - agroshow\Brutos Expo\agroshow extrator somente\extracao\1 _2_\quadros\q014_00-00-11.jpg`  
  placa-base · provavel · dia · nota 48.2  
  *nadir da arena: terra escura batida com rastro circular de arraste, halo de terra vermelha, luz encoberta difusa. A melhor fonte de POSICAO do acervo depois do satelite, e mais recente.*

- `F:\Extração quadros expo 2025\IMG_9133\quadros\q005_00-00-05.jpg`  
  placa-base · provavel · dia · nota 48.3  
  *a pista batida VAZIA inteira, em arco, do nivel do chao, recinto sem gente. Unico registro da pista sem nada em cima -- a placa mais limpa que existe para a IA vestir.*

- `F:\Extração quadros expo 2025\DJI_0961_stabilized\quadros\q015_00-00-11.jpg`  
  forma · provavel · fim de tarde · nota 84.8  
  *o perfil da bacia com palco e tendas 5x5 de regua.*


**Prompt de imagem:**

```
Ultra-photorealistic photograph, not a 3D render and not an illustration. Southern Brazil agricultural fairground in Dois Vizinhos, Parana. Shot on a full-frame camera, natural colour, real atmospheric haze, believable depth of field, no CGI look, no plastic surfaces, no oversaturation, no HDR halo. rodeo arena — an oval dirt track with a bucking bull and a mounted rider, chutes at one end, a stage facing the arena and VIP boxes along the sides. THERE ARE NO GRANDSTAND BLEACHERS around this arena: only the track, the side boxes and the facing stage. white peaked event marquees and tents pitched across the grounds, guy ropes and steel poles visible. one bucking bull, 6 visitors. late-afternoon golden hour, 18:15 on 27 November, sun low at ~10 degrees above the horizon, long warm raking shadows, clear sky with soft high cloud. 35 mm lens from a drone about 26 m above the ground, roughly 85 m from the subject, looking down at a shallow angle — the ground plane still reads, this is not a top-down map view. 16:9 horizontal frame, 2560x1440.
```

**Negativo:**

```
cartoon, illustration, 3D render, videogame, CGI, plastic skin, distorted faces, extra limbs, warped text, unreadable signage, watermark, logo overlay, oversaturated colours, fisheye distortion, grandstand bleachers around the rodeo arena
```

**Prompt de movimento (Seedance):**

```
slow orbital arc around the subject, camera holding distance and height. Duration 12.0 seconds. The camera moves slowly and deliberately at a constant speed — this is a drone shot, not a fast fly-through. Everything in the frame stays physically consistent: people walk, flags and banners move in a light breeze, animals shift naturally, the light does not change. No morphing, no warping architecture, no drifting text, no zoom.
```

**Salvar em:** `out/plano-b/P19/gerado/` e `out/plano-b/P19/video/`


### P20 — Palco Principal

`PRONTO COM RESSALVA` · 7.0 s · 24 mm · push-in · câmera a 19.0 m


> **Bloqueio:** Ha uma arvore plantada na frente da concha, tapando a boca de cena -- out/concha/frente.png. Ou a arvore sai, ou a concha nao aparece em plano nenhum. E decisao dele.


**Placas** (abrir estas):


- `E:\Projetos todos\Mapa - agroshow\Brutos Expo\agroshow extrator somente\extracao\1 _4_\quadros\q012_00-00-02.jpg`  
  forma · confirmado · dia · nota 68.9  
  *o palco existente de frente, em SOL RASANTE: estrutura branca sobre base azul, nao madeira. E a melhor luz do lote 01 e a que casa com o HDRI do filme. No mesmo quadro, grama proxima e uma pessoa em pe dando escala.*

- `F:\Extração quadros expo 2025\IMG_9133\quadros\q004_00-00-04.jpg`  
  forma · confirmado · dia · nota 54.0  
  *o palco fixo da bacia vazio e de dia, quatro angulos dentro da janela. E a concha que entrou na cena em 15/08.*

- `F:\Extração quadros expo 2025\DJI_20251127184447_0110_D\quadros\q005_00-00-02.jpg`  
  forma · confirmado · fim de tarde · nota 64.2 · **EM PÉ, o filme é deitado**  
  *palco de EVENTO montado e vazio, e na frente dele o esquema real dos camarotes: deck de madeira modular, gradil branco, terreo, SEM ARQUIBANCADA. Prova por imagem da restricao 1.*


**Prompt de imagem:**

```
Ultra-photorealistic photograph, not a 3D render and not an illustration. Southern Brazil agricultural fairground in Dois Vizinhos, Parana. Shot on a full-frame camera, natural colour, real atmospheric haze, believable depth of field, no CGI look, no plastic surfaces, no oversaturation, no HDR halo. main stage at dusk, a performer singing, stage lighting on, the crowd below with hands raised. white peaked event marquees and tents pitched across the grounds, guy ropes and steel poles visible. a dense crowd of several hundred visitors, 4 visitors. late-afternoon golden hour, 18:15 on 27 November, sun low at ~10 degrees above the horizon, long warm raking shadows, clear sky with soft high cloud. 24 mm lens from a drone about 19 m above the ground, roughly 38 m from the subject, looking down at a shallow angle — the ground plane still reads, this is not a top-down map view. 16:9 horizontal frame, 2560x1440.
```

**Negativo:**

```
cartoon, illustration, 3D render, videogame, CGI, plastic skin, distorted faces, extra limbs, warped text, unreadable signage, watermark, logo overlay, oversaturated colours, fisheye distortion, grandstand bleachers around the rodeo arena
```

**Prompt de movimento (Seedance):**

```
slow steady push-in, camera advancing straight toward the subject at constant speed. Duration 7.0 seconds. The camera moves slowly and deliberately at a constant speed — this is a drone shot, not a fast fly-through. Everything in the frame stays physically consistent: people walk, flags and banners move in a light breeze, animals shift naturally, the light does not change. No morphing, no warping architecture, no drifting text, no zoom.
```

**Salvar em:** `out/plano-b/P20/gerado/` e `out/plano-b/P20/video/`


### P21 — 'Aqui sera um grande balcao de negocios' -- subida final

`PRONTO` · 7.0 s · 24 mm · subida · câmera a 48.0 m


**Placas** (abrir estas):


- `E:\Projetos todos\Mapa - agroshow\Brutos Expo\agroshow extrator somente\extracao\1 _3_\quadros\q044_00-00-30.jpg`  
  placa-base · confirmado · dia · nota 41.4  
  *nadir alto com o recinto INTEIRO dentro do quadro. E o unico quadro que mostra a coisa toda de uma vez.*

- `E:\Projetos todos\Mapa - agroshow\Brutos Expo\agroshow extrator somente\extracao\1 _11_\quadros\q083_00-00-20.jpg`  
  placa-base · confirmado · dia · nota 55.1  
  *sobe do predio redondo e abre para o recinto com as TENDAS BRANCAS montadas -- e o unico aereo do lote com evento em pe.*


**Prompt de imagem:**

```
Ultra-photorealistic photograph, not a 3D render and not an illustration. Southern Brazil agricultural fairground in Dois Vizinhos, Parana. Shot on a full-frame camera, natural colour, real atmospheric haze, believable depth of field, no CGI look, no plastic surfaces, no oversaturation, no HDR halo. high wide aerial of the whole fairground at dusk, every area lit, tents, pavilions, the arena and the show field all readable at once. white peaked event marquees and tents pitched across the grounds, guy ropes and steel poles visible. late-afternoon golden hour, 18:15 on 27 November, sun low at ~10 degrees above the horizon, long warm raking shadows, clear sky with soft high cloud. 24 mm lens from a drone about 48 m above the ground, roughly 132 m from the subject, looking down at a shallow angle — the ground plane still reads, this is not a top-down map view. 16:9 horizontal frame, 2560x1440.
```

**Negativo:**

```
cartoon, illustration, 3D render, videogame, CGI, plastic skin, distorted faces, extra limbs, warped text, unreadable signage, watermark, logo overlay, oversaturated colours, fisheye distortion, grandstand bleachers around the rodeo arena
```

**Prompt de movimento (Seedance):**

```
slow vertical crane-up, camera rising steadily while holding the subject centred. Duration 7.0 seconds. The camera moves slowly and deliberately at a constant speed — this is a drone shot, not a fast fly-through. Everything in the frame stays physically consistent: people walk, flags and banners move in a light breeze, animals shift naturally, the light does not change. No morphing, no warping architecture, no drifting text, no zoom.
```

**Salvar em:** `out/plano-b/P21/gerado/` e `out/plano-b/P21/video/`


### P22 — Saida pelo portal

`PRONTO COM RESSALVA` · 6.0 s · 35 mm · push-in · câmera a 12.0 m

**Letreiro na tela:** Aqui será um grande balcão de negócios — *entra na edição, nunca no prompt.*


> **Bloqueio:** O mesmo do P02, e pesa mais aqui: nao existe nenhuma vista lateral, traseira, de topo ou de perto do portal. Para modelar em 3D, uma frontal e pouco.


**Placas** (abrir estas):


- `E:\Projetos todos\Mapa - agroshow\WhatsApp Image 2026-08-12 at 13.15.32.jpeg`  
  forma · confirmado · foto do cliente, nao e footage · nota None  
  *restricao 6: o plano final sai pelo portal. A mesma e unica foto.*


**Prompt de imagem:**

```
Ultra-photorealistic photograph, not a 3D render and not an illustration. Southern Brazil agricultural fairground in Dois Vizinhos, Parana. Shot on a full-frame camera, natural colour, real atmospheric haze, believable depth of field, no CGI look, no plastic surfaces, no oversaturation, no HDR halo. the same rustic timber barn portal seen from inside the grounds, visitors walking out through it, night falling behind them. white peaked event marquees and tents pitched across the grounds, guy ropes and steel poles visible. late-afternoon golden hour, 18:15 on 27 November, sun low at ~10 degrees above the horizon, long warm raking shadows, clear sky with soft high cloud. 35 mm lens from a low drone, camera about 12 m above the ground, roughly 26 m from the subject, slight downward tilt. 16:9 horizontal frame, 2560x1440.
```

**Negativo:**

```
cartoon, illustration, 3D render, videogame, CGI, plastic skin, distorted faces, extra limbs, warped text, unreadable signage, watermark, logo overlay, oversaturated colours, fisheye distortion, grandstand bleachers around the rodeo arena
```

**Prompt de movimento (Seedance):**

```
slow steady push-in, camera advancing straight toward the subject at constant speed. Duration 6.0 seconds. The camera moves slowly and deliberately at a constant speed — this is a drone shot, not a fast fly-through. Everything in the frame stays physically consistent: people walk, flags and banners move in a light breeze, animals shift naturally, the light does not change. No morphing, no warping architecture, no drifting text, no zoom.
```

**Salvar em:** `out/plano-b/P22/gerado/` e `out/plano-b/P22/video/`

