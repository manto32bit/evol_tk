import pandas as pd
from os.path import *
import os
from tqdm import tqdm
from subprocess import check_call
import multiprocessing as mp
from glob import glob


dependent_params = '/home-user/thliao/data/plancto/bayesTraits_genes_test/depend_params.txt'
independent_params = '/home-user/thliao/data/plancto/bayesTraits_genes_test/independ_params.txt'
exe_path = "/home-user/thliao/software/BayesTraitsV3.0.2-Linux/BayesTraitsV3"

gene_presence_tab = "./protein_annotations/kegg_diamond.crosstab"
basic_habitat_txt = "./bayesTraits_test/m2nm.txt"
intree = "./bayesTraits_test/test.trees"
odir = './bayesTraits_genes_test'

# read habitat metadata
habitat_text = open(basic_habitat_txt).read()
all_gids = [_.split('\t')[0] for _ in habitat_text.split('\n')]
# read gene table 
gid2habitat = dict([_.split('\t') for _ in habitat_text.split('\n')])
genes_df = pd.read_csv(gene_presence_tab,sep='\t',index_col=0)

# habitat mapping table...
habitat_mapping_dict = {"M":'1',
                        "N":'0',
                        "NM":'-'}

tqdm.write("Iterating genes to generating metadata.txt for each gene")
for ko in tqdm(genes_df.columns):
    gid2gene = genes_df.loc[:,ko].to_dict()
    g_dir = join(odir,'each_gene',ko.split(':')[-1])
    if not exists(g_dir):
        os.makedirs(g_dir)
    metadata_txt = []
    for gid,v in gid2habitat.items():
        hv = habitat_mapping_dict[v]
        gene_v = str(int(gid2gene[gid]))
        metadata_txt.append(f"{gid}\t{hv}\t{gene_v}")
    with open(join(g_dir,'metadata.txt'),'w') as f1:
        f1.write('\n'.join(metadata_txt))
        
cmds = []
for ko in tqdm(genes_df.columns):
    g_dir = join(odir,'each_gene',ko.split(':')[-1])
    mtext = join(g_dir,'metadata.txt')
    os.system(f"cp {mtext} {mtext.replace('.txt','_D.txt')}" )
    os.system(f"cp {mtext} {mtext.replace('.txt','_ID.txt')}" )
    if not exists():
        
    cmds.append(f"{exe_path} {intree} {mtext.replace('.txt','_D.txt')} < {dependent_params}")
    cmds.append(f"{exe_path} {intree} {mtext.replace('.txt','_ID.txt')} < {independent_params}")        


with mp.Pool(processes=50) as tp:
    r = list(tqdm(tp.imap(run,cmds),total=len(cmds)))     
        