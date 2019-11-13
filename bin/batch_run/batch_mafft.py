import sys
from os.path import *
import os
#sys.path.insert(0,dirname(dirname(dirname(dirname(__file__)))))
from subprocess import check_call
import click
from glob import glob
from tqdm import tqdm
import multiprocessing as mp

command_template = 'mafft --maxiterate 1000 --genafpair --thread -1 {in_file} > {o_file} '
def run(args):
    unit_run(*args)
    
def unit_run(in_file,o_file):
    check_call(command_template.format(in_file=in_file,
                                       o_file=o_file), 
               shell=1)
    
def main(in_dir,odir,num_parellel,suffix='',new_suffix='',**kwarg):
    suffix = suffix.strip('.')
    new_suffix = new_suffix.strip('.')
    if not exists(odir):
        os.makedirs(odir)
    if suffix:
        suffix = '.'+suffix
    file_list = glob(join(in_dir,f'*{suffix}'))
    tqdm.write("start to process %s file with '%s' as suffix" % (len(file_list),suffix))
    params = []
    for in_file in tqdm(file_list):
        if new_suffix and suffix:
            ofile = join(odir,
                         basename(in_file).replace(suffix,
                                                   '.'+new_suffix))
        else:
            ofile = join(odir,
                         basename(in_file))
        params.append((in_file,ofile))
    with mp.Pool(processes=num_parellel) as tp:
        list(tp.imap(run,tqdm(params)))

@click.command()
@click.option('-i','indir')
@click.option('-o','odir')
@click.option('-s','suffix',default='faa')
@click.option('-ns','new_suffix',default='aln')
@click.option('-np','num_parellel',default=10)
def cli(indir,odir,num_parellel,suffix,new_suffix):
    main(indir,odir,num_parellel,suffix,new_suffix)



if __name__ == "__main__":
    cli()