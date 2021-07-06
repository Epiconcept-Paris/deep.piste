from . import dal
import pandas as pd
from . import utils as dputils
from . import script_cnam
from types import SimpleNamespace

def p12_001_safe_test(date_depot, nom_projet, num_projet):
    conf = {
    "path2output" : dputils.get_home("output", "cnam", "safe_test"),
    "date_depot" : date_depot,
    "num_projet" : num_projet,
    "nom_projet" : nom_projet
    }
    script_cnam.generate_normed_file(dal.cnam.dummy_cnam_for_safe(),SimpleNamespace(**conf))
"""
    with open(conf.path2nirlist, 'r') as csvfile:
        dialect = csv.Sniffer().sniff(csvfile.readline(),delimiters=[',',';','|'])
        delimiter = dialect.delimiter
    nir_list = pd.read_csv(
                    conf.path2nirlist,
                    sep=delimiter,
                    dtype='string'
                    )
"""

def p12_002_safe(date_depot, nom_projet, num_projet):
    conf = {
    "path2output" : dputils.get_home("output", "cnam", "safe_test"),
    "date_depot" : date_depot,
    "num_projet" : num_projet,
    "nom_projet" : nom_projet
    }
    script_cnam.generate_normed_file(dal.cnam.cnam_for_safe(),SimpleNamespace(**conf))
