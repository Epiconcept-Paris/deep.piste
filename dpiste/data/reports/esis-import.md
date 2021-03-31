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

pd.set_option('display.max_rows', None)
plt.rcParams['figure.figsize'] = [10, 5]
```
# Esis import analysis

```python tags=["hide-cell"]
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
guid = dal.esis.dicom_guid(dfs)
```

## mammogram guid import
```python tags=["hide-input"]
stat_df(dfs["dicom_guid"])
```

## guid na & dup
```python tags=["hide-input"]
print(f"NAq: {dfs['dicom_guid_na'].shape[0]}")
print(f"Duplicated: {dfs['dicom_guid_dup'].shape[0]}")
```

## mammogram exams
```python tags=["hide-input"]
stat_df(dal.esis.dicom_exams(dfs))
```

```python tags=["hide-input"]
guid["esis_links"] = (
  (guid.file_guid.str.len() > 10) |
  (guid.study_instance_uid.str.len() > 10) | 
  (guid.dicom_study_id.str.len() > 10)
)
lines = guid.shape[0]
without_links = guid[~guid.esis_links]
linked = guid[guid.esis_links]
linked_and_mammodate = linked[pd.notna(linked.mammogram_date)]

print(f"{without_links.shape[0]/lines:,.0%} without link to esis via (file_guid, study_instance_id or dicom_study_id)")
print(f"{lines - without_links.shape[0]:,.0f} with link to esis via (file_guid, study_instance_id or dicom_study_id)")
print(f"{linked_and_mammodate.shape[0]/linked.shape[0]:,.0%} have also a mammogram date")
```

## Groups of dicom links

```python tags=["hide-input"]
pd.DataFrame({
  "file_guid":np.where(pd.notna(guid.file_guid), "Some", "-"),
  "study_instance_uid":np.where(pd.notna(guid.study_instance_uid), "Some", "-"), 
  "dicom_study_id": np.where(pd.notna(guid.dicom_study_id), "Some", "-")
}).groupby(
  ["file_guid", "study_instance_uid", "dicom_study_id"]
).size()

```

## Mammograms per year with esis links

```python tags=["hide-input"]
dates = linked.set_index(linked.appointment_date)
ret = (dates[["person_id"]]
  .groupby(dates.index.year)
  .count()
)
ret
```
## Mammograms per rediologist with esis links

```python tags=["hide-input"]
ret = (linked[["person_id"]]
  .groupby(linked.center_name)
  .count()
)
ret
```

## Distribution of months between appointment date and mammogram date
```python tags=["hide-input"]
months = (linked_and_mammodate.appointment_date - linked_and_mammodate.mammogram_date).map(lambda d: d.days/30)
negs = months.loc[lambda m: m < 0]
n, bins, patches = plt.hist(negs/12, bins = 50)
plt.ylabel('Number of images')
plt.xlabel('mammogram years before appointment date')
plt.show()
```
 
```python tags=["hide-input"]
less5y = months.loc[lambda m: (m >= 0) & (m <= 12*10)]
n, bins, patches = plt.hist(less5y, bins = 50)
plt.ylabel('Number of images')
plt.xlabel('Mammogram months after appointment date less than 10y')
plt.show()
```

```python tags=["hide-input"]
more5y = months.loc[lambda m: m > 12*10]
n, bins, patches = plt.hist(more5y/12, bins = 50)
plt.ylabel('Number of images')
plt.xlabel('Mammogram years 10y after appointment date')
plt.show()
```
## Number of images per mammogram appointment
```python tags=["hide-input"]
mammo_count = (
  linked
      .groupby([linked.person_id, linked.appointment_date])
          .count()["center_name"]
          )
less10 = mammo_count[lambda c: c <= 12]
more10 = mammo_count[lambda c: c > 12]
n, bins, patches = plt.hist(less10, bins = 12)
plt.ylabel('Number of mammogramm per appointment')
plt.xlabel('Number of images when less than 10')
plt.show()

n, bins, patches = plt.hist(more10, bins = 50)
plt.ylabel('Number of mammogramm per appointment')
plt.xlabel('Number of images taken where more than 12')
plt.show()
```


