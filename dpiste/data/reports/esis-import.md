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
import matplotlib.pyplot as plt


plt.rcParams['figure.figsize'] = [10, 5]
dfile = os.path.join(get_home(), "esis_dicom_guid.parquet")
guid = pd.read_parquet(dfile)
```

# Esis import analysis

## General metrics

```python tags=["hide-input"]
lines = guid.shape[0]
print(f"{lines:,.0f} lines")
print(f"{guid[guid.person_id.isnull()].shape[0]/lines:,.0%} without person_id")
print(f"{guid[guid.appointment_date.isnull()].shape[0]/lines:,.0%} without appointment_date")
print(f"{guid[guid.center_name.isnull()].shape[0]/lines:,.0%} without radiologist")
print(f"{guid[guid.mammogram_date.isnull()].shape[0]/lines:,.0%} without mammogram date")
guid["esis_links"] = (
  (guid.file_guid.str.len() > 10) |
  (guid.study_instance_uid.str.len() > 10) | 
  (guid.dicom_study_id.str.len() > 10)
)
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
  "file_guid":np.where(guid.file_guid.str.len() > 10, "Some", "-"),
  "study_instance_uid":np.where(guid.study_instance_uid.str.len() > 10, "Some", "-"), 
  "dicom_study_id": np.where(guid.dicom_study_id.str.len() > 10, "Some", "-")
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
n, bins, patches = plt.hist(months, bins = 50)
plt.ylabel('Number of images')
plt.xlabel('Months between appointment and mammogram date')
plt.show()

```

## Number of images per mammogral appointment
```python tags=["hide-input"]
mammo_count = ( 
  linked
    .groupby([linked.person_id, linked.appointment_date])
    .count()["center_name"] 
)
n, bins, patches = plt.hist(mammo_count)
plt.ylabel('Number of mammogramm per appointment')
plt.xlabel('Number of images taken')
plt.show()
```

