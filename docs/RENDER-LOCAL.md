# Como rodar o render na sua máquina

O render final **não sai do ambiente remoto**: lá não há placa de vídeo. Cycles
em CPU leva de 2 a 4 minutos por quadro em 2760 × 1380, e são 4440 quadros —
entre 6 e 12 dias. Com uma GPU e o EEVEE, o mesmo filme fecha em cerca de uma
hora.

Tudo abaixo roda na sua máquina, uma vez só.

---

## 1. O que instalar

| Programa | Para quê | Onde |
|---|---|---|
| **Blender 4.2 ou mais novo** | monta e renderiza a cena | blender.org/download |
| **Python 3.10+** | roda os scripts | python.org (no macOS e Linux já vem) |
| **ffmpeg** | gera o `.mov` e os `.mp4` | ffmpeg.org/download |
| **Git** | baixa o projeto | git-scm.com |

No Blender, confira em **Edit → Preferences → System** se o *Cycles Render
Device* está em CUDA, OptiX (placas NVIDIA) ou HIP (AMD). Se estiver em CPU, o
render vai demorar o mesmo tanto que no servidor.

## 2. Baixar o projeto

```bash
git clone https://github.com/sullproducoes-hue/render-expovizinhos.git
cd render-expovizinhos
git checkout claude/video-mapa-3d-assembly-4hcbty
pip install pymupdf pillow numpy
```

## 3. Montar a cena

Este passo não precisa de GPU e leva segundos:

```bash
blender --background --python scripts/build_scene.py -- --out cena.blend
```

No **Windows**, se o comando `blender` não for reconhecido, use o caminho
inteiro:

```
"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe" --background --python scripts/build_scene.py -- --out cena.blend
```

## 4. Conferir antes de gastar horas

```bash
python3 scripts/overlay_check.py
```

Abra `docs/conferencia-planta.png`. É a cena desenhada por cima da planta
oficial: se algo estiver fora do lugar, aparece aqui, não depois de uma noite
de render.

## 5. Renderizar

**Caminho fácil, pela interface:** abra `cena.blend` no Blender, confira o
enquadramento no visor da câmera (tecla `0` do teclado numérico), escolha
*Render → Render Animation* e deixe rodando. Os quadros saem em PNG.

**Caminho por linha de comando**, que já faz tudo e ainda codifica os arquivos
de entrega:

```bash
bash scripts/render_final.sh
```

No Windows isso pede **Git Bash** (vem com o Git) ou o **WSL**. Se preferir não
mexer com isso, use o caminho pela interface e depois rode só os três comandos
de `ffmpeg` que estão no fim do `render_final.sh`.

Para testar antes de soltar o filme inteiro, renderize dez segundos:

```bash
bash scripts/render_final.sh 1 300
```

## 6. O que entregar

Três arquivos, sempre os três:

- `AGROSHOW2026_percurso_2760x1380.mov` — ProRes 422 HQ, o master
- `AGROSHOW2026_percurso_2760x1380.mp4` — H.264, para reprodução
- `AGROSHOW2026_percurso_1380x690.mp4` — reserva leve

Mais a **cartela de teste de 10 s** com marcas de canto e a caixa de 90 %
(2484 × 1242) desenhada, para o operador conferir o recorte antes de rodar o
filme. Nunca embuta tarja preta no arquivo: tarja embutida não se desfaz, e num
processador em modo preencher ela estica junto com a imagem.

---

## Se der errado

**"blender: command not found"** — o Blender não está no PATH. Use o caminho
completo do executável, como no passo 3.

**O render sai preto ou trava** — placa sem memória para o terreno. Em
*Render Properties → Performance → Memory*, ligue *Persistent Data* e reduza os
*samples* para 64.

**Ficou lento mesmo com placa** — confira se o dispositivo do Cycles está mesmo
na GPU (passo 1) e se a cena está no EEVEE quando você só quer velocidade:
`--motor BLENDER_EEVEE` no passo 3.

**Quer mudar enquadramento de um bloco** — mexa na lista `PERCURSO`, no começo
de `scripts/build_scene.py`. Cada bloco é uma linha com `altura`, `recuo`,
`alvo` e `pausa`. Troque o número, rode o passo 3 de novo e confira com
`--conferencia docs/conferencia/`. Nunca edite o `.blend` à mão: ele é
descartável, o script é a fonte.
