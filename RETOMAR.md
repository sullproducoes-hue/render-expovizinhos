# RETOMAR — handoff do render-agroshow

**AGROSHOW 2026 · Parque de Exposições de Dois Vizinhos, PR**
Reescrito em 14/08/2026, fim da **terceira** sessão.

Abra este arquivo, depois `docs/FOOTPRINTS.md`, depois `ESTADO.md`.
Aqui está só o que a próxima sessão precisa para continuar sem reler conversa.

---

## COMO A CENA ESTÁ AGORA — leia estes 12 números primeiro

```
8 pavilhoes .............. forma medida do desenho, area fechada na cota da planta
9 zonas medidas .......... footprint do desenho + altura declarada (BASE)
33 zonas estimadas ....... caixa por tipo declarada    (colecao ESTIMADO)
418 arvores .............. 6 bosques, 2 matas, alameda (1 malha instanciada)
4 estruturas ............. portal, palco, 2 camarotes
42 vias · 134 estandes · 22 planos de camera
luz .................... kloppenheim_06, 27/11 18:15, sol a 10,1 graus, 8 bits
materiais .............. cor-base MEDIDA no footage; terreno com mancha de 2 gramas
render ................. 2760x1380, Cycles 128 samples, OptiX
custo .................. 33,1 s/quadro -> 42,6 h o filme inteiro
```

**A delegação em vigor**, palavras dele em 14/08: *"isso tudo já pode fazendo,
se realmente precisa de mim me chama"* e *"deixa sem o Yan e continua todo
processo até a finalização"*. Ou seja: decidir sozinho o que for reversível e
declarado, e só interromper quando a resposta dele mudar o trabalho.

**O Yan não cobre este projeto** — perguntado em 14/08. O `yan/YAN.md` diz que
ele *não executa no lugar dos sistemas*, e `render-expovizinhos` não aparece em
lugar nenhum da pasta `yan/`: ele lê oito sistemas, este é o décimo. Para ele ao
menos carregar as decisões pendentes faltaria uma linha na tabela de roteamento
dele, e isso é Engenharia — com o sim do Natan entre as etapas.

---

## A ordem mudou: posição primeiro, luz depois

Ordem do Natan, literal: **"isso tem que bater primeiro e depois o sol e
iluminação"**, dita quando ele perguntou *"tenho uma dúvida em relação a posição
das coisas está tudo correto?"*.

Ele está certo e o plano da rodada anterior estava invertido. **A luz está
pronta e suspensa** — não é trabalho a refazer, é trabalho a religar quando a
posição fechar.

---

## Decisões dele nesta sessão

| decisão | consequência |
|---|---|
| Luz de **golden hour** | HDRI de fim de tarde, sol rasante |
| **Posição antes da luz** | a Rodada 1 virou conferência de planta |
| **Construir tudo que a planta descreve** (113 zonas) | escopo grande, ver "o que falta" |
| **Ele marca o centro da arena** | marcou; o centro atual está certo |
| **Biblioteca primeiro** — *"quero que baixe tudo que tem de material e formas sem precisar fazer quase nada do zero"* | só se gera do zero o que não existe pronto |
| Medir o custo da vegetação antes de escolher o teto de horas | nada de estimativa |

### Correção de registro dele, e é importante

Ele disse: *"manifesto esta errado pois nunca disse que estava dentro dessa
pasta"*. A afirmação de que ele teria decidido guardar asset **dentro** do
repositório existia só no `RETOMAR.md` anterior, escrita por mim e carimbada
como ordem dele. **Era inferência minha.** Foi repetida três vezes e chegou a
servir de motivo para recusar biblioteca — que é o oposto do que ele quer.

Hoje vale: **CC0, biblioteca primeiro, e onde o arquivo mora não é dogma.**
O que está em disco: binário em `assets/` fora do git (`assets/.gitignore`), com
`assets/MANIFESTO.md` e `assets/_procedencia.json` versionados e md5 conferido,
para `scripts/assets.py` rebaixar tudo. Se ele quiser outro arranjo, é dele.

---

## O que a conferência de posição fechou

Detalhe completo em **`docs/CONFERENCIA-POSICAO.md`**. Resumo:

**CONFERE — a escala 0,5611 m/pt.** Era pendência aberta desde o começo.
Espaçamento entre pavilhões consecutivos: **22,9 e 23,1 m** medidos no satélite
contra **23,0 m** da planta. *(Medir a extensão total da fileira dá 23% de erro
e é falso — há mais galpões no satélite do que na planta. O que vale é o
espaçamento, que é local e não acumula.)*

**CONFERE — os pavilhões de animais estão no lugar.** Projetados no satélite
caem dentro dos galpões reais.

**RESOLVIDO — o norte, pela rosa dos ventos da prancha.** N em (778,0 · 528,3)
pt e S em (792,9 · 601,6) dão **−11,5°** do topo da prancha; o E confirma
(78,1° medido, 78,5° previsto). Gravado em `data/luz.json` como
`norte_do_mapa_graus: 11.5`. A medição por satélite deu 8,6° por outro caminho —
serviu de segunda fonte, e os 2,9° de diferença são a incerteza de medir por
imagem.

**CONFIRMADO PELO NATAN — o centro da arena está certo.** Ele marcou na planta e
caiu praticamente em cima do rótulo `ARENA DE RODEIO`, (−74,7 · −3,2) m.

> **Eu tinha diagnosticado 70 m de erro, e estava errado.** Comparei o rótulo
> com um ajuste de círculo nos 93 estandes da série C — que não estão num anel
> só, os raios vão de 42 a 169 m — e com uma leitura a olho da bacia no
> satélite. Duas fontes fracas concordando não viram uma forte. **Não repetir:**
> quando a referência tem dispersão desse tamanho, perguntar a ele sai mais
> barato que inferir.

**ERRADO — a forma dos pavilhões.** O código faz `profundidade = 12.0` e
`largura = area/12` = 60 × 12 m, com o comentário *"proporção assumida"*.
Medido no desenho: **45,9 × 16,8 m**, com área batendo em +6% contra os 720 m²
cotados, viés constante nos quatro que dão para conferir.

**CERTO POR SORTE — `RUMO_PAVILHOES = 341.0`.** O valor está escrito como se
fosse azimute e `estruturas._girar()` aplica como ângulo matemático, resultando
em azimute 109°. Cheguei a marcar como bug. **Não é:** o footprint medido dá
rumo 108°. A convenção é enganosa e vai enganar de novo — não mexer.

---

## O buraco: a cena tem uma fração da planta

A planta descreve **113 zonas**. Viram geometria hoje: 6 pavilhões, arena,
portal, palco, 2 camarotes, 42 vias, 134 estandes, terreno.

**Os 3 pavilhões que somem em silêncio** — `construir_pavilhoes` filtra por
`"PAVILHÃO -"` **com hífen**, então `PAVILHÃO 1`, `2` e `3` são descartados sem
aviso. São os de Expositores Indústria/Comércio, no norte. Foi o Natan que
apontou, mandando o PDF: *"esses são os pavilhões que tem que ter"*.

> **Corrigido em 14/08 à noite:** "construir tudo que a planta descreve" não é
> executável como estava escrito. A planta **descreve** 113 zonas, mas só
> **desenha** footprint para 18. O resto é rótulo sobre chão aberto. Ver a seção
> do extrator, abaixo.

Não existem na cena: Praça de Alimentação Coberta e Aberta, Saguão Aberto,
Mercado do Produtor / Café Colonial / Cozinha Didática, Recinto de Leilões,
Mangueiras, Pista de Julgamentos, Centro de Convivência do Idoso, Auditório,
CCO, Portaria, Controle Sanitário, banheiros, Área de Show, Fazendinha,
Exposição de Máquinas, Expositores Externo, estacionamentos.

---

## O extrator de footprint: consertado, e o conserto trouxe má notícia

**Fechado em 14/08, à noite. Detalhe inteiro em `docs/FOOTPRINTS.md`.**

A desconfiança da rodada anterior — *"contagem não é qualidade"* — estava certa,
e o buraco era maior. **Metade das 104 medidas do v1 era a tinta da própria
palavra escrita no mapa.** A cadeia, cada elo medido:

- a âncora de cada zona é **o centro da caixa de texto do rótulo** (o centro do
  span de `MANGUEIRAS` bate com o `x,y` da zona na primeira decimal);
- a máscara de EDIFICAÇÕES pega cinza de V 120 a 242, e o **preenchimento do
  prédio é 247** — fora da faixa. Ela pega o **hachurado**, não o prédio;
- o cinza antisserrilhado da **fonte** cai bem nessa faixa;
- então, onde não há prédio desenhado, a mancha sob o rótulo **é a palavra**.

Era daí que vinham `Talude` de 3 m², `Bosque` de 12 m², oito `ESTACIONAMENTO`
de 9 a 27 m² — e `MANGUEIRAS` de 14,1 × 2,4 m, que é o tamanho da palavra
MANGUEIRAS.

O v2 (padrão agora; `--metodo hachura` reproduz o v1 inteiro) separa por
`area_fora_do_rotulo_m2` — quanto da mancha sobra fora da caixa do texto. Letra
não deixa sobra, prédio deixa. Das 103 zonas:

| | zonas |
|---|---|
| **footprint que serve** — vira geometria | **18** |
| medido mas duvidoso | 10 |
| só o rótulo: não há footprint desenhado | 35 |
| fora do alcance (talude, bosque, trilha, rua) | 38 |
| sem mancha nenhuma | 2 |

**Bloco fundido: resolvido.** O norte é um bloco contínuo no desenho — conferido
no recorte, não deduzido. A mancha é repartida por watershed com os rótulos como
marcadores e o desenho como relevo. `PAVILHÃO 1` 51,9 × 25,6 m, `PAVILHÃO 2`
46,0 × 30,8 m, `Praça Coberta` 145,5 × 33,6 m, no lugar dos três iguais a
180,9 × 35,3 m.

**Casamento a distância: resolvido.** Semeia pela caixa do rótulo e não pelo
ponto. Das 19 candidatas, 18 encostam na mancha no primeiro passo (6 pt) com 343
px ou mais; a exceção foi um `Bar` que cresceu até 14 pt para abocanhar 893 m² —
reprovado.

**Mancha vazada: NÃO tem conserto por processamento.** Três primitivos testados
e recusados pelo número: casco convexo por raio (a medida cresce com o raio),
densidade de traço (de 3.000 a 50.000 m² conforme o parâmetro), região fechada
(o recinto inteiro vira uma região só). A causa é comum e já estava no
`ESTADO.md`: **o desenho é um bitmap reamostrado e linha fina não sobrevive.**

## Onde parei, e é daqui que se continua

**As 35 zonas que só têm rótulo precisam de decisão, não de mais script.** Três
caminhos, e a escolha é dele:

1. **print com posição e tamanho**, como ele já combinou fazer para a Fazendinha
   e o portão (pendência 2);
2. **caixa padrão por categoria**, declarada como estimativa e carimbada;
3. **não construir** a zona nesta versão.

O que não vale é o caminho que estava em curso — tratar 14,1 × 2,4 m como o
tamanho das mangueiras porque um script devolveu esse número.

E segue de pé: **construir sobre footprint errado é pior que não construir.**

---

## Arquivos novos desta sessão

| arquivo | o que faz | onde roda |
|---|---|---|
| `scripts/sol.py` | posição solar NOAA, direção no mundo, cor por temperatura | venv **e** Blender (sem dependência) |
| `scripts/assets.py` | baixa CC0 do Poly Haven, confere md5, escreve o manifesto | venv (stdlib) |
| `scripts/medir_hdri.py` | acha o disco solar dentro do HDRI, por pixel | **dentro do Blender** |
| `scripts/conferir_norte.py` | norte pela fileira de pavilhões, planta × satélite | venv (cv2) |
| `scripts/conferir_sol.py` | prova o casamento sol × céu num quadro | Blender |
| `scripts/conferir_posicao.py` | vista de topo ortográfica na escala do satélite | Blender |
| `scripts/sobrepor.py` | põe a vista de topo sobre o satélite | venv (cv2) |
| `scripts/extrair_footprints.py` | mede footprint de cada zona no desenho | venv (pymupdf+cv2) |
| `scripts/provas_luz.py` | folha de 4 provas: 2 HDRIs × 2 enquadramentos | Blender |
| `data/luz.json` | contrato declarado da luz | — |
| `data/hdri-medido.json` | onde está o sol em cada HDRI | — |
| `data/footprints.json` | dimensões medidas do desenho, com confiança item a item | — |
| `data/footprints-v1-hachura.json` | a saída do v1, guardada. **Não construir a partir dela** | — |
| `docs/CONFERENCIA-POSICAO.md` | a conferência inteira, com o erro registrado | — |
| `docs/FOOTPRINTS.md` | o que a planta consegue dizer, e o que ela não diz | — |
| `data/estimativas.json` | tamanho ESTIMADO das zonas que a planta não desenha, por tipo, com o fundamento de cada número | — |
| `scripts/estimativas.py` | resolve a estimativa por zona (roda sem bpy) | venv |
| `scripts/conferir_estimados.py` | acusa estimativa em cima de geometria medida | Blender |
| `scripts/medir_materiais.py` | tira a cor-base de cada material do footage, com âncora e teste de controle | venv |
| `data/materiais-medidos.json` | as cores medidas, com o recorte de cada amostra | — |
| `data/vegetacao.json` | contrato da vegetação: porte, raio da mancha, densidade | — |
| `scripts/cronometrar_vegetacao.py` | mede o custo das árvores por quadro, com e sem | Blender |

---

## A luz, pronta e suspensa

Não precisa refazer. Está em `data/luz.json` e no `build_scene.py`:

- **Sol calculado**, não chutado. 27/11 18:15 → elevação 10,1°, azimute 251,2°.
  Valida contra a telemetria dos 62 voos (golden hour 18:23–19:00; o modelo dá
  6,8° às 18:30). Meio-dia solar às 12:20, pico 85,5°.
- **HDRI casado e provado.** `belfast_sunset_puresky` (sol medido a 2,07°,
  disco = 8,0% da irradiância) e `kloppenheim_06_puresky` (8,04°, 0,1%), os dois
  de Mpumalanga a −25,69° — a mesma latitude de Dois Vizinhos, então o arco
  solar é fisicamente o mesmo. Céu girado 114,9°.
- **O teste do sol foi corrigido antes de passar.** Medir o azimute da sombra
  não testa nada: o disco do HDRI está estourado de propósito e não joga sombra,
  então a sombra vem só da SUN e o teste valida a SUN contra ela mesma. O teste
  bom tem **sombra e disco solar no mesmo quadro** — `conferir_sol.py`, e ele
  grava um segundo quadro com exposure −6 para achar o sol num céu lavado.
- **Energia 5.0**, calibrada na cena real. Em 1.5 o HDRI afogava a SUN e as
  sombras de 5,6× sumiam.
- **Cor: AgX + Punchy, `color_depth = "8"`.** O AgX default desatura os tons
  quentes; em AgX default ele julgaria a *luz* por um defeito de *visualização*.
  Dither só age em 8 bits — a 16 fica inerte.
- **8 ou 16 bits é decisão dele**, com os números: ~15 GB contra ~30 GB, e o
  `encode.sh` lê os dois. EXR foi recusado (contradiz o passo 4 dele, *"quem
  exporta é ele"*).

Provas em `out/luz/`, geradas em ~10 s cada a 1380×690. **Refeitas em 14/08 à
noite sobre a cena nova** — as anteriores mostravam um recinto com 6 pavilhões e
mais nada; as de agora têm as 9 zonas medidas e as 33 estimadas.

**A proposta de HDRI mudou nessa rodada, e por medição.** O sítio pede o sol a
10,1°. Dentro do `kloppenheim_06` o sol está a 8,0° (erro de 2,1°); dentro do
`belfast_sunset`, a 2,1° (erro de 8,0°). O belfast tem disco muito melhor — 8,0%
da irradiância contra 0,06% —, mas **disco forte na altura errada é pior que
disco fraco na altura certa**: num contraluz com céu no quadro, o sol que se vê
tem que concordar com a sombra que cai, e quem dá a direção da sombra é a SUN,
que é calculada. Continua sendo escolha dele: um campo em `luz.json`.

---

## Consertos que entraram

**O portal renderizava como metal escovado.** `build_scene.py` fazia
`aplicar(o, MAT_PAVILHAO if "Camarote" not in o.name else MAT_LONA)` sobre uma
lista que contém `PortalCeleiro`, `Palco` e `CAMAROTES - LADO A/B`. O teste
procura `"Camarote"` num nome todo em MAIÚSCULAS: dá verdadeiro para os quatro.
Eram **dois** defeitos — consertar o `if` jogaria o portal em `MAT_LONA`, branco
de tenda, porque **`MAT_MADEIRA` não existia**. Agora cada estrutura declara o
próprio material em `estruturas.py` e o teste de string sumiu do `main()`.

**Cor de viewport.** `mat.diffuse_color` nunca era setado, então a cena abria
toda cinza no modo sólido — que é como ele vai olhar o `.blend`.

**Erro meu, achado e corrigido no mesmo dia.** O disco de entorno que criei para
fechar o horizonte estava chapado em z=10 (nível do platô), e a bacia é escavada
até z=0: cobria a arena e metade do terreno. De frente não dava para ver; só
apareceu na vista de topo. Agora é um grid que usa a mesma `terreno.elevacao()`.

---

## Comandos

```bash
"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background --python scripts/build_scene.py -- --out out/cena.blend
```

```bash
"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background out/cena.blend --python scripts/conferir_estimados.py
```

```bash
"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background out/cena.blend --python scripts/cronometrar_vegetacao.py
```

```bash
.venv/Scripts/python.exe scripts/medir_materiais.py --debug out/amostras-materiais.png
```

```bash
.venv/Scripts/python.exe scripts/estimativas.py
```

```bash
"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background --python scripts/provas_luz.py -- --saida out/luz
```

```bash
.venv/Scripts/python.exe scripts/extrair_footprints.py --diagnostico --debug out/footprints-v2.png
```

```bash
.venv/Scripts/python.exe scripts/sol.py --tabela 2026-11-27
```

**Nunca com `--factory-startup`** — derruba os addons e o Cycles some.
Nenhum addon está instalado (13 no total, nenhum de sol ou de terreno), então
nada de addon pode entrar no caminho crítico do gerador.

---

## Armadilhas novas, somadas às oito antigas

9. **`cv2.imread` não abre caminho com acento no Windows** — usa a API ANSI e
   devolve `None`. As imagens do Natan estão em `Localização das coisas`. Use
   `cv2.imdecode(np.fromfile(...))`.
10. **`HoughLinesP` mudou de shape** — cv2 4.x devolve `(N,1,4)` e o 5.x `(N,4)`.
    Normalize com `reshape(-1,4)`.
11. **Câmera ortográfica de topo precisa de `clip_end`** — o default é 100 m e a
    câmera fica a 1200 m: o quadro sai vazio e parece que a cena não existe.
12. **Medir extensão total quando o certo é medir espaçamento** — foi o que
    produziu o falso "23% de erro de escala".
13. **Workbench usa `diffuse_color`, não o Principled** — sem setar, tudo cinza.
14. **A máscara de EDIFICAÇÕES pega a tinta da letra** — o cinza da fonte cai na
    faixa V 120–242 e o preenchimento do prédio (247) não. Qualquer coisa
    semeada pela âncora de uma zona pode acabar medindo a palavra. O teste que
    separa é `area_fora_do_rotulo_m2`.
15. **Medir a hachura não é medir o prédio** — repartir a máscara crua reparte as
    LISTRAS, e o `minAreaRect` de um punhado de listras devolve retângulo
    girado. Foi de onde saiu rumo de 138° num prédio que corre a 108°. Fechar a
    componente no contorno externo antes de medir.
16. **Parâmetro que muda a resposta não é medida** — casco convexo por raio e
    densidade de traço davam qualquer número que se quisesse. Se a saída varia
    com o ajuste, o método está errado, não o ajuste.
17. **Há nome repetido no recinto** — três `RESIDÊNCIA`, oito `ESTACIONAMENTO`,
    seis `Bar`. Indexar footprint por rótulo colapsa os repetidos: o gerador
    construiu 7 zonas onde deveria construir 9, **sem erro nenhum na tela**.
    Lista, nunca dicionário por nome.
18. **`matrix_world` não vale dentro do laço de construção** — só depois que o
    Blender atualiza a cena. Ler pegada ali dá tudo na origem: a primeira versão
    do teste de colisão concluiu que a cena inteira estava dentro do
    PAVILHÃO - EQUÍNOS e afastou 33 objetos em 20 m cada. Ou
    `view_layer.update()`, ou conta fechada (`pegada_prevista`).
19. **Construtor e conferidor com régua diferente é ter dois juízes** — o
    afastamento usava 25% e a conferência 10%: o CCO nascia com 12% de si dentro
    do AUDITÓRIO, passava na construção e era acusado depois.

---

## O que está aberto

| # | pendência | com quem |
|---|---|---|
| ~~1~~ | ~~Os dois modos de falha do extrator~~ — **fechado em 14/08.** Bloco fundido e casamento a distância, resolvidos; mancha vazada não tem conserto por processamento. Ver `docs/FOOTPRINTS.md` | Resolvida |
| ~~2~~ | ~~Construir as demais zonas com footprint que serve~~ — **feito em 14/08.** As 9 que faltavam entraram: Praça de Alimentação Coberta, Recinto de Leilões, Café Colonial, Auditório, Palco After, Lavagem de Animais e as 3 residências. Nelas o **footprint é medido e só a altura é declarada** — cada objeto leva `footprint_medido` e `altura_estimada` | Resolvida |
| ~~3~~ | ~~Corrigir a forma dos pavilhões~~ — **feito em 14/08.** O gerador lê `data/footprints.json`; a cena passou de 6 para **8 pavilhões** (entraram o 1 e o 2), e o `PAVILHÃO 3` agora é **recusado com motivo impresso**, não descartado em silêncio | Resolvida |
| ~~3b~~ | ~~O `PAVILHÃO - EQUÍNOS` mede diferente dos irmãos~~ — **resolvido em 14/08, olhando o desenho.** Era mancha contaminada: a componente dele engole um estande de 5×5 e um pedaço do bloco da lavagem, e isso aparece no **preenchimento** — 0,71 do próprio retângulo, contra 0,99 dos cinco irmãos. O gerador agora detecta isso e usa a **profundidade mediana da família** (medida em cinco prédios) com a largura tirada da cota. Os seis fecham exatos: 720 m² e 560 | Resolvida |
| ~~2b~~ | ~~As 35 zonas sem footprint desenhado~~ — **decidido por ele em 14/08: _"pode fazer com uma estimativa aproximada"_.** Feito: `data/estimativas.json` + `scripts/estimativas.py`, 33 construídas na coleção **ESTIMADO**, 4 recusadas por já existirem | Resolvida |
| 2c | Trocar as estimativas **mais fracas** quando ele mandar print: os 8 estacionamentos e as MANGUEIRAS | **Natan** |
| 4 | A bacia é ferradura aberta para nordeste; o código faz cilindro fechado | próxima sessão |
| ~~5~~ | ~~Religar a luz depois que a posição fechar~~ — **feito em 14/08**, por ordem dele (*"pode fazer a luz"*). As 4 provas em `out/luz/` foram refeitas **sobre a cena nova**, com as 9 zonas medidas e as 33 estimadas dentro | Resolvida |
| ~~6~~ | ~~8 ou 16 bits no master~~ — **decidido em 14/08, com ele delegando: fica 8.** O painel P2,9 é 8 bits, a entrega é ProRes e H.264, e o dither só age na conversão para 8 (a 16 fica inerte, e é ele que segura o banding no céu de fim de tarde). ~15 GB contra ~30 GB | Resolvida |
| 7 | Qual HDRI — **proposta trocada para `kloppenheim_06` por medição**: o sítio pede o sol a 10,1° e o sol dentro dele está a 8,0 (erro de 2,1°) contra 2,1 do belfast (erro de 8,0°). Um campo em `luz.json`, reversível. Provas novas em `out/luz/` | Natan |
| 11 | **O horizonte é uma linha reta.** O entorno é um disco chapado de 3 km. **Prova em imagem:** o quadro `DJI_20251129182345_0168_D` 00:00:52 mostra o morro atrás do recinto, a lavoura subindo em socalco e o conjunto de silos — nada disso existe na cena. Com o sol a 10° e a câmera baixa, isso lê como CG. Precisa de relevo regional (TOPODATA/OpenTopography, que só funciona na máquina dele) | próxima sessão |
| 12 | **Falta textura.** A cor-base foi medida e o terreno já mistura as duas gramas por ruído de duas frequências — o que falta são mapas CC0 (normal, variação fina) em telha, lona, brita e grama. É o que ainda faz o gramado ler como feltro em close | próxima sessão |
| 13 | **Vegetação: falta o arbusto dos 15 taludes.** Bosques, matas e alameda estão feitos (418 árvores) | próxima sessão |
| 14 | **Povoamento** — gente, gado, montaria, laçada, salão do leiloeiro. É o que o áudio do cliente descreve dentro de cada ambiente, e hoje o recinto está vazio | próxima sessão |
| 15 | **Títulos e letreiros** — passo 4 do fluxo dele. Logo se resolve com o JPEG achado ou o nome simples; não esperar vetor. Restrições duras: a palavra "Kids" é proibida (usar *Fazendinha*), e os quatro diferenciais ganham mais tela | próxima sessão |
| 8 | Alturas dos patamares (0 → 3,5 → 7 → 10 m) seguem estimadas | cliente |
| 9 | Traçado das vias: 42 lidas do bitmap, `conferido_pelo_natan: false` | Natan |
| 10 | 37 estandes com categoria ambígua | cliente |

**Disco:** saída de render vai para o **F:** (299 GB). O `E:` tem 107 GB e já
chegou a zero. **O `G:` mencionado na versão anterior deste arquivo não existe.**

**Máquina:** Xeon E5-2680 v4 (28 threads), RTX 4060 8 GB, 32 GB RAM.
Render é OptiX na GPU; ffmpeg é CPU e não briga — mas **cronometrar com a
máquina ocupada mede ruído**.
