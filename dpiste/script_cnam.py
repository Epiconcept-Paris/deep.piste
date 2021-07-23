# GENERATION DU FICHIER NORME
# Version : 0.2 - 06/04/2021
# Pour toute erreur observée, merci de contacter Tim Vlaar (tim.vlaar@health-data-hub.fr)

import configparser
import pandas as pd
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
        


    def parameters_check_report(self):
        """
        Génère un rapport après plusieurs vérification
        Le rapport est un fichier txt signalant toute erreur dans les paramètres donnés
        """
        self.path2report = os.path.join(
                os.path.split(self.path2output)[0],
                'rapport_des_verifications.txt'
        )
        with open(self.path2report,'w',encoding='utf-8') as report:
            report.write("RAPPORT DES VERIFICATIONS \n\n")
            #input parameters
            report.write("PARAMETRES EN ENTREE:\n")
            report.write(f"Fichier normé .txt créé : {self.path2output}\n")
            report.write(f"Fichier en entrée avec la liste des NIR : {self.path2nirlist}\n")
            report.write(f"Date de dépôt/création renseignée : {self.date_depot}\n")
            report.write(f"Numéro du projet : {self.num_projet}\n")
            report.write(f"Nom du projet : {self.nom_projet}\n")
            report.write('\nERREUR SUR LES PARAMETRES:\n')
            #check date
            if (len(self.date_depot)!=10) or \
                (re.match('[0-9]{2}/[0-9]{2}/[0-9]{4}',self.date_depot) is None):
                report.write("ERREUR : date_depot_fichier_crea n'est pas au format JJ/MM/AAAA \n")
            if len(self.num_projet)!=3:
                report.write("ERREUR : num_projet n'est pas au bon format (3 caractères) \n")
            if len(self.nom_projet)!=5:
                report.write("ERREUR : nom_projet n'est pas au bon format (5 caractères) \n")

            if not os.path.exists(self.path2nirlist):
                report.write("ERREUR : Le chemin vers le fichier en entrée (chemin_list_NIR) est erroné \n")
            report.close()


def input_file_check_report(nir_list,config):
    """
    Complète le rapport initié par la fonction parameters_check_report
    Vérifie la conformité du fichier d'entrée et signale toute erreur ou anomalie détectée.
    Parameters
    ----------
    :nir_list: pandas.DataFrame, fichier d'entrée
    :config: instance de la classe Config
    """
    with open(config.path2report,'a',encoding='utf-8') as report:
        report.write("\nERREURS SUR LE FICHIER EN ENTREE : \n")
        if nir_list.isna().values.any():
            print(nir_list.isna())
            report.write("ERREUR : Le fichier en entree (fichier_entree) ne doit contenir aucune cellule vide \n")
        if any(nir_list['NIR_du_beneficiaire'].apply(len)!=13):
            report.write("ERREUR : Un ou plusieurs NIRs du bénéficiaire ne sont pas au bon format (13 caractères) \n")
        if any(nir_list['NIR_du_ouvrant_droit'].apply(len)!=13):
            report.write("ERREUR : Un ou plusieurs NIRs de l'ouvrant droit ne sont pas au bon format (13 caractères) \n")
        if not all(nir_list['Date_de_naissance'].str.fullmatch('[0-9]{2}/[0-9]{2}/[0-9]{4}')):
            report.write("ERREUR : Une ou plusieurs Dates de naissance ne sont pas au bon format (JJ/MM/AAAA) \n")
        if not all(nir_list['Code_sexe'].isin(['1','2'])):
            report.write("ERREUR : Un ou plusieurs Codes sexe ne sont pas au bon format (1 = Homme, 2 = Femme) \n")
        if any(nir_list['Identifiant_temporaire'].apply(len)>20):
            report.write("ERREUR : Un ou plusieurs Identifiants temporaires sont pas au bon format (<= 20 caractères) \n")
        if any(nir_list['Identifiant_temporaire'].duplicated()):
            report.write("ERREUR : L'unicité de l'identifiant temporaire n'est pas vérifiée \n")

        #description
        report.write("\nDESCRIPTION DU FICHIER EN ENTREE : \n")
        report.write(f"Nombre de patients (Identifiant_temporaire) : {nir_list['Identifiant_temporaire'].unique().shape[0]}\n")
        report.write(f"Femmes: {sum(nir_list['Code_sexe']=='2')}\n")
        report.write(f"Hommes: {sum(nir_list['Code_sexe']=='1')}\n")
        report.write(f"Date de naissance du patient le plus âgé : {nir_list['Date_de_naissance'].min()}\n")
        report.write(f"Date de naissance du patient le plus jeune : {nir_list['Date_de_naissance'].max()}\n")
        report.close()


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
        nf.write("000000000000KMLEI       \n")


if __name__=='__main__':
    args = parse_args()
    conf = Config(args)
    conf.parameters_check_report()

    with open(conf.path2nirlist, 'r') as csvfile:
        dialect = csv.Sniffer().sniff(csvfile.readline(),delimiters=[',',';','|'])
        delimiter = dialect.delimiter
    nir_list = pd.read_csv(
                    conf.path2nirlist,
                    sep=delimiter,
                    dtype='string'
                    )
    input_file_check_report(nir_list,conf)
    generate_normed_file(nir_list,conf)
