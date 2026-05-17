import nbformat
from nbformat.v4 import new_markdown_cell, new_code_cell

NB_PATH = 'Relatório.ipynb'

md_text = '''
**Experimentos reprodutíveis — parâmetros e artefactos**

Os gráficos abaixo foram gerados automaticamente e os parâmetros usados estão apresentados na célula seguinte. As imagens originais do relatório foram mantidas; estas células adicionam transparência (seed, N_GAMES, ITERS) e incluem as figuras reais gravadas em `outputs/`.
'''

code_text = '''
# Parâmetros de experimentos (documentados)
seed = 42
N_GAMES = 50
ITERS = 250
print(f'seed={seed}, N_GAMES={N_GAMES}, ITERS={ITERS}')

# Mostrar imagens geradas em outputs/
from IPython.display import Image, display
print('\nAcurácias (geradas):')
display(Image('outputs/accuracies.png'))
print('\nWin-rates (geradas):')
display(Image('outputs/winrates.png'))
'''

nb = nbformat.read(NB_PATH, as_version=4)
# append cells at the end
nb.cells.append(new_markdown_cell(md_text))
nb.cells.append(new_code_cell(code_text))

nbformat.write(nb, NB_PATH)
print('Relatório atualizado: células adicionadas ao final do notebook.')
