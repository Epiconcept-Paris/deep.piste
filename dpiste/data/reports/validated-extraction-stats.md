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
import pandas as pd
import numpy as np
import dpiste.dal as dal
import dpiste.dal.screening
from dpiste.utils import stat_df

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
cnam = dal.screening.cnam(dfs0)
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

## Confirming that only the excluded women explain the difference on the count per year of birth


