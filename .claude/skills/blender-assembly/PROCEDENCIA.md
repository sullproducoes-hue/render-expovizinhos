# Procedência — de onde esta skill veio e onde ela manda

**Não é doutrina desta casa.** É skill de terceiro, instalada por ordem do Natan
em 15/08/2026, depois de eu recomendar não instalar e ele mandar instalar.

| | |
|---|---|
| origem | `https://github.com/ProfRino/Blender-MCP-Assembly-Skill` |
| commit | `afad3b1874c838c8058218581b34cae301a133cd` |
| autor | ProfRino |
| conteúdo | markdown puro — **nenhum código executável, nenhum addon, nenhum servidor MCP** |
| escopo | instalada **dentro do `render-expovizinhos`**, não no cofre inteiro. Ela é de Blender, e os outros nove sistemas da casa não têm nada com isso (`CLAUDE.md`: *"nove sistemas convivem aqui e não devem se misturar"*) |

**Os arquivos estão verbatim.** Não editei uma linha do `SKILL.md` — skill de
terceiro se instala como está ou não se instala. O que esta casa pensa dela fica
aqui, ao lado, e não misturado dentro.

---

## Onde ela entra na precedência

O `CLAUDE.md` já fixa a ordem, e ela não se inverte:

```
vetos  →  núcleo e deltas  →  pegada do projeto  →  doutrina do ofício  →  skill
```

E fixa também o que fazer com o tom dela. Esta skill se anuncia como *"always
invoke this skill before writing any Blender geometry code"* — o mesmo padrão
das 25 do HyperFrames, e vale o mesmo: **isso descreve a casa de quem escreveu,
não esta.**

---

## O que dela serve aqui

Uma coisa, e é boa: o **mapa de conexões** — declarar, antes de construir,
quais peças se tocam e com que sobreposição mínima; e `verify_overlap()` para
conferir junta por junta.

Isso preenche um buraco real: este projeto testa **colisão** (o que *não pode*
se encostar, em `afastar_do_medido` e `conferir_estimados.py`) e não testa
**contato** (o que *tem* que se encostar). Até 15/08 não fez falta porque tudo
era caixa solta. Passa a fazer: a concha tem laje sobre porão e cobertura sobre
parede, o prédio redondo terá saia sobre embasamento, as mangueiras têm grade em
série. Peça que não encosta lê como modelo explodido, e nenhum teste daqui
pegaria isso.

---

## O que dela NÃO serve, e por quê

Não é opinião: foi conferido no código antes de instalar.

| regra da skill | por que não se aplica |
|---|---|
| `size=2` em cubo primitivo | **0 usos** de `primitive_cube_add` no projeto. `estruturas._cubo()` põe vértice por vértice em bmesh |
| nunca rotacionar cilindro (Euler falha) | já é bmesh com coordenada explícita, e as 22 rotações do projeto são **só em Z** — o caso em que a ordem XYZ não tem como falhar |
| `transform_apply(scale=True)` dentro do laço | **0 usos** de `transform_apply`; nenhum builder escala objeto |
| compensar encolhimento de subsurf | **0 subsurf** na cena |
| derivar dimensão do vizinho medido | já existe em forma mais forte — a dimensão desce de footprint medido em `data/footprints.json` |

### E duas quebram a cena — estas são veto

**`finalize()` chama `shade_smooth()` em todo objeto.** Em caixa de arquitetura
isso arredonda quina no render. O conserto certo para aresta viva já está
escrito na etapa 5 deste projeto e é **bevel**, não sombreamento suave.

**`audit_all()` exige `rotation = (0,0,0)` em todo objeto.** A cena inteira
depende de rotação em Z — `RUMO_PAVILHOES`, `RUMO_CONCHA`, o giro de cada zona
medida. Esse audit reprovaria todo prédio que está **certo**.

---

## Um erro dentro dela, e ele é o nosso erro de 14/08

O `verify_bounds()` da skill lê `matrix_world` sem chamar `view_layer.update()`
antes. É exatamente a **armadilha 18** deste projeto — a que fez a conferência
concluir que a cena inteira estava dentro do `PAVILHÃO - EQUÍNOS` e afastar 33
objetos em 20 m cada, sem erro nenhum na tela.

**Quem usar `verify_bounds()` daqui tem que chamar `view_layer.update()` antes,
ou ler pegada por conta fechada (`pegada_prevista`).** A skill não avisa.
