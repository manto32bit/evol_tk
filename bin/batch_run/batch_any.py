"""
Advanced script for who wants to modify or manipulate the batch_run script
"""

import multiprocessing as mp
import os
from glob import glob
from os.path import *
from subprocess import check_call

import click
from tqdm import tqdm

command_template = 'mafft --maxiterate 1000 --genafpair --thread -1 {infile} > {ofile}'


def run(cmd):
    check_call(cmd,
               shell=True)


def main(indir, odir, num_parellel, suffix='', new_suffix='', force=False, cmd=command_template, test=False):
    suffix = suffix.strip('.')
    new_suffix = new_suffix.strip('.')
    odir = abspath(odir)
    if not exists(odir):
        os.makedirs(odir)
    if suffix:
        suffix = '.' + suffix
    file_list = glob(join(indir, f'*{suffix}'))
    if not file_list:
        exit(f"empty files, please check your suffix ({indir}/{suffix}) ")
    tqdm.write("start to process %s file with '%s' as suffix" % (len(file_list), suffix))
    params = []
    for infile in tqdm(file_list):
        if new_suffix and suffix:
            ofile = join(odir,
                         basename(infile).replace(suffix,
                                                  '.' + new_suffix))
        else:
            ofile = join(odir,
                         basename(infile))
        if not exists(ofile) or force:
            filled_cmd = cmd.format(infile=infile,
                                    ofile=ofile)
            params.append(filled_cmd)
    if test:
        print(params)
        return
    with mp.Pool(processes=num_parellel) as tp:
        r = list(tqdm(tp.imap(run, params), total=len(params)))


@click.command(
    help="This script accept input directory(-i) which contains files with suffix(-s) and output directory(-o) which will stodge result with its name and new suffix (-ns). It could auto parellel your command into (-np) times. ")
@click.option('-i', 'indir', help="input directory for iterations. ")
@click.option('-o', 'odir', help="ouput directory for stodge the output files")
@click.option('-s', 'suffix', default='', help="suffix of input files needed to be iterated within the indir,default is empty")
@click.option('-ns', 'new_suffix', default='', help="new suffix of output files, default is empty")
@click.option('-np', 'num_parellel', default=10, help="num of processes could be parellel.. default is 10")
@click.option('-f', 'force', help='overwrite?', default=False, required=False, is_flag=True, help="overwrite the output files or not.")
@click.option('-t', 'test', help='test?', default=False, required=False, is_flag=True)
@click.option('-cmd', "cmd",
              help="it shoulw accept a command with {} as indicator of string format. e.g. mafft --maxiterate 1000 --genafpair --thread -1 {infile} > {ofile}, the suffix of original file and new file could be ignore. The suffix should be assigned at parameter `ns` or `s`. now default is empty. If you want to add more flexible parameters, it should modify this script directly. ")
def cli(indir, odir, suffix, new_suffix, force, test, num_parellel, cmd):
    main(indir=indir,
         odir=odir,
         num_parellel=num_parellel,
         suffix=suffix,
         new_suffix=new_suffix,
         force=force,
         cmd=cmd,
         test=test)


if __name__ == "__main__":
    cli()
