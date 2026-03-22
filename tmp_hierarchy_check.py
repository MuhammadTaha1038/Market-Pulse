import pandas as pd
from pathlib import Path

p = Path('Processed_Colors_Output.xlsx')
df = pd.read_excel(p)
print('rows', len(df))
need = ['MESSAGE_ID', 'CUSIP', 'IS_PARENT', 'PARENT_MESSAGE_ID', 'RUN_ID']
print('has_cols', all(c in df.columns for c in need))

parents = df[df['IS_PARENT'] == True][['RUN_ID', 'MESSAGE_ID', 'CUSIP']].copy()
parents['k'] = parents['RUN_ID'].astype(str) + '|' + parents['MESSAGE_ID'].astype(str)
pmap = parents.groupby('k')['CUSIP'].first().to_dict()

children = df[df['IS_PARENT'] != True][['RUN_ID', 'MESSAGE_ID', 'CUSIP', 'PARENT_MESSAGE_ID']].copy()
children['k'] = children['RUN_ID'].astype(str) + '|' + children['PARENT_MESSAGE_ID'].astype(str)
children['parent_cusip'] = children['k'].map(pmap)

bad = children[
    children['parent_cusip'].notna()
    & (
        children['CUSIP'].astype(str).str.strip().str.upper()
        != children['parent_cusip'].astype(str).str.strip().str.upper()
    )
]

print('cross_cusip_child_links', len(bad))
if len(bad) > 0:
    print(bad[['RUN_ID', 'MESSAGE_ID', 'CUSIP', 'PARENT_MESSAGE_ID', 'parent_cusip']].head(30).to_string(index=False))
