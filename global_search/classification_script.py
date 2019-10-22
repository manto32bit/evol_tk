import pandas as pd
from tqdm import tqdm

# classifiy_word_table = {'MAGs':['metageno'],
                        
#                         }

infile = './nr_retrieve_hao/manual_annotated_biosample.csv'

ori_df = pd.read_csv(infile,index_col=0)
ori_df.loc[:,'classification'] = ''
ori_df.loc[:,'habitat'] = ''

for _,row in tqdm(ori_df.iterrows(),total=ori_df.shape[0]):
    row_text = ';'.join(map(str,row.values))
    if 'metageno' in row_text:
        ori_df.loc[_,'classification'] = 'MAGs'
    if 'soil' in row_text:
        ori_df.loc[_,'habitat'] = 'terrestrial'
    if 'sea' in row_text:
        ori_df.loc[_,'habitat'] = 'marine'
    if 'wastewater' in row_text or 'activated sludge' in row_text:
        ori_df.loc[_,'habitat'] = 'waste water'
    if 'groundwater' in row_text:
        ori_df.loc[_,'habitat'] = 'ground water'
    if 'bioreactor' in row_text:
        ori_df.loc[_,'habitat'] = 'bioreactor'
    if 'Whole genome' in row_text or 'type strain' in row_text:
        ori_df.loc[_,'classification'] = 'isolate'
    if 'single cell' in row_text:
        ori_df.loc[_,'classification'] = 'SAGs'
    if not pd.isna(row['attribute:host']) and str(row['attribute:host']) != 'not applicable':
        ori_df.loc[_,'habitat'] = 'host associated'
ori_df.to_csv('./nr_retrieve_hao/test.csv',index=1)