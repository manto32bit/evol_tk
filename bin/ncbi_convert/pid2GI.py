"""
This script is the first kit of ncbi convertor. It is also a simple example for this convertor.
Other convertor would follow the structure of this script.
"""
from bin.ncbi_convert import edl, access_intermedia, parse_id
from os.path import exists, join, dirname
from tqdm import tqdm
from Bio import Entrez
import io
import os
import click


def pid2GI(id_list):
    suffix = 'pid2gi'
    _cache = access_intermedia(id_list, suffix=suffix)
    if _cache is not None:
        id2gi = _cache
    else:
        tqdm.write('from protein Accession ID to GI')
        results, failed = edl.esearch(db='protein',
                                      ids=id_list,
                                      result_func=lambda x: Entrez.read(
                                          io.StringIO(x))['IdList'],
                                      batch_size=1
                                      )
        id2gi = dict(results)
        # stodge the result into intermedia file for second access.
        access_intermedia(id2gi, suffix=suffix)
    return id2gi


def main(infile, ofile, force=False):
    order_id_list, id2annotate = parse_id(infile)
    if isinstance(next(id2annotate.values()), dict):
        # it is a dict, so it contains other infomation or implemented GI. it may be passed over.
        if 'GI' in next(id2annotate.values()):
            print("provided file already contains `GI` column(doesn't check the validation/completeness). Giving `force` param to overwrite/implement it. ")
            if not force:
                return
        # todo: re-implemented original infomation into `ofile` from `infile`
    else:
        # no header, just a list of IDs
        pass
    id2gi = pid2GI(order_id_list)
    if not exists(dirname(ofile)):
        os.makedirs(dirname(ofile))

    with open(ofile, 'w') as f1:
        print('#accession ID\tGI', file=f1)
        for id, GI in id2gi.items():
            print(f'{id}\t{GI}', file=f1)


@click.command()
@click.option('-i', 'infile', help='input file which contains protein accession id ')
@click.option('-o', 'ofile', help='output file')
@click.option('-f', 'force', help='force overwrite?', default=False, required=False, is_flag=True)
def cli(infile, ofile, force):
    main(infile, ofile, force)


if __name__ == "__main__":
    cli()