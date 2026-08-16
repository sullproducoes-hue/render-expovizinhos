# PENDÊNCIAS — o que as quatro fontes não responderam

Regra da Pergunta (`NOITE-3-QUADROS.md`): dúvida se resolve consultando
`DECISOES.md` e os deltas → contratos → documentos do projeto → sessões
anteriores. Resolvida, vira **precedente aplicado** em `DECISOES.md`.
**Só chega aqui o que as quatro fontes deixaram mudo.**

Cada item traz o que foi escolhido provisoriamente para não parar, marcado
`PROVISORIO`. O Natan revê de manhã, e o que ele disser vira o precedente.

---

## P01 · O portal não é coberto por nenhuma nuvem de pontos — câmera do Q1

**A dúvida.** A Fase A.4 manda travar a câmera numa imagem que **entrou na
reconstrução**, porque aí a pose já existe resolvida por bundle adjustment. O Q1
é o portal — e o portal **não aparece em nenhum dos 173 vídeos** do acervo
(`docs/MATERIAIS-referencia.md`, os 12 relatórios de triagem convergem). Também
não tem telemetria, porque não tem voo. O fallback escrito (cair na telemetria
dos 62 voos) **não se aplica**: não há voo do portal para cair.

**O que ela trava.** A câmera do Q1 inteiro.

**As saídas possíveis.**
1. casar a câmera 3D com a perspectiva da **foto do cliente** — a única imagem
   que existe do portal. Frontal, sol alto, sem vista lateral;
2. escolher uma câmera livre de aproximação baixa, sem match-frame, e apresentar
   o Q1 sozinho em vez de `real | 3D`;
3. trocar o Q1 por um quadro coberto pela nuvem `montagem`.

**PROVISORIO — escolhi a 1.** Motivo: a Lei 3 diz que a entrega é `real | 3D`
lado a lado, e a foto do cliente é o "real" que existe. E o portal ainda **não
foi construído no parque** — a foto é o conceito que ele mandou, não um registro.
Então `real | 3D` aqui lê como *"você pediu isso; aqui está, dentro do parque"*,
que é mais forte que match-frame de um prédio existente. A pose sai de casamento
de perspectiva contra a foto, e fica registrado que **esta câmera não tem
qualidade de bundle adjustment** — é a única das três assim.

---

## P02 · `askUserQuestionTimeout` não existe na configuração

**A dúvida.** O adendo manda confirmar `askUserQuestionTimeout` ativo e modo de
permissão sem confirmação de escrita.

**O que ela trava.** Nada — a noite roda.

**O disco.** A chave **não existe** em nenhum dos settings
(`C:\Users\natan\.claude\settings.json`,
`E:\I.A Edit\.claude\settings.local.json`). O modo de permissão da sessão é
definido no lançamento e não se lê nem se muda por dentro.

**PROVISORIO.** O que resolve na prática foi feito: o allow-list de
`E:\I.A Edit\.claude\settings.local.json` foi ampliado para Blender, Python,
COLMAP, ffmpeg e escrita em `render-expovizinhos/**` e `F:`. O teto de 600.000 ms
do Bash foi contornado pondo **todo render em background**, que não tem esse
limite.

---

## P03 · `_cilindro` aceita `eixo="X"` e ignora, em silêncio

**A dúvida.** Nenhuma — é defeito conhecido, e o conserto é de uma linha.

**O que ela trava.** Nada agora. O Q3 foi montado com `_tubo_entre`, que recebe
os dois pontos explícitos.

**Por que não consertei.** `heroi_portal.py:_cilindro` é **compartilhado** com o
`heroi_portal` e o `heroi_arena` — os dois quadros que o Natan acabou de aprovar
(D089). Mexer num helper compartilhado depois da aprovação muda os dois pelas
costas, e a regra da casa é que aprovação dele não se altera sem ele saber.

**O conserto, quando ele autorizar:** `else: raise ValueError(f"eixo {eixo}")`.
Parâmetro que o helper não entende tem que **abortar**, nunca cair no default.
Detalhe em **D090**.

---

## P04 · O rumo do Pavilhão 1 não foi aplicado, e isso é escolha declarada

**A dúvida.** O footprint de `PAVILHÃO 1` traz `rumo_graus: 90,0` **com
`rumo_confiavel: false`** e `preenchimento 0,706`.

**O que ela trava.** Só o Q3, e só na luz: o rumo decide de que lado o sol entra
pela boca. Não muda geometria nenhuma.

**PROVISÓRIO — cena montada em eixos locais** (comprimento em Y, boca em −Y,
lado aberto em −X). Motivo: aplicar um rumo em que a própria planta declara não
confiar trocaria a luz do quadro por um número que não se sustenta. Quando o
Natan mandar o print da orientação do Pavilhão 1, ou quando a nuvem `montagem`
cobrir esse prédio, o rumo entra e o quadro se refaz — é um argumento de linha
de comando, não uma remodelagem.

---

## P05 · Asfalto não tem cor medida no acervo

**A dúvida.** O piso do Pavilhão 1 na foto é **asfalto escuro**. Em
`data/materiais-medidos.json` não existe asfalto — o mais próximo é `MAT_SAIBRO`
(brita da área de máquinas), que é marrom.

**O que ela trava.** A cor do chão do Q3, e do chão de qualquer plano que passe
por área pavimentada.

**PROVISÓRIO — usei `MAT_SAIBRO` medido**, e o chão puxa para o marrom. A
alternativa honesta é medir o asfalto num quadro do footage pelo mesmo método do
`medir_materiais.py` — é meia hora de máquina, não é pesquisa. Fica esperando a
decisão dele sobre se vale.
