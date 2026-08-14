# Extração de quadros do footage

`scripts/extrair_quadros.py` tira quadros de referência dos vídeos das edições
anteriores e monta folhas de contato para escolher.

**Rode na sua máquina.** O footage está local, o container remoto não enxerga
esses arquivos.

## Instalação

Precisa de **ffmpeg** e **ffprobe** no PATH — https://ffmpeg.org/download.html.
No Windows, baixe o build do gyan.dev, descompacte e ponha a pasta `bin` no PATH.

Opcional, mas recomendado:

```bash
pip install pillow numpy
```

Sem eles o script funciona: as folhas de contato saem pelo ffmpeg, só que sem a
etiqueta de timecode embaixo de cada miniatura, e a opção `--nitidez` fica
indisponível.

## Uso normal

```bash
python scripts/extrair_quadros.py --pasta "E:/AGROSHOW/footage"
```

Ele lista os vídeos da pasta com a duração de cada um:

```
  [ 1]  00:04:12  agroshow 2024 abertura.mp4
  [ 2]  00:02:38  rodeio_2025.mov
  [ 3]  00:06:55  drone parque.mp4
```

Você escolhe por número — `1,3`, ou um intervalo `1-3`, ou `todos` — e ele
pergunta a quantidade de quadros **de cada vídeo**, um por um. Enter aceita 30.

Vídeo longo pede mais: para um percurso de 6 minutos, 30 quadros dá um a cada
12 segundos, o que pula área inteira do parque. Regra prática: **um quadro a
cada 4 a 6 segundos** de footage.

## Uso direto, sem perguntas

```bash
python scripts/extrair_quadros.py --videos abertura.mp4 rodeio.mov --quadros 60 40
```

Um número só vale para todos os vídeos; vários, um por vídeo, na mesma ordem.

## Opções

| Opção | Efeito |
|---|---|
| `--saida PASTA` | Onde gravar os quadros. Padrão: `extracao` |
| `--folhas PASTA` | Folhas de contato em outro lugar — inclusive outro HD |
| `--png` | PNG em vez de JPEG. Arquivo grande, sem perda |
| `--qualidade N` | Qualidade JPEG, 2 = melhor (padrão), 31 = pior |
| `--nitidez` | Testa 3 instantes por quadro e guarda o menos borrado |
| `--sem-folhas` | Só os quadros, sem folha de contato |
| `--sem-pausa` | Não espera Enter no final (para rodar dentro de outro script) |

### Folhas em outro HD

```bash
python scripts/extrair_quadros.py --pasta "E:/AGROSHOW/footage" ^
    --saida "E:/AGROSHOW/extracao" --folhas "D:/AGROSHOW/folhas"
```

Os quadros ficam no `--saida`, as folhas vão para o `--folhas`, cada vídeo na sua
subpasta com o nome dele. O `INDICE.md` fica junto dos quadros e registra os dois
caminhos completos, então você acha as folhas depois mesmo tendo separado.

As duas pastas são criadas **antes** de começar a extrair. Se o HD das folhas não
estiver conectado, o script para na hora com a mensagem — não depois de meia hora
extraindo.

### Sobre `--nitidez`

Footage de drone e de câmera na mão entrega muito quadro com motion blur, e um
quadro borrado não serve como referência visual. Com a opção ligada, o script
extrai três candidatos em volta de cada instante (−0,4s, 0, +0,4s) e guarda o de
maior variância do laplaciano — o mais definido dos três.

Custa três vezes mais tempo. Vale para o footage de drone e de percurso; não
vale para material estático em tripé.

## O que sai

```
extracao/
  agroshow 2024 abertura/
    quadros/   q001_00-00-04.jpg
               q002_00-00-12.jpg
               ...
    folhas/    contato-01.jpg      (grade 6 × 5, 30 quadros por folha)
               contato-02.jpg
  rodeio_2025/
    quadros/
    folhas/
  INDICE.md
```

O timecode está **no nome do arquivo**. Achou um quadro bom na folha de contato,
o nome te diz o minuto exato para voltar no vídeo e cortar o trecho na edição.

Os quadros são distribuídos por igual ao longo do vídeo, com uma folga de 2% nas
pontas — fade de entrada e de saída costumam ser preto, e não vale gastar quadro
com eles.

## Se a janela fechar sozinha

O console do Windows fecha assim que o script termina — inclusive quando termina
com erro. Por isso o script agora **espera Enter no final**, dê certo ou dê
errado. Se aparecer um traceback, ele fica na tela para você copiar.

Se mesmo assim fechar rápido demais, abra o Prompt de Comando e rode de lá em vez
de dois cliques:

```
cd /d E:\AGROSHOW
python caminho\para\extrair_quadros.py --pasta "E:\AGROSHOW\footage"
```

Erro de ffmpeg em quadro individual também não é mais silencioso: o script conta
quantos falharam e mostra o que o ffmpeg reclamou. Se os três primeiros falharem
seguidos, ele para em vez de tentar as outras dezenas à toa — quase sempre é
codec sem suporte, arquivo corrompido ou caminho de rede que caiu.

## Para que serve o INDICE.md

Ele lista todos os quadros com timecode e uma coluna **Bloco** vazia. Preencha
com o número do bloco de `docs/prompts-higgsfield.md` que aquele quadro atende.

Esse é o ponto da extração: **quadro real vale mais que geração**. Onde o footage
antigo tiver o plano, ele entra no lugar da imagem de IA — sai de graça, é o
parque de verdade e não corre risco de o modelo inventar arquibancada na arena.
O que sobrar sem footage é a lista real do que precisa ser gerado no Higgsfield.
