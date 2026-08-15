# DECISÕES — registro de ambiguidade resolvida sem perguntar

**AGROSHOW 2026 · render-expovizinhos**

Este arquivo existe por ordem do Natan, 15/08/2026, literal:

> *"Trabalhe de forma autônoma até o fim. Não me pergunte nada: quando houver
> ambiguidade, escolha a opção mais conservadora, registre a decisão e o motivo
> em DECISOES.md e siga. Se algo travar de vez, pule para a próxima tarefa da
> fila e documente o bloqueio."*

Toda linha aqui é uma escolha que eu fiz no lugar dele. Ele pode reverter
qualquer uma — é para isso que o motivo está escrito.

**Precedência em vigor:** ordem do Natan → `reference/DOUTRINA-RENDER-3D.md` →
revisão do plano (15/08) → doutrina do projeto.

---

## 2026-08-15

### D001 · Snapshot antes da etapa destrutiva
**Ambiguidade:** o plano manda "snapshot versionado", sem dizer onde nem o quê.
**Decisão:** `out/_snapshots/2026-08-15_pre-formas-reais/` com `cena.blend` e
`cena-empacotada.blend`, md5 conferido (`57280DC6…` bate nos dois).
**Motivo:** conservador — copiar os dois custa 81 MB e devolve a cena inteira,
inclusive as texturas, se a etapa 3 der errado. `nada se apaga`.

### D002 · Onde a doutrina dele mora
**Ambiguidade:** o arquivo veio em `C:\Users\natan\Downloads`, que é pasta volátil.
**Decisão:** copiado para `reference/DOUTRINA-RENDER-3D.md` e citado na precedência
do agente. O original fica onde está — não apago nada dele.
**Motivo:** `Downloads` some numa faxina; doutrina que rege o processo não pode
depender de pasta temporária.

### D003 · Divergências entre a doutrina e o que já foi decidido por ele
A doutrina é ordem norteadora, mas **ordem direta dele vence**. Divergências
registradas, sem mudar nada por conta própria:

| ponto | doutrina | o que vale aqui | por quê |
|---|---|---|---|
| Golden hour | *"não fazer golden hour em todas as imagens"* `[Provável]` | **golden hour fica** | ordem do cliente; e a regra da doutrina é para stills de prazo curto, não para um filme com hora declarada e HDRI casado por medição |
| Samples | Noise Threshold 0,01 + max alto `[Certo]` | **128 / 0,1 continua** | config ditada por ele em 14/08. Medido no passo 0.4 e levado como número — não mudo sozinho |
| Saída | EXR MultiLayer + Cryptomatte `[Certo]` | **EXR + Cryptomatte** | ele decidiu em 15/08; supera o PNG-8 de 14/08. O espelho PNG continua para o `encode.sh` |
| Crowd 3D | *"não colocar crowd 3D, use billboard"* `[Provável]` | **proxies ficam por ora** | a decisão 14b (Plano A vs B) é dele e ainda está aberta; billboard vira proposta dentro da 14b |

### D004 · Cryptomatte Levels 2 — conferido, não assumido
**Ambiguidade:** a revisão manda "2, no máximo 3", contra o default 6, com o
argumento de que arquitetura opaca não precisa de mais.
**Decisão:** **2**, e agora está medido: dos pixels que têm objeto,
**99,69% fecham cobertura em 1,0**; os 0,16% parciais do quadro inteiro são
borda de folhagem. **Fecha.** Prova em `scripts/conferir_matte.py`.
**Motivo:** o argumento estava certo, mas argumento não é medida — e o custo de
descobrir tarde era a fila inteira.

### D005 · `Position` e `Vector` fora do slot de dado
**Ambiguidade:** o plano listava os quatro passes de dado; medido, o total dos
três slots deu **266 GB de 299 GB livres** no F:. 33 GB de folga para um render
de 47 s/quadro que roda dias é folga que não existe.
**Decisão:** cortados os dois. Restam Cryptomatte, Depth e Normal — e o total
caiu para **199 GB**, com 100 GB de folga.
**Motivo, item a item:** `Vector` serve para borrar em pós o que saiu nítido, e
**o motion blur já é renderizado na câmera** — guardar os dois é pagar duas
vezes pelo mesmo borrão. `Position` é recuperável de `Depth` mais a matriz da
câmera, que está no `.blend` e no `planos.json`. Nenhum dos dois entrega nada
que já não esteja lá.
**Bônus da mesma rodada:** `Normal` e `Position` estavam declarados como RGBA e
gravavam um quarto canal morto. Agora são `VECTOR` (XYZ).

### D006 · A armadilha do `save_as_render`, provada nos dois lados
Não bastava configurar: o defeito (AgX assado dentro do EXR, ou PNG lavado) é
invisível até tarde. Medido no quadro do smoke:

| | evidência | veredito |
|---|---|---|
| **beauty EXR** | **18,5% dos pixels acima de 1,0**, máximo 6,80 | linear de cena, headroom inteiro. Nenhum view transform aplicado — AgX comprime tudo abaixo de 1,0 |
| **preview PNG** | máximo 0,922; mediana 0,549 contra 0,705 do sRGB ingênuo do mesmo pixel | AgX aplicado, e é AgX mesmo, não gama 2,2 |

### D007 · Nome de arquivo com 5 dígitos
**Ambiguidade:** o File Output do Blender 5.x nomeia sozinho, e o primeiro
smoke gravou `Untitled.exr` e `Image.png` — o mesmo arquivo por cima a cada
quadro.
**Decisão:** `saida.nomear()` crava `{quadro:05d}` antes de cada render, e o
item do slot PNG tem nome vazio.
**Motivo:** cinco dígitos é o que o `encode.sh` procura (`%05d.png`); quatro
entregariam PNG que o ffmpeg não enxerga. E nome repetido quebra a retomada do
`render_shots.py`, que decide o que já foi feito olhando o disco.

### D009 · ACHADO — o render vinha na CPU, e ninguém sabia

Não é decisão minha, é defeito encontrado, e é o maior desta sessão.

A cena guarda `cycles.device = "GPU"`. **O dispositivo, não.** Ele mora nas
*preferências*, que são da instalação do Blender e não do arquivo `.blend`.
Aberto numa sessão limpa, o `cena.blend` anunciava GPU e as preferências vinham
com `compute_device_type = NONE`, **nenhum dispositivo marcado**. É o fallback
silencioso da doutrina §12, acontecendo há sessões.

| | tempo do quadro | filme (4.635 quadros) |
|---|---|---|
| como estava (CPU, sem saber) | 47 s a 100% | **~60 h** |
| com OptiX ligado | ~11,6 s a 100% | **14,9 h** |

O `RETOMAR.md` declara *"36–38 s/quadro → 46–49 h o filme"*. **Esse número é de
CPU** e nunca foi de GPU. Vai corrigido.

**Conserto:** `medir_render.garantir_gpu()` liga OptiX, marca as duas entradas
da RTX 4060 e **desliga a CPU** — com os dois marcados o Cycles divide o
trabalho e o tempo medido deixa de ser o da placa. O mesmo tem que entrar no
`render_shots.py` antes da fila. Achou a placa: `NVIDIA GeForce RTX 4060`.

### D010 · Samples: a config dele de 14/08 se sustenta, e agora está medida
Medido no P08 (Café Colonial, 50 mm, câmera a 4,5 m — o plano mais fechado, com
luz indireta de dentro de estrutura), a 50%, os quatro cruzamentos:

| config | tempo | ruído local |
|---|---|---|
| 128 / 0,1 **sem** denoise | 3,9 s | 0,00765 |
| **128 / 0,1 com denoise** | **2,9 s** | **0,00261** |
| max / 0,01 sem denoise | 10,1 s | 0,00374 |
| max / 0,01 com denoise | 10,3 s | 0,00262 |

**0,01 custa +255% de tempo e entrega −0,4% de ruído.** Empatam. O OpenImage
Denoise já resolveu o granulado; baixar o limiar é 38 horas a mais por uma
diferença que não existe na imagem — e o filme sairia em 53 h no lugar de 14,9 h.

**A doutrina pede 0,01 `[Certo]` e aqui ela não se aplica**, e o motivo é o que
ela mesma diz na §7.2: a regra existe contra *compensar samples baixos com
denoise agressivo*. O denoise aqui não é agressivo — é OIDN com prefilter Fast e
qualidade Balanced, e a medida mostra que 128 samples **já converge** nesta cena.
Nada muda sem ele; o número está aqui para ele decidir.

### D011 · O denoise fica no render, e agora por medida
O contrato de saída já declarava `denoise.onde = "render"` por herança da ordem
dele. Medido: com denoise o quadro fica **26% mais rápido** (2,9 s contra 3,9 s
— o denoise deixa o amostrador adaptativo parar mais cedo) e o ruído cai 66%.
Não há caso para mover para post: seria mais lento e exigiria guardar os passes
de denoise em float 32 no slot de dado.

### D012 · A projeção de disco de um plano só estava 43% errada
**Ambiguidade:** o critério de aceite pedia "tabela de disco recalculada com
números reais". Recalculei — de **um** quadro, o P01.
**O que aconteceu:** o P01 é o plano mais aberto do filme, com metade do quadro
em céu liso, e céu comprime quase de graça. Amostrados **seis** planos, a média
real deu **63 MB/quadro** e o filme **285 GB de 300 GB livres**. Quinze GB de
folga para um render de horas é um render que morre em 90%.
**Decisão:** projeção de disco só vale com pelo menos seis planos amostrados, e
o pior caso medido à parte. `scripts/medir_compressao.py` faz isso.
**Motivo:** é a mesma falha que o `RETOMAR.md` já registra duas vezes nesta
sessão — medir uma coisa e chamar de outra. Um quadro não é o filme.

### D013 · Os passes de difuso e glossy saíram do beauty
Medido no P11, quadro fechado, custo do slot beauty:

| arranjo | MB/quadro |
|---|---|
| 8 camadas | 19,8 |
| Combined + Diff + Gloss (5) | 18,2 |
| **só Combined** | **2,2** |

Os quatro passes de difuso/glossy custam **16,0 MB**; Emit, Env e AO custam
**1,6 MB somados**. O peso do beauty são eles, e o resto é troco.

**Decisão:** beauty = `Combined + Emit + Env + AO`. Resultado medido nos mesmos
seis planos: **38,9 MB/quadro, 176 GB no filme, 124 GB de folga** — e o quadro
ficou mais rápido, **10,0 s** contra 13,6 s, porque são menos passes a compor.

**Divergência consciente com a doutrina §7.4**, que pede "luz separada" entre os
AOVs que dão margem: o que ela protege — mexer sem re-renderizar — segue
protegido por Cryptomatte (isolar qualquer objeto), Depth (atmosfera, separação
de plano) e Normal (relight de superfície). O que se perde é rebalancear difuso
contra especular no filme inteiro, que ninguém pediu. O que se ganha é o render
caber no disco. **AO fica** porque a doutrina o nomeia e custa quase nada.

### D014 · `write_still=False` no render de verdade
O Blender gravava, além dos três slots, um `_descartar_.png` de 5 MB por quadro
que ninguém usa — **23 GB no filme**. Os File Output gravam durante a
composição, independente do `write_still`. Desligado.

### D015 · O footage de quinta NÃO é HDR — e isso era a suposição perigosa
`ffprobe` nos 17: **3840×2160, yuv420p10le, bt709** em transferência, primárias
e matriz. **SDR de ponta a ponta.**

Isto contraria o que o material antigo deste mesmo cliente ensinou: os `IMG_91xx`
da triagem de 14/08 são HLG bt2020 / Dolby Vision e exigiram tonemap, e a
memória do projeto guarda *"material do AgroShow é HDR"* como armadilha. **Aqui
não.** Aplicar a cadeia de HLG neste material destruiria a cor — e em silêncio,
porque a imagem sai, só sai errada.

O `extrair_linear.py` **lê o ffprobe de cada arquivo e monta a cadeia a partir
dele**, em vez de aplicar uma receita fixa; e recusa transferência que não
conhece em vez de inventar. Conferido: a mediana do quadro linear dá **0,0174**
contra **0,1588** se fosse sRGB — está linear de verdade.

**E o 4:2:0 tem consequência prática:** croma subamostrado, e os dois materiais
mais críticos do parque são o pior caso — parede/chapa **vermelha** saturada e
coluna **azul** saturada. Regra escrita no contrato: medir só em região grande e
chapada, longe de borda de cor.

### D016 · Regra de desempate footage × planta
A ordem dele — *"os locais que já estão lá não mudam"* — não diz o que fazer
quando o footage contradiz o footprint. Sem regra, a etapa 3 vira decisão ad hoc
quadro a quadro. Declarada em `data/footage-quinta.json`:

- **forma e proporção → footage vence.** A planta é bitmap reamostrado e não
  desenha forma; a câmera desenha.
- **posição e footprint → planta vence.** É a ordem dele, e a conferência de
  14/08 foi validada contra satélite.
- **altura → footage, por datum declarado em quadro.** Altura de *patamar*
  continua com o cliente (pendência 8) — patamar não aparece em quadro.
- **divergência acima de 5 m → não escolho.** Vira pendência com o quadro
  recortado. O limiar é maior que a incerteza de medir por imagem e menor que um
  erro que muda a leitura do plano.

### D017 · Os três achados dele, avaliados e declarados

| achado | o que é | veredito |
|---|---|---|
| **`85-grasss.zip`** | contém `grasss.c4d` — um arquivo **Cinema 4D** — e três JPEGs | **não entra.** O Blender não importa `.c4d`; é formato proprietário e fechado, e não há C4D nesta máquina. Não é falta de vontade: não há caminho. A grama da cena continua vindo do `aerial_grass_rock` CC0 com cor medida no footage dele, e agora ganha o reforço do footage de quinta |
| **`workbook_v1.xlsx`** | três abas — Checklist Geral, Bibliotecas de Assets, Parâmetros de Render. Checklist genérica de pipeline 3D | **referência, não doutrina.** O que ela pede e que já está feito: OptiX, AgX, unidades métricas, Cycles GPU. O que ela pede e **não se aplica**: RTX 3090/4090 (a máquina é 4060 e o projeto já está dimensionado para ela), Quixel Bridge e BlenderKit premium (a verba de asset é **zero** e só CC0 entra). Fica em `reference/` como registro |
| **`blosm`** (addon + repo) | importa OpenStreetMap e terreno para o Blender | **não entra no caminho crítico.** O entorno já vem de fonte melhor e medida: SRTM até 12 km conferido em ±5 m contra segunda fonte, e ESA WorldCover a 10 m para a cobertura. O que o blosm somaria é edificação urbana de Dois Vizinhos a 3–8 km — que aparece como silhueta de poucos pixels num filme cujo assunto é o recinto. E `RETOMAR.md` já fixa que **nenhum addon entra no caminho crítico do gerador**, porque addon derrubado deixa o render sair errado em silêncio. Fica como proposta, com o custo dito |

### D008 · Nota de API — Blender 5.2 não é 4.x
Custou duas rodadas e fica escrito: o compositor virou
`scene.compositing_node_group` (era `scene.node_tree`); o File Output trocou
`layer_slots`/`file_slots` por `file_output_items` + `directory`/`file_name`;
`format.media_type` **filtra** o enum de `file_format` e tem que ser atribuído
antes; e os sockets de passe viraram nome por extenso (`Diffuse Direct`, não
`DiffDir`). O passe `Shadow` não existe mais no Cycles daqui — foi removido do
contrato em vez de virar slot preto.

---

## 2026-08-15 — sexta sessão (etapa 2: medir os materiais do footage novo)

### D018 · A âncora de 14/08 não serve neste footage, e o erro é de ORIENTAÇÃO
**Ambiguidade:** o plano diz *"estender `medir_materiais.py` para os quadros
lineares"*, e o método de 14/08 é âncora de albedo conhecido no mesmo quadro.
Não diz o que fazer quando não há superfície branca de albedo conhecido no
quadro — e nos 17 vídeos de 13/08 não há.

**O que eu tentei primeiro, e como o número denunciou.** Declarei a telha
metálica clara em 0,70, mesma lógica da lona 0,75. O tijolo saiu com **albedo
1,000 no vermelho** — a parede refletiria mais vermelho do que o branco reflete.
Isso não existe.

**A causa é física e não é escolha de caixa.** O footage de 13/08 é de **dia
encoberto**, e em céu encoberto a irradiância depende da **orientação** da
superfície: a água de telhado vê o hemisfério de céu inteiro, a parede vertical
vê metade dele. Âncora no telhado mede uma luz que a parede não recebe, e todo
albedo de parede sai inflado — 85% inflado, medido. A doutrina de 14/08 já
avisava disso numa linha (*"superfície de âncora tem que estar iluminada como as
que se quer medir"*), e naquele quadro havia a sorte de a lona estar virada para
o sol junto com o resto.

**Decisão: o céu do próprio quadro vira o fotômetro.**

    E_horizontal = pi * L_ceu
    E_orientacao = E_horizontal * FATOR_VISTA[orientacao]
    albedo       = pi * L_superficie / E_orientacao

`FATOR_VISTA` está declarado valor por valor em `medir_materiais_quinta.py`:
horizontal 1,00 · vertical aberta 0,54 · vertical sob beiral 0,32 · telhado de
baixa inclinação 0,96 — cada um com a conta atrás.

**Motivo de ser a opção conservadora:** é um modelo derivável, escrito e
**conferível**, contra um número que eu escolheria porque a imagem "parecia
branca". E só foi possível porque o quadro `1 (17)__0006s` tem o céu **não
estourado** — 99,9% dos pixels em 0,957, só 0,06% no teto. Nos outros o céu está
saturado e o método não se aplica; está dito no JSON.

**E ele passou em dois controles independentes**, contra a medição de 14/08 que
saiu de outro quadro, outro dia, outra luz e outro método:

| controle | 14/08 | agora | razão de luminância |
|---|---|---|---|
| mata (perene) | 0,132 / 0,154 / 0,046 | 0,135 / 0,144 / 0,066 | **0,96×** |
| terra batida | 0,266 / 0,188 / 0,155 | 0,339 / 0,240 / 0,159 | 1,27× |

Duas medições que não se falam concordando é o que separa medida de conta.

### D019 · O tijolo estourou no vermelho, e a cadeia carrega só o nível
**Ambiguidade:** a coluna azul larga e o portão de chapa só aparecem grandes e
chapados no plano fechado `1 (17)__0037s` — que **não tem céu no quadro** e tem
8,7% dos pixels no teto.

**Decisão:** o quadro fechado entra por **âncora transferida** do quadro aberto,
usando a mesma alvenaria — mas **só nos canais G e B**. No plano fechado a
câmera expôs para o interior escuro do vão e **41% dos pixels do tijolo estão no
teto do vermelho**. Então a cadeia carrega só o **nível** (fator k = 4,665,
medido em G e B) e reusa a **cor** do iluminante do quadro aberto — mesmo dia,
mesmo céu encoberto, mesmo balanço de branco da câmera.

**Motivo:** ancorar num canal saturado transporta um valor que a câmera não viu.
Ancorar só nos limpos transporta o que ela viu. E a conferência fecha: o tijolo
medido pelos dois caminhos dá **0,564/0,073/0,071** e **0,551/0,083/0,061**.

**Trava nova em código, não em parágrafo:** `ESTOURO_MAXIMO = 0,5%` — amostra
com mais que isso de pixel no teto é **recusada com o número impresso**. Foi ela
que pegou as duas caixas erradas desta sessão; nenhuma delas dava erro na tela.

### D020 · Rotulei uma amostra de `grama` e ela era chão batido
**Ambiguidade:** nenhuma — foi erro meu, e fica escrito porque é o terceiro
desta série (o anel bege do entorno em 14/08, o centro da arena em 14/08).

Declarei uma caixa como `grama` e ela devolveu 0,339/0,240/0,159, que é bege. O
debug em quadro mostrou terra pisada entre as árvores. **Renomeada para
`chao_batido` em vez de forçada para outro lugar** — rótulo errado sobre medida
certa é pior que medida faltando —, e promovida a segundo controle, onde bate
com a classe `terra` de 14/08.

**O que se repete e vale como regra:** três vezes nesta série eu li a imagem e o
número desmentiu, e nas três o que pegou foi **desenhar a caixa no quadro e
olhar**. O `--debug` deixou de ser conveniência: nenhuma amostra entra em
contrato sem a folha de prova gerada.

### D021 · O que NÃO deu para medir, e por que fica sem número
**Ambiguidade:** o plano lista sete classes novas. Três delas só aparecem em
quadro sem fotômetro ou em peça fina, e a saída fácil seria arbitrar um albedo.

**Decisão: entregar o que está medido e nomear o que não está.**

| classe | estado | motivo |
|---|---|---|
| tijolo vermelho | **medido** 0,564/0,073/0,071 | céu não estourado no quadro |
| chapa azul (telhado) | **medido** 0,036/0,274/0,592 | idem |
| coluna azul | **medido** 0,018/0,060/0,165 | cadeia por canal limpo |
| portão de chapa | **medido** 0,066/0,077/0,098 | idem |
| terra batida (interna) | **medido** 0,097/0,033/0,016 | idem |
| brita / estrada | **medido** 0,261/0,189/0,162 | e confere com `terra` de 14/08 |
| concreto, grade, piso de curral | **só a cor** | não há céu medível nas mangueiras |
| estrutura de telhado vermelha | **sem medida** | só existe em terça e rufo, peças de 20–40 px. Croma 4:2:0 de peça fina é mistura inventada pelo decodificador, e a caixa que tentei ainda vinha com 1,25% no teto |

**E um achado que muda como se lê o quadro das mangueiras:** ali a luz não é
uniforme — o primeiro plano recebe céu pelos vãos abertos e o fundo coberto não.
A coluna que eu havia escolhido como referência lê **3× mais escura** que as
grades, e isso **não é albedo, é iluminação**. A referência passou para a grade,
que está no mesmo regime do piso, e o JSON carrega o campo
`_a_razao_NAO_e_reflectancia_entre_regimes` dizendo exatamente isso.

**Correção de decupagem, de quebra:** `footage-quinta.json` descrevia o piso das
mangueiras como *"piso de brita"*. O quadro mostra **terra com maravalha**. A cor
sai do quadro, não do rótulo.

### D022 · A ferradura da bacia, conferida contra foto de drone
**Ambiguidade:** a pendência 4 foi fechada em 14/08 por **inferência sobre o
desenho** — duas testemunhas indiretas (nenhum dos 15 `Talude` e nenhum dos 93
estandes da série C no setor de 240° a 360°). Inferência boa, mas indireta. O
vídeo `1 (2)` é nadir de drone e mostra a ferradura **direto**.

**O problema:** foto não sabe onde é o norte.

**Decisão: medir o ÂNGULO ENTRE duas direções dentro da própria imagem** — o
eixo da fileira de pavilhões (cujo rumo o desenho já dá, azimute 108°) e a boca
da bacia. Ângulo entre direções não depende de saber o norte; e o quadro é
nadir, então ângulo na imagem é ângulo no mundo.

| | |
|---|---|
| ângulo entre, medido na imagem | **56,8°** |
| eixo dos pavilhões, do desenho | azimute 108,0° |
| abertura da bacia | rumo de mapa **164,8°** ou 344,8° |
| o que `data/bacia.json` diz, derivado | rumo de mapa **150,0°** |
| desvio | **14,8°**, com tolerância de 20° |

**A ambiguidade de 180° é real e está declarada:** a reta dos pavilhões tem dois
sentidos e a foto não os separa. Quem desempata é a planta — que já havia dito
que não há talude nenhum entre 240° e 360°. **Duas fontes que não se falam
concordando é o resultado; não é uma fonte só com duas contas.**

**Correção, no mesmo turno em que o erro apareceu:** a primeira versão deste
registro dizia **0,2° de desvio** contra "os 165,0° que a planta já dizia".
**Os 165 eram meus, não do arquivo.** A convenção de `data/bacia.json` está
escrita nele e não é a da bússola — *"0 graus = +x (leste do mapa), 90 = +y
(norte do mapa), anti-horário"*. Derivando em vez de afirmar, o centro da boca
de lá dá **rumo de mapa 150°**, e o desvio verdadeiro é **14,8°**.

**O veredito não muda: CONFERE.** 14,8° é grande para uma linha e pequeno para
uma boca de 120° — as duas fontes apontam para o mesmo quadrante, que era o que
estava em questão. O que muda é a honestidade do número, e o erro é o mesmo dos
outros três desta semana: eu escrevi de cabeça uma coisa que o arquivo tinha
escrita, e não abri o arquivo.

**Trava que entrou por causa disso:** o script agora **lê `bacia.json` e faz a
conversão em código**, com a conta no docstring. Número de referência que mora
numa constante escrita à mão é número que ninguém confere.

### D023 · O que o footage prova de forma, e o que ele ainda não prova
**Ambiguidade:** o plano manda "corrigir a forma de todos os prédios que têm
footage". Fazer isso agora significaria trocar geometria a partir de leitura de
quadro sem o footprint casado — e `construir sobre footprint errado é pior que
não construir` já está escrito.

**Decisão: separar o que a câmera prova do que ela não prova, e entregar
`data/formas-quinta.json` como registro antes de mexer em geometria.**

O que ficou **provado** e não estava:

- o **prédio redondo é POLÍGONO REGULAR de ~10 faces**, não círculo, e tem dois
  pavimentos com o superior recuado, varanda em volta, guarda-corpo de 1,10 m e
  telhado de quatro águas de baixa inclinação sobre polígono. Contado nas
  quebras da saia do telhado inferior e do guarda-corpo em `1 (6)__0012s` e
  `1 (10)__0041s`. **Confiança média** — os segmentos aparecem desiguais no
  quadro, e isso é perspectiva de polígono regular, mas uma vista de topo
  fecharia a contagem;
- há um **anexo retangular** encostado nele, que é outro volume. Modelar junto
  deformaria o polígono;
- o **PALCO é branco sobre base azul**, e na cena ele herdou **madeira**.

O que **não** ficou provado, e por isso não virou geometria: qual zona da planta
é cada prédio (sem isso a forma medida não sabe onde pousar), a contagem exata
das faces, e as alturas por datum. Os datums estão listados no JSON — pessoas na
varanda (1,70 m), guarda-corpo (1,10 m, norma), carro (4,4 m).

### D024 · Correção: eu errei sobre o palco, e o erro descobriu uma contradição
**O que eu escrevi em D023 e está errado:** *"o PALCO é branco sobre base azul,
e na cena ele herdou MADEIRA"*. Duas coisas erradas numa frase só.

1. `estruturas.palco` não usa `MAT_MADEIRA` — usa `MAT_PRETO`. `MAT_MADEIRA` é
   do **Portal**. Eu li a linha errada do `grep` e não abri a função.
2. E, mais importante: **`1 (4)` não mostra o palco da cena.** Olhando os oito
   quadros, é uma **concha permanente de alvenaria** — base azul de ~1,2 m,
   paredes claras, cobertura inclinada escura — plantada num gramado ao lado de
   uma pista de terra. O que `estruturas.palco` constrói é outra coisa:
   deck de 16 × 11 m, quatro torres de treliça de 10,5 m, cobertura tensionada,
   telão de LED e caixas empilhadas. É o **palco de evento**, montado, e a
   procedência dele está citada na própria função:
   `DJI_20251127184447_0110_D` 00:00:02, de novembro.

**A contradição que apareceu no caminho, e ela não é minha:**
`data/estimativas.json` afirma, sobre a Praça de Alimentação Coberta, que *"não
usa `estruturas.palco` porque aquele é o **palco fixo** da arena"*. Mas
`estruturas.py` documenta o mesmo objeto como o palco **de evento**, de
novembro, e o código constrói treliça e telão. **Os dois não podem estar certos.**

**Decisão, conservadora:** não reescrevo geometria nenhuma por causa disso. O
que faço é:

- **corrigir o comentário** em `estimativas.json`, que é documentação e é
  reversível — `estruturas.palco` é o palco **de evento**;
- **registrar o palco fixo como estrutura que a cena NÃO tem.** Ele é um "local
  que já está lá", e a ordem dele diz que esses não mudam — mas não existir é
  diferente de mudar. Vira pendência com o quadro apontado;
- **não medir a cota dele agora.** O `ESTADO.md` já dizia que a pessoa em pé no
  `1 (4)` 00:00:02 dá 1,70 m *"no mesmo quadro que o palco fixo"* — só que ela
  está no primeiro plano e o palco a uns 40 m atrás. **Altura em pixel de coisa
  a outra profundidade não escala**, e é exatamente a armadilha que a série de
  erros desta semana tem em comum. Fica pendente por falta de datum na mesma
  profundidade, não por falta de vontade.

**O que se repete e vira regra:** eu afirmei sobre um arquivo a partir de uma
linha de `grep` e sobre uma estrutura a partir de uma folha de contato. Nas duas
vezes o conserto foi **abrir o arquivo e olhar o quadro inteiro**. É o mesmo que
a memória do projeto já guarda como *ver antes de afirmar*, e é a terceira vez
nesta semana.

### D025 · A sobreposição das vias não certifica as 42 — e mostra por quê
**Ambiguidade:** a pendência 9 diz que as 42 vias estão `conferido_pelo_natan:
false` e que o aéreo nadir "destrava" a conferência. Destrava, mas não do jeito
que eu esperava.

**Feito:** `scripts/sobrepor_aereo.py` projeta as vias sobre `1 (2)__0076s` por
uma semelhança (escala, rotação, translação), com cada parte tirada de coisa já
medida — centro da arena `(−74,7 / −3,2)` marcado por ele, rotação do eixo dos
pavilhões (rumo de mapa 108°), escala do raio dos patamares.

**A validação é honesta porque o validador não entra no ajuste:** centro, escala
e rotação saem da arena e dos pavilhões; quem confere são as **vias**, que não
foram usadas em nada disso.

**O que a folha mostra:**

- a **escala e o centro fecham bem** — os anéis de 45 e 62 m do modelo pousam em
  cima dos terraços que aparecem na foto. A primeira leitura do centro estava
  470 px fora, e foi a própria sobreposição que denunciou;
- **e boa parte das "vias" cai em cima dos terraços da arena.** V19, V24, V27,
  V32, V35, V43, V50 e vizinhas desenham arcos concêntricos dentro da bacia. Isso
  não é estrada: **é a curva de nível da arquibancada, lida como linha pelo
  Hough**. O `vias.json` já avisava que o traçado é leitura de bitmap; a foto
  mostra o que ele leu.

**Decisão: não marcar nenhuma como conferida.** O campo se chama
`conferido_pelo_natan` e o nome diz de quem é. O que fica escrito é uma
suspeita **com prova em quadro** — que um subconjunto das 42 é contorno de
patamar, não via — e ela é acionável: quem for usar `vias.json` para geometria
precisa separar isso antes.

**O que fecharia:** classificar por forma. Traçado que é arco concêntrico ao
centro da arena, dentro de r < 150 m, é candidato a patamar; o resto é candidato
a via. É conta sobre dado que já está no arquivo — não precisa dele.

### D026 · Plano A destravado: as cenas vão para IA por quadro-para-vídeo
**Ambiguidade:** ele mandou *"gerar as cenas no flow (...) ou no flow ou no
higgsfield mas não posso cometer erros o lugar tem que ser exatamente o lugar"*,
sem dizer **como** garantir o lugar.
**Decisão:** **nenhum clipe é texto-para-vídeo.** Todo clipe é quadro-para-vídeo,
com os DOIS extremos renderizados da cena medida — e o prompt **proibido de
descrever posição**. Contrato em `data/cenas-ia.json`, gerador em
`scripts/cenas_ia.py`, doc operável em `docs/CENAS-IA.md`.
**Motivo:** é a única forma que não deixa a escolha do lugar com a IA. Descrever
o parque em palavras piora: quanto mais detalhe, mais ela compõe *um* parque e
menos *este*. Travando os dois extremos, ela só preenche o meio. E a decupagem
já entregava isso de graça — cada plano declara câmera de início e de fim desde
14/08, que é literalmente o que o *Frames to Video* pede.
**Fecha a pendência 14b** do `RETOMAR.md`: é o Plano A, e o proxy do povoamento
passa a ser o certo — ele dá massa, silhueta e escala, e a IA põe a pele.

### D027 · Flow como caminho principal, e o motivo é a grade de duração
**Ambiguidade:** ele deixou a escolha aberta entre as duas.
**Decisão:** **Flow**. Higgsfield fica para os planos em que o movimento é o
assunto (P19 touro, P20 público).
**Motivo:** medido, não preferido. A grade do Flow é 4/6/8 s e a do Higgsfield é
5/10 s. Como o caminho da câmera não muda, encaixar um plano numa duração
diferente **muda a velocidade** — e a faixa cinematográfica de drone é o motivo
de a decupagem existir. Na grade do Flow os 22 planos cabem; na do Higgsfield
**4 não cabem** (P04, P10, P13, P22): para esses, nem 5 s nem 10 s ficam dentro
da faixa. O conserto existe e é pequeno (encurtar percurso para 87–98%), então o
Higgsfield não está descartado — só cobra quatro correções que o Flow não cobra.

### D028 · O encaixe na grade obedece à faixa de velocidade, não ao relógio
**Ambiguidade:** com que critério quebrar um plano de 9,0 s numa grade de 4/6/8.
**Decisão:** a regra de velocidade vem **antes** do erro de duração no critério
de escolha.
**Motivo:** a primeira versão desempatava por "menos clipes" e escolhia 8,0 s
(um clipe, erro 1,0 s) em vez de 4+6 (dois clipes, erro 1,0 s). Os dois erram o
mesmo 1 segundo — mas **encurtar acelera a câmera e alongar desacelera**. Os 8 s
jogavam o push-in do P02 a 2,35 m/s, fora da faixa; os 10 s o deixavam em 1,88,
dentro. **Empate em duração não é empate em cinema.** Foi o próprio conferidor
que pegou, acusando 5 planos fora da faixa antes de eu perceber o defeito.

### D029 · A negativa de arquibancada só entra onde há público
**Ambiguidade:** a restrição 1 do cliente vale para o filme inteiro; o prompt é
por clipe.
**Decisão:** a negativa *"no grandstands"* entra em **6** dos 22 planos — P10,
P12, P18, P19, P20, P21 —, os que têm público assistindo alguma coisa. Lista
declarada em `data/cenas-ia.json`, revisável.
**Motivo:** negativa só protege onde o risco existe, e modelo generativo carrega
o conceito que a palavra traz **mesmo na negativa**. Citar arquibancada num
plano de estacionamento não protege nada e pode desenhar uma.

### D030 · Os letreiros não passam pela IA
**Decisão:** `render_guias.py` esconde a coleção `LETREIROS`. O texto entra na
montagem, por cima do clipe pronto.
**Motivo:** modelo generativo destrói tipografia — reescreve letra, troca acento,
inventa palavra. As duas frases dele são **literais** por ordem escrita, e a
palavra *Kids* é proibida: nenhuma das duas coisas sobrevive a um modelo que
resolve "melhorar" um letreiro. A regra de 8%/4% continua valendo, medida sobre
o master 2760×1380, que é onde ela sempre foi medida.

### D031 · 16:9 no guia, 2:1 no corte — e a prova de que não se perde nada
**Ambiguidade:** a entrega é 2:1 e nenhuma das duas plataformas gera 2:1.
**Decisão:** guia e geração em **16:9**; a entrega sai cortando a faixa central.
Nunca esticar. `sensor_fit` declarado **HORIZONTAL** no render do guia.
**Motivo:** o corte é seguro **por construção**, não por sorte — toda câmera
mira o alvo por constraint *Track To*, então o assunto está no centro do quadro,
e corte simétrico de topo e base não pode perdê-lo. A largura não muda: 16:9 e
2:1 têm a mesma horizontal. O `sensor_fit` vai explícito porque no AUTO o
Blender ajusta pela maior dimensão — daria no mesmo hoje, mas passaria a
depender da resolução, e isso é o fallback mudo da doutrina §12.

### D032 · Os 134 estandes viram tenda, e a planta provou a família
**Ambiguidade:** ele mandou *"colocar as tendas nas posições reais"*; as posições
já eram reais desde sempre — o que era falso era a **forma** (caixa de 3,2 m).
**Decisão:** cada estande vira tenda piramidal de lona da família padrão mais
próxima (3×3, 5×5, 10×10), com escala em X/Y fechando a área cotada e **Z sem
escalar**. Teto de ±30%: **131 dos 134 viram instância de 3 malhas**, 3 saem com
malha própria. Contrato em `data/tendas.json`, conferidor sem `bpy`.
**Motivo, e não é escolha de gosto:** o histograma das áreas cotadas mostra que
**a planta foi desenhada na grade de tenda padrão** — 35 dos 41 estandes da
série A têm 25,00 m² (5×5 exata) e 39 dos 93 da série C têm 100,00 m² (10×10
exata). As duas modas caem em cima das medidas que a doutrina manda não errar.
Z não escala porque pé-direito é medida de mercado, não proporção: tenda maior
tem mais chão, não mais pé.
**De quebra fecha a pendência 12b:** a lona ganhou barriga (flecha de 3,5% do vão
no beiral, 2% na água), que era o defeito de "ler como placa rígida de perto".
E a Praça de Alimentação Coberta deixou de ser laje de 0,3 m sobre pilares e
virou cobertura de lona em naves de duas águas — o contrato dela **já declarava**
`MAT_LONA`; laje de lona não existe.

### D033 · As três tendas saem da área de espera
**Decisão:** peça com `posicao` diferente de `"espera"` não é mais construída na
`AREA_DE_ESPERA`. As três tendas saíram; as outras 8 peças ficam.
**Motivo:** a área de espera é, por definição, "peça cujo lugar eu não sei".
Agora que a tenda tem lugar — 134 deles, medidos —, deixar uma cópia parada ao
lado do mapa faz o arquivo abrir com duas verdades e ninguém sabendo qual vale.

### D034 · Flow travado como plataforma, e os 166 s aceitos
**Ordem dele, 15/08:** *"O filme fica 12 s mais longo pode ser não tenho limite
de tempo. quero fazer no flow então."*
**Decisão:** `flow` gravado como plataforma escolhida em `data/cenas-ia.json`;
o filme fica com **166 s**. O Higgsfield continua no arquivo como segunda opção
medida, e `--plataforma higgsfield` continua funcionando e continua acusando os
4 planos que não cabem na grade dele.
**Consequência:** nenhum plano precisou de ajuste de câmera — os 22 entraram na
grade de 4/6/8 s com a velocidade dentro da faixa cinematográfica.

### D035 · Cinco letreiros estavam no plano errado
**O que aconteceu:** montando a linha de tempo da montagem, o cruzamento entre
`letreiros.json` e `planos.json` mostrou que **5 dos 17 letreiros estavam
amarrados ao plano errado** — "Pista de Julgamentos" no plano das máquinas,
"Área de Shows" no do palco, e a frase de assinatura na saída pelo portal. Pior:
o TAMANHO de cada um tinha sido calculado com a lente e a distância do plano
errado, então nem a regra de 8% valia para o plano em que ele apareceria.
**Decisão:** os cinco reamarrados (P16→P12, P17→P13, P18→P16, P20→P18, P22→P21),
com o motivo gravado em cada item.
**Por que ninguém tinha visto:** os dois arquivos só se falavam pelo `id`, e
**id errado é id válido**. Agora `cenas_ia.py --conferir` compara o TEXTO do
letreiro com o TÍTULO do plano em que ele está, e falha na divergência.
**E a checagem é apertada de propósito:** as duas divergências legítimas
("Pavilhão 3" para o plano das Agroindústrias, "Alimentação no Bosque" para a
Praça Aberta) tiveram de ser **declaradas no arquivo**, item a item. Afrouxar o
comparador para engoli-las deixaria passar de novo as cinco de cima.

### D036 · Três planos não tinham letreiro, e a falta estava mascarada
**Ambiguidade:** com os cinco no lugar certo, P01, P17 e P20 ficaram sem
letreiro nenhum — a ausência estava escondida pelos que sentavam em cima deles.
**Decisão:** acrescentados os três (*Estacionamento*, *Veículos e Motos
Náuticas*, *Palco Principal*). São 20 letreiros.
**Motivo:** não é invenção de texto de cliente — `docs/BRIEFING.md` já dita os
três nos blocos 00, 15 e 18, e `planos.json` já intitula os três planos com
essas mesmas palavras. É transcrição.

### D037 · No Plano A o letreiro é texto 2D, não o objeto 3D da cena
**Ambiguidade:** os letreiros foram construídos em 15/08 como billboards 3D,
dimensionados pela lente e pela distância de cada plano.
**Decisão:** no Plano A eles entram na montagem como **texto 2D**, por
`drawtext`, e a regra de 8%/4% vira conta direta sobre os 1380 px do master.
**Motivo, e é o que decide:** o clipe da IA **não segue o caminho da câmera
quadro a quadro** — ela interpola entre os dois extremos travados do jeito dela.
Um letreiro renderizado do nosso percurso exato ia **deslizar contra a imagem**.
A geometria 3D deles não foi apagada: continua válida e é o que vale no Plano B.

### D038 · O texto do letreiro vai em arquivo, não dentro do filtro
**O que o teste pegou:** *"Dois, em frente ao parque"* tem **vírgula**, e vírgula
é o separador de filtros do ffmpeg. E a primeira versão trocava apóstrofo por
`’` para escapar — ou seja, **alterava texto de cliente em silêncio** para se
proteger de um problema de sintaxe.
**Decisão:** `textfile=` com `expansion=none`, um arquivo por campo.
**Motivo:** a string é lida verbatim e a classe inteira de bug desaparece de uma
vez -- vírgula, dois-pontos, apóstrofo, porcento e acento passam iguais. Nenhum
escape, nenhuma substituição, nenhum texto do cliente alterado. Conferido: 35
filtros, aspas balanceadas, e o texto sai byte a byte.
