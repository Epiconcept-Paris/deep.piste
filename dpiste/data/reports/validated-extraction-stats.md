---
jupyter:
  jupytext:
    cell_markers: region,endregion
    formats: ipynb,.pct.py:percent,.lgt.py:light,.spx.py:sphinx,md,Rmd,.pandoc.md:pandoc
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.1'
      jupytext_version: 1.1.0
  kernelspec:
    display_name: Python 3
    language: python
    name: python3
---

```python tags=["hide-cell"]
# imports and global parameters
import os
import json
import pandas as pd
import numpy as np

import dpiste.dal as dal
import dpiste.dal.screening
from dpiste.utils import stat_df, get_home, cleandir
from dpiste.tools.evaluate_consistency import run
from dpiste.p12_SNDS_match import p12_004_safe_file
from dpiste.p06_mammogram_extraction import (
  filter_depistage_pseudo,
  calculate_l1_l2_result,
  get_positive_studies_only,
  keep_only_studies_with_images
)

pd.options.mode.chained_assignment = None  # default='warn'

dfs = {}
cnam = dal.screening.cnam(dfs)
mapping = dal.screening.table_correspondance(dfs)
screening = dal.screening.depistage_pseudo(dfs)
mail = dal.screening.mail(dfs) 

pd.set_option('display.max_rows', None)
pd.set_option('display.max_colwidth', -1)

```
   
# Neoscope import statistiques

## CNAM
```python tags=["hide-input"]
stat_df(cnam)
```
## CNAM na & dup
```python tags=["hide-input"]
print(f"NAq: {dfs['cnam_na'].shape[0]}")
print(f"Duplicated: {dfs['cnam_dup'].shape[0]}")
```

## CNAM NSS na & dup
```python tags=["hide-input"]
print(f"NAq: {dfs['cnam_na_NNI_2'].shape[0]}")
print(f"Duplicated: {dfs['cnam_dup_NNI_2'].shape[0]}")
```


## NSS Mapping table
```python tags=["hide-input"]
stat_df(mapping)
```

## Risque na & dup
```python tags=["hide-input"]
print(f"NAq: {dfs['table_correspondance_na'].shape[0]}")
print(f"Duplicated: {dfs['table_correspondance_dup'].shape[0]}")
```

## Mails
```python tags=["hide-input"]
stat_df(mail)
```

## Mails na & dup
```python tags=["hide-input"]
print(f"NAq: {dfs['mail_na'].shape[0]}")
print(f"Duplicated: {dfs['mail_dup'].shape[0]}")
```

## Pseudonimized screening
```python tags=["hide-input"]
stat_df(screening, disclose_limit = 500, undisclosed_types = ["datetime64[ns]"], metadata = dal.screening.metadata("dépistage_pseudo") )
```

## Pseudonimized na & dup
```python tags=["hide-input"]
print(f"NAq: {dfs['dépistage_pseudo_na'].shape[0]}")
print(f"Duplicated: {dfs['dépistage_pseudo_dup'].shape[0]}")
```

## Validating reconstruction of ACRS after anonymisation
```python tags=["hide-input"]

# rebuilding dataframe using mapping table
dfs0 = {}
cnam = p12_004_safe_file()
mapping = dal.screening.table_correspondance(dfs0)
screening = dal.screening.depistage_pseudo(dfs0)

rebuilt = (screening
  .join(mapping.join(cnam, "id_random", rsuffix = "_cn", lsuffix = "_mp"), "id_random", rsuffix = "_mp", lsuffix="_sc")[["NNI_2", "L1_ACR_SG", "Date_Mammo"]]
  .drop_duplicates(subset=["NNI_2", "Date_Mammo"], keep='last')
  .set_index(["NNI_2", "Date_Mammo"])
  )

# getting dataframe from neoscope extractions
dfs1 = {}
depist = dal.neoscope.depistage_df(dfs1)
pop = dal.neoscope.population_df(dfs1)

orig = (depist
  .join(pop, "id_bci", lsuffix = "dep", rsuffix = "pop")[["NNI_2", "L1_ACR_SG", "Date_Mammo"]]
  .drop_duplicates(subset=["NNI_2", "Date_Mammo"], keep='last')
  .set_index(["NNI_2", "Date_Mammo"])
)

#comparing results
joined = orig.join(rebuilt, on = ["NNI_2", "Date_Mammo"], how = "outer", lsuffix="_ori", rsuffix="_reb")
equals = joined[joined["L1_ACR_SG_ori"]==joined["L1_ACR_SG_reb"]]
print(f"Rebuilding a {rebuilt.shape[0] / orig.shape[0]:.4%}  of rows")
print(f"{equals.shape[0] / rebuilt.shape[0]:.4%} of rows are equal")

```

## Testing exclusion from refusing list
```python tags=["hide-input"]

refusing = dal.crcdc.refusing_list()
cnam = dal.screening.cnam()
notexcluded = cnam[cnam.NNI_2.astype(str).isin(refusing["NIR"].astype(str))]
print(f"{notexcluded.shape[0]} where found on CNAM extractions from {refusing.shape[0]} refusals")

```

## Validating HDH extraction
```python tags=["hide-input"]
#testpath = os.path.join(get_home(), 'consistency')
#os.mkdir(testpath) if not os.path.exists(testpath) else cleandir(testpath)
#s1, s2 = run(testpath, verbose=True)
#print('s1: Sum of field \'RelativeXRayExposure\' for deidentified DICOMs')
#print('s2: Sum of field \'RelativeXRayExposure\' for identified DICOMs')
#if s1 == s2:
#  print(f'Success: Both sums are equals to {s1} and {s2} on field comparison!')
#else:
#  print(f'Failure: s1 = {s1} and s2  = {s2}')
print("test ignored")
```
## Confirming that only the excluded women explain the difference on the count per year of birth

```python tags=["hide-input"]

df = dal.screening.depistage_pseudo()
df_with_study_id = filter_depistage_pseudo(df)
df_with_study_id["has_mammogram"] = df_with_study_id.apply(lambda row: 1 if not pd.isna(row["DICOM_Study"]) else 0, axis=1)
df_with_study_id_and_lecture_results = calculate_l1_l2_result(df_with_study_id)
df_with_positive_only = get_positive_studies_only(df_with_study_id_and_lecture_results)
df_without_nan_study_ids = keep_only_studies_with_images(df_with_positive_only)
```

## Matched study ids (screening with mammograms)

```python tags=["hide-input"]
df_with_study_id.groupby("has_mammogram")["has_mammogram"].count().to_frame()
```

## Testing L1L2_Results coherence

```python tags=["hide-input"]
print("Depistage Pseudo without has_mammogram: ")
print("Unfiltered")

df_with_study_id_and_lecture_results.groupby(["L1L2_positif", "L1_Result", "L2_Result"])["Date_Mammo"].count().to_frame().reset_index()
```

```python tags=["hide-input"]
print("Depistage Pseudo with has_mammogram: ")
print("Unfiltered")

df_with_study_id_and_lecture_results.groupby(["has_mammogram", "L1L2_positif", "L1_Result", "L2_Result"])["Date_Mammo"].count().to_frame().reset_index()
```
## Testing L1_Result coherence

```python tags=["hide-input"]
df_without_nan_study_ids.groupby(["L1_Result", "L1_ACR_SD", "L1_ACR_SG"])["Date_Mammo"].count().to_frame().reset_index()
```

## Testing L2_Result coherence

```python tags=["hide-input"]
df_without_nan_study_ids.groupby(["L2_Result", "L2_ACR_SD", "L2_ACR_SG"])["Date_Mammo"].count().to_frame().reset_index()
```

## Valid DICOM Extraction

```python tags=["hide-input"]
print("Number of DICOM Studies not NA")
print(df_with_study_id[pd.notna(df_with_study_id["DICOM_Studies"])]["DICOM_Studies"].count())

df_studies_no_mammo = df_with_study_id[(pd.notna(df_with_study_id["DICOM_Studies"])) & (df_with_study_id["has_mammogram"] == 0)]
print("Number of DICOM Studies not NA and has_mammogram == 0:")
print(df_studies_no_mammo["DICOM_Studies"].count())

ids = [patient_id for patient_id in df_studies_no_mammo["id_random"]]
print(f"Number of ids with studies and has_mammogram == 0: {len(ids)}")
total_common_dates = 0
total_dict_lines = 0
dates_without_mammo_per_year = {}
for patient_id in ids:
  df_for_patient = df_studies_no_mammo[df_studies_no_mammo["id_random"] == patient_id]
  dates_mammo = set([date.date() for date in set(df_for_patient["Date_Mammo"])])
  patient_studies_json = list(df_for_patient["DICOM_Studies"])
  studies_dates = set()
  nb_dict_lines = len(patient_studies_json)
  # Get all dates in DICOM_Studies and compare them to the dates in the col Date_Mammo
  for patient_study_json in patient_studies_json:
    patient_study_dict = json.loads(patient_study_json)
    new_studies_dates = [pd.Timestamp(study_date).date() for study_date in list(patient_study_dict.keys())]
    studies_dates.update(new_studies_dates)
  dates_without_mammo = dates_mammo - studies_dates
  # Mark down dates without associated mammograms in the referential
  for date in dates_without_mammo:
    try:
      dates_without_mammo_per_year[date.year] += 1
    except KeyError:
      dates_without_mammo_per_year[date.year] = 1

print("Number of Date_Mammo with no associated DICOM_Study per year:")
for year, number_of_dates_without_mammo in sorted(dates_without_mammo_per_year.items()):
  print(f"Year {year} : {number_of_dates_without_mammo}")
```

