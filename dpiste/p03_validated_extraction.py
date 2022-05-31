import os
import pandas as pd
import numpy as np
import urllib.parse
from . import dal
from . import report 
from . import utils


def p03_001_generate_validated_extraction():                                                                                                                       
  dfs = {}
  cnam = dal.screening.cnam(dfs)
  mapping = dal.screening.table_correspondance(dfs)
  screening = dal.screening.depistage_pseudo(dfs)
  mail = dal.screening.mail(dfs) 
  dal.screening.check_fks(dfs)


def p03_002_validated_extraction_report():                                                                                                                       
  report.generate(report = "validated-extraction-stats")                     


def p03_003_export_emails_to_epifiles(epifiles, login, password):
  dfs = {}
  mail = dal.screening.mail(dfs)
  source = utils.get_home("data", "output", "crcdc-oc", "mail_femmes.csv")
  mr = "(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
  clean = mail["email"].str.extract(mr)[0]
  clean = clean[pd.notna(clean)]
  clean.to_csv(source)
  dest = f"epi://{urllib.parse.quote_plus(login)}:{urllib.parse.quote_plus(password)}@{epifiles}/mail_femmes.csv"
  utils.sparkly_cp(source = source, dest = dest) 
