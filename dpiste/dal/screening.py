import os
import pandas as pd
import numpy as np
from .. import utils as dputils
from . import utils
from . import neoscope
from . import esis

def depistage_pseudo(dfs = {}): return screening_df("dépistage_pseudo", dfs)
def cnam(dfs = {}): return screening_df("cnam", dfs)
def table_correspondance(dfs = {}): return screening_df("table_correspondance", dfs)
def mail(dfs = {}): return screening_df("mail", dfs)


def screening_pks(): return {"dépistage_pseudo":["id_random", "Date_Mammo"], "cnam":"id_random", "table_correspondance":"id_random", "mail":"email"}
def screening_unique(): return {"cnam":["NNI_2"]}
def screening_fks(): 
  return  [
    {"fktable":"dépistage_pseudo", "fkcol":"id_random", "pktable":"table_correspondance"},
    {"fktable":"cnam", "fkcol":"id_random", "pktable":"table_correspondance"},
  ]

def check_fks(dfs):
  depistage_pseudo(dfs)
  cnam(dfs)
  table_correspondance(dfs)
  mail(dfs)
  utils.check_fks(dfs = dfs, fks = screening_fks(), pks = screening_pks())
  
def screening_path(name): return dputils.get_home("input", "screening", f"{name}.parquet")
def screening_df(name, dfs = {}): 
  if dfs.get(name) is None:
    if os.path.exists(screening_path(f"{name}_orig")):
      df = pd.read_parquet(screening_path(f"{name}_orig"))
    else:
      df = calculate_df(name, dfs)
      df.to_parquet(screening_path(f"{name}_orig"), engine = "pyarrow")
    pk = screening_pks()[name]
    dfs[f"{name}_na"] = utils.get_na_rows(df, pk) 
    notna = utils.get_notna_rows(df, pk)
    dfs[f"{name}_dup"] = utils.get_dup_rows(notna, pk) 
    dfs[name] = utils.force_pk(df, pk)

    # checking unique keys
    if name in screening_unique():
      for i, u in enumerate(screening_unique()[name]):
        dfs[f"{name}_na_{u}"] = utils.get_na_rows(df, u) 
        notnau = utils.get_notna_rows(df, u)
        dfs[f"{name}_dup_{u}"] = utils.get_dup_rows(notnau, u)
      
    # storing final dataset as parquet
    if not os.path.exists(screening_path(name)):
      dfs[name].to_parquet(screening_path(name), engine = "pyarrow")
  return dfs[name]

def calculate_df(name, dfs = {}):
  if name == "table_correspondance":
    ret = neoscope.population_df(dfs)[["id_random", "id_bci"]]
  elif name == "cnam":
    # creating
    ret =  neoscope.population_df(dfs)[[
      "id_random",
      "NNI_2",      
      "NNI_2_cle", 
      "sexe",
      "nom",
      "nom_jf",
      "prenom",
      "date_naiss",
    ]]
    ret = ret[pd.notna(ret["id_random"]) & pd.notna(ret["NNI_2"]) & pd.notna(ret["NNI_2_cle"])]
  elif name == "mail":
    ret = neoscope.population_df(dfs)[["email"]]
    ret = ret[pd.notna(ret["email"])]
    ret = ret.drop_duplicates(inplace = False, ignore_index = True)
  elif name == "dépistage_pseudo":
    # Producing the joined dataframe
    ret = (
      neoscope.depistage_df(dfs)
        .join(other = neoscope.suivi_df(dfs), on = ["id_event"], how = "left", lsuffix = "_Dépistage", rsuffix= "_Suivi") 
        .join(other = neoscope.risque_df(dfs), on = "id_event_Dépistage", how = "left", rsuffix= "_Risque") 
        .join(other = neoscope.adicap_df(dfs), on = "k_adicap", how = "left", rsuffix= "_Adicap") 
        .join(other = neoscope.adicap_df(dfs), on = "k_adicap2", how = "left", rsuffix= "_Adicap2") 
        .join(other = neoscope.population_df(dfs), on = "id_bci_Dépistage", how = "left", rsuffix= "_Population")
        .join(other = esis.dicom_exams(dfs), on = "id_bci_Dépistage", how = "left", rsuffix = "_Dicom")
    )
    to_remove_cols = [
      "num_ref_Dépistage",
      "id_assure_Dépistage",
      "id_bci_Dépistage",
      "id_event_Dépistage",
      "num_ref_Suivi",
      "id_assure_Suivi",
      "id_bci_Suivi",
      "id_event_Suivi",
      "Date_Mammo_Suivi",
      "num_ref",
      "id_assure",
      "id_bci",
      "id_event",
      "Date_Mammo",
      "Age_Mammo",
      "num_ref_Population",
      "id_assure_Population",
      "id_bci_Population",
      "NNI_2",
      "NNI_2_cle",
      "sexe",
      "nom",
      "nom_jf",
      "prenom",
      "date_naiss",
      "email",
      "count",
      "person_id",
      "k_adicap",
      "k_adicap2"
    ]
    
    for col in to_remove_cols:
      del ret[col]
    to_rename_cols = {
      "Date_Mammo_Dépistage":"Date_Mammo",
      "resultat_global_L1L2": "L1L2_positif",
      "L1_Type_Image_SD":"L1_Type_Anomalie_SD",
      "L1_Type_Image_SG":"L1_Type_Anomalie_SG",
      "BDI_Type_Image_SD":"BDI_Type_Anomalie_SD",
      "BDI_Type_Image_SG":"BDI_Type_Anomalie_SG",
      "L2_Type_Image_SD":"L2_Type_Anomalie_SD",
      "L2_Type_Image_SG":"L2_Type_Anomalie_SG",
      "comparaison_SD_plus_suspecte":"L1_comparaison_SD_plus_suspecte",
      "comparaison_SG_plus_suspecte":"L1_comparaison_SG_plus_suspecte",
      "Examen_Clinique_Sein_Normal":"L1_Examen_Clinique_Sein_Normal",
      "Examen_Clinique_Sein_Anormal":"L1_Examen_Clinique_Sein_Anormal",
      "Examen_Clinique_Sein_Refus":"L1_Examen_Clinique_Sein_Refus",
      "Echo_L1_Negative":"L1_Echo_Negative",
      "Echo_L1_Suspecte":"L1_Echo_Suspecte", 
      "pT":"Anapath_TNM_T",
      "pN":"Anapath_TNM_N",
      "M":"Anapath_TNM_M" ,
      "Taille_en_mm":"Anapath_taille_en_mm",
      "localisation":"Anapath_localisation",
      "code_adicap":"Anapath_code_adicap",
      "adicap":"Anapath_adicap",
      "code_adicap_Adicap2":"Anapath_code_adicap2",
      "adicap_Adicap2":"Anapath_adicap2",
      "Grade_SBR":"Anapath_Grade_SBR",
      "RH_Progesterone":"Anapath_RH_Progesterone",
      "RH_Oestreogene":"Anapath_RH_Oestrogene",
      "HER2":"Anapath_HER2",
      "Si_Malin":"Anapath_Type_Si_Malin",
      "Si_Benin":"Anapath_Type_Si_Benin",
      "Date_Anapath":"Anapath_Date",
      "Date_Inter_Chir":"Trait_Date_Inter_Chir",
      "Trait_Radi":"Trait_Radiotherapie",
      "Date_Radi":"Trait_Date_Radiotherapie",
      "Trait_Horm":"Trait_Hormonotherapie",
      "Date_Horm":"Trait_Date_Hormonotherapie",
      "Trait_Chim":"Trait_Chimiotherapie",
      "Date_Chim":"Trait_Date_Chimiotherapie",
      "KS_confirme":"Anapath_Cancer_Confirme",
      "THS":"ATCD_THS",
      "Age_ATCD_Cancer":"ATCD_Age_Cancer",
      "Age_ATCD_Cancer_Bilateral":"ATCD_Age_Cancer_Bilateral",
      "Age_ATCD_Chir_Esth":"ATCD_Age_Chir_Esth",
      "ATCD_Famil_Mere":"ATCD_Cancer_Mere",
      "Age_ATCD_Famil_Mere":"ATCD_Age_Cancer_Mere",
      "ATCD_Famil_Soeur":"ATCD_Cancer_Soeur",
      "Age_ATCD_Famil_Soeur":"ATCD_Age_Cancer_Soeur",
      "ATCD_Famil_Fille":"ATCD_Cancer_Fille",
      "Age_ATCD_Famil_Fille":"ATCD_Age_Cancer_Fille",
      "ATCD_Famil_Autre":"ATCD_Cancer_Autre",
      "Age_ATCD_Famil_Autre":"ATCD_Age_Cancer_Autre",
      "dicom_studies":"DICOM_Studies"
    }
    if len(to_rename_cols) > 0:
      ret.rename(columns = to_rename_cols, inplace = True)
  else:
    raise ValueError(f"{name} is not recognized as a screening calculated table")
  return ret

def metadata(name):
  if name == "table_correspondance":
    raise NotImplementedError(f"metadata for table {name} has not been defined")
  elif name == "cnam":
    raise NotImplementedError(f"metadata for table {name} has not been defined")
  elif name == "mail":
    raise NotImplementedError(f"metadata for table {name} has not been defined")
  elif name == "dépistage_pseudo":
    ret = [
    {"column":"id_random", "description":"Id patient aléatoire", "sensitivity":"pseudonym"},
    {"column":"Date_Mammo", "description":"Date de la mammographie", "sensitivity":"event_date"},
    {"column":"L1_ACR_SD", "description":"Classification ACR sein droit en première lecture", "sensitivity":"property"},
    {"column":"L1_ACR_SG", "description":"Classification ACR sein gauche en première lecture", "sensitivity":"property"},
    {"column":"L1_Type_Anomalie_SD", "description":"Type d'anomalie identifié dans le sein droit en première lecture", "sensitivity":"property"},
    {"column":"L1_Type_Anomalie_SG", "description":"Type d'anomalie identifié dans le sein gauche en première lecture", "sensitivity":"property"},
    {"column":"L1_comparaison_SD_plus_suspecte", "description":"Si la comparaison avec l'antériorité du sein droit est plus suspecte que l'antérieur", "sensitivity":"property"},
    {"column":"L1_comparaison_SG_plus_suspecte", "description":"Si la comparaison avec l'antériorité du sein gauche est plus suspecte que l'antérieur", "sensitivity":"property"},
    {"column":"L1_Examen_Clinique_Sein_Normal", "description":"Si l'examen clinique des seins est normal", "sensitivity":"property"},
    {"column":"L1_Examen_Clinique_Sein_Anormal", "description":"Si l'examen clinique des sein est anormal", "sensitivity":"property"},
    {"column":"L1_Examen_Clinique_Sein_Refus", "description":"Si la patiente refure l'examen clinique des seins", "sensitivity":"property"},
    # quel difference entre L1 et BDI
    {"column":"BDI", "description":"Rélisation d'un Bilan immédiat", "sensitivity":"property"},
    {"column":"BDI_Agrandissement", "description":"Si le bilan immédiat comprend un agrandissement", "sensitivity":"property"},
    {"column":"BDI_Cytoponction", "description":"Si le bilan immédiat comprend une cytoponction", "sensitivity":"property"},
    {"column":"BDI_Echographie", "description":"Si le bilan immédiat comprend une echographie", "sensitivity":"property"},
    {"column":"BDI_ACR_SD", "description":"Classification ACR sein droit après bilan immédiat", "sensitivity":"property"},
    {"column":"BDI_ACR_SG", "description":"Classification ACR sein gauche après bilan immédiat", "sensitivity":"property"},
    {"column":"BDI_Type_Anomalie_SD", "description":"Type d'anomalie identifié après bilan immédiat dans le sein droit en première lecture", "sensitivity":"property"},
    {"column":"BDI_Type_Anomalie_SG", "description":"Type d'anomalie identifié après bilan immédiat dans le sein gauche en première lecture", "sensitivity":"property"},
    {"column":"L1_Echo_Negative", "description":"Si l'examan d'echographie réalisé en première lecture ne revèle pas d'anomalie", "sensitivity":"property"},
    {"column":"L1_Echo_Suspecte", "description":"Si l'examen d'echographie réalise en première lecture est suspect", "sensitivity":"property"},
    {"column":"L1_Conduite_a_tenir_Surveillance", "description":"Si la conduite à tenir après la première lecture est la surveillance", "sensitivity":"property"},
    {"column":"L1_Conduite_a_tenir_Cytoponction", "description":"Si la conduite à tenir après la première lecture est une Cytoponction", "sensitivity":"property"},
    {"column":"L1_Conduite_a_tenir_Microbiopsie", "description":"Si la conduite à tenir après la première lecture est une Microbipsie", "sensitivity":"property"},
    {"column":"L1_Conduite_a_tenir_Macrobiopsie", "description":"Si la conduite à tenir après la première lecture est une Macrobiopsie", "sensitivity":"property"},
    {"column":"L1_Conduite_a_tenir_Autre", "description":"Si la conduite à tenir après L1 est autre", "sensitivity":"property"},
    {"column":"L2_Type_Anomalie_SD", "description":"Type d'anomalie identifié après bilan immédiat dans le sein droit en deuxième lecture", "sensitivity":"property"},
    {"column":"L2_Type_Anomalie_SG", "description":"Type d'anomalie identifié après bilan immédiat dans le sein gauche en deuxième lecture", "sensitivity":"property"},
    {"column":"L2_Conduite_a_tenir_Surveillance", "description":"Si la conduite à tenir après la deuxième lecture est la surveillance", "sensitivity":"property"},
    {"column":"L2_Conduite_a_tenir_Cytoponction", "description":"Si la conduite à tenir après la deuxième lecture est ", "sensitivity":"property"},
    {"column":"L2_Conduite_a_tenir_Microbiopsie", "description":"Si la conduite à tenir après la deuxième lecture est une Microbiopsie", "sensitivity":"property"},
    {"column":"L2_Conduite_a_tenir_Macrobiopsie", "description":"Si la conduite à tenir après la deuxième lecture est une Macrobiopsie ", "sensitivity":"property"},
    {"column":"L2_Conduite_a_tenir_Autre", "description":"Si la conduite à tenir après la deuxième lecture est autre ", "sensitivity":"property"},
    {"column":"L2_ACR_SD", "description":"Classification ACR sein droit en deuxième lecture", "sensitivity":"property"},
    {"column":"L2_ACR_SG", "description":"Classification ACR sein gauche en deuxième lecture", "sensitivity":"property"},
    {"column":"L1L2_positif", "description":"Si le resultat final dépistage est positif", "sensitivity":"property"},
    {"column":"Anapath_TNM_T", "description":"T de la classification TNM: La lettre « T » symbolise la tumeur initiale. Elle est cotée de T0 (quand la lésion primitive n’est pas localisée) à T4 pour les tumeurs les plus étendues. Cette cotation dépend du volume tumoral, représenté par le diamètre maximum de la lésion, et de la fixation aux organes voisins (peau, vaisseaux, nerfs, os, etc.). Source (https://fr.wikipedia.org/wiki/Classification_TNM)", "sensitivity":"property"},
    {"column":"Anapath_TNM_N", "description":"N de la classification TNM: La lettre « N », de N0 à N3, dépend du territoire ganglionnaire, plus ou moins proche de la tumeur, des dimensions des adénopathies, de leur nombre et de leur éventuelle fixation aux tissus voisins. Le pathologiste pourra noter Nx dans le cas ou il ne reçoit pas de ganglions ou trop peu pour se prononcer sur le pronostic. Attention, la résection des ganglions pour analyse n'est pas curative, mais uniquement diagnostique. Source (https://fr.wikipedia.org/wiki/Classification_TNM)", "sensitivity":"property"},
    {"column":"Anapath_TNM_M", "description":"M de la classification TNM: La lettre « M » est cotée M0 en l’absence de métastases connues ou M1 en leur présence, quel que soit leur siège, unique ou multiple. De même qu'avec le 'N', le pathologiste rendra Mx si aucune information concernant d'éventuelles métastases ne lui sont transmises par le clinicien. Source (https://fr.wikipedia.org/wiki/Classification_TNM)", "sensitivity":"property"},
    {"column":"Anapath_taille_en_mm", "description":"Taille en milimetres du tumeur identifié", "sensitivity":"property"},
    {"column":"Anapath_localisation", "description":"Localisation du tumeur ", "sensitivity":"property"},
    {"column":"Anapath_code_adicap", "description":"Code Adicap 1: Le thésaurus ADICAP permet de décrire un prélèvement tissulaire examiné en anatomie et cytologie pathologiques (ACP). Ce thésaurus a été élaboré par les pathologistes français de l’Association pour le Développement de l’Informatique en Cytologie et Anatomo-Pathologie (ADICAP). Source (https://smt.esante.gouv.fr/terminologie-adicap/)", "sensitivity":"property"},
    {"column":"Anapath_adicap", "description":"Description Adicap 1: Le thésaurus ADICAP permet de décrire un prélèvement tissulaire examiné en anatomie et cytologie pathologiques (ACP). Ce thésaurus a été élaboré par les pathologistes français de l’Association pour le Développement de l’Informatique en Cytologie et Anatomo-Pathologie (ADICAP). Source (https://smt.esante.gouv.fr/terminologie-adicap/)", "sensitivity":"property"},
    {"column":"Anapath_code_adicap2", "description":"Code Adicap 2: Le thésaurus ADICAP permet de décrire un prélèvement tissulaire examiné en anatomie et cytologie pathologiques (ACP). Ce thésaurus a été élaboré par les pathologistes français de l’Association pour le Développement de l’Informatique en Cytologie et Anatomo-Pathologie (ADICAP). Source (https://smt.esante.gouv.fr/terminologie-adicap/)", "sensitivity":"property"},
    {"column":"Anapath_adicap2", "description":"Adicap 2: Le thésaurus ADICAP permet de décrire un prélèvement tissulaire examiné en anatomie et cytologie pathologiques (ACP). Ce thésaurus a été élaboré par les pathologistes français de l’Association pour le Développement de l’Informatique en Cytologie et Anatomo-Pathologie (ADICAP). Source (https://smt.esante.gouv.fr/terminologie-adicap/)", "sensitivity":"property"},
    # Difference Adicap1 et 2
    {"column":"Anapath_Grade_SBR", "description":"Le grade d'un cancer correspond à la somme des notes obtenues en fonction de l'architecture, le noyau et l'activité mitotique des tumeurs. Le grade I correspond aux tumeurs les moins agressives; Le grade III correspond aux tumeurs les plus agressives; Le grade II est un grade intermédiaire entre les grades 1 et 3. Sourcz (https://www.e-cancer.fr/Patients-et-proches/Les-cancers/Cancer-du-sein/Les-grades-du-cancer)", "sensitivity":"property"},
    {"column":"Anapath_RH_Progesterone", "description":"Si le tumeur est positif aux récepteurs de progestérone positifs", "sensitivity":"property"},
    {"column":"Anapath_RH_Oestrogene", "description":"Si le tumeur est positif aux récepteurs d’œstrogènes positifs", "sensitivity":"property"},
    {"column":"Anapath_HER2", "description":"Si le tumeur est positif aux récepteurs à la protéine HER2", "sensitivity":"property"},
    {"column":"Anapath_Type_Si_Malin", "description":"Type de cancer si Malin", "sensitivity":"property"},
    {"column":"Anapath_Type_Si_Benin", "description":"Type de cancer si Benin", "sensitivity":"property"},
    {"column":"Anapath_Date", "description":"Date d'obtenton du compte rendu d'anatomie et cytologie pathologique du prelevement", "sensitivity":"event_date"},
    # Date s'obtention ou date de prelevement??
    {"column":"Trait_Date_Inter_Chir", "description":"Date de chirurgie si réalisé", "sensitivity":"event_date"},
    # C'est quoi chir??
    {"column":"Trait_Radiotherapie", "description":"Si un traitement de radiothérapie de radiologie a été réalisé", "sensitivity":"property"},
    # dates ou indicateur de prescription ou réalisation
    {"column":"Trait_Date_Radiotherapie", "description":"Date de réalisation de radiothérapie", "sensitivity":"event_date"},
    {"column":"Trait_Hormonotherapie", "description":"Si l'hormonothérapie a été réalisée", "sensitivity":"property"},
    {"column":"Trait_Date_Hormonotherapie", "description":"Date de réalisation de hormnonothérapie", "sensitivity":"event_date"},
    {"column":"Trait_Chimiotherapie", "description":"Si la chimiothérapie a été réalisée", "sensitivity":"property"},
    {"column":"Trait_Date_Chimiotherapie", "description":"Date de réalisation de chimiothérapie", "sensitivity":"event_date"},
    {"column":"Anapath_Cancer_Confirme", "description":"Si un cancer du sein a été identifié", "sensitivity":"property"},
    {"column":"ATCD_THS", "description":"Si la patiente déclare avoir suivi un traitement hormonale sustitutif contre la ménopause", "sensitivity":"property"},
    {"column":"ATCD_Cancer", "description":"Si la patiente a déjà eu un cancer", "sensitivity":"property"},
    #Tout cancer ou cancer de sein
    {"column":"ATCD_Age_Cancer", "description":"Age déclaré de survenue de cancer", "sensitivity":"property"},
    {"column":"ATCD_Cancer_Bilateral", "description":"Se la patiente déclare avoir eu un cancer bilateral", "sensitivity":"property"},
    {"column":"ATCD_Age_Cancer_Bilateral", "description":"Age déclaré de survenu du cancer bilateral ", "sensitivity":"property"},
    {"column":"ATCD_Chir_Esth", "description":"Si la patiente déclare avoir réalisé un chirurgue esthétuque", "sensitivity":"property"},
    {"column":"ATCD_Age_Chir_Esth", "description":"Age déclaré de réalisation de chirurgue esthétique", "sensitivity":"property"},
    {"column":"ATCD_Cancer_Mere", "description":"Si la patiente déclare que sa mêre a déjà eu un cancer du sein", "sensitivity":"property"},
    {"column":"ATCD_Age_Cancer_Mere", "description":"Age déclaré de survenu du cancer du sein de la mêre", "sensitivity":"property"},
    {"column":"ATCD_Cancer_Soeur", "description":"Si la patiente déclare que sa soeur a déjà eu un cancer du sein", "sensitivity":"property"},
    {"column":"ATCD_Age_Cancer_Soeur", "description":"Age déclaré de survenu du cancer du sein de la soeur", "sensitivity":"property"},
    {"column":"ATCD_Cancer_Fille", "description":"Si la patiente déclare que sa fille a déjà eu un cancer su sein", "sensitivity":"property"},
    {"column":"ATCD_Age_Cancer_Fille", "description":"Age déclaré de survenu du cancer du sein de la fille", "sensitivity":"property"},
    {"column":"ATCD_Cancer_Autre", "description":"Si la patiente déclare qu'une autre membre de sa famille a déjà eu un cancer du sein", "sensitivity":"property"},
    {"column":"ATCD_Age_Cancer_Autre", "description":"Age déclaré de survenu du cancer du sein d'un autre membre de la famille", "sensitivity":"property"},
    {"column":"DICOM_Studies", "description":"Liste des dates et identifiants des mammographies", "sensitivity":"technical_id"}
  ]
  else:
    raise ValueError(f"{name} is not recognized as a screening calculated table")
  return ret


def unmatched_people(dfs):
  dep = neoscope.depistage_df(dfs)
  dico_exams = esis.dicom_exams(dfs)
  return dico_exams.loc[~mammo_exams.person_id.isin(dep.id_bci)]



