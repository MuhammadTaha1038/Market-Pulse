import pandas as pd
from pathlib import Path
p = Path('Processed_Colors_Output.xlsx')
df = pd.read_excel(p)
print('rows', len(df))
need = ['MESSAGE_ID','CUSIP','IS_PARENT','PARENT_MESSAGE_ID','RUN_ID']
print('has_cols', all(c in df.columns for c in need))
parents = df[df['IS_PARENT'] == True][['RUN_ID','MESSAGE_ID','CUSIP']].copy()
parents['k'] = parents['RUN_ID'].astype(str) + '|' + parents['MESSAGE_ID'].astype(str)
pmap = parents.groupby('k')['CUSIP'].first().to_dict()
ch = df[df['IS_PARENT'] != True][['RUN_ID','MESSAGE_ID','CUSIP','PARENT_MESSAGE_ID']].copy()
ch['k'] = ch['RUN_ID'].astype(str) + '|' + ch['PARENT_MESSAGE_ID'].astype(str)
ch['parent_cusip'] = ch['k'].map(pmap)
bad = ch[ch['parent_cusip'].notna() & (ch['CUSIP'].astype(str).str.strip().str.upper() != ch['parent_cusip'].astype(str).str.strip().str.upper())]
print('cross_cusip_child_links', len(bad))
print(bad[['RUN_ID','MESSAGE_ID','CUSIP','PARENT_MESSAGE_ID','parent_cusip']].head(20).to_string(index=False))
