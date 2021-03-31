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
import dpiste.dal.neoscope

def stat_df(df):
 lines = df.shape[0]
 return pd.DataFrame(
  ([col, 
    f"{df[(df[col].isnull())].shape[0]/lines:,.0%}", 
    f"{df[col].dtype}", 
    f"{df[~df[col].isnull()][col].nunique()}",
    f"{df[~df[col].isnull()][col].size/df[~df[col].isnull()][col].nunique():.2f}"
    ] for col in df.columns)
  ,columns = ("column", "type", "empty", "unique", "avg repetition")
)

dfs = {}
dal.neoscope.neo_dfs(dfs)
```
# Neoscope import statistiques

## Dépistage
```python tags=["hide-input"]
stat_df(dal.neoscope.depistage_df(dfs))
```

## Dépistage na & dup
```python tags=["hide-input"]
print(f"NAq: {dfs['dépistage_na'].shape[0]}")
print(f"Duplicated: {dfs['dépistage_dup'].shape[0]}")
```

## Risque
```python tags=["hide-input"]
stat_df(dal.neoscope.risque_df(dfs))
```

## Risque na & dup
```python tags=["hide-input"]
print(f"NAq: {dfs['risque_na'].shape[0]}")
print(f"Duplicated: {dfs['risque_dup'].shape[0]}")
```

## Suivi
```python tags=["hide-input"]
stat_df(dal.neoscope.suivi_df(dfs))
```

## Suivi na & dup
```python tags=["hide-input"]
print(f"NAq: {dfs['suivi_na'].shape[0]}")
print(f"Duplicated: {dfs['suivi_dup'].shape[0]}")
```

## Population 
```python tags=["hide-input"]
stat_df(dal.neoscope.population_df(dfs))
```

## Population na & dup
```python tags=["hide-input"]
print(f"NAq: {dfs['population_na'].shape[0]}")
print(f"Duplicated: {dfs['population_dup'].shape[0]}")
```
