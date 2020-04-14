"""
It mainly for running prokka after download genomes.
It includes
1. check the missing ID
2. perform prokka and rename the ID
3. generate metadata.csv
"""
import os
from glob import glob
from os.path import join, exists, basename, dirname, isdir, expanduser
from subprocess import check_call

import click
from Bio import SeqIO
from tqdm import tqdm

from dating_workflow.toolkit.concat_aln import convert_genome_ID


def run_cmd(cmd):
    check_call(cmd, shell=True,
               stderr=open('/dev/null', 'w'),
               stdout=open('/dev/null', 'w'))


def get_faa_from_prokka_r(infile, odir, sample_name, prokka_p, return_cmd=False):
    locustag = convert_genome_ID(sample_name)
    oprefix = f"{odir}/{sample_name}/{sample_name}"
    if exists(f'{oprefix}.faa'):
        return f'{oprefix}.faa'
    cmd = f'{prokka_p} {infile} --outdir {odir}/{sample_name} --force --prefix {sample_name} --locustag {locustag} --cpus 0 '
    if return_cmd:
        return cmd
    run_cmd(cmd)
    return f'{oprefix}.faa'


def cli(indir, odir=None, reformatted_name=False, force=False, prokka_p=" `which prokka`"):
    if odir is None:
        odir = './genome_protein_files'
    all_dir = [_
               for _ in glob(join(indir, '**', 'GC*'), recursive=True)
               if isdir(_)]
    tmp_dir = './tmp'
    if not exists(tmp_dir):
        os.makedirs(tmp_dir, exist_ok=True)

    for p_dir in tqdm(all_dir):
        p_files = glob(join(p_dir, '*.faa.gz'))
        ofile = join(odir, basename(p_dir)) + '.faa'
        if exists(ofile) and not force:
            continue
        if not p_files:
            fna_file = glob(join(p_dir, '*.fna.gz'))[0]
            new_fna = fna_file.replace('.gz', '')
            if not exists(new_fna):
                run_cmd(f'gunzip -d -c {fna_file} > {new_fna}')
            p_files = [get_faa_from_prokka_r(infile=new_fna,
                                             odir=tmp_dir,
                                             sample_name=basename(dirname(fna_file)),
                                             prokka_p=prokka_p,
                                             return_cmd=False
                                             )]
        p_file = p_files[0]

        if (not exists(ofile)) and p_file.endswith('.gz') and exists(p_file):
            run_cmd(f'gunzip -d -c {p_file} >{ofile}')
        elif (not exists(ofile)) and exists(p_file):
            run_cmd(f'cat {p_file} >{ofile}')
        else:
            # print(p_file,ofile)
            pass

    # format protein id
    if reformatted_name:
        name_map = {}
        for p in tqdm(glob(join(odir, '*.faa'))):
            name = basename(p).replace('.faa', '')
            locus_prefix = convert_genome_ID(name)
            records = []
            for idx, record in enumerate(SeqIO.parse(p, format='fasta')):
                new_name = locus_prefix + '_{:0>5}'.format(idx + 1)
                name_map[record.id] = new_name
                record.id = new_name
                records.append(record)
            SeqIO.write(records,
                        open(p, 'w'),
                        format='fasta-2line')


@click.command()
@click.option("-i", "indir", default="./genbank", )
@click.option("-o", "odir", default="./genome_protein_files")
@click.option("-id", "id_file", default='./assembly_ids.list')
@click.option('-f', 'force', help='overwrite?', default=False, required=False, is_flag=True)
def main(indir, odir, id_file, force):
    if not exists(indir):
        raise IOError("input dir doesn't exist")
    if not exists(odir):
        os.makedirs(odir, exist_ok=True)

    # for indir in ['./genbank', './refseq']:
    #     if exists(indir):

    name = indir.split('/')[-1]
    base_tab = expanduser(f'~/.cache/ncbi-genome-download/{name}_bacteria_assembly_summary.txt')
    all_g_ids = set([basename(_)
                     for _ in glob(join(indir, 'bacteria', '*'))])
    # from downloaded dir
    all_ids = open(id_file).read().split('\n')
    all_ids = [_ for _ in all_ids if _]
    all_ids = set(all_ids)
    # from id list

    metadatas = open(base_tab).read().split('\n')
    rows = [_
            for _ in tqdm(metadatas)
            if _.split('\t')[0] in all_g_ids]

    if exists('./metadata.csv'):
        f1 = open('./metadata.csv', 'a')
    else:
        f1 = open('./metadata.csv', 'w')
    f1.write(metadatas[1].strip('# ') + '\n')
    f1.write('\n'.join(rows))
    f1.close()
    if set(all_ids) != set(all_g_ids):
        print('inconsistent id, missing ids: ' + '\n'.join(all_ids.difference(all_g_ids)))

    cli(indir, odir, force)


if __name__ == "__main__":
    main()
    # python3 /home-user/thliao/script/evolution_relative/dating_workflow/toolkit/postdownload.py -i ./genbank -o ./genome_protein_files

