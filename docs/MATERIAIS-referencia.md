# Materiais — o que o footage real do recinto entrega

**AGROSHOW 2026 · Parque de Exposições de Dois Vizinhos, PR**
Escrito em 14/08/2026, depois da triagem completa dos 137 GB de footage.

Este documento existe para atacar o **passo 3** do `ESTADO.md` — texturas PBR no
lugar das cores base — sem inventar material. A regra 3 do realismo pede:

> Sem tile visível. Grama com variação de altura, cor e densidade, e desgaste nas
> rotas de circulação — onde passa gente, a grama morre. Lona com translucidez e
> sujeira nas dobras. Piso e brita com deslocamento real, não normal map sozinho.

O que segue é o que o recinto **de fato** tem, medido em quadro, e não o que uma
biblioteca de textura acha que um parque de exposições parece.

---

## Onde o material mora, e por que não está aqui

Os vídeos e os quadros ficam em `E:\Projetos todos\Mapa - agroshow\Brutos Expo`.
**Nada disso entra neste repositório**: é material de cliente e o `origin` é
público. Aqui vai o caminho absoluto e o timecode; o arquivo fica lá.

| o que | onde |
|---|---|
| Vídeos | `Brutos Expo\` — 173 arquivos, 137 GB |
| Folhas de contato | `Brutos Expo\_triagem\<video>\FOLHA_<video>.jpg` |
| Quadros da triagem | mesma pasta, `<video>_t00.jpg` a `_t09.jpg` |
| Análise das 173 folhas | `_triagem\analise\notas-lote-01.md` … `-12.md` |
| Placar das escolhas | `_triagem\analise\lideres.md` |
| **Provas em resolução nativa** | `_triagem\provas-materiais\<classe>\` |
| Telemetria de voo | `_triagem\telemetria\` |

Para regerar tudo do zero, os scripts estão em
`E:\Projetos todos\Mapa - agroshow\Comandos\`.

---

## Como a triagem foi feita

Uma folha de contato por vídeo, 10 quadros em grade 5×2, com nome do arquivo e
timecode gravados no pixel — é o que permite pedir "o trecho de 01:23 do
DJI_0960" em vez de descrever o quadro. As 173 folhas foram lidas e pontuadas de
0 a 3 por classe de material.

Três correções de ferramenta foram necessárias antes de rodar, e as três valem
registro porque cada uma silenciava um erro:

1. **O `drawtext` estava abortando.** A build do ffmpeg no Windows não tem
   fontconfig: o filtro existe, é aceito, e o processo morre com violação de
   acesso. O resultado eram folhas **sem timecode** — e o script seguia em
   frente, porque o fallback dele era exatamente "extrai sem rótulo". As 22
   folhas geradas em 13/08 saíram assim. Consertado apontando o arquivo da fonte
   (`fontfile`), e as 22 foram refeitas; as antigas estão em
   `_triagem\descartado\sem-timecode-13ago\`.
2. **Três vídeos são HDR** (HLG bt2020, Dolby Vision 8.4 — os `IMG_91xx` de
   iPhone). Sem conversão de cor, os quadros saem lavados e dessaturados, o que é
   fatal justamente numa triagem que julga cor e material. Entrou uma cadeia de
   tonemap (`zscale` linear → `tonemap=hable` → bt709) aplicada só a eles.
3. **Decode na GPU** (`-hwaccel cuda`), com rebaixamento para CPU se a placa
   falhar. O encode continua na CPU por impossibilidade técnica: o NVENC não
   codifica JPEG.

---

## O que a telemetria de voo mede — e o que ela não mede

Os brutos da DJI carregam telemetria embutida, mas **não onde o script procurava**:
ela está num stream de dados `djmd` em protobuf, não numa faixa de legenda. Por
isso a primeira rodada de metadados relatou "zero vídeos com telemetria" em 172
arquivos. São, na verdade, **62 voos com telemetria completa** — GPS, altitude
absoluta e relativa, gimbal, ISO, obturador e temperatura de cor, a ~60 amostras
por segundo.

### O que ela resolve: a câmera

Esta é a medida mais útil que saiu da noite, porque o `ESTADO.md` dizia que a
câmera está baixa demais e ninguém sabia qual era a altura certa. Agora sabe-se,
e não por analogia — é o próprio Natan voando **neste** recinto:

| grandeza | mín | q1 | **mediana** | q3 | máx |
|---|---|---|---|---|---|
| altura de voo (m) | 2,6 | 18,2 | **24,0** | 44,7 | 122,3 |
| gimbal pitch (°) | −87,4 | −28,8 | **−18,8** | −12,4 | +22,7 |
| temperatura de cor (K) | 3318 | 4610 | **5206** | 5407 | 8061 |

E a distribuição do ângulo diz mais que a mediana:

| enquadramento | fatia dos quadros |
|---|---|
| nadir (≤ −80°) | **0,7 %** |
| oblíquo (−80° a −20°) | 48,0 % |
| quase horizonte (> −20°) | 51,3 % |

**Ele praticamente não filma de cima.** Metade do material está perto do
horizonte. Isso é a assinatura de percurso, não de mapa — e confirma, por
medida, a decisão do cliente de abandonar o mapa animado 2.5D em favor da cena
3D navegável.

ISO travado em 100 nos 62 voos: material limpo, sem ganho, bom para amostrar cor.

### O que ela NÃO resolve: as cotas dos patamares

Registrado porque a tentativa é óbvia e alguém vai refazê-la. A ideia era:
`AbsoluteAltitude − RelativeAltitude` = cota do ponto de decolagem; com 62 voos
espalhados pelo recinto, sai uma nuvem topográfica e a pendência 2 morre.

**Não funciona.** Dentro de uma sessão de voo, a DJI mantém a referência
barométrica do **primeiro** takeoff — ela não recalibra a cada decolagem. O
resultado: **9 das 10 sessões dão desnível de 0,00 m**, mesmo com 6 a 8 pontos de
decolagem distintos e separados por centenas de metros. O número mede a
calibração do barômetro, não o terreno.

E o dado bruto engana de forma convincente: a amplitude entre todos os voos é de
**60,0 m**, que num recinto de 808 × 454 m seria uma montanha. Ela vem de deriva
de pressão atmosférica entre dias — as cotas se agrupam por data, não por lugar,
e a "amplitude" encolhe conforme a janela de tempo diminui.

**As alturas dos patamares (0 → 3,5 → 7 → 10 m) seguem ESTIMADAS por proporção.**
A pendência 2 continua aberta, e agora se sabe exatamente o que pedir: um voo
**lateral rasante**, com o drone à altura do patamar intermediário e um elemento
de altura conhecida no quadro. Contas em `_triagem\telemetria\cotas-do-terreno.json`.

---

## As escolhas — vencedor e reservas por classe

Placar completo, com o porquê de cada escolha, em
`_triagem\analise\lideres.md`. As reservas **não** são segunda opção: cada uma
entra por trazer uma condição que o vencedor não tem — outro ângulo, outra hora,
outra luz. É assim que se evita o tile visível.

| classe | vencedor | tc | por que |
|---|---|---|---|
| **grama sã** | `DJI_20251128151122_0141_D.MP4` | 00:00:02 | close máximo do acervo: folha legível, mistura de gramíneas, palha e solo entre tufos |
| **grama desgastada** | `IMG_9133.MOV` | 00:00:29 | a borda onde a grama morre e vira pista, em close, do nível do chão, recinto vazio |
| **terra / pista** | `IMG_9133.MOV` | 00:00:05 | a pista batida vazia inteira, com rastro circular de arraste e variação de umidade |
| **lona / tenda** | `DJI_20251128150932_0138_D.MP4` | 00:00:06 | dobra, vinco, translucidez e sujeira na bainha — os três itens da regra 3 num quadro |
| **brita / piso** | `DJI_20251127184025_0104_D.MP4` | 00:00:40 | asfalto → saibro → cascalho solto com o sol a ~5° do horizonte |
| **telha metálica** | `DJI_20251129182345_0168_D.MP4` | 00:00:52 | sol rasante desenhando cada onda; dois estados de idade no mesmo quadro |
| **portal / palco / camarotes** | `IMG_9133.MOV` | 00:00:04 | o palco fixo da bacia, vazio e de dia, em quatro ângulos dentro da janela |
| **arena / patamares** | `DJI_0961_stabilized.mp4` | 00:00:11 | a bacia inteira num quadro, com palco e tendas 5×5 servindo de régua |

**Ressalva de cor:** o `IMG_9133` está com o verde 5–10% mais ácido que os outros
dois iPhone. Dessaturar antes de amostrar cor de grama.

### Duas correções feitas conferindo o quadro extraído

A escolha de **grama sã** foi revista depois de olhar as provas em resolução
nativa, e vale registrar porque muda o que se pode fazer com o material:

- O vencedor indicado (`DJI_20251128151122_0141_D` 00:00:02) foi descrito como
  "close máximo, folha individual legível". **Não é.** É um aéreo de evento com
  multidão, e a grama aparece coberta de gente, cones e sombra de corpo. Usar
  esse quadro como albedo assaria pessoas dentro da textura. A reserva 1
  (`0137_D`) tem o mesmo problema, com mais área limpa.
- **O melhor material de grama do acervo é `1 (4)` 00:00:02** — grama próxima em
  sol rasante de fim de tarde, com a luz lateral entregando altura de tufo e
  irregularidade de corte, a pista de terra com rastro de arraste ao lado, a
  transição entre as duas, o palco fixo da bacia ao fundo **e uma pessoa em pé
  no canto**, dando escala. Um quadro que resolve quatro classes.

**A consequência prática:** não existe, em 173 vídeos, um close de grama rente
ao chão. A textura de grama vai ter que vir de biblioteca CC0 (Poly Haven,
ambientCG) e ser **calibrada** pela cor, pelo padrão de mancha e pela proporção
de desgaste medidos nas provas aéreas — não copiada delas. Isso é diferente do
que vale para brita, telha e lona, onde o footage entrega o material de perto.

**Oportunidade que caiu no colo:** a pessoa em pé no `1 (4)` 00:00:02 está no
mesmo quadro que o palco fixo. Um adulto dá ~1,70 m. Não é medida de trena — a
pendência 3 continua aberta — mas é a primeira referência de escala vertical do
acervo, e é muito melhor que proporção sobre planta. Vale cotar o pé-direito do
palco contra ela antes do render.

### As provas em resolução nativa

Cada escolha virou uma **rajada** de quadros na resolução da câmera, sem rótulo
queimado, em `_triagem\provas-materiais\<classe>\`. Rajada e não quadro único
por três motivos, e os três pesam: o quadro exato pode estar em movimento e o
vizinho a meio segundo está parado; material sem tile visível precisa de mais de
uma amostra da mesma superfície, senão o que se constrói é o mesmo tile de novo;
e ângulos ligeiramente diferentes da mesma superfície são o que permite montar a
variação que a regra 3 pede.

Janela de 8 s para textura, 12 s para modelagem, passo de 0,5 s. Nome do arquivo
carrega classe, vídeo e timecode. Para refazer:

```bash
python "E:\Projetos todos\Mapa - agroshow\Comandos\extrair_provas.py" --lista "E:\Projetos todos\Mapa - agroshow\Brutos Expo\_triagem\analise\provas.json" --pasta "E:\Projetos todos\Mapa - agroshow\Brutos Expo"
```

---

## Portal, palco e camarotes — referência de modelagem

### Portal — não está no footage, e a foto estava fora do repositório

Os 12 relatórios de triagem convergem: **o portal celeiro não aparece em nenhum
dos 173 vídeos.** O que aparece é o pórtico atual do parque (metálico, azul, com
esferas e telão — `DJI_20251127211702_0126_D` 00:00:16), que é outra coisa.

A referência do portal é a foto que o cliente mandou em 12/08, descrita em
`reference/PORTAL-referencia.md` — mas o arquivo em si nunca foi para o
repositório e não estava citado por caminho em lugar nenhum:

> `E:\Projetos todos\Mapa - agroshow\WhatsApp Image 2026-08-12 at 13.15.32.jpeg`

Conferida contra a descrição do `PORTAL-referencia.md`: bate item por item —
fachada de tábua vertical marrom-tabaco, frontão com treliça em V invertido,
portões de correr com travessas em X, letreiro **PARQUE DE EXPOSIÇÕES** /
★★★ DE DOIS VIZINHOS - PR ★★★, luminárias de ferro preto, janelas brancas
quadriculadas, alas laterais mais baixas com telha ondulada, barris de madeira,
três vãos com portões de ferro, piso de saibro escuro, mastro azul à esquerda.

Vale lembrar a ressalva do áudio: *"vamos dar um jeito dele, fazer mais barato."*
Na dúvida entre duas leituras de um detalhe, a mais econômica.

**Achado colateral, e é bom:** o vocabulário construtivo do celeiro já existe no
recinto, em obra real — `DJI_20251127211745_0128_D` 00:00:00 mostra duas casas de
madeira com tabuado vertical, telha cerâmica e varanda. É a leitura econômica do
mesmo repertório, e serve tanto ao portal quanto à Fazendinha.

### Camarotes — a restrição 1 está confirmada por imagem

`DJI_20251128224305_0163_D` 00:00:09 mostra o camarote inteiro e legível: deck de
madeira elevado, módulos separados por gradil branco de tubo, bar de tenda
dentro do setor. **Não há arquibancada em nenhum quadro do recinto inteiro** — em
todos os eventos filmados, o público senta no talude gramado. A restrição do
cliente não é só uma ordem: é como o parque funciona.

### Palco

`DJI_20251127184447_0110_D` 00:00:02 — montado e **vazio**, que é o que serve para
modelar: treliça, cobertura tensionada, telões, deck de madeira, grades formando
os setores laterais. `DJI_20251126232103_0102_D` 00:00:03 dá o ângulo frontal com
os corredores cercados que já desenham a lógica Lado A / Lado B.

---

## Luz — o que o footage sustenta

O material se parte em três blocos, e só dois servem para material:

- **Sol a pino** (26/11, 11:57–12:07): céu azul com cumulus, sombra curta e dura.
  Achata o talude e some com o microrrelevo. Se o render for de meio-dia, que
  seja com cumulus espalhado — nunca céu limpo.
- **Golden hour** (27 a 29/11, 18:23–19:00): sol a poucos graus do horizonte,
  haze, sombras longuíssimas. **É onde está o melhor material de textura**, porque
  a luz rasante desenha o grão da brita, a onda da telha e o relevo da terra
  batida. É também a luz que o LOOK LOCK do projeto pede.
- **Noturno**: quase metade do footage. Excelente para palco em operação,
  povoamento e lona iluminada; inútil para PBR.

Temperatura de cor medida: mediana 5206 K, com os extremos em 3318 K (golden
hour) e 8061 K (sombra aberta e nublado).

**Recomendação:** HDRI de fim de tarde do Poly Haven, com o sol a oeste/noroeste
baixo — é o que casa com a maior parte do material que vai virar textura.

---

## O que o footage NÃO tem — isto é pedido ao cliente

Levantado pelos 12 relatórios, e nenhum deles achou o contrário:

1. **Portal celeiro** — só existe na foto. Nenhum vídeo.
2. **Perfil lateral da arena com cota conferível** — a pendência 2, agora com o
   pedido preciso: voo lateral rasante, à altura do patamar intermediário, com
   elemento de altura conhecida no quadro.
3. **Arena de rodeio em uso** — pista com animal, brete, porteira. O que existe é
   a pista vazia e a Arena de Eventos gramada.
4. **Telha oxidada** — todas as coberturas do recinto são trapezoidais brancas ou
   galvanizadas novas. Se a pegada pedir telha envelhecida, ela não desce do
   material real e vira proposta.
5. **Gente em plano próximo, de dia, com escala conferível** — o povoamento bom
   está à noite; de dia o parque aparece vazio ou distante.
6. **Ortomosaico nadir dedicado** — só 0,7 % dos quadros são nadir. Para retraçar
   a planta com precisão, continua faltando um voo nadir com 70–80 % de
   sobreposição e exposição travada.

---

## O que não é certeza

Registrado como incerteza, e não arbitrado — posição de área e nomenclatura são
material de venda de espaço físico:

- **Se a bacia concêntrica que aparece no footage é a arena de rodeio.** Vários
  relatórios apontaram o mesmo oval de pista de terra com miolo gramado como
  candidato mais provável, e nenhum viu placa ou elemento que confirme. Pode ser
  a arena, pode ser o campo de shows.
- **Se todos os clipes `DJI_09xx` são deste recinto.** Os `1 (N)` e os
  `DJI_2025112x_D` estão confirmados por placa — "Sociedade Rural Vale do
  Iguaçu · Dois Vizinhos/PR", "EXPO VIZINHOS · GADO DE LEITE", "RECINTO DE
  LEILÕES ERVELINO COLETTI". Nos `DJI_09xx` o elo é indireto. **Para textura
  tanto faz; para copiar geometria, confirmar antes.**
- **Se os anéis gramados servem de assento hoje.** Isso encosta na restrição da
  arquibancada e não é decisão de agente.
- **A raia retangular de terra vermelha** vista em vários planos não foi
  identificada.

---

## Material descartado, e por quê

Nada foi apagado — o descarte mora em `_triagem\descartado\`:

- 22 folhas de 13/08 **sem timecode** (drawtext quebrado), já refeitas.
- 1 folha de 0 byte (`DJI_0935_stabilized_2`), regerada.
- `IMG_0706.MOV` — 21,6 s de tela vermelha chapada, gravação acidental. Estava
  numa subpasta cujo nome é uma instrução do cliente ("Fala do drone colocar como
  finalização e anoitecendo depois entra a logo animada"), então **a instrução é
  real mas o vídeo não a cumpre** — vale perguntar qual arquivo deveria estar ali.
- 4 pares de vídeos duplicados por conteúdo idêntico (3,2 GB), mantidos.
