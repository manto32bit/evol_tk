import pandas as pd
from subprocess import check_call
from os.path import *
import os
from Bio import SeqIO
from tqdm import tqdm

def run_blast(in_fa,db_path,ofile):
    cmd_template = f'blastp -query {in_fa} -db {db_path} -outfmt 6 -max_hsps 1 -evalue 1e-5 -num_threads 60 > {ofile}'
    check_call(cmd_template,shell=1)
    
def split_out(in_fa,db_files,remained_db):
    tmp_dir = './tmp'
    if not exists(tmp_dir):
        os.makedirs(tmp_dir,exist_ok=1)
    all_ids = [_.id for _ in SeqIO.parse(in_fa,format='fasta')]
    collect_diff_db_identity = {}
    for db_file in db_files:
        db_name = basename(db_file).split('.')[0]
        in_name = basename(in_fa).split('.')[0]
        ofile = join(tmp_dir,f'{in_name}_{db_name}_blast.out')
        if not exists(ofile):
            run_blast(in_fa,db_file,ofile)
        result_df = pd.read_csv(ofile,sep='\t',header=None)
        result_df = result_df.sort_values([10,2],ascending=[True,False])
        # SPECIAL FOR narG
        #result_df = result_df.loc[result_df.iloc[:,1]!= 'CAJ72445',:]
        
        r = result_df.groupby(0).head().groupby(0).mean()
        pid2db_identity = dict(zip(r.index,r.loc[:,3]))
        collect_diff_db_identity[db_name] = pid2db_identity
    
    pid2cloest_db = {}
    for pid in tqdm(all_ids):
        cloest_db = ''
        cloest_db_v = 0
        #not_in_REMAINED_DB = []
        for db_name,identity in collect_diff_db_identity.items():
            this_db_identity = identity.get(pid,0)
            if this_db_identity>=cloest_db_v:
                cloest_db = db_name
                cloest_db_v = this_db_identity
        if cloest_db_v !=  0:
            pid2cloest_db[pid] = (cloest_db,cloest_db_v)
        else:
            pid2cloest_db[pid] = ('',0)
    dropped_ids = [pid for pid,v in pid2cloest_db.items() if v[0] != remained_db]
    return dropped_ids

odir = '/home-user/thliao/project/nitrogen_cycle/nitrification/reference_genomes/manual_remove/'

in_fa = 'nitrification/reference_genomes/align_v3/complete_ko/K00371.fa'
db_files = ['curated_genes/narH.faa',
            'curated_genes/nxrB.faa']
remained_db = 'nxrB'
others_db = [basename(_).replace('.faa','')
             for _ in db_files
             if basename(_).replace('.faa','') != remained_db]
other_db_names = '_'.join(others_db)
ko_str = basename(in_fa).replace('.fa','')
dropped_ids = split_out(in_fa,db_files,remained_db)
print('need to drop %s sequences' % len(dropped_ids))

output_file = join(odir,
                   f'{ko_str}_{other_db_names}_in_{remained_db}.txt')
with open(output_file,'w') as f1:
    f1.write('\n'.join(dropped_ids))

in_fa = 'nitrification/reference_genomes/align_v3/complete_ko/K00370.fa'
db_files = ['curated_genes/narG.faa',
            'curated_genes/nxrA.faa']
remained_db = 'nxrA'
others_db = [basename(_).replace('.faa','')
             for _ in db_files
             if basename(_).replace('.faa','') != remained_db]
dropped_ids = split_out(in_fa,db_files,remained_db)
print('need to drop %s sequences' % len(dropped_ids))
output_file = join(odir,
                   f'{ko_str}_{other_db_names}_in_{remained_db}.txt')
with open(output_file,'w') as f1:
    f1.write('\n'.join(dropped_ids))
