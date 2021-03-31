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
dal.screening.check_fks(dfs)
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
