import os
datadir = os.path.abspath('data')

flowdatadir = os.path.join(datadir, 'flows')

outdir = os.path.abspath('out')

patfile = os.path.join(datadir, 'apat63_99.txt')
citefile = os.path.join(datadir, 'cite75_99.txt')

def ensure_dir(dirpath):
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)

def ensure_dirs():
    ensure_dir(datadir)
    ensure_dir(outdir)
    ensure_dir(flowdatadir)

ensure_dirs()

def download():
    # TODO: download data
    pass 

