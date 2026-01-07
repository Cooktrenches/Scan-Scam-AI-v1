import pandas as pd

df = pd.read_csv('dataset/features.csv')
print(f'\nFEATURES UTILISEES PAR LE ML ({len(df.columns)} au total):')
print('='*80)
for i, col in enumerate(df.columns, 1):
    print(f'{i}. {col}')

print(f'\n{"-"*80}')
print(f'Total samples: {len(df)}')
print(f'RUG samples: {(df["label"]==1).sum() if "label" in df.columns else "N/A"}')
print(f'SAFE samples: {(df["label"]==0).sum() if "label" in df.columns else "N/A"}')
