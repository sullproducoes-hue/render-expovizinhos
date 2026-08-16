# FILA-CENA — o que construir, em que ordem, com que prova

Companheiro de `NOITE-3-QUADROS.md`. Aquele diz **como rodar uma noite**; este
diz **o que construir**, e vale por muitas noites.

O agente não "termina a cena". O agente **fecha o próximo item aberto**. Noite
que acaba no meio do item 12 é seguida por noite que começa no item 12.

---

## LEI DO DETALHAMENTO — distância manda, não importância

| faixa | classe | o que ganha |
|---|---|---|
| ≤ 8 m | **HERO** | modelagem própria, textura de foto, 2k, detalhe de peça |
| 8–30 m | **MÉDIO** | modelagem simplificada ou biblioteca retexturizada, 1k |
| > 30 m | **FUNDO** | instância ou proxy, textura genérica, 512 |

Mediana de voo medida nos 62 voos: **24 m**, gimbal −18,8°. A maior parte do
recinto é FUNDO — e é só por isso que este escopo cabe em 8 GB.

**Nenhum item é promovido a HERO por parecer importante.** Só por número.
`scripts/classificar_distancia.py` ainda **não existe** — é o primeiro item
técnico da próxima noite.

---

## O QUE JÁ ESTÁ FEITO (16/08)

| item | estado |
|---|---|
| índice de material do recinto | ✅ 25 mapas deiluminados, cor medida com erro < 0,5% |
| assets CC0 baixados | ✅ 4 árvores, 12 figuras humanas, 5 props, licença gravada |
| configuração de render | ✅ `data/render-config.json` |
| Q1 portal | ✅ hero fechado, `scripts/heroi_portal.py` |
| Q2 arena e palco fixo | ✅ hero fechado, `scripts/heroi_arena.py` |
| fotogrametria lida e medida | ✅ 6 modelos, erro 0,60 a 0,89 px (D072) |

---

## A FILA

### BLOCO A — esqueleto estrutural *(o mais caro que está parado)*

| # | item | classe | contrato de pronto |
|---|---|---|---|
| A1 | **`cota_da_agua(y)` como fonte única em `estruturas.py`** | — | pilar, oitão e cobertura leem da mesma função. Hoje cada um tem a sua conta e **divergem 16 a 26 cm** (`estruturas.py:301-321`). Já existe implementado em `heroi_arena.py:_cota_cobertura` — é portar |
| A2 | Pavilhões em peças sob Empty pai | — | `pilares`, `oitões`, `cobertura` como objetos separados. **Sem isso `conferir_contato()` não tem dois objetos para comparar** e a junção não é medível |
| A3 | Pés e sapatas de todo pilar | HERO no interno | pé pousado em `terreno.elevacao`, zero flutuando |
| A4 | Espessura real de telhado (~12 cm), oitão fechado até a cumeeira | — | hoje a água é face única sem solidify e o triângulo da empena **vaza céu** |
| A5 | `_fechar()` com `remove_doubles` + `recalc_normals` | — | hoje a cumeeira tem vértice duplicado (`estruturas.py:84`). Já corrigido em `heroi_portal.py:_fechar` — é portar |
| A6 | Palco de evento desenterrado | — | `build_scene.py:1633` passa `z=0.0` onde o terreno está a **10,0 m**. Antes, decidir se ele é duplicata da concha (D024) |
| A7 | Tendas e lonas | MÉDIO | cloth simulada e **congelada em malha** |

### BLOCO B — o portão de estrutura *(não passa sem)*

| # | item | contrato |
|---|---|---|
| B1 | **Contato estendido** | `CONTATOS_EXIGIDOS` (`build_scene.py:1683`) hoje declara **3 pares, todos da concha**. Passa a declarar par por peça. Regra nova: **encostar rente não passa** — exige sobreposição de 5 cm |
| B2 | Folhas 3D × real regeradas | as 22, em Workbench (Cycles come a janela). Auto-reprovação escrita em `data/quadros-ia.json` → `_quadros_3d_reprovados` |
| B3 | Orçamento de malha | total de triângulos dentro do teto; zero cópia onde cabia instância |

**Bloco C só abre com B verde.**

### BLOCO C — chão e fundo

| # | item | nota |
|---|---|---|
| C1 | Terreno e patamares | cota relativa da nuvem esparsa, agora que ela é gabarito de medida (D072) |
| C2 | Grama com desgaste nas rotas | a cor da grama pisada já está medida (0,278); falta a **máscara**, que sai das vias, das bocas de pavilhão e do entorno da arena |
| C3 | Hair de grama **só** onde a câmera desce | P19, P14 e o interno a ~2 m. Hair no terreno inteiro são 367.000 m² e não cabe em 8 GB |
| C4 | Fundo de horizonte | decisão já tomada, sem MapsModelsImporter |

### BLOCO D — máquinas e veículos
Trator (HERO na exposição), colheitadeira, implemento (MÉDIO), caminhão e
estacionamento (FUNDO). Item que não baixar sem login vira pendência **com a URL
do modelo que serviria** — não vira modelagem do zero.

### BLOCO E — circulação
Estradas e vias internas, rotas de público, praças e bocas de pavilhão.

### BLOCO F — arquitetura de repertório
Casinha rústica (HERO), `PREDIO_REDONDO` + anexo (polígono de ~10 faces, dois
pavimentos, guarda-corpo 1,10), `GALPAO_AZUL_E_TIJOLO`, `GALERIA_DE_PILARES` —
os cinco de `data/formas-quinta.json`, que **nunca viraram geometria**.

Fazendinha, Café Colonial e Mercado do Produtor nascem como `origem: PROPOSTA`:
**não têm uma única imagem confirmada por placa** (D037) e são os planos mais
longos do filme.

### BLOCO G — pecuária, e cada espécie tem o seu material
Estrebaria, gado de corte, gado de leite, ovinos, caprinos — **cerca própria,
piso próprio, material próprio**. Não repetir uma cerca genérica: é pedido
explícito dele.

### BLOCO H — comércio e gente
Praça de alimentação (HERO), ambulantes (MÉDIO), público instanciado (as 12
figuras do Quaternius já estão em disco, com **materiais separados de roupa e
pele** — dá variação por instância sem gastar um mapa).

### BLOCO I — vegetação
3–4 variantes de árvore instanciadas (as 4 já estão em disco), pedra procedural.

---

## O QUE ESTÁ ESPERANDO DECISÃO DELE

- **`data/vegetacao.json` declara "malha compartilhada / árvore procedural"** e
  agora existem 4 assets CC0 em disco. O parágrafo `GEOMETRIA` do contrato
  precisa ser reescrito, e isso é doutrina, não execução.
- **`assets/MANIFESTO.md` não lista as 25 texturas novas**, e elas são de uma
  classe de procedência diferente das CC0: são **derivadas de material do
  cliente**. O `.gitignore` já barra binário, então não sobem para o `origin`
  público — mas o manifesto precisa da linha.
- **Escala de textura**: só telha (2,432 m) e madeira (2,10 m) têm `lado_m`
  medido. Terra 8,0 / brita 2,2 / grama 4,5 / concreto 2,0 são estimadas com
  ±40 a 50%. **É um número no JSON** — não precisa regerar mapa nenhum.
- **A regra `por_que_aerial` ficou parcialmente vencida**: ela pedia grama de
  15–25 m para não virar grade, e a grama do recinto tem 4,5 m reais. Está em
  normal-only por isso.

---

## O PEDIDO MAIS BARATO DA NOITE

Uma **foto de celular da parede do portal a 2 metros**. A madeira de hoje está
ampliada ~14× (166 px nativos → 2048): cadência, largura de tábua e junta são
reais, a fibra fina é interpolação. Uma tomada resolve.
