import pandas as pd
import configparser
import os
import re
from datetime import datetime
import argparse
from pathlib import Path
import csv

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-conf','--path2config',type=str,help="chemin vers le fichier de configuration")
    parser.add_argument('--chemin_emplacment_crea',type=str,help="emplacement de création du fichier normé")
    parser.add_argument('--chemin_list_nir',type=str,help="chemin vers le fichier contenant la liste des NIR")
    parser.add_argument('--date_depot_fichier_crea',type=str,help="date de depot du fichier")
    parser.add_argument('--num_projet',type=str,help="numero du projet")
    parser.add_argument('--nom_projet',type=str,help="nom du projet")
    args = parser.parse_args()
    return args

class Config():

    config = configparser.ConfigParser()

    def __init__(self,args):
        """
        Lit le fichier de configuration si son chemin est fourni, sinon considère que les arguments sont tous données en ligne de commande.

        Parameters
        ----------
        :args: dict, output d'un argparser
        """
        if args.path2config:
            self.config.read(args.path2config)
            self.path2output = self.config['DEFAULT']['chemin_emplacment_crea']
            self.path2nirlist = self.config['DEFAULT']['chemin_list_NIR']
            self.date_depot = self.config['DEFAULT']['date_depot_fichier_crea']
            self.num_projet = self.config['DEFAULT']['num_projet']
            self.nom_projet = self.config['DEFAULT']['nom_projet']
        else:
            self.path2output = args.chemin_emplacment_crea
            self.path2nirlist = args.chemin_list_nir
            self.date_depot = args.date_depot_fichier_crea
            self.num_projet = args.num_projet
            self.nom_projet = args.nom_projet


def create_line(x,nom_projet):
    """
    Crée une ligne du fichier normé à partir d'une ligne du fichier d'entrée
    Parameters
    ----------
    :x: ligne de pandas.DataFrame
    :nom_projet: string, nom du projet
    """
    line = "11099"
    line += x.NIR_du_ouvrant_droit
    line += x.Date_de_naissance[6:]
    line += x.Date_de_naissance[3:5]
    line += x.Date_de_naissance[:2]
    line += x.Code_sexe
    line += x.NIR_du_beneficiaire
    line += "    "
    line += nom_projet
    line += f'{x.Identifiant_temporaire: <20}'
    return line[:69] + "\n"

def generate_normed_file(nir_list,config):
    """
    Parameters
    ----------
    :nir_list: pandas.DataFrame, obtenu à partir du fichier d'entrée
    :config: instance de la classe Config
    """
    nir_list['line'] = nir_list.apply(create_line,nom_projet=config.nom_projet,axis=1)
    nbr_enregistrement = str(nir_list.shape[0]).zfill(8)
    nbr_lignes = str(nir_list.shape[0]+4).zfill(9)
    quantiem_jour = datetime.strptime(config.date_depot,'%d/%m/%Y').strftime('%j')

    with open(config.path2output,'w') as nf:
        nf.write("00000RG00000000080036CRIP          CN00000000001003SNE800362016183201630520161108EI010000V80036")
        nf.write(config.date_depot[6:])
        nf.write(quantiem_jour)
        nf.write(config.num_projet)
        nf.write("   0000000000000000000000KMLEI       \n")
        nf.write("10001H0000001\n")
        for l in nir_list['line']:
            nf.write(l)
        nf.write(f"99001NT_LOT    10001{nbr_enregistrement}\n")
        nf.write("99900RG00000000080036CRIP          CN00000000001003SNE800362016183201630520161108EI010000V80036")
        nf.write(config.date_depot[6:])
        nf.write(quantiem_jour)
        nf.write(config.num_projet)
        nf.write("   0")
        nf.write(nbr_lignes)
        nf.write("000000000000KMLEI       ")

"""
if __name__=='__main__':
    args = parse_args()
    conf = Config(args)

    with open(conf.path2nirlist, 'r') as csvfile:
        dialect = csv.Sniffer().sniff(csvfile.readline(),delimiters=[',',';','|'])
        delimiter = dialect.delimiter
    nir_list = pd.read_csv(
                    conf.path2nirlist,
                    sep=delimiter,
                    dtype='string'
                    )
    generate_normed_file(nir_list,conf)
    """
