@echo off
REM Lanca o render do filme inteiro, destacado de qualquer sessao de shell.
REM
REM Por que existe. Em 15/08 o render foi lancado direto de um shell e morreu
REM aos 36 minutos, no quadro 238 de 5.280: quem foi encerrado foi o processo
REM PAI, e o Blender caiu junto. Ficou ate um blender.exe zumbi vivo e mudo,
REM que enganou o vigia. Um .bat chamado por `start` nao tem esse laco -- ele
REM vira processo do Windows e sobrevive a quem o chamou.
REM
REM render_shots.py PULA quadro que ja existe, entao rodar isto de novo nunca
REM refaz trabalho: retomar custa zero.
REM
REM   cmd /c start "" /MIN cmd /c scripts\render_agroshow.bat

cd /d "E:\I.A Edit\render-expovizinhos"
"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background ^
    --python scripts\render_shots.py -- ^
    --blend out\cena.blend ^
    --saida "F:/render-agroshow/final" >> out\render-final.log 2>&1
