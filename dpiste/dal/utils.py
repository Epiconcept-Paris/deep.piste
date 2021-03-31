import pandas as pd
import numpy as np
import functools
import json

def get_na_rows(df, pk):
  pk = [pk] if type(pk)==str else pk 
  nacond = map(lambda pkcol: pd.isna(df[pkcol]), pk)
  nacond = functools.reduce(lambda a,b: a | b , nacond)
  return df.loc[nacond]

def get_notna_rows(df, pk):
  pk = [pk] if type(pk)==str else pk 
  nacond = map(lambda pkcol: pd.isna(df[pkcol]), pk)
  nacond = functools.reduce(lambda a,b: a | b , nacond)
  return df.loc[~nacond]

def get_dup_rows(df, pk):
  pk = [pk] if type(pk)==str else pk 
  return df.loc[df.duplicated(subset = pk, keep = False)].sort_values(by = pk)

def get_nodup_rows(df, pk):
  pk = [pk] if type(pk)==str else pk 
  return df.drop_duplicates(pk, keep = "last", inplace = False, ignore_index = True)

def force_pk(df, pk):
  """
  Forcing pk to become uniques and not empty (removing rows not fulfilling this rule)
  """
  notna = get_notna_rows(df, pk)
  nodup = get_nodup_rows(notna, pk)

  assert nodup.shape[0] == nodup.groupby(pk).ngroups, f"variable {pk} is not unique on  Dataframe"
  
  pk = [pk] if type(pk)==str else pk 
  # setting pk as index
  nodup.set_index(keys = pk, inplace = True, drop = False)
  if len(pk) == 1:
    iname= "pk"
  else:
    iname = []
    for i in range(len(pk)):
      iname.append(f"pk_{i + 1}")
  nodup.index.rename(iname, inplace = True)
  return nodup

def check_fks(dfs, fks, pks):
  for fk in fks:
    fkcol = dfs[fk["fktable"]][fk["fkcol"]]
    pkcol = dfs[fk["pktable"]][pks[fk["pktable"]]]
    assert fkcol.dtype == pkcol.dtype, f"different dtypes on {fk} {fkcol.dtype} != {pkcol.dtype}"
    diff = set(fkcol.values).difference({pd.NA}).difference(set(pkcol.values))
    assert len(diff) == 0, f"foreign key {fk} violated by {len(diff)} elements, e.g. {list(diff)[0]}"


