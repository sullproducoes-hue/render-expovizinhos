# NOITE-3-QUADROS — o alvo é convencer amanhã

**Escrito pelo Natan em 16/08/2026, com o adendo de aceite integrado.**
Substitui `NOITE-FRENTE1.md` e `FILA-CENA.md` **nesta sessão**. Aqueles miravam a
cena inteira; o alvo real é **três quadros que convençam o cliente amanhã**.

Sessão sem operador, até as 11h. **Regra Zero: nunca perguntar.**

---

## AS TRÊS LEIS DESTA NOITE

> **1. Só existe o que está dentro do enquadramento.**
> Objeto fora dos três quadros escolhidos não é construído, não é texturizado,
> não é conferido. É o que faz 10 dias virarem 10 horas.

> **2. Um quadro pronto vale mais que três a 60%.**
> Fecha o Q1 inteiro — geometria, material, luz, render, folha — antes de tocar
> no Q2. Se às 10:00 existir só um, existe um que convence.

> **3. O 3D tem que ganhar da folha, não só existir.**
> A entrega é `real | 3D` lado a lado. Se o 3D não ganha, o quadro não vai à mesa.

---

## REGRA DA PERGUNTA — nenhuma chega a ele

Subagente com dúvida **não pergunta e não decide sozinho**. Devolve ao
orquestrador em uma linha: qual é a dúvida, qual objeto do quadro ela trava, e o
que muda em cada saída possível.

O orquestrador responde **pesquisando a base dele**, nesta ordem:

1. `DECISOES.md` e os deltas — decisão já tomada manda, mesmo que em outro contexto;
2. as regras escritas nos contratos (este arquivo, D016, D023, D024, D037, D067, D069);
3. os documentos do projeto — planta, mapas, transcrições dos áudios do cliente;
4. sessões anteriores, se houver registro em disco.

Responde **citando a fonte** — arquivo e linha, ou o número da decisão. Grava em
`DECISOES.md` como **precedente aplicado**, não como decisão nova.

Só se as quatro fontes ficarem mudas: vira `PENDENCIAS.md` com a dúvida, as
saídas possíveis, e o que o orquestrador escolheu provisoriamente para não parar,
marcado **PROVISORIO**. A execução segue. Ele revê de manhã e o que disser vira
precedente.

**Nunca parar esperando resposta. Perguntar é falha de execução, não cautela.**

---

## ESCOPO

**Entra:** iluminação (golden hour 18:15, HDRI por `medir_hdri.py`, sol por
`sol.py` — num quadro parado a luz é a maior parte do resultado); render (três
quadros parados, Cycles + OptiX); fotogrametria como fonte de câmera e de forma.

**Sai:** o parque. Cerca por espécie, praça de alimentação, ambulante, máquina,
casinha — só se aparecerem em quadro. Perfeição estrutural fora de quadro.

**N/A nesta sessão:** `enquadramento.py`. Não é vermelho.

---

## RENDER — configuração definida, gravada em `data/render-config.json`

- **Amostragem adaptativa: mínimo 10, máximo 50.** É a configuração medida na
  máquina dele e é o padrão da noite. **Não inventar configuração de Cycles.**
- Denoise **OptiX**.
- Especificação de sessão anterior manda sobre recomendação genérica.

**Teste comparativo único, no Q1, teto de 10 minutos:** um render com bounces
cheios e ~200 samples lado a lado com o preset de 50. Preset rápido calibrado
para plano aéreo a 24 m pode matar o contraluz da golden hour, e o portal é plano
baixo. Sem diferença visível → mantém o preset e ganha a noite. Com diferença →
**o Q1 é exceção e usa a configuração cheia.** Resultado em `DECISOES.md` com o
número dos dois tempos.

**Tempo economizado vai para mais ciclos de comparação contra a foto real.
Nunca para um quarto quadro.**

## ORDEM DE SACRIFÍCIO QUANDO A VRAM ESTOURAR

1. descarregar a nuvem de referência (serviu para modelar, não para renderizar);
2. baixar textura de 2k para 1k nas superfícies distantes;
3. reduzir samples e confiar mais no OptiX;
4. **só por último**, baixar a resolução de saída.

Resolução por último porque é a única que o cliente enxerga direto. Degrau usado
em cada quadro registrado em `DECISOES.md`.

---

# FASE A · 0:00 → 1:15 — a câmera vem da fotogrametria

Serial. **Esta é a fase que decide a noite:** câmera errada mata o match-frame, e
match-frame é o produto.

## A.1 · Ler o dado antes de confiar nele — FEITO em 16/08 02:31

`model_analyzer` nos seis modelos, **lendo todos os submodelos, nunca só o `0`**.

| modelo | imagens | pontos | erro reproj. | trilha |
|---|---|---|---|---|
| `montagem/sparse/1` | 100/100 | 42.090 | 0,797 px | 5,67 |
| `montagem/sparse311/1` | 100/100 | 42.300 | 0,796 px | 5,65 |
| `montagem/sparse4/1` | 100/100 | 42.199 | 0,886 px | 5,75 |
| `montagem/sparsec/2` | 100/100 | 42.020 | **0,794 px** | 5,67 |
| `fazendinha/sparse/1` | 150/150 | 37.730 | 0,602 px | 10,35 |
| `fazendinha/sparse3/0` | 150/150 | 37.945 | 0,616 px | 10,31 |

**Todos ≤ 1,5 px → a nuvem entra como GABARITO DE MEDIDA.**

**Mas o número não diz o conteúdo** (D073): `fazendinha` é o evento **à noite,
com a arena tomada de gente**. O erro baixo e a trilha dobrada vêm de multidão e
luz darem feature demais. Ela reconstruiu um mar de pessoas — inútil como
geometria de prédio. **`montagem` é a nuvem que presta**: dia, montagem do
evento, prédio redondo poligonal, galpões de telha, pátio de saibro.

## A.2 · Escalar e prumar a nuvem
COLMAP entrega em escala e eixo arbitrários. Escala por elemento de altura
conhecida do acervo (pessoa em pé no `1 (4)` 00:02, ~1,70 m; ou tendas 5×5 do
`DJI_0961`). Prumo: Z na vertical real. Gravar em
`data/fotogrametria-alinhamento.json`.

## A.3 · Os três quadros
Regra de pontuação: menor volume de geometria em quadro > objeto coberto por
modelo que fechou > marco que o cliente reconhece.

| # | quadro | por quê |
|---|---|---|
| **Q1** | **Portal**, aproximação baixa | única foto que o cliente mandou; ver o próprio portal reconstruído é o golpe mais forte |
| **Q2** | **Arena de rodeio**, P19 | folha mais feia hoje — tábua fina flutuando torta no lugar da tesoura de aço; o antes/depois vende sozinho |
| **Q3** | **Boca de pavilhão**, plano baixo | estrutura resolvida — pilar, sapata, cobertura com espessura — em volume pequeno |

## A.4 · Travar a câmera — o match-frame
**Escolher imagem que ENTROU na reconstrução.** A câmera dela já existe, resolvida
por bundle adjustment. Importar direto — o match bate **por construção**.

Objeto não coberto por nenhum modelo → cai na telemetria dos 62 voos **e vira
pendência** registrando que aquele quadro tem câmera de qualidade inferior.
Câmera fora de ±30% da mediana de 24 m, ou pitch longe de −18,8° → trocar a
imagem de referência e registrar. Não perguntar.

Gravar em `data/quadros-heroi.json`: câmera, imagem real, modelo de origem, e a
**lista fechada de objetos em quadro**, que passa a ser o escopo da noite.

## A.5 · A nuvem como gabarito de forma
Nuvem esparsa concentra ponto em textura rica e abandona superfície lisa. Serve
para **volume e silhueta**; **não** serve para conferir a curva de uma água de
telhado.

## A.6 · Vistoria de mapas e documentos — teto 30 min
`Localização das coisas\`, planta oficial e transcrições dos áudios,
**restrito aos objetos dos três quadros**. **Procurar primeiro cota, dimensão ou
escala** — isso escala a nuvem com muito mais confiança que a pessoa no vídeo.

**Hierarquia:** nuvem > footage > planta > áudio do cliente. Vale D016 (planta
manda em footprint, footage manda em forma, proporção e cor). Divergência que a
hierarquia não resolve vira `PENDENCIAS.md`, nunca decisão autônoma.

**Corte duro 1:15.**

---

# TRILHA PARALELA — desde 0:00

| agente | dono de |
|---|---|
| `materiais` | `assets/textura/*`, entradas em `data/texturas.json` |
| `assets-quadro` | `assets/modelo/*`, `assets/_procedencia.json` |

`materiais`: madeira do portal (foto do cliente) → telha → terra da pista →
grama → concreto. Pipeline: recorte → **deiluminar** (dividir pela gaussiana
~1/8 do lado) → tileável → albedo normalizado para a cor **medida** → roughness
do luminance invertido → normal from-height. **Sem deiluminação não passa.**

`assets-quadro`: Poly Haven → ambientCG → Quaternius. Sketchfab só com token em
variável de ambiente. **Pediu conta → pendência com a URL e passa adiante.**
Só CC0 ou CC-BY com atribuição. **Instância, nunca cópia.**

---

# FASES B, C, D — um quadro por vez

| fase | janela | quadro |
|---|---|---|
| **B** | 1:15 → 4:15 | **Q1 portal** |
| **C** | 4:15 → 6:45 | **Q2 arena** — a tesoura de aço em balanço; entrega o antes/depois do P19 |
| **D** | 6:45 → 8:45 | **Q3 boca de pavilhão** — pilar com sapata, cobertura de 12 cm, oitão fechado até a cumeeira, cumeeira e terça aparentes |

**O ciclo, igual nos três:**
1. geometria em quadro, modelada sobre a nuvem; `cota_da_agua(y)` como fonte
   única; pé pousado em `terreno.elevacao`; contato com **sobreposição de 5 cm**
   — encostar rente não passa;
2. material;
3. entorno mínimo — só o que a lente pega;
4. luz — HDRI golden hour travado, `conferir_sol.py` verde;
5. teste 960×540 / 64 samples, olhado **contra a foto real**;
6. final 2560×1440, EXR linear 32 bits, denoise OptiX;
7. folha `real | 3D` em `out/heroi/Q<n>.jpg`.

> **GATILHO DO Q3 (adendo):** o Q3 **só abre se Q1 e Q2 estiverem ambos com zero
> reprovação em aberto do verificador.** Havendo qualquer reprovação aberta, as
> duas horas do Q3 vão para ela. Dois quadros fortes convencem; três medianos
> denunciam obra inacabada.

---

# FASE E · 8:45 → 10:00 — a mesa

1. render final em fila, alta amostragem, EXR linear 32 bits;
2. **grade** — no Premiere, como o projeto já decidiu (grain, vinheta e aberração
   ficam fora do Blender). Sem tempo: entrega o EXR **e** um JPG com grade por
   script. **EXR cru não se mostra a cliente** — linear sem grade parece lavado;
3. `out/heroi/APRESENTACAO.html` — folhas `real | 3D` em ordem, sem texto técnico;
4. `ENTREGA.md`, `PENDENCIAS.md`, `ESTADO.md`, `DECISOES.md` consolidados.

---

## O VERIFICADOR

Agente `render3d-verificador` (`.claude/agents/render3d-verificador.md`), voz
separada de quem constrói — **nunca o `render-agroshow`**, que é quem planeja.

**Reprova sozinho, nunca aprova sozinho.** Contradisse o construtor, o
verificador ganha e o quadro volta ao loop.

## LOOP, POR QUADRO
```
1. hipótese em UMA linha antes de editar
2. teste 960×540 / 64 samples
3. olhar o teste CONTRA a foto real, nunca sozinho
4. pior divergência primeiro
5. terceira falha na mesma divergência → BLOQUEADO, registra, passa adiante
```
**Prioridade quando o tempo apertar: silhueta > luz > material > detalhe.**
**Se a correção não bate com a hipótese, a hipótese estava errada** — vira delta
registrado, não conserto empurrado.

---

## PROIBIÇÕES

Não construir fora da lista de objetos em quadro · não renderizar o filme · não
sobrescrever `cena.blend` (saída `out/cena-heroi.blend`) · não criar conta · não
instalar addon · não usar `&&` (PowerShell 5.1 quebra no parser) · não apagar
nada em `data/`, `assets/`, `out/quadros-ia/` · não se auto-aprovar · não mostrar
EXR cru · escrita pesada em `F:`.

## PARADAS DURAS

`F:` abaixo de 20 GB · falta de VRAM que não cede com os quatro degraus · dois
quadros seguidos BLOQUEADOS · qualquer login ou senha · o teste 960×540 falhando
três vezes seguidas.

Ao parar: `ESTADO.md` com o motivo, encerra. **Não contornar.**

---

## O QUE ESTARÁ NA MESA

`out/heroi/APRESENTACAO.html` · renders 2560×1440 com grade, mais os EXR · o
**antes/depois da arena** · `out/cena-heroi.blend` · as reprovações do
verificador com número · o alinhamento da fotogrametria gravado · `PENDENCIAS.md`
e a fila com blocos D a I abertos.

**A aprovação continua sendo dele.**
