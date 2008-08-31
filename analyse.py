'''Code to do structural analaysis of patent data using dirichlet trees.

Assumes the basic citation matrix has already been produced.
'''
# from numpy import random, array
from numpy import array
import mdp

def make_closure(M):
    nn = M.shape[0]
    for kk in range(nn):
        for ii in range(nn):
            for jj in range(nn):
                M[ii,jj] = (M[ii,jj] or (M[ii,kk] and M[kk,jj]))
    return M

import rpy
def reduce_dimensions(myarray):
    # with std test input get
    # Covariance matrix may be singular.Try instantiating the node with svd=True.
    return mdp.pca(myarray, svd=True)

def reduce_dimensions_rpy(myarray):
    return rpy.r.prcomp(myarray)

def plot_distbn(myarray):
    do_plot()

def dump_array(arr, filepath):
    # ff = file(filepath, 'w')
    # ff.write(str(arr))
    rpy.r.write_table(arr, filepath, col_names=False, row_names=False, quote=False)

def fit_dirichlet(array):
    pass

def fit_gaussian(array):
    pass


