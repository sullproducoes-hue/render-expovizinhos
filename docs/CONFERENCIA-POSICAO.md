# Conferência de posição — 14/08/2026

Feita porque o Natan mandou: *"mas tenho uma dúvida em relação a posição das
coisas está tudo correto?"* e *"isso tem que bater primeiro e depois o sol e
iluminação"*.

Ele está certo, e a ordem estava invertida no plano da Rodada 1. Iluminar uma
cena onde as coisas estão no lugar errado é trabalho jogado fora. A luz foi
suspensa até isto fechar.

**Fonte de verdade:** as imagens de satélite que ele mandou em
`E:\Projetos todos\Mapa - agroshow\Localização das coisas`.
**Régua:** a barra de escala do Google, medida em pixel — **94 px = 50 m**,
ou seja **0,53191 m/px**.

---

## O que CONFERE

### A escala 0,5611 m/pt está certa

Era a pendência nº 2 do `RETOMAR.md`, aberta desde o começo, e a tentativa
anterior pelas 282 cotas do mapa tinha dado inconclusivo (q1 0,357 / q3 0,557).

Método: espaçamento entre pavilhões de animais consecutivos, medido nos dois.

| | espaçamentos medidos |
|---|---|
| **Satélite** | 22,9 · 23,1 · 32,4 · 35,1 m |
| **Planta** | 23,0 · 23,0 · 22,9 · 23,2 · 23,3 m |

Os dois primeiros batem **exatamente**. Os dois últimos são maiores porque o
detector pulou galpão — há mais galpões na fileira do satélite do que os seis
pavilhões de animais da planta.

> **Cuidado que custou uma medição errada:** medir a *extensão total* da fileira
> dá 155,7 m no satélite contra 127,0 m na planta, sugerindo 23% de erro de
> escala. É falso — a extensão inclui galpões que não estão na planta. O que
> vale é o **espaçamento**, que é local e não acumula.

### Os pavilhões de animais estão no lugar

Na sobreposição, os retângulos da cena caem praticamente em cima dos galpões
reais.

---

## O que NÃO CONFERE

### 1. ~~O centro da arena está 70,6 m fora~~ — DERRUBADO pelo Natan em 14/08

> **O Natan marcou o centro na planta e ele cai praticamente em cima do rótulo
> que o código já usa.** O diagnóstico abaixo estava errado e fica registrado
> porque nada se apaga — e porque o erro de método vale mais que a conclusão.
>
> **Onde eu errei:** comparei o rótulo com duas referências ruins e tratei a
> concordância delas como confirmação.
>
> 1. **O ajuste de círculo nos estandes da série C** dá (−109,5 · −64,7), mas os
>    93 estandes não estão num anel só — os raios vão de 42 a 169 m. Ajustar um
>    círculo a uma nuvem dessas devolve um centro que não significa nada, e a
>    dispersão estava na minha frente: eu registrei "incerteza" e mesmo assim
>    usei o número.
> 2. **A leitura da bacia no satélite** foi a olho, e a bacia real é grande e de
>    borda difusa. Achar que o centro dela estava "abaixo e à direita" da cruz
>    foi impressão, não medida.
>
> Duas fontes fracas concordando não viram uma forte. O que valia era perguntar,
> e o Natan é quem conhece o parque.
>
> **O centro segue sendo o rótulo `ARENA DE RODEIO`, (−74,7 · −3,2) m.**

O texto original, mantido como registro:

### 1'. (errado) O centro da arena está 70,6 m fora

`terreno.centro_da_arena()` devolve `ponto_da_zona(dados, "ARENA DE RODEIO")`,
que é **a posição do rótulo de texto na planta**, não o centro geométrico da
bacia. O texto ainda por cima está inclinado (`angulo_graus: 26.2`), então nem
o meio dele cai no meio da arena.

| origem | centro |
|---|---|
| rótulo de texto (**o que o código usa hoje**) | (−74,7 · −3,2) m |
| ajuste de círculo nos 93 estandes da série C | (−109,5 · −64,7) m |
| **deslocamento** | **70,6 m** |

Duas fontes independentes concordam que está errado: o ajuste dos anéis de
estandes, e a sobreposição no satélite, onde a cruz do centro da cena cai
visivelmente fora da ferradura real.

**Por que isso é grave:** `centro_da_arena` é o argumento de
`terreno.elevacao(x, y, centro_arena)`, que define **todos os patamares** —
arena 0 m → shows 3,5 m → anel 7 m → platô 10 m. O relevo do parque inteiro
está centrado 70 m fora do lugar. Não é detalhe de um objeto: é o terreno.

**Ressalva honesta:** o ajuste de círculo tem dispersão grande (raios de 42,5 a
169 m, mediana 128), porque a série C está em mais de um anel. O número 70,6 m
tem incerteza. O que não tem incerteza é a **direção** do erro, que o satélite
confirma.

### 2. A bacia é ferradura, e a cena faz círculo fechado

`Mapa-Palco e arena.png` mostra a bacia **aberta para nordeste**. O código faz
`primitive_cylinder_add(radius=45)` e `terreno.py` monta anéis concêntricos
fechados. Já estava anotado; a sobreposição confirma.

### 3'. A planta TEM rosa dos ventos, e ninguém tinha lido

O Natan mandou o PDF e ele traz uma **rosa dos ventos** no canto inferior
direito. Isso deixa o norte de ser inferência e vira dado da prancha.

| letra | posição (pt) |
|---|---|
| N | (778,0 · 528,3) |
| S | (792,9 · 601,6) |
| E | (821,3 · 557,4) |

Centro em (785,5 · 565,0). O vetor até o N dá **−11,5°** em relação ao topo da
prancha; o S dá exatamente o oposto e o E cai em 78,1° (previsto 78,5°). As três
fecham.

**`norte_do_mapa_graus` passou de 8,6 para 11,5.** A medição por satélite deu
8,6 por outro caminho — as duas concordam em direção e ordem de grandeza, e a
diferença de 2,9° é a incerteza real de medir por imagem. Vale a rosa: é
declaração do projetista.

### 3. O norte medido por satélite — 8,6°, hoje segunda fonte

Medido por `scripts/conferir_norte.py`: fileira dos 6 pavilhões a **160,3°** na
planta (SVD nos rótulos, resíduo 2,3 m) contra **169,0°** no satélite (PCA na
mancha dos telhados). Estável em três recortes diferentes: 168,9 / 169,0 / 169,0.

Gravado em `data/luz.json` como `norte_do_mapa_graus: 8.6`.

### 4'. A forma dos pavilhões está errada: 60×12 assumido, 46×17 medido

`construir_pavilhoes` faz `profundidade = 12.0` e `largura = area / profundidade`,
com o comentário *"Proporcao 60 x 12 m assumida para os de 720 -- confira em
campo"*. Medido no desenho por `scripts/extrair_footprints.py`:

| pavilhão | medido | área medida | cotada |
|---|---|---|---|
| GADO CORTE | 45,9 × 16,8 m | 765 m² | 720 (+6%) |
| NÚCLEO CARA BRANCA | 45,9 × 16,8 m | 767 m² | 720 (+6%) |
| OVINOS E CAPRINOS | 45,9 × 16,8 m | 764 m² | 720 (+6%) |
| PEQUENOS ANIMAIS | 45,9 × 17,0 m | 772 m² | 720 (+7%) |

O viés de +6% é o contorno do traço entrando na mancha, e é constante — o que
dá confiança no método. **A proporção assumida não se sustenta: o galpão real é
bem mais curto e mais largo.**

### 4. `RUMO_PAVILHOES` — a convenção é confusa, mas o valor está certo

`build_scene.py` declara `RUMO_PAVILHOES = 341.0` como se fosse azimute, e
`estruturas._girar()` aplica como rotação matemática (`rotation_euler.z`). Isso
resulta em eixo longo apontando para **azimute 109°**.

Cheguei a marcar como erro. Não é: o footprint medido no desenho dá **rumo
108°** para os seis. Bate dentro de 1°. **A convenção é enganosa e vai enganar
de novo, mas o número está certo — não mexer.**

### 4''. `PAVILHÃO 1` e `PAVILHÃO 3` não saíram na medição

O extrator achou footprint para **91 das 113 zonas**. Entre as 22 que faltaram
estão justamente `PAVILHÃO 1` e `PAVILHÃO 3` — e mais `Praça de Alimentação`,
`Aberta`, `Café Colonial`, `Cozinha Didática`, `Mercado do Produtor`,
`ESPAÇO P/ MESAS`, `É CHURRASCO!`, `PALCO AFTER`.

Parte é esperada: `Talude` (6×) e `Mata Nativa` não são edificação e não têm
mancha cinza — está certo não acharem. Mas os pavilhões e as praças **são**
construção, e o motivo mais provável é que o rótulo delas fica escrito fora do
polígono (o texto está posicionado no espaço livre, apontando para o bloco),
além do raio de busca de 45 pt.

Fica aberto: aumentar o raio, ou casar rótulo com bloco por proximidade de
borda em vez de centroide.

`build_scene.py` declara `RUMO_PAVILHOES = 341.0` com o comentário de que sai do
`angulo_graus` do rótulo. Mas `estruturas._girar()` aplica o valor como
**rotação matemática** (`rotation_euler.z`), não como azimute de compasso. O
resultado é que o eixo longo do galpão aponta para **azimute 109°**, enquanto a
fileira corre a 160,3°.

Não mexi: é geometria e precisa de medição própria, e mexer sem medir seria
trocar um erro por outro.

---

## Erro meu, encontrado e corrigido no mesmo dia

O disco de entorno que criei para fechar o horizonte foi feito chapado em z=10
(o nível do platô). A bacia da arena é **escavada até z=0**, então o disco
passou por cima dela e de metade do terreno. De frente, com a câmera baixa, não
dava para ver; só apareceu na vista de topo.

Corrigido: o entorno agora é um grid que usa a mesma `terreno.elevacao()` do
terreno detalhado e fica 5 cm abaixo dele.

---

## Como refazer esta conferência

```bash
.venv/Scripts/python.exe scripts/conferir_norte.py --debug out/norte-eixo.png
```

```bash
"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background --python scripts/conferir_posicao.py
```

```bash
.venv/Scripts/python.exe scripts/sobrepor.py --arena 861 510
```

A âncora `861 510` não é chute: sai do georreferenciamento pelos pavilhões —
centro da mancha de galpões no satélite (442,8 · 779,9) px, centro dos 6
pavilhões na planta (−315,9 · −112,0) m, girado pelos 8,6° do norte e escalado
por 0,53191 m/px.

---

## A cena constrói uma fração do que a planta descreve

Levantado depois que o Natan mandou o PDF dizendo *"esses são os pavilhões que
tem que ter"*.

**Os 3 pavilhões que somem em silêncio.** `construir_pavilhoes` filtra por
`"PAVILHÃO -"` **com hífen**:

```python
if z["categoria"] != "pavilhoes" or "PAVILHÃO -" not in z["rotulo"]:
    continue
```

A planta tem **9** zonas de pavilhão. Os seis de animais têm hífen e passam;
**PAVILHÃO 1, PAVILHÃO 2 e PAVILHÃO 3 não têm, e são descartados sem aviso.**
São os de Expositores Indústria/Comércio e Serviços, no norte, junto do Saguão
Aberto e da Praça de Alimentação Coberta — e aparecem na sobreposição como os
galpões compridos perto da entrada, sem correspondente na cena.

**A planta não declara a área deles.** A busca por cota mais próxima devolveu
25, 25 e 100 m² a 26–40 pt de distância: são de estandes vizinhos. Os seis de
animais, ao contrário, têm a área colada no rótulo (720 m², e 560 no de
equinos, a 5,2 pt). Para os três numerados a dimensão terá que sair do desenho.

**E o buraco é maior que três pavilhões.** A planta descreve 113 zonas:

| categoria | zonas | vira geometria hoje? |
|---|---|---|
| paisagem | 32 | não |
| infra | 27 | não |
| alimentação | 20 | não |
| pavilhões | 9 | **6 de 9** |
| pecuária | 9 | não |
| vias | 9 | via `vias.json` |
| arena | 7 | parcial |

Nomeando o que se vê na prancha e não existe na cena: Praça de Alimentação
Coberta e Aberta, Saguão Aberto, Mercado do Produtor / Café Colonial / Cozinha
Didática, Recinto de Leilões, Mangueiras, Pista de Julgamentos, Centro de
Convivência do Idoso, Auditório, CCO, Portaria, Controle Sanitário, banheiros,
Área de Show, Fazendinha, Exposição de Máquinas, Expositores Externo, e os
estacionamentos.

Isso é **escopo**, não conserto — e é decisão do Natan.

## O que precisa de decisão do Natan

| # | questão |
|---|---|
| 1 | Trocar o centro da arena do rótulo para o ajuste geométrico? Muda o relevo do parque inteiro |
| 2 | A bacia vira ferradura agora, junto com o centro? As duas mexem no mesmo lugar |
| 3 | `RUMO_PAVILHOES`: medir a orientação real dos galpões no satélite e corrigir a convenção? |
