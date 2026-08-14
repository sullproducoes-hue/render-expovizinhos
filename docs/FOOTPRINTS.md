# Footprints — o que a planta consegue dizer, e o que ela não diz

**AGROSHOW 2026 · Parque de Exposições de Dois Vizinhos, PR**
Escrito em 14/08/2026, depois da rodada que conserta o extrator.

Este documento existe por um motivo: a rodada anterior registrou
*"104 de 113 medidas"* e anotou, com razão, que **contagem não é qualidade**.
Ao conferir, a desconfiança estava certa e era pior do que parecia.

---

## O achado

**Metade das 104 medidas do v1 era a tinta da própria palavra escrita no mapa.**

A cadeia é esta, e cada elo foi medido:

1. A âncora de cada zona é **o centro da caixa de texto do rótulo** no PDF — o
   centro do span de `MANGUEIRAS` bate com o `(x, y)` da zona na primeira
   decimal. As zonas nasceram da extração de texto, não do desenho.
2. A máscara de `EDIFICAÇÕES` do v1 pega cinza com **V entre 120 e 242**. O
   preenchimento dos prédios é **247** — está *fora* da faixa. O que ela pega de
   verdade é o **hachurado** de dentro, e o fechamento morfológico junta o resto.
3. O cinza antisserrilhado da **fonte** cai exatamente nessa faixa. Ou seja: a
   letra entra na máscara.
4. Logo, onde não há prédio desenhado sob o rótulo, a mancha mais próxima da
   âncora **é a palavra**. E ela é medida, e vira "footprint".

Foi assim que saíram `Talude` de 3 m², `Bosque` de 12 m², oito
`ESTACIONAMENTO` de 9 a 27 m² e `MANGUEIRAS` de 14,1 × 2,4 m — que é,
literalmente, o tamanho da palavra MANGUEIRAS.

Contagem depois do conserto, das 103 zonas (113 rótulos, ver *fragmento* abaixo):

| | zonas |
|---|---|
| **footprint que serve** — vira geometria | **18** |
| medido mas duvidoso — não construir sem olhar | 10 |
| só o rótulo: não há footprint desenhado | 35 |
| fora do alcance: talude, bosque, trilha, rua | 38 |
| sem mancha nenhuma | 2 |

---

## Como o extrator separa uma coisa da outra

O teste é `area_fora_do_rotulo_m2`: **quanto da mancha sobra fora da caixa de
texto**. Letra não deixa sobra; prédio deixa.

Usar a *fração* dentro da caixa não serve, e a exceção diz por quê:
`PAVILHÃO - NÚCLEO CARRA BRANCA` é um nome comprido sobre um prédio pequeno, e
**65% da mancha real** cai dentro da caixa do rótulo. Já a **área absoluta** que
sobra fora separa limpo: abaixo de 20 m² é a palavra; entre 20 e 60 m² mede-se
alguma coisa mas não se constrói.

Os outros três consertos desta rodada:

- **Fragmento de rótulo.** A planta quebra nome comprido em linhas, e cada linha
  virou uma zona: `Praça de Alimentação` + `Coberta`, `CASA DO` + `MÉDICO` +
  `VETERINÁRIO`. Nove nomes foram remontados — sem isso o watershed repartia um
  prédio entre duas metades do mesmo nome. `BANHEIROS FEM.` e `MASC.` ficam a
  13,3 pt e continuam separados de propósito.
- **Semear pela caixa, não pelo ponto.** A zona fica com a mancha de maior
  encontro com o retângulo do rótulo, crescendo aos poucos. Acabou o
  *"PAVILHÃO 1 casou com mancha a 172 px de distância"*: das 19 candidatas, 18
  encostam na mancha já no primeiro passo (6 pt) com 343 px ou mais de encosto.
  A exceção foi um `Bar` que cresceu até 14 pt e encostou em 96 px para abocanhar
  uma mancha de 893 m² — que não é um bar. Está reprovado.
- **Classe de cor que faltava.** O bloco do Mercado do Produtor / Café Colonial /
  Cozinha Didática é **laranja** (S de 77 a 106), não cinza, e caía fora da
  máscara: eram 4 das 9 zonas perdidas.

## O bloco fundido, resolvido

O norte é **um bloco contínuo no desenho** — isso foi conferido no recorte, não
deduzido. Quem separa cômodo lá dentro é a parede interna, então a mancha é
repartida por **watershed com os rótulos como marcadores e o desenho como
relevo**: o corte cai na parede onde ela existe, e vira divisa por proximidade
onde não existe.

| | antes (v1) | agora |
|---|---|---|
| PAVILHÃO 1 | 180,9 × 35,3 m | 51,9 × 25,6 m |
| PAVILHÃO 2 | 180,9 × 35,3 m | 46,0 × 30,8 m |
| Praça de Alimentação Coberta | 180,9 × 35,3 m | 145,5 × 33,6 m |

**Medir a hachura não é medir o prédio.** A primeira versão da partição saiu em
listras diagonais, porque o watershed repartia o traço do hachurado e não a
área. Um `minAreaRect` sobre um punhado de listras devolve retângulo girado — era
daí que vinha rumo de 138° num prédio que corre a 108°. Agora cada componente é
fechada no contorno externo antes de medir.

O **rumo de uma fatia não vale**: a célula tem contorno irregular. Quem tem rumo
é o bloco, e ele sai em `rumo_do_bloco`, com `rumo_confiavel: false`.

---

## O que NÃO tem conserto por processamento

**MANGUEIRAS** é o caso exemplar: um galpão dividido em dezenas de currais,
desenhado como grade quase toda branca. Três primitivos foram testados e os três
foram recusados **pelo número**, não por opinião:

| primitivo | por que caiu |
|---|---|
| casco convexo por raio | a medida cresce com o raio: 31 m a raio 30 pt, 89 m a raio 80 pt. Parâmetro virando resposta não é medida |
| densidade de traço | a mesma grade dá de 3.000 a 50.000 m² conforme janela e limiar — e a densidade dentro do pavilhão cotado dá 0,000, porque preenchimento não é traço |
| região fechada (inundar o branco pela borda) | o recinto inteiro vira UMA região de 591 × 441 m: o contorno externo fecha, os internos vazam |

A causa comum: **o desenho é um bitmap de 1806 × 1383 reamostrado**, e linha fina
não sobrevive. É a mesma limitação já registrada no `ESTADO.md` — nem o PDF nem o
DWG têm geometria vetorial.

Então, para as 35 zonas que só têm rótulo, **a saída não é mais processamento, é
decisão**. O Natan escolheu em 14/08: *"pode fazer com uma estimativa
aproximada"* — o caminho da **caixa padrão declarada**.

Isso virou `data/estimativas.json` + `scripts/estimativas.py`, e as regras da
separação são estas:

- **Medida e estimativa não se misturam.** O que foi medido continua em
  `footprints.json` e não passa pelo estimador; o que é estimado vai para a
  coleção **ESTIMADO** do `.blend`, que dá para esconder inteira num clique e
  ver quanto da cena ainda é palpite.
- **Cada objeto sai carimbado** com `estimado = True`, o `tipo_estimado` e a
  procedência do número colada nele.
- **Onde a planta cota, a cota manda.** Dois casos: `ARENA DO CONHECIMENTO`
  (200 m², a 5 pt do rótulo) e `EQ. LIMPEZA` (100 m², a 3 pt) — ali só a
  proporção é assumida.
- **O rumo não é estimado.** Vem de `angulo_graus` em `locais.json`, o ângulo
  com que a planta escreve o rótulo, porque o nome de um galpão é escrito no
  eixo dele. O sinal inverte da página para o mundo — a mesma relação que já
  ligava `RUMO_PORTAL = 73` ao ângulo −73,2 do rótulo do portal.
- **Estacionamento não vira caixa.** É superfície: sai como chapa no chão. Um
  pátio de 60 × 40 m virando galpão de 3 m apareceria no sobrevoo.
- **Estimativa não atropela medida.** `conferir_estimados.py` compara pegada por
  pegada; quem nascia dentro de sólido medido é afastado e o deslocamento fica
  gravado no objeto. Foram dois casos: um `Bar` 99% dentro do `CAMAROTES - LADO
  B` (andou 6,5 m) e a `ORDENHADEIRA` 51% dentro do `PAVILHÃO - GADO LEITE`
  (5,5 m).

Placar: **33 estimadas, 4 recusadas** (arena, os dois camarotes e o portal já
têm construção própria — estimá-los seria duplicar).

**As mais fracas, e elas estão nomeadas:** os 8 estacionamentos e as
`MANGUEIRAS`. Trocar assim que houver print dele.

O que **não** vale é o caminho que estava em curso: tratar 14,1 × 2,4 m como o
tamanho das mangueiras porque um script devolveu esse número. Estimativa
declarada é honesta; medida falsa não.

---

## A cota agora vem da planta, e o meu erro de cota fica registrado

A conferência era feita contra uma tabela digitada à mão, e a tabela estava
errada: dizia **560 m² para o `PAVILHÃO - PEQUENOS ANIMAIS`**, o que produzia um
falso erro de +38%. A causa foi um teste de substring — o original era
`"EQU" in rotulo`, e **PEQUENOS contém EQU**.

A planta escreve `720,00 m²` a 5,2 pt daquele rótulo. Agora `cotas_do_pdf()` lê
as **158 cotas em texto** do PDF e casa cada uma com o rótulo mais próximo, e
cada item da saída carrega `area_cotada_m2`. Com a cota certa:

| pavilhão | medido | cotado | erro |
|---|---|---|---|
| GADO CORTE | 765,1 m² | 720 | +6% |
| NÚCLEO CARRA BRANCA | 766,8 m² | 720 | +6% |
| OVINOS E CAPRINOS | 764,2 m² | 720 | +6% |
| PEQUENOS ANIMAIS | 772,4 m² | 720 | **+7%** *(era "+38%")* |
| GADO LEITE | 782,9 m² | 720 | +9% |
| EQUÍNOS | 717,3 m² | 560 | **+28%** |

Cinco dos seis num viés de +6 a +9%, que é a morfologia de fechamento inchando o
contorno em ~1,5 px de cada lado. **O EQUÍNOS continua fora da curva** e é o
único caso que ainda merece o olho — mede 49,5 × 20,2 m onde os outros medem
45,9 × 16,8.

## O DWG foi conferido de novo, em 14/08, e não resolve

O Natan perguntou se o `Mapa_AGROSHOW26 (2) (1).dwg` da pasta
`E:\Projetos todos\Mapa - agroshow\` serviria. **É o mesmo arquivo que já está
em `reference/`, byte a byte** (md5 `b07c5e4b153e1b1e8f7e91ed3226ac23`).

Reconferido sem depender da auditoria antiga — varredura crua do DXF contando
entidade por tipo, **inclusive dentro dos BLOCKS**, que é onde o texto mora:

| seção | entidades |
|---|---|
| `ENTITIES` | 4 INSERT, 1 IMAGE |
| `BLOCKS` | 4883 TEXT, 2 HATCH, 1 SOLID, 1 LINE |

**Quatro entidades de desenho no arquivo inteiro.** O mapa é uma imagem mais
uma camada de texto, e o veredito antigo estava certo.

Três coisas a mais que a conferência trouxe, para ninguém repetir o caminho:

- **O raster é linkado, não embutido.** O DWG aponta para
  `.\Mapa_AGROSHOW26 (2) (1)\Mapa_AGROSHOW26 (2) (1)_2.BMP`, 1806 × 1383 px, e
  essa pasta **não veio junto** — não existe no disco. Não adianta pedir: o
  bitmap dentro do PDF é **FlateDecode, sem perda**, e tem exatamente as mesmas
  1806 × 1383. O BMP seria o mesmo pixel.
- **O PDF também não tem vetor.** `get_drawings()` devolve 2 caminhos, e os dois
  são o retângulo branco de fundo da página.
- **Medir no nativo não muda nada, e isso foi medido.** O raster ocupa 1057,9 pt
  de página, o que dá **1,707 px/pt**, e o extrator renderiza a 2,5 — ou seja,
  vinha interpolando. Rodando nos dois: erro médio contra as cotas **16% nos
  dois**, diferença de até 0,3 m por prédio, e o nativo entrega 17 footprints
  contra 18. Fica em 2,5 px/pt de propósito.

## Arquivos

| arquivo | o que é |
|---|---|
| `scripts/extrair_footprints.py` | o extrator. `--metodo v2` é o padrão; `--metodo hachura` reproduz o v1 inteiro |
| `data/footprints.json` | saída do v2 — com `metodo`, `confianca`, `suspeitas` e `area_fora_do_rotulo_m2` em cada item |
| `data/footprints-v1-hachura.json` | a saída do v1, guardada para conferência. **Não usar para construir** |
| `out/footprints-v2.png` | a máscara e as caixas de texto sobre a prancha |

```bash
.venv/Scripts/python.exe scripts/extrair_footprints.py --diagnostico
```
