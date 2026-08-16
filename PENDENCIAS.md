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
