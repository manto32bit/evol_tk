import json
import os
from os.path import join, exists,basename,dirname
from glob import glob
import pandas as pd
from subprocess import check_call
from Bio import SeqIO
import seaborn as sns
from ete3 import Tree
import plotly.express as px



odir = 'json_dump_v2'
indir = 'genome_protein_files_more'
og_tsv = f'./{indir}/OrthoFinder/Results_Oct01/Orthogroups/Orthogroups.tsv'
genome_info = './genome_info_full.xlsx'
MAG_annotate_file = '/home-user/thliao/data/metagenomes/update_0928_nitrification/confirmed_locus2info.tsv'
ref_file = '/home-user/thliao/project/nitrogen_cycle/nitrification/reference_genomes/outgroup and reference.xlsx'

# load all necessary data
with open(join(odir, 'ko2og.json'), 'r') as f1:
    ko2og = json.load(f1)
with open(join(odir, 'manually_blast_r.json'), 'r') as f1:
    manually_blast_r = json.load(f1)
with open(join(odir, 'ko2og2names.json'), 'r') as f1:
    ko2og2names = json.load(f1)

og_df = pd.read_csv(og_tsv, sep='\t', low_memory=False, index_col=0)
def rename(x):
    if pd.isna(x):
        return x
    if ', ' not in x:
        return str(x).split(' ')[0]
    else:
        return ', '.join([str(_).split(' ')[0] for _ in x.split(', ')])
og_df = og_df.applymap(rename)
g_df = pd.read_excel(genome_info, index_col=0)

# name2dirname
name2dirname = {}
for ofile in glob(join(indir,'*.faa')):
    real_ofile = os.path.realpath(ofile)
    name = basename(ofile).replace('.faa','')
    if '/prokka_o/' in real_ofile:
        dir_name = basename(dirname(real_ofile)).replace('.faa','')
        name2dirname[name] = dir_name

# special_annotate_file (out group )
# generate annoating file
def generate_id2org(og_names, ofile):
    all_seq_ids = [_.id for _ in SeqIO.parse(ofile, format='fasta')]
    if isinstance(og_names,str):
        og_names = [og_names]
    id2org = {}
    for og_name in og_names:
        row = og_df.loc[og_name, :]
        for seq_id in all_seq_ids:
            org_ids = row.index[row.fillna('').str.contains(seq_id)]
            if not list(org_ids):
                #print('Error', seq_id, og_name)
                continue
            org_id = org_ids[0]
            id2org[seq_id] = org_id
    return id2org

def get_color_info(each_og, ofile,info_col='type',extra={}):
    id2org = generate_id2org(each_og, ofile)
    colors = px.colors.qualitative.Dark24 + px.colors.qualitative.Light24
    id2info = {}
    for id, org in id2org.items():
        org = name2dirname.get(org,org)
        if org in g_df.index:
            #name = g_df.loc[org, 'genome name']
            id2info[id] = g_df.loc[org,info_col]
        elif info_col == 'phylum/class' and name2dirname.get(org,org) in sname2info:
            id2info[id] = sname2info[org]
    if extra:
        id2info.update(extra)   
    set_v = set(id2info.values())
    num_v = len(set_v)
    cols = colors[:num_v]
    total_info2col = dict(zip(set_v,cols))
    if info_col in color_scheme:
        _info2col = color_scheme[info_col]
        info2col = {k:_info2col[k] for k in set_v if k in _info2col}
        fix_missed = {k:total_info2col[k] for k in set_v if k not in info2col}
        info2col.update(fix_missed)
    else:
        info2col = total_info2col.copy()
    return id2info,info2col

# rename
def to_label(each_og,ofile,odir,ko_name=None):
    template_text = open(
        '/home-user/thliao/template_txt/labels_template.txt').read()
    id2org = generate_id2org(each_og, ofile)
    full_text = template_text[::]
    for id, org in id2org.items():
        if org in g_df.index:
            name = g_df.loc[org, 'genome name']
        else:
            name = id
        full_text += '%s,%s\n' % (id, name)
    if ko_name is not None:
        each_og = ko_name
    with open(join(odir, f'{each_og}_label.txt'), 'w') as f1:
        f1.write(full_text)

# rename the internal node
def renamed_tree(in_tree_file,outfile):
    count = 0
    t = Tree(open(in_tree_file).read())
    for n in t.traverse():
        if not n.name:
            n.name = 'Internal_%s' % count
            count += 1
    t.write(outfile=outfile,format=3)
    return t

color_scheme = {'type':{'NOB': '#e41a1c', 'comammox': '#edc31d', 
                        'AOB': '#bad5b9', 'AOA': '#358f0f'},
                'phylum/class':{'Thaumarchaeota': '#358f0f',
                                'Nitrospirae': '#edc31d',
                                'Gammaproteobacteria': '#78fce0',
                                'Chloroflexi': '#e41a1c',
                                'Betaproteobacteria': '#956cb4',
                                'Alphaproteobacteria': '#8c613c'}

                }

# annotate MAGs lineage
remained_ID = og_df.columns.difference(g_df.index)
MAG_annotate_df = pd.read_csv(MAG_annotate_file,sep='\t',index_col=0)
derep_df = MAG_annotate_df.drop_duplicates('sample name')
filtered_df = derep_df.loc[derep_df.loc[:,'sample name'].isin(remained_ID),:]
phylum_from_metadata_count = filtered_df.groupby('phylum(from metadata)').count().iloc[:,0]
sname2phylum_metadata = dict(zip(MAG_annotate_df.loc[:,'sample name'],MAG_annotate_df.loc[:,'phylum(from metadata)']))
sname2class_metadata = dict(zip(MAG_annotate_df.loc[:,'sample name'],MAG_annotate_df.loc[:,'class(from metadata)']))

sname2phylum_metadata = {k:v for k,v in sname2phylum_metadata.items() if not pd.isna(v)}
sname2info = {k:v if v !='Proteobacteria' else sname2class_metadata[k] for k,v in sname2phylum_metadata.items()}
sname2info = {k:v for k,v in sname2info.items() if not pd.isna(v)}


# data dependent transform
from api_tools.itol_func import *   
def write2colorstrip(id2info,odir,info2color, unique_id,info_name='type',):
    content = to_color_strip(id2info,info2color,info_name=info_name)
    info_name = info_name.replace('/','_')
    with open(join(odir, f'{unique_id}_{info_name}_colorstrip.txt'), 'w') as f1:
        f1.write(content)

def write2colorbranch(id2info,odir,info2color, unique_id,info_name='type',):
    content = to_color_branch(id2info,info2color,dataset_name=info_name)
    info_name = info_name.replace('/','_')
    with open(join(odir, f'{unique_id}_{info_name}_colorbranch.txt'), 'w') as f1:
        f1.write(content)

def write2colorbranch_clade(id2info,odir,info2color,treefile, unique_id,info_name='type',):
    content = to_color_Clade(id2info,info2color,treefile,info_name)
    info_name = info_name.replace('/','_')
    with open(join(odir, f'{unique_id}_{info_name}_colorbranch_clade.txt'), 'w') as f1:
        f1.write(content)


def write2binary_dataset(ID2infos, odir,info2style, unique_id):
    
    annotate_text = annotate_outgroup(ID2infos,info2style)
    with open(join(odir,f'{unique_id}_marker_outgroup_ref.txt'),'w') as f1:
        f1.write(annotate_text)
        
        
# ref or outgroup seq, additionally add to
ref_df = pd.read_excel(ref_file,index_col=None)
ref_df = ref_df.loc[ref_df.loc[:,'note']!='removed',:] 
def get_add_text(sub_df,used_ids):
    new_ref = []
    t_text = '' 
    id2info = {}
    for _,row in sub_df.iterrows():
        aa_id = row['AA accession']
        gene_name = row['gene name']
        seq = row['seq']
        info = row['phylum/class']
        if aa_id not in used_ids:
            t_text+= f'>{aa_id}_{gene_name}\n{seq}\n'
            
            id2info[f'{aa_id}_{gene_name}'] = info
        else:
            new_ref.append(aa_id)
    return t_text,new_ref,id2info


def get_outgroup_info(sub_df,ref_others=[]):
    ID2infos = {}
    for _,row in sub_df.iterrows():
        aa_id = row['AA accession']
        gene_name = row['gene name']
        name = f'{aa_id}_{gene_name}'
        if row['type'] == 'outgroup':
            ID2infos[name] = ['outgroup']
        else:
            ID2infos[name] = ['reference']
    for rid in ref_others:
        ID2infos[rid] = ['reference']
    info2style = {}
    info2style['outgroup'] = {'status':'0'}
    info2style['reference'] = {'status':'1'}
    return ID2infos,info2style

# necessary for nxr and nar relative
# necessary for hao and hzo 

def refine_some_genes(fa_file,ko_name):
    removed_ids = glob(join('./manual_remove',ko_name+'*'))
    
    if removed_ids:
        removed_ids = open(removed_ids[0]).read().split('\n')
        records = [_ for _ in SeqIO.parse(fa_file,format='fasta')
                   if _.id not in removed_ids]
        with open(fa_file,'w') as f1:
            SeqIO.write(records,f1,format='fasta-2line')
        print('refined ',fa_file)
    else:
        pass
    
import multiprocessing as mp
def process_ko(ko,og_list):
    sub_ref_df = ref_df.loc[ref_df.loc[:,'outgroup/ref for which KO']==ko,:]
    predir = dirname(dirname(og_tsv))

    fa_files = [f'{predir}/Orthogroup_Sequences/{each_og}.fa' for each_og in og_list]
    used_ids = [record.id for fa_file in fa_files for record in SeqIO.parse(fa_file,format='fasta')]
    
    add_text,used_ref_ids,ref_id2info = get_add_text(sub_ref_df,used_ids)
    ID2infos,info2style = get_outgroup_info(sub_ref_df,ref_others=used_ref_ids)
    
    new_file = join(final_odir, ko+'.fa')
    fa_file = ' '.join(fa_files)
    check_call(
        f'cat {fa_file} > {new_file}', shell=1)
    ori_text = open(new_file,'r').read()
    with open(new_file,'w') as f1:
        f1.write(add_text+ori_text)
    refine_some_genes(new_file,ko)
    
    ofile = join(final_odir, ko+'.aln')
    if not exists(ofile):
        check_call(
            f'mafft --anysymbol --thread -1 {new_file} > {ofile}', shell=1)
    if not exists(ofile.replace('.aln','.treefile')):
        #pass
        check_call(f'iqtree -nt 64 -m MFP -redo -mset WAG,LG,JTT,Dayhoff -mrate E,I,G,I+G -mfreq FU -bb 1000 -pre {final_odir}/{ko} -s {ofile}',
                  shell=1)
    #else:
    renamed_tree(ofile.replace('.aln','.treefile'),
                ofile.replace('.aln','.newick'))

    to_label(og_list,ofile,final_odir,ko_name=ko)
    # annotate with type
    id2info,info2col = get_color_info(og_list,ofile,info_col='type')
    write2colorstrip(id2info,final_odir,info2col,unique_id=ko,info_name='type')
    # annotate with phylum/class as a color strip
    id2info,info2col = get_color_info(og_list,ofile,info_col='phylum/class',extra=ref_id2info)
    write2colorstrip(id2info,final_odir,info2col,unique_id=ko,info_name='phylum/class')
    # annotate with tree
    write2colorbranch_clade(id2info,
                            final_odir,
                            info2col,
                            treefile=ofile.replace('.aln','.newick'),
                            unique_id=ko,
                            info_name='branch_color')
    write2binary_dataset(ID2infos,final_odir,info2style,unique_id=ko)

final_odir = join('./align_v2', 'complete_ko')
os.makedirs(final_odir, exist_ok=1)
params_list = []
for ko,og_list in ko2og.items():
    og_list = og_list[::]
    if ko == 'K10944':
        og_list.remove('OG0006386')  # arachaea amoA
        #og_list.append('OG0001887')  # amoA of Heterotrophic nitrification
    #process_ko(ko,og_list)
    params_list.append((ko,og_list))
def run_c(x):
    process_ko(*x)

with mp.Pool(processes=10) as mp:
    mp.map(run_c,params_list)
