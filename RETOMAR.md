# RETOMAR — handoff do render-agroshow

**AGROSHOW 2026 · Parque de Exposições de Dois Vizinhos, PR**
Reescrito em 15/08/2026, fim da **sexta** sessão.

> **Entrega desta sessão, e é por onde ele volta:**
> `data/materiais-quinta.json` (a paleta do parque, medida),
> `data/formas-quinta.json` (o que a câmera prova de forma) e
> `data/ferradura-conferida.json` (a bacia conferida contra foto de drone).
> A cena em disco **não mudou** — nenhuma geometria foi trocada ainda, e o
> motivo está em D023.

Abra este arquivo, depois **`DECISOES.md`**, depois `docs/FOOTPRINTS.md`, depois
`ESTADO.md`. Aqui está só o que a próxima sessão precisa para continuar sem
reler conversa.

---

## O QUE MUDOU NA SEXTA SESSÃO (15/08, à noite) — leia antes de tudo

Etapa 2 fechada, etapa 3 **medida mas não aplicada**, e a pendência 4 ganhou uma
segunda testemunha que não é a planta.

**68 quadros lineares** extraídos dos 17 vídeos, mais 90 densos nos que provam
forma (`1 (10)` com 24, `1 (2)` com 16, `1 (3)`, `1 (5)`, `1 (4)`, `1 (14)`,
`1 (15)`). Ferramenta nova: `scripts/preview_linear.py`, que faz a versão
olhável com **grade em pixel do quadro original** — sem ela eu chutaria caixa de
amostra, e chute em caixa é chute em cor.

### A paleta do parque está medida, e o método mudou por um motivo físico

`data/materiais-quinta.json`, gerado por `scripts/medir_materiais_quinta.py`:

| classe | albedo linear | hex |
|---|---|---|
| tijolo vermelho | 0,564 / 0,073 / 0,071 | `#c64c4b` |
| chapa azul (telhado) | 0,036 / 0,274 / 0,592 | `#358fca` |
| coluna azul | 0,018 / 0,060 / 0,165 | `#244571` |
| portão de chapa | 0,066 / 0,077 / 0,098 | `#494f58` |
| terra batida (interna) | 0,097 / 0,033 / 0,016 | `#583323` |
| brita / estrada | 0,261 / 0,189 / 0,162 | `#8c7870` |

**A âncora de 14/08 não serve aqui, e o número denunciou antes de mim.** Com a
telha declarada em 0,70 o tijolo saiu com albedo **1,000 no vermelho** — parede
refletindo mais vermelho que o branco reflete. A causa é orientação: em dia
encoberto o telhado vê o hemisfério de céu inteiro e a parede vê metade. O
conserto foi **usar o céu do próprio quadro como fotômetro** (`1 (17)__0006s`
tem o céu não estourado — 99,9% em 0,957). Doutrina inteira em D018.

**E ele passa em dois controles independentes**, contra a medição de 14/08 que
saiu de outro dia, outra luz e outro método: mata **0,96×**, terra **1,27×**. E
a estrada aqui dá 0,261/0,189/0,162 contra 0,266/0,188/0,155 da classe `terra`
de lá — dois caminhos que não se falam chegando no mesmo número.

### A ferradura da bacia, agora com testemunha direta

Em 14/08 ela foi deduzida do desenho, por ausência de talude e de estande num
setor. O `1 (2)` é **nadir de drone e mostra a boca**. Medindo o ângulo entre o
eixo dos pavilhões (azimute 108°, do desenho) e a boca, dentro da mesma imagem:
**rumo de mapa 164,8°** contra os **150,0°** do `data/bacia.json` — **14,8° de
desvio**, dentro de uma boca que tem 120° de largura. `conferir_ferradura.py`, e
D022, inclusive a parte de que a primeira versão publicou **0,2°** e o número
estava errado: eu tinha escrito 165 à mão dizendo que era o que o arquivo dizia,
e a convenção de azimute daquele arquivo não é a da bússola.

### O prédio redondo é polígono, e há duas estruturas chamadas "palco"

`data/formas-quinta.json`. O edifício-símbolo tem **~10 faces**, dois pavimentos
com o superior recuado, varanda com guarda-corpo de 1,10 m, telhado de quatro
águas de baixa inclinação, e um **anexo retangular** encostado que é outro
volume. **E o "palco" são dois objetos, não um** — errei isso primeiro e a correção está
em D024. O `1 (4)` mostra uma **concha permanente de alvenaria** que a cena não
tem; `estruturas.palco` é o **palco de evento** de novembro, com treliça e telão.
De quebra apareceu uma contradição que não é minha: `estimativas.json` chamava
`estruturas.palco` de *"palco fixo"*. Comentário corrigido, geometria intocada.

**Nada disso virou geometria ainda, de propósito** (D023): falta casar cada
prédio com a zona da planta, e `construir sobre footprint errado é pior que não
construir`.

### Trava nova, em código

`ESTOURO_MAXIMO = 0,5%` — amostra com mais que isso de pixel no teto é recusada
com o número impresso. Foi ela que pegou **três** caixas erradas nesta sessão, e
nenhuma delas dava erro na tela. Some-se a ela a regra que virou hábito: **o
`--debug` não é conveniência.** Três vezes nesta série eu li a imagem e o número
desmentiu, e nas três o que pegou foi desenhar a caixa no quadro e olhar.

---

## O QUE MUDOU NA QUINTA SESSÃO (15/08) — leia antes de tudo

Ele entregou três coisas novas e deu uma ordem de regime:

1. **17 vídeos de quinta-feira (13/08)** em
   `E:\Projetos todos\Mapa - agroshow\Brutos Expo\agroshow extrator somente\`
   — o parque **como está hoje**, vazio, em luz difusa, de perto. Ordem:
   *usar como cores e texturas; os locais que já estão lá não mudam; o que falta
   é completado pelo mapa (a planta).* Decupagem em `data/footage-quinta.json`.
2. **`reference/DOUTRINA-RENDER-3D.md`** — ordem norteadora do processo.
   Precedência: **ordem do Natan → doutrina → resto**.
3. **Regime autônomo**, palavras dele: *"Trabalhe de forma autônoma até o fim.
   Não me pergunte nada: quando houver ambiguidade, escolha a opção mais
   conservadora, registre a decisão e o motivo em DECISOES.md e siga."*
   → **`DECISOES.md` é obrigatório e é onde estão os 17 registros desta sessão.**

E ele decidiu duas coisas: **saída em EXR MultiLayer + Cryptomatte** (supera o
PNG-8 de 14/08) e **corrigir a forma de todos os prédios que têm footage**,
mantendo a posição.

### Três números deste arquivo estavam ERRADOS, e agora estão medidos

| | dizia antes | é |
|---|---|---|
| tempo por quadro | 36–38 s | **10,0 s** |
| filme inteiro | 46–49 h | **12,9 h** |
| disco | — | **176 GB** de 300 GB livres no F: |

**A causa do erro é o achado maior da sessão: o render vinha rodando na CPU.**
A cena guarda `cycles.device = "GPU"`, mas o dispositivo mora nas *preferências*,
que são da instalação e não do `.blend`. Aberto numa sessão limpa, o arquivo
anunciava GPU e o Cycles caía para a CPU **sem avisar** — é o fallback
silencioso da doutrina §12. Conserto em `scripts/placa.py`, e `render_shots.py`
agora **aborta** se não achar GPU (`--permitir-cpu` para forçar).

### O que passou a existir

| arquivo | o que faz |
|---|---|
| `DECISOES.md` | as 17 decisões desta sessão, com o motivo de cada uma |
| `data/saida.json` + `scripts/saida.py` | os **três slots** de saída e por que são três |
| `scripts/conferir_matte.py` | abre o EXR e **extrai um matte de verdade**. É o portão |
| `scripts/smoke_saida.py` | 1 quadro + medida real de disco |
| `scripts/placa.py` | liga a GPU. Chamar **sempre**, e no começo |
| `scripts/medir_render.py` + `medir_ruido.py` | o comparativo de amostragem |
| `scripts/medir_compressao.py` | custo em disco de cada arranjo, no mesmo quadro |
| `data/footage-quinta.json` | a decupagem dos 17, com datum e regra de desempate |
| `scripts/extrair_linear.py` | a **segunda** extração: linear 16 bits, para medir |

### A saída são TRÊS arquivos por quadro, e o motivo não é gosto

| slot | conteúdo | formato |
|---|---|---|
| `beauty/` | Combined + Emit + Env + AO | EXR MultiLayer, **Half, DWAA** |
| `data/` | CryptoObject + CryptoMaterial + Normal + Depth | EXR MultiLayer, **Full Float 32, ZIP** |
| `preview/` | a entrega | **PNG 8**, `%05d.png` — o `encode.sh` não mudou |

**Half + DWAA destrói o Cryptomatte.** O hash do nome do objeto é um float 32;
DWAA é *lossy* e altera o valor, e Half tem 10 bits de mantissa e não representa
o hash. Num pixel de cor, alterar um pouquinho é imperceptível; num pixel que
carrega um hash, é trocar o objeto por outro. **E o defeito não aparece no
render** — aparece no dia em que alguém for isolar um objeto no Resolve.

**`save_as_render` é a mesma chave invertida entre os slots:** ligada no PNG (que
precisa do AgX) e desligada nos EXR (que não podem tê-lo assado dentro).
Provado: o EXR tem **18,5% dos pixels acima de 1,0** (headroom linear intacto) e
o PNG tem máximo 0,922 com mediana 0,549 contra 0,705 do sRGB ingênuo.

**Cryptomatte conferido de verdade:** `Terreno` → hash `0x1ed9a684`, casado bit a
bit no arquivo; 99,69% dos pixels com objeto fecham cobertura em 1,0 com
**levels 2**. O matte extraído bate com o gramado do preview.

### A config de amostragem dele se sustenta, e agora está medida

Medido no P08 (o plano mais fechado, com luz indireta), as quatro combinações:

| config | tempo | ruído local |
|---|---|---|
| 128 / 0,1 **sem** denoise | 3,9 s | 0,00765 |
| **128 / 0,1 com denoise** | **2,9 s** | **0,00261** |
| max / 0,01 com denoise | 10,3 s | 0,00262 |

**0,01 custa +255% de tempo e entrega −0,4% de ruído.** Empatam — o OIDN já
resolveu. A doutrina pede 0,01 `[Certo]` e aqui não se aplica: a regra dela
existe contra *compensar samples baixos com denoise agressivo*, e 128 já
converge nesta cena. **Nada muda sem ele.**

---

## COMO A CENA ESTÁ AGORA — leia estes 12 números primeiro

```
8 pavilhoes .............. forma medida do desenho, area fechada na cota da planta
9 zonas medidas .......... footprint do desenho + altura declarada (BASE)
33 zonas estimadas ....... caixa por tipo declarada    (colecao ESTIMADO)
418 arvores .............. 6 bosques, 2 matas, alameda (1 malha instanciada)
189 arbustos ............. so onde o terreno TEM declive (os 15 taludes)
1681 figuras PROXY ....... censo tirado do audio do cliente -- NAO sao os finais
209 pecas de mobiliario .. mesa e cadeira CC0 de verdade, nas duas pracas
11 pecas na ESPERA ....... silo, tendas, porteira, curral, torre -- ele posiciona
16 letreiros ............. texto do audio dele; tamanho resolvido pela regra de 8%
4 estruturas ............. portal, palco, 2 camarotes
bacia .................... ferradura aberta 120 graus para SUL-SUDESTE (medida)
42 vias · 134 estandes · 22 planos de camera
luz .................... kloppenheim_06, 27/11 18:15, sol a 10,1 graus, 8 bits
materiais .............. cor-base MEDIDA no footage; terreno com mancha de 2 gramas
textura ................ PBR CC0 em 4 materiais (normal + rugosidade + mancha)
entorno ................ relevo REAL ate 12 km (SRTM) + cobertura ESA WorldCover
render ................. 2760x1380, Cycles 128 samples, OptiX
saida .................. beauty EXR + data EXR (crypto) + preview PNG
custo .................. 10,0 s/quadro -> 12,9 h o filme, 176 GB (6 planos medidos)
```

> **O custo acima foi remedido em 15/08 com a GPU de fato ligada.** A versao
> anterior deste arquivo dizia 36-38 s/quadro e 46-49 h: era **CPU**, sem
> ninguem saber. E a projecao de disco so vale amostrando varios planos --
> medida so no P01, que e o plano mais aberto e com metade do quadro em ceu,
> ela saiu **43% otimista**.

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
| `data/texturas.json` | contrato da textura: qual asset CC0 por material, em que escala real, com que força — e o que ficou de fora, com motivo | — |
| `data/texturas-medidas.json` | luminância média de cada Diffuse. É ela que normaliza a mancha e faz a cor medida sobreviver | — |
| `scripts/texturas.py` | `--medir` (venv) mede a média; `--conferir` prova a conta; `aplicar()` monta os nós dentro do Blender | venv **e** Blender |
| `scripts/provas_textura.py` | folha de provas com e sem textura, nos dois enquadramentos, e o custo por quadro | Blender |
| `scripts/relevo_entorno.py` | baixa o DEM público e grava o desnível do entorno; `carregar()`/`altura()` servem o gerador | venv (baixa) **e** Blender (lê) |
| `data/relevo-entorno.json` | procedência e estatística do DEM: fonte, licença, altitude do sítio, desnível, amortecimento | — |

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

## A textura entrou, e a regra dela é uma só

**Feito em 14/08, à noite. Contrato inteiro em `data/texturas.json`.**

**A cor-base é medida e a biblioteca não a sobrescreve.** O albedo de cada
classe saiu do footage do próprio recinto; um Diffuse do Poly Haven é a cor de
outro lugar, com outra luz. Então a textura entra por três portas, e albedo não
é uma delas: **normal** (relevo), **rugosidade** (e aqui ela dá a *variação*,
não o valor — um Map Range centra a faixa no valor declarado, senão a telha,
que é brilhante de propósito, viraria fosca junto com o resto) e **variação de
luminância normalizada** — o Diffuse dividido pela própria média, o que deixa a
mancha com média 1,0 e a cor final com **exatamente** a cor medida como média.
Isso não é retórica: `python scripts/texturas.py --conferir` imprime a conta.

O critério que escolheu cada asset não foi beleza, foi **o lado real**: o
terreno tem 808 m e uma grama de 2 m repete 404 vezes, o que do alto lê como
grade. A categoria `aerial` do Poly Haven tem 15 a 25 m de lado.

| material | asset | lado | o que entra |
|---|---|---|---|
| `MAT_TERRENO` | `aerial_grass_rock` | 15 m | só normal e rugosidade — a **cor já é medida** (duas gramas) |
| `MAT_ARENA` | `dirt_aerial_03` | 25 m | + mancha de luminância |
| `MAT_SAIBRO` | `gravel_road` | 2 m | + mancha (2 m é fatal no terreno e correto numa via de 6 m) |
| `MAT_TELHA` | `corrugated_iron_02` | 2,7 m | normal a **força 1,0**, a única do contrato |

A telha é a que mais paga: a onda não é cor, é relevo, e com o sol a 10° cada
onda joga a própria sombra. É o que faz o telhado ler como telhado de longe.

**Ficaram de fora, com motivo escrito:** `MAT_LONA` (o que se vê numa tenda de
longe é a barriga do pano entre os esticadores — isso é geometria, não mapa),
`MAT_COPA` (instâncias já variam de cor, e folha não aparece do sobrevoo) e
`MAT_MADEIRA` (o portal merece a textura da **foto do cliente**, não uma tábua
de biblioteca).

**O que a prova mostrou, e metade não foi o que eu esperava:**

- **Funciona de perto e não funciona de longe.** Na câmera a 6 m o chão deixou
  de ser pastel chapado; na de 48 m a diferença é quase nula.
- **Custo medido no master, mesmo plano com e sem:** 36,3 → **38,2 s/quadro**,
  **+5,2%**, +2,4 h no filme inteiro. Barato pelo que entrega de perto.
- **A calibração que ninguém tinha conferido.** A rampa das duas gramas dizia no
  comentário *"mais campo que desgaste"* e entregava **meio a meio**: albedo
  médio do recinto 0,192 contra os **0,129 medidos**, e p05 de 0,151 — em lugar
  nenhum o gramado chegava à cor do footage. Varrida a rampa e medida por render
  ortográfico de mundo branco, ficou em 0,50/0,85: **média 0,152, 15% de
  desgaste**. É a mesma falha do *"cara de deserto"*, em dose menor e por isso
  mais difícil de ver.

> **Diagnóstico meu que o número desmentiu, de novo.** Olhei o quadro alto, vi
> um anel bege em volta do recinto verde e escrevi que o `Entorno` estava com
> material trocado. Medi os dois separados, com o mesmo mundo branco: **albedo
> 0,152 contra 0,151** — são iguais. O anel é a **linha de sombra da mata**, com
> o sol a 10° projetando 5,6× a altura. Está fisicamente certo. Segunda vez
> nesta sessão que eu leio defeito num quadro e a medição diz que não há.

---

## ONDE PAREI NA QUINTA SESSÃO — é daqui que se continua

Os passos 0.1 a 0.4 e a etapa 1 do plano estão **fechados**. O que sobra, em
ordem, e cada um já tem a ferramenta pronta:

### Próximo passo: etapa 2 — medir os materiais do footage novo
`data/footage-quinta.json` diz qual vídeo serve para qual material. Falta rodar:

```bash
.venv/Scripts/python.exe scripts/extrair_linear.py --todos --por-video 4
```

e estender `medir_materiais.py` para os quadros **lineares**, com as classes que
o parque de verdade tem e que a cena ainda não tem: **tijolo vermelho, coluna
azul, estrutura de telhado vermelha, concreto, terra batida, brita** e a banda
branca do prédio redondo. O método não muda — âncora conhecida **no mesmo
quadro**, mediana, linear. Duas travas novas:

- **medir só em região grande e chapada.** O material é 4:2:0 e os dois
  materiais mais críticos são vermelho e azul saturados, o pior caso de croma;
- **textura tirada de foto precisa de de-lighting** antes de virar albedo —
  dividir pela versão muito borrada e renormalizar pela mediana medida. Foto tem
  luz e AO assados dentro, e usar direto dá sombra dupla ao relightar.

### Etapa 3 — as formas reais
**O prédio redondo de dois andares é o achado do footage: sete dos dezessete
vídeos são ele**, e o `1 (10)` é uma **órbita completa** — a melhor prova de
forma que este projeto já teve. Hoje ele é uma caixa na cena. Também têm forma
provada: o **palco** (branco sobre base azul, não madeira), o **galpão azul**, a
**galeria de pilares** e as **mangueiras** (grades em série sobre brita — e a
pendência 2c listava as mangueiras como estimativa fraca, porque a planta só
tinha o rótulo e `14,1 × 2,4 m` era o tamanho da **palavra**).

Regras que já estão escritas e não se negociam:
- **âncora da troca de forma = centroide do footprint.** Canto move tudo e a
  conferência de posição de 14/08 deixaria de valer sem ninguém perceber;
- reexecutar `conferir_posicao.py` + `sobrepor.py` **depois de cada troca**;
- **altura por datum declarado em quadro**, registrado por prédio;
- **re-ancorar os 16 letreiros** depois — fachada que muda de forma leva o
  letreiro junto, e a fração de 8% recalcula onde a distância mudou.

### E há uma etapa 3b que o footage abriu sozinho
Os vídeos **`1 (2)` e `1 (3)` são aéreos verticais de drone** e mostram a arena
com as **arquibancadas em arco** e o traçado real das vias. É a melhor fonte de
posição depois do satélite, **e é mais recente que ele**. Serve para fechar a
pendência 9 (as 42 vias com `conferido_pelo_natan: false`) e para conferir a
ferradura da bacia sem esperar o quadro lateral da pendência 3.

### Etapa 5 — o passe do "não fazer"
Nada feito ainda. A lista está no plano; a parte que a doutrina chama de erro
nº 1 é **aresta viva sem bevel**, e o gerador cria tudo sem chanfro. Cuidado
medido: com 1.681 proxies em 8 GB, **variação de instância tem que ser no
transform** (Geometry Nodes: Random Value → Rotate/Scale Instances), nunca
duplicando malha.

Cuidado que já se vê no quadro do smoke: há **retângulos cinza chapados
deitados no gramado** (as zonas ESTIMADO planas) e nomes com sufixo `.001`
(`Bar.001`, `Cadeira.024`) — a doutrina §2.11 avisa que **Cryptomatte usa esses
nomes**, e agora que o crypto existe de verdade isso deixou de ser teoria.

---

## A ÁREA DE ESPERA

**Ordem dele, 15/08, literal:** *"faça o silo ao lado do mapa que eu
reposiciono no blender depois, quero que crie todos as tendas e estruturas e
posicione no lugar que já sabe mas o que não sabe quero que deixe do lado"*.

**Onde:** coleção `AREA_DE_ESPERA`, canto em **(520, −240)** — fora do terreno
detalhado, fora do recinto e fora dos 22 planos, mas em chão existente do
entorno. Cada peça leva uma **etiqueta de texto flutuante** ao lado, para ele
não ter que clicar objeto por objeto no outliner.

**As 11 peças:** Silo · Conjunto de 3 silos (já com objeto pai, arrasta junto) ·
Tenda piramidal 10×10 · Tenda piramidal 5×5 · Tenda galpão · Porteira da
Fazendinha · Guichê · Curral de manejo · Torre de iluminação · Brinquedo
inflável · Trator.

Contrato em `data/pecas-avulsas.json`, gerador em `scripts/avulsas.py`, com a
medida e o fundamento de cada uma. Quatro nascem de pedido literal dele: a
porteira `[03:18]`, o guichê `[01:04]`, o inflável `[03:31]` e o silo, que tem
**prova em imagem** no quadro `DJI_20251129182345_0168_D` 00:00:52.

### Por que nada disso veio de biblioteca — e isto muda o próximo passo

Ele mandou o `free3d.com/pt/3d-models/arquitetura` e depois o TurboSquid, e
ofereceu criar conta. O que foi conferido, site por site:

| fonte | o que barrou |
|---|---|
| **free3d** | os dois silos gratuitos são **"Licença de Uso Pessoal"** — e isto é entrega de CLIENTE. **Conta não resolve**: o problema é a licença. Além disso são modelos de impressão 3D, sem textura e fora de escala agrícola |
| **TurboSquid** | exige **conta** até no gratuito. Mas o gratuito de lá é **Royalty Free e SERVE** |
| **Poly Haven** | 521 modelos, nenhum silo, nenhuma tenda de evento — é biblioteca de props de interior |

A categoria "Arquitetura" do free3d tem **26 modelos grátis** e nenhum serve:
são Notre Dame, martelos de guerra e robôs.

**Então:** silo, tenda e porteira são geometria de revolução e caixa — saem mais
rápido feitas do que negociadas, na escala certa e já com os materiais MEDIDOS
da cena. O que **não** vale fazer à mão está nomeado abaixo.

> **A oferta dele continua de pé e é o caminho da 14d:** *"se precisa eu posso
> criar a conta onde tiver o modelo que precisar"*. Vale para o **TurboSquid**.
> Ele cria e **entra no Chrome**; eu baixo pela sessão aberta — **não digito
> senha**. O que buscar lá é o que não sai bem à mão: **colheitadeira,
> implementos agrícolas e caminhão**.

---

## Os letreiros entraram, e o tamanho deles é conta, não gosto

**Feito em 15/08. 16 letreiros, 29 objetos de texto.** Contrato em
`data/letreiros.json`, gerador em `scripts/letreiros.py`.

**O texto é a sua palavra.** Cada linha carrega o minuto: *"É daqui que sai o
alimento que sustenta o mundo"* (ÁUDIO 3 `[00:36]`, que você repetiu duas vezes
seguidas), *"Aqui será um grande balcão de negócios"* (ÁUDIO 2 `[02:04]`), e os
títulos ditados de `[00:03]` a `[01:08]`. As duas frases são literais, como o
`ESTADO.md` manda.

**O tamanho deixou de ser gosto.** A sua regra de entrega diz *"título com no
mínimo 8% da altura do quadro; apoio nunca abaixo de 4%"*. Isso tem solução
exata:

    fração = altura_m × lente_mm / (distância_m × 18)      (18 mm = sensor vertical em 2:1)
    logo    altura_m = fração × distância × 18 / lente

E `data/planos.json` já declara alvo, lente e distância dos 22 planos. Então
**cada letreiro é dimensionado pelo plano que o mostra**, pela **maior** das
duas distâncias — porque "no mínimo 8%" tem de valer o plano inteiro, e o texto
é menor na tela quando a câmera está mais longe. O script imprime a fração
obtida de cada um e **acusa** quem cair abaixo. Hoje: 16 de 16 dentro.

**As suas restrições duras, cumpridas e escritas:** a palavra **"Kids" não
entra** (`[00:55]`, *"Kids é muito americanizado"*) — o letreiro é
**Fazendinha**, nome grande com a descrição pequena embaixo, na hierarquia que
você ditou em `[00:42]`. Os **quatro diferenciais** — Fazendinha, Rodeio, Café
Colonial e Mercado do Produtor — ganham 1,35× o título, porque você os nomeou
um a um de `[01:29]` a `[01:38]`.

**Três defeitos que só a prova em quadro pegou:**

1. **Os 16 letreiros existiam o filme inteiro** e apareciam flutuando ao fundo
   dos outros planos. Agora cada um só existe durante o plano dele, com meio
   segundo de respiro em cada ponta — ligar no quadro exato do corte faz o texto
   piscar junto com a troca de câmera, e isso lê como falha de render.
2. **O letreiro da Fazendinha saía metade tapado por uma árvore.** Ele estava
   plantado no rótulo, atrás do bosque que o próprio plano atravessa. Agora vem
   45% do caminho na direção da câmera — e o tamanho é **recalculado pela
   distância nova**, senão aproximar deixaria todo letreiro acima da regra.
3. **Tentei resolver isso subindo o texto para 17 m** "para passar da copa", e
   ele saiu **fora do quadro**: a câmera olha para a mira do plano, e texto
   muito acima dela não está no enquadramento. Quem resolve oclusão é a
   aproximação, não a altura.

**Tipografia é proposta, não decisão** (pendência 15b). Archivo Narrow Bold, por
dois motivos: condensada cabe mais texto nos mesmos 8%, e é **OFL** — uso
comercial liberado, o que importa porque isto é entrega de cliente e há fontes
na sua pasta marcadas *personal use only*. Não repropus a Barlow Condensed, que
você já reprovou em outro projeto.

---

## As mesas e cadeiras entraram, e são CC0 de verdade

**Feito em 14/08, à noite. 209 peças.** Contrato em `data/mobiliario.json`,
posicionador em `scripts/mobiliario.py`.

Pedido literal seu: *"mesas, cadeiras, o pessoal com os guichês lá"* `[00:57]`.
Era **o caminho mais barato do projeto e estava parado.**

| peça | o quê | onde |
|---|---|---|
| `plastic_monobloc_chair_01` | a cadeira branca de plástico monobloco | praça coberta e Café Colonial |
| `wooden_picnic_table` | mesa de piquenique com banco junto | praça aberta, sob o bosque |
| `wooden_table_02` | mesa de 1,13 × 0,71 m, quatro lugares | praça coberta e Café Colonial |

A cadeira monobloco não é escolha estética: é **a** cadeira de evento no Brasil,
e é reconhecível de longe pela silhueta e pelo branco. O Café Colonial entrou
porque é um dos **quatro diferenciais** que você manda dar mais tela — se ganha
plano próprio, não pode aparecer como galpão vazio.

**A diferença que importa, e ela ficou visível num quadro só:** aqui o modelo
CC0 **existe e serve** — vem com textura, na escala certa, e lê como móvel de
verdade. Gente e gado não têm equivalente, e no mesmo quadro os proxies ao lado
das mesas leem como balizador. É a melhor ilustração da pendência 14b que eu
poderia ter feito de propósito, e ela apareceu sozinha.

**Cuidado que custou 117 peças, em silêncio:** o teste que impede móvel dentro
de prédio estava rejeitando as cadeiras que estão **dentro da própria praça
coberta** — que é um sólido construído. Móvel de praça coberta fica dentro da
praça coberta. Agora o teste ignora o prédio da própria zona e vale só para os
alheios. Foram 99 peças na primeira rodada e 209 na segunda.

---

## O recinto deixou de estar vazio — mas as figuras são proxy, e isso é o ponto

**Feito em 14/08, à noite. 1.681 figuras, 8 malhas compartilhadas.**
Censo em `data/povoamento.json`, povoador em `scripts/povoamento.py`.

**O censo saiu do seu áudio**, que o `ESTADO.md` já declarava ser *"a régua do
que vai dentro de cada ambiente"*. Cada linha carrega o minuto citado: o touro
pulando na arena `[04:14]`, a área de shows *"toda ela lotada de público"*
`[04:33]`, o gado de leite no primeiro pavilhão `[02:28]`, o Hereford de
**corpo vermelho e cara branca** no segundo `[02:40]` — que é por isso que o
quadrúpede tem dois slots de material —, o nelore branco no terceiro `[02:47]`,
os Border Collie com as ovelhas na Fazendinha `[03:37]`, o leilão
**acontecendo** `[02:18]`.

Cada figura sai carimbada com o áudio que a pediu e o fundamento da quantidade.
**Quem está e onde é palavra sua; quantos é declarado por mim.**

### O elefante na sala, dito na cara

**Não existe figura humana nem animal em CC0 que sirva direto.** O Poly Haven
tem 521 modelos e nenhum é ser vivo — é biblioteca de props. Kenney e Quaternius
têm, em CC0 de verdade, mas em estilo de jogo estilizado.

E a prova em quadro é dura: **a 130 m de câmera o proxy lê como público; a 6 m
lê como balizador de estacionamento.** As duas imagens estão em
`out/povoamento/`, com e sem.

**Isso não se resolve escolhendo melhor: depende do Plano A vs Plano B, que é
decisão sua.** No Plano A os quadros viram entrada de IA geradora — e ali proxy
é exatamente o certo, porque o que a IA precisa é massa, silhueta, escala e
composição. No Plano B o render local é a entrega, e aí gente e gado precisam de
modelo e animação de verdade.

O proxy serve aos dois: no A é o produto da etapa; no B é o layout que os
modelos reais substituem um a um, **sem refazer o censo**. Fica na coleção
`POVOAMENTO`, que se esconde num clique igual à `ESTIMADO`.

**Custo:** +8% no quadro que mostra a multidão (19,4 s contra 17,9 s).

**O que o áudio pede e ainda não está lá,** com o motivo: os `PEQUENOS ANIMAIS`
do pavilhão 5 (o áudio não diz quais, e eu não invento seis espécies), os
brinquedos infláveis da Fazendinha (é modelagem, não povoamento), as máquinas e
implementos do anel — e **as mesas e cadeiras da praça, que o Poly Haven tem em
CC0 e é o caminho mais barato que existe.**

---

## Os taludes ganharam arbusto, e quem escolheu o lugar foi o gradiente

**Feito em 14/08, à noite. 189 arbustos.** O contrato de `data/vegetacao.json`
já reservava isto: *"arbusto de talude entra na Rodada de textura, não aqui"*.

O que faz isso ser medida e não enfeite é uma linha: **o arbusto só nasce onde
o terreno tem declive de verdade** (gradiente ≥ 0,08 m/m, medido na própria
`terreno.elevacao`). O rótulo `Talude` dá a *região* — ele fica onde coube no
desenho, nem sempre em cima da rampa. O gradiente dá o *lugar*.

Conferido no `.blend` construído, e o resultado é limpo:

| faixa de raio | banda do `PATAMARES` | arbustos |
|---|---|---|
| 45–62 m | **talude 0 → 3,5 m** | 66 |
| 62–78 m | shows (plano) | **0** |
| 78–95 m | **talude 3,5 → 7 m** | 57 |
| 95–125 m | anel (plano) | **0** |
| 125–150 m | **talude 7 → 10 m** | 66 |
| > 150 m | platão (plano) | **0** |

Zero em chão com declive abaixo do limite, e **zero no setor aberto** — que
ficou plano depois da correção da ferradura e portanto não leva contenção. Os
1.251 recusados são isso: pontos sorteados que caíram no plano.

Reusa `MAT_COPA`, que é **cor medida** no footage, com variação por instância.
Arbusto de talude não tem amostra própria no acervo, e inventar um verde novo
seria decisão estética sem dado.

**Cuidado que quase entrou:** ao acrescentar `"Talude": "talude"` no
`por_rotulo`, o laço das árvores passou a enxergar o rótulo e plantaria
**árvore de 12 m** no talude. Uma linha de `continue` resolve, e ela está
comentada no código com o motivo.

---

## A bacia deixou de ser cilindro — e o rumo que estava escrito aqui era outro

**Feito em 14/08, à noite.** Contrato em `data/bacia.json`, prova em
`docs/conferencia-bacia-ferradura.png`.

Este arquivo dizia *"a bacia é ferradura aberta para nordeste"*, sem número
atrás. **Nordeste é azimute ~45°, e é onde estão QUATRO dos 15 taludes**
(34,2 / 38,1 / 38,1 / 39,0) — o lado mais arrimado que existe. A abertura
aponta para o outro quadrante.

**Duas testemunhas independentes da planta, e elas concordam sem se falarem:**

| setor (0°=leste, 90°=norte) | os 15 `Talude` | os 93 estandes série C |
|---|---|---|
| 30° – 240° | 15 | 91 |
| **240° – 360°** | **0** | **0** |

O arrimo envolve ~210° de arco e a bacia fica **aberta em ~120°**, para
sul-sudeste. Dentro da abertura estão o `PALCO` (az 303°, r 21–26 m), os
sanitários, a `ÁREA RESTRITA` e o bosque. Palco no chão da pista olhando para a
arena é o esperado num rodeio, e o acesso de animal e de veículo também precisa
chegar em nível — é por ali que chega.

**A mudança só alcança o que a medição alcança.** Os taludes medidos vão de
27,8 a 137,1 m, então em **r = 150 m os dois perfis se reencontram na mesma
cota** e o platão continua em 10 m em todos os rumos. Abrir a cunha até a borda
da prancha rebaixaria em 10 m a `ÁREA RESTRITA` (179 m), o bosque e a mata sem
uma única medida pedindo isso — seria trocar um erro simétrico por um maior e
assimétrico.

Quatro testes, e passam: fora de 150 m a diferença é **0,000000 m**; no setor
arrimado a diferença é **0,000000 m**; no centro da abertura a pista se estende
de 45 para 78 m; e o maior degrau entre azimutes vizinhos é **4 cm** — um corte
reto daria 3,5 m.

**O que isto NÃO resolve:** as alturas (3,5 / 7 / 10 m) seguem estimadas por
proporção. O que a planta confirmou foi **onde há arrimo e onde não há**. A
pendência 3 com o cliente — um quadro de drone lateral — continua sendo o que
trava as cotas.

---

## O horizonte ganhou perfil

**Feito em 14/08, à noite.** Era a pendência 11, e ela estava travada por rede,
não por dificuldade: o `ESTADO.md` registrava que o proxy da sessão remota
bloqueia o `portal.opentopography.org`. Na sua máquina não bloqueia nada.

**A fonte é AWS Terrain Tiles** — SRTM, domínio público, **sem chave e sem
cadastro**. Foi escolhida contra as outras duas por isso: o OpenTopography
exige criar conta e chave de API, e conta eu não crio; o TOPODATA/INPE é livre
e ótimo, mas entrega zip por folha de 1 grau para o mesmo resultado a 30 m.

O sítio está a **602 m** e a região cai a **−435 m** dentro de 12 km — o
terreno despenca para o norte (412 m a 8 km). É isso que dá cumeada ao
horizonte no lugar da linha de régua.

**Conferido contra fonte independente** (opentopodata, SRTM 30 m), em 5 pontos
ao longo de 16 km: **±5 m**, o pior deles.

Duas travas escritas no código, e as duas existem por motivo já medido:

- **O DEM não encosta no recinto.** Dentro de 600 m o desnível é zerado, com
  rampa suave até 1500 m. 30 m de resolução dão ~27 pixels no recinto inteiro e
  os taludes somem — isso já estava no `ESTADO.md`. A bacia continua vindo da
  planta, que é mais precisa.
- **O disco vai até onde o DEM vai, e nem um metro além.** Fora dele o desnível
  seria zero e voltaria a reta que se está consertando.

Sem o DEM baixado o gerador **cai no disco chapado de antes e avisa** — a cena
continua saindo, com a limitação antiga dita em voz alta.

### E a cobertura do solo veio junto, na mesma noite (era a 11b)

**ESA WorldCover 10 m, 2021 v200** — CC-BY 4.0, S3 público, sem chave. E a
resolução é **três vezes melhor que a do DEM**, então o desenho do talhão
aparece, que é justamente o que dá leitura de lavoura à distância.

**Não baixou os 103 MB do azulejo.** O GeoTIFF é em blocos e o S3 aceita
`Range`, então um objeto tipo-arquivo por HTTP trouxe só a janela: **6
requisições, 3,1 MB**.

**O par de fontes é o que faz isto valer.** O WorldCover diz *o que* é cada
pedaço de chão; `data/materiais-medidos.json` diz *que cor aquilo tem naquela
luz*. **Cinco das sete classes saem com cor medida no seu próprio footage.**

E há um achado dentro disso: a amostra **`campo`** foi medida em 14/08 apenas
como **controle do método** — *"qualquer um olha e diz que é verde; se a
inversão devolver isto oliva, quem está errado é a inversão"* — e estava
carimbada `"NAO entra em material nenhum"`. Ela é a **lavoura ao fundo do
quadro**, e é exatamente a classe 40 do WorldCover. Deixou de ser só controle.

| classe | fração | cor de onde |
|---|---|---|
| lavoura | 44,6% | **medida** — a amostra `campo` |
| mata | 37,6% | **medida** — a copa |
| campo | 14,4% | **medida** — a grama sã |
| cidade | 2,1% | declarada |
| água | 1,1% | declarada |

No PNG dá para reconhecer o **Rio Chopim** serpenteando, a **mancha urbana de
Dois Vizinhos** e os **corredores de mata** acompanhando a drenagem.

Mesmo amortecimento do DEM: dentro de 600 m é a grama medida, e a cobertura
real entra inteira só a partir de 1400 m — senão o WorldCover encostaria mata
na divisa do recinto e apareceria uma emenda reta, que é o que se está
consertando.

**No render fica discreto**, e isso é correto: com o sol a 10° o golden hour
converge tudo para o quente. Saturar para "aparecer" seria inventar.

**O que ainda falta (pendência 11c):** os **silos** do quadro
`DJI_20251129182345_0168_D` 00:00:52 são geometria, não cobertura; e o
**socalco** é relevo de ~10 m que um DEM de 30 m não enxerga.

> **CC-BY exige crédito**, e ele está no `assets/MANIFESTO.md`:
> *ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data.*
> Essa linha não pode sumir da entrega.

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

**Os da quinta sessão, na ordem em que se usam:**

```bash
"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background out/cena.blend --python scripts/smoke_saida.py -- --saida out/smoke --quadro 1 --escala 100
```

```bash
.venv/Scripts/python.exe scripts/conferir_matte.py out/smoke/data/00001.exr --objeto Terreno --png out/smoke/matte.png
```

```bash
"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background out/cena.blend --python scripts/medir_render.py -- --plano P08 --escala 50
```

```bash
.venv/Scripts/python.exe scripts/medir_ruido.py out/medicao
```

```bash
"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background out/cena.blend --python scripts/medir_compressao.py -- --plano P11
```

```bash
.venv/Scripts/python.exe scripts/extrair_linear.py --listar
```

```bash
.venv/Scripts/python.exe scripts/extrair_linear.py --todos --por-video 4
```

**O render de verdade — os três slots, GPU exigida, retomável:**

```bash
"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background --python scripts/render_shots.py -- --blend out/cena.blend --saida F:/agroshow/render
```

**Os de antes:**

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

```bash
.venv/Scripts/python.exe scripts/assets.py --texturas
```

```bash
.venv/Scripts/python.exe scripts/relevo_entorno.py
```

```bash
.venv/Scripts/python.exe scripts/texturas.py --medir
```

```bash
.venv/Scripts/python.exe scripts/texturas.py --conferir
```

```bash
"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background out/cena.blend --python scripts/provas_textura.py
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
20. **`nor_gl`, nunca `nor_dx`** — o Blender lê normal em convenção OpenGL. O
    DirectX inverte o eixo verde e o relevo sai com a luz vindo do lado errado.
    Não dá erro: só fica estranho, e com o sol a 10° fica estranho de propósito.
21. **Medir albedo sem `film_transparent` mede o céu junto** — a primeira
    medição da cor do gramado deu média 0,449 e p95 de 1,000. Era o céu branco
    entrando na conta pelas bordas do enquadramento ortográfico.
22. **Comentário que afirma o que o valor não entrega** — `# mais campo que
    desgaste` sobre uma rampa que dava meio a meio. Passou por três sessões.
    Número em comentário não é número medido; se dá para medir, mede.

### As da quinta sessão (15/08)

23. **A GPU não mora no `.blend`.** `cycles.device = "GPU"` é da cena; o
    **dispositivo** é das preferências, que são da instalação. Aberto numa
    sessão nova o arquivo anuncia GPU e o Cycles renderiza na **CPU**, sem uma
    linha de aviso. Foi assim por sessões, e é por isso que o custo declarado
    era 4× o real. Chame `placa.ligar()` **depois de abrir o .blend, sempre**.
24. **Half + DWAA destrói o Cryptomatte, e não dá erro.** O hash é float 32;
    DWAA é lossy e Half não representa o valor. O arquivo sai, os canais
    existem, e o matte é lixo. Slot de dado é **Full Float 32 + lossless**, e a
    prova é extrair um matte de verdade, não olhar a lista de canais.
25. **`save_as_render` é a mesma chave invertida entre slots** — ligada, o PNG
    sai com AgX (certo); ligada, o EXR sai com AgX assado (irrecuperável).
    Desligada, o EXR fica linear (certo) e o PNG sai lavado.
26. **Projeção de disco de um quadro só mente.** Medida no P01 deu 199 GB; a
    média de seis planos deu 285 GB. O P01 tem metade do quadro em céu, e céu
    comprime quase de graça. **Sempre amostrar vários planos.**
27. **`import gpu` devolve o módulo do Blender.** Ele já está em `sys.modules`
    antes do script rodar, e `scripts/` na frente do `sys.path` não adianta. O
    sintoma é `AttributeError` numa função que existe. Por isso o arquivo se
    chama `placa.py`.
28. **O Blender resolve caminho relativo contra a raiz do DRIVE**, não contra o
    cwd. `--saida out/provafinal` gravou em `C:\out\provafinal` — longe do
    projeto e longe do F:, que é o disco com espaço. Resolver para absoluto
    antes de entregar ao File Output.
29. **No Blender 5.x o compositor é outro.** `scene.compositing_node_group` (era
    `scene.node_tree`); `file_output_items` (era `layer_slots`/`file_slots`);
    `format.media_type` **filtra** o enum de `file_format` e tem que vir antes;
    e os sockets de passe são nome por extenso (`Diffuse Direct`, não
    `DiffDir`). Ligar um socket que não existe entrega **slot preto sem erro**.
30. **`write_still=True` com File Output grava um quadro a mais.** Os File
    Output gravam durante a composição; o `write_still` somava um PNG de 5 MB
    por quadro que ninguém usa — **23 GB no filme**.
31. **Nem todo material do AgroShow é HDR.** Os `IMG_91xx` antigos são HLG
    bt2020 e exigiram tonemap; **os 17 de 13/08 são bt709 SDR**. Aplicar a
    cadeia de HLG neles destruiria a cor em silêncio. `ffprobe` **antes** de
    medir, sempre — e montar a cadeia a partir do que o arquivo diz que é.
32. **Medir em JPEG sRGB dá número errado que passa no teste.** O método divide
    a amostra pela âncora, e divisão só vale em linear. Em sRGB a conta roda,
    devolve número consistente, e o `--conferir` não acusa nada. Por isso a
    extração de medição é **separada** da de triagem, e linear de 16 bits.
33. **Pixel de céu tem cobertura zero no Cryptomatte, e isso é o certo.** A
    primeira versão do conferidor exigia cobertura ~1 em todo pixel e reprovou
    um arquivo bom porque metade do quadro é céu. O que acusa defeito é a
    terceira faixa: pixel que **tem** objeto e não fecha.

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
| ~~4~~ | ~~A bacia é ferradura aberta para nordeste; o código faz cilindro fechado~~ — **feito em 14/08 à noite, e o rumo estava errado: a abertura é para SUL-SUDESTE.** Medido por duas testemunhas independentes da planta que concordam: no setor de 240° a 360° não há **nenhum** dos 15 `Talude` e **nenhum** dos 93 estandes da série C. Contrato em `data/bacia.json`, prova em `docs/conferencia-bacia-ferradura.png` | Resolvida |
| ~~5~~ | ~~Religar a luz depois que a posição fechar~~ — **feito em 14/08**, por ordem dele (*"pode fazer a luz"*). As 4 provas em `out/luz/` foram refeitas **sobre a cena nova**, com as 9 zonas medidas e as 33 estimadas dentro | Resolvida |
| ~~2c~~ | ~~Trocar as estimativas mais fracas quando ele mandar print~~ — **as MANGUEIRAS não precisam mais de print: o vídeo `1 (14)` as mostra inteiras**, grades em série sobre brita, com cobertura. Sai por medição em quadro, não por estimativa. Os 8 estacionamentos continuam com ele | **Natan** (só os estacionamentos) |
| ~~6~~ | ~~8 ou 16 bits no master~~ — **superado em 15/08 pela decisão dele de EXR + Cryptomatte.** A cadeia agora é: beauty EXR Half/DWAA (linear, para grading) + data EXR Float32/ZIP (crypto, normal, depth) + **preview PNG 8**, que é o que o `encode.sh` lê e o que vai para o telão P2,9. Os 8 bits que ele decidiu continuam valendo **para a entrega**; o que mudou é que agora existe um master linear atrás dela. 176 GB no F: | Resolvida |
| ~~6b~~ | ~~8 ou 16 bits no master (versão de 14/08)~~ — **decidido em 14/08, com ele delegando: fica 8.** O painel P2,9 é 8 bits, a entrega é ProRes e H.264, e o dither só age na conversão para 8 (a 16 fica inerte, e é ele que segura o banding no céu de fim de tarde). ~15 GB contra ~30 GB | Resolvida |
| 7 | Qual HDRI — **proposta trocada para `kloppenheim_06` por medição**: o sítio pede o sol a 10,1° e o sol dentro dele está a 8,0 (erro de 2,1°) contra 2,1 do belfast (erro de 8,0°). Um campo em `luz.json`, reversível. Provas novas em `out/luz/` | Natan |
| ~~11~~ | ~~O horizonte é uma linha reta~~ — **a silhueta foi resolvida em 14/08 à noite.** `scripts/relevo_entorno.py` baixa o DEM público (AWS Terrain Tiles/SRTM, **sem chave e sem cadastro**) e o entorno passou de disco chapado de 3 km a terreno real de 12 km de raio. O sítio está a 602 m e a região cai até −435 m: o horizonte ganhou cumeada e ondulação. Conferido contra o opentopodata em 5 pontos ao longo de 16 km, **±5 m**. Custo: nenhum mensurável | Resolvida |
| ~~11b~~ | ~~Falta a cobertura do solo do entorno~~ — **feito em 14/08 à noite.** ESA WorldCover 10 m (CC-BY, sem chave) diz **o que** é cada pedaço de chão; `materiais-medidos.json` diz **que cor** aquilo tem. Censo: 45% lavoura, 38% mata, 14% campo, 2% cidade, 1% água — e **5 das 7 classes com cor medida no footage dele**. Só 3,1 MB baixados de um azulejo de 103 MB, por *range request* | Resolvida |
| 11c | **O silo está feito, a posição não.** Silo e conjunto de 3 construídos em 15/08 e postos na `AREA_DE_ESPERA`, por ordem dele. A posição está no quadro `DJI_20251129182345_0168_D` 00:00:52 e **não foi medida** — dá para tirar dali, é trabalho de verdade | **Natan** posiciona, ou medir no quadro |
| 11d | **O socalco da lavoura** continua faltando: relevo de ~10 m que um DEM de 30 m não enxerga | próxima sessão |
| ~~12~~ | ~~Falta textura~~ — **feito em 14/08 à noite.** 4 materiais com normal, rugosidade e mancha CC0, contrato em `data/texturas.json`, custo medido de +5,2%. Lona, copa e madeira ficaram de fora **com motivo escrito**. A rampa das duas gramas foi calibrada de quebra (0,192 → 0,152 de albedo) | Resolvida |
| 12b | **A barriga do pano das tendas** é geometria, não textura — a lona ficou de fora do contrato por isso, e continua lendo como plano rígido de perto | próxima sessão |
| ~~13~~ | ~~Vegetação: falta o arbusto dos 15 taludes~~ — **feito em 14/08 à noite: 189 arbustos.** O que faz isso ser medida e não enfeite é o **filtro de declive**: o rótulo dá a região, o gradiente do terreno dá o lugar. Conferido — caíram **só** nas três faixas de talude do `PATAMARES`, zero nos platôs, zero no setor aberto | Resolvida |
| 14 | **Povoamento** — **o censo está feito e 1.681 figuras estão na cena, mas são PROXY.** `data/povoamento.json` tira do áudio dele, minuto a minuto, quem está em cada ambiente e quantos. A forma é que não existe: não há gente nem gado em CC0 que sirva (o Poly Haven tem 521 modelos e nenhum é ser vivo). **A 130 m lê como público; a 6 m lê como balizador.** | **Natan** — ver 14b |
| 14b | **A pergunta que destrava a 14: Plano A ou Plano B?** No **Plano A** (quadros → IA geradora com prompt ultra-realista) o proxy é o certo e a etapa está pronta: ele dá massa, silhueta, escala e composição, e a IA põe a pele. No **Plano B** (render local é a entrega) gente e gado precisam de modelo e animação de verdade — outro tamanho de trabalho, e vale a pena eu pesquisar Quaternius/Kenney com o seu aval | **Natan** |
| ~~14c~~ | ~~Mesas e cadeiras da praça~~ — **feito em 14/08 à noite: 209 peças CC0 de verdade**, não proxy. Cadeira de plástico monobloco branca (a cadeira de evento no Brasil), mesa de piquenique na praça aberta e mesa de 4 lugares na coberta e no Café Colonial. Contrato em `data/mobiliario.json` | Resolvida |
| 14d | **Máquinas e implementos** — o **trator existe como PROXY GROSSEIRO** na espera, declarado como tal. Falta **colheitadeira, implemento e caminhão**, e esses NÃO valem proxy: mal feitos chamam mais atenção que a ausência. **Caminho destravado:** ele cria conta no TurboSquid (gratuito = Royalty Free), entra no Chrome, eu baixo pela sessão | **Natan** cria a conta |
| ~~15~~ | ~~Títulos e letreiros~~ — **feito em 15/08. 16 letreiros, 29 objetos de texto.** O TEXTO é a sua palavra, com o minuto citado em cada linha. O TAMANHO é conta, não gosto: a sua regra de 8% da altura do quadro tem solução exata, e o script **acusa** quem cair abaixo. "Kids" não entra; os quatro diferenciais ganham 1,35× | Resolvida |
| 15b | **A tipografia é proposta, não decisão.** Archivo Narrow Bold, escolhida por ser condensada (cabe mais texto nos mesmos 8%) e **OFL** — há fontes na sua pasta marcadas *personal use only* e elas estão fora de entrega de cliente. Trocar é uma linha em `data/letreiros.json` | **Natan** |
| 15c | **O logo AGROSHOW 2026 ainda não existe em arquivo.** Os letreiros usam o **nome simples**, que foi o caminho que você autorizou | **Natan** |
| 8 | Alturas dos patamares (0 → 3,5 → 7 → 10 m) seguem estimadas. **Os aéreos `1 (2)` e `1 (3)` mostram as arquibancadas em arco de cima** — dão a forma, não a cota; a cota continua precisando do quadro lateral | cliente |
| 9 | Traçado das vias: 42 lidas do bitmap, `conferido_pelo_natan: false`. **16 quadros nadir do `1 (2)` extraídos em 15/08 e o traçado aparece inteiro.** Falta sobrepor contra `data/vias.json` — é trabalho de medir, não de descobrir | próxima sessão |
| ~~4b~~ | ~~A ferradura veio só da planta~~ — **conferida em 15/08 contra o aéreo nadir `1 (2)__0076s`, por caminho que não usa a planta**: ângulo entre o eixo dos pavilhões e a boca, medido dentro da imagem. Azimute **164,8°** contra os 165,0° do `data/bacia.json`. Ambiguidade de 180° declarada e desempatada pela planta. Ver D022 | Resolvida |
| 20 | **A CONCHA permanente do `1 (4)` não existe na cena** — base azul, paredes claras, cobertura inclinada, num gramado ao lado de pista de terra. Ela é um *local que já está lá*, e não existir é diferente de mudar. **Não é o palco da cena:** `estruturas.palco` é o palco DE EVENTO, de novembro. Ver D024 | próxima sessão |
| 21 | **O prédio redondo é polígono de ~10 faces**, medido no `1 (10)` e no `1 (6)`, e na cena é caixa. Não virou geometria porque falta casar qual zona da planta é ele. Ver `data/formas-quinta.json` e D023 | próxima sessão |
| 22 | **Concreto, grade e piso de curral saíram só com a COR**, sem nível: nas mangueiras não há céu medível nem superfície de albedo conhecido. Uma palavra dele sobre o albedo daquela coluna de concreto (0,20–0,30 de mercado) fecha o quadro inteiro | **Natan**, se quiser |
| 23 | **A estrutura de telhado vermelha não tem medida**: só existe em terça e rufo, peças de 20–40 px, e croma 4:2:0 de peça fina é mistura inventada pelo decodificador | próxima sessão, com quadro mais fechado |
| 10 | 37 estandes com categoria ambígua | cliente |
| ~~16~~ | ~~Saída de render~~ — **fechado em 15/08.** Três slots provados, Cryptomatte extraído com hash casado bit a bit, `save_as_render` conferido nos dois sentidos, 176 GB medidos em seis planos. Ver `DECISOES.md` D004–D014 | Resolvida |
| ~~17~~ | ~~Amostragem: 128/0,1 ou 0,01/max~~ — **medido em 15/08: empatam.** 0,01 custa +255% de tempo e entrega −0,4% de ruído. A config que ele ditou se sustenta. Números em `out/medicao/relatorio.json` | Resolvida |
| 18 | **`85-grasss.zip` não entra** — é `.c4d`, formato do Cinema 4D, que o Blender não importa. Se ele tiver a grama em outro formato (`.fbx`, `.abc`, `.blend`), entra | **Natan**, se quiser |
| 19 | **`blosm` fica como proposta**, não entra no caminho crítico: o entorno já vem de SRTM conferido em ±5 m e WorldCover a 10 m, e o que o addon somaria é silhueta urbana a 3–8 km. Motivo inteiro em `DECISOES.md` D017 | **Natan** decide |

**Disco:** saída de render vai para o **F:** (299 GB). O `E:` tem 107 GB e já
chegou a zero. **O `G:` mencionado na versão anterior deste arquivo não existe.**

**Máquina:** Xeon E5-2680 v4 (28 threads), RTX 4060 8 GB, 32 GB RAM.
Render é OptiX na GPU; ffmpeg é CPU e não briga — mas **cronometrar com a
máquina ocupada mede ruído**.
