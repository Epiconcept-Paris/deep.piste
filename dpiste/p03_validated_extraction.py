import os
import pandas as pd
import numpy as np
from . import dal
from . import report 


def p03_001_generate_validated_extraction():                                                                                                                       
  dfs = {}
  cnam = dal.screening.cnam(dfs)
  mapping = dal.screening.table_correspondance(dfs)
  screening = dal.screening.depistage_pseudo(dfs)
  mail = dal.screening.mail(dfs) 
  dal.screening.check_fks(dfs)


def p03_002_validated_extraction_report():                                                                                                                       
  report.generate(report = "validated-extraction-stats")                     

