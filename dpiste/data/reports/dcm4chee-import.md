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
from dpiste.utils import get_home 
from dpiste import dal
import matplotlib.pyplot as plt


plt.rcParams['figure.figsize'] = [10, 5]
dicom_df = dal.esis.dicom_df()
```
# Esis import analysis

## General metrics

```python tags=["hide-input"]
lines = dicom_df.shape[0]
print(f"{lines:,.0f} lines")
df = pd.DataFrame(
  ([col, 
    f"{dicom_df[(dicom_df[col].isnull()) | (dicom_df[col] == 'None')].shape[0]/lines:,.0%}", 
    f"{dicom_df[~((dicom_df[col].isnull()) | (dicom_df[col] == 'None'))][col].nunique()}",
    f"{dicom_df[~((dicom_df[col].isnull()) | (dicom_df[col] == 'None'))][col].size/dicom_df[~((dicom_df[col].isnull()) | (dicom_df[col] == 'None'))][col].nunique():.2f}",
    f"{', '.join(dicom_df[~((dicom_df[col].isnull()) | (dicom_df[col] == 'None'))][col].value_counts()[:10].index.tolist())}"[0:100]
    ] for col in dicom_df.columns)
  ,columns = ("column", "empty", "unique", "avg repetition", "samples")
)
pd.set_option('display.max_colwidth', None)
pd.options.display.max_rows = None
df
```



