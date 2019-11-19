import sys
from os.path import *
import os
# sys.path.insert(0,dirname(dirname(dirname(dirname(__file__)))))
from subprocess import check_call
import click
from glob import glob
from tqdm import tqdm
import multiprocessing as mp

command_template = 'iqtree -nt 20 -m MFP -redo -mset WAG,LG,JTT,Dayhoff -mrate E,I,G,I+G -mfreq FU -wbtl -bb 1000 -pre {ofile} -s {infile}'


def run(args):
    unit_run(*args)


def unit_run(infile, ofile):
    if not exists(dirname(ofile)):
        os.makedirs(dirname(ofile))
    check_call(command_template.format(infile=infile,
                                       ofile=ofile),
               shell=True)


def main(in_dir, odir, num_parellel, suffix='', new_suffix='',force=False):
    suffix = suffix.strip('.')
    new_suffix = new_suffix.strip('.')
    if not exists(odir):
        os.makedirs(odir)
    if suffix:
        suffix = '.' + suffix
    file_list = glob(join(in_dir, f'*{suffix}'))
    tqdm.write("start to process %s file with '%s' as suffix" % (len(file_list), suffix))
    params = []
    for in_file in tqdm(file_list):
        name = basename(in_file).replace(suffix,'')
        if new_suffix and suffix:
            ofile = join(odir,
                         name,
                         basename(in_file).replace(suffix,
                                                   '.'+new_suffix))
        else:
            ofile = join(odir,
                         name,
                         basename(in_file))
        if not exists(ofile) or force:
            params.append((in_file, ofile))
    with mp.Pool(processes=num_parellel) as tp:
        for _ in tp.imap(run, tqdm(params)):
            pass


@click.command()
@click.option('-i', 'indir')
@click.option('-o', 'odir')
@click.option('-s', 'suffix', default='aln')
@click.option('-ns', 'new_suffix', default='iqtree')
@click.option('-f','force',help='overwrite?',default=False,required=False,is_flag=True)
def cli(indir,odir,suffix,new_suffix,force):
    main(indir,odir,suffix,new_suffix,force)


if __name__ == "__main__":
    cli()