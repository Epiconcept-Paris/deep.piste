import os
from tkinter import Tk
from tkinter import filedialog
from kskit import java
from kskit import password
import os
import datetime
import pandas as pd
import json

def get_home(*paths):
  if os.environ.get('DP_HOME') == None :
    print("Please select the deep.piste home folder")
    os.environ['DP_HOME'] = filedialog.askdirectory()
    print(f"you have set  {os.environ.get('DP_HOME')} as epi home")
  base = os.environ.get('DP_HOME')
  paths = list(paths)
  paths.insert(0, base)
  if len(paths) > 1:
    os.makedirs(os.path.join(*paths[0:len(paths)-1]), exist_ok = True)
  return os.path.join(*paths)

def get_password(name, message):
  return password.get_password(f"DP_PWD_{name}", message)

def prepare_sparkly(repo):
  home = get_home()
  jars_path = os.path.join(home, "libs/jars")
  os.makedirs(jars_path, exist_ok=True)
  
  package_dir = os.path.abspath(os.path.dirname(__file__))
  sparkly_paths = os.path.join(package_dir, "data", "sparkly-maven-paths.url")
  
  java.build_classpath(repo, sparkly_paths, jars_path)


def sparkly_cp(source, dest):
  """
    Moving files from sparkly supported storage systems
  """ 
  java.java_job(main_class = "fr.epiconcept.sparkly.Command", class_path = f"{os.path.join(get_home(), 'libs', 'jars')}" , memory = "1g", args = ["storage", "cp", "from", source, "to", dest, "force", "true"])

def log(message):
  print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {message}")


def stat_df(df, disclose_limit = 100, undisclosed_types = {}, metadata = None):
  lines = df.shape[0]
  df =  pd.DataFrame(
    ([col, 
      f"{df[col].dtype}", 
      f"{df[(df[col].isnull())].shape[0]/lines:,.0%}", 
      f"{df[~df[col].isnull()][col].nunique()}",
      f"{df[~df[col].isnull()][col].size/df[~df[col].isnull()][col].nunique():.2f}",
      f"""{
        (
          df[col].astype('string')
            .to_frame()
            .groupby(col)[col]
            .size()
            .sort_values(ascending = False)
            .head(10)
            .to_dict()
        ) if df[col].nunique() < disclose_limit and df[col].dtype.name not in set(undisclosed_types) else 'undisclosed' }
      """
      ] for col in (df.columns if metadata is None else map(lambda m: m["column"], metadata))
    )
    ,columns = ("column", "type", "empty", "unique", "avg repetition", "values")
  )
  if metadata is not None:
    m = dict(map(lambda e: (e["column"], e), metadata))
    df["description"] = df["column"].map(lambda c: m[c]["description"])
    df["sensitivity"] = df["column"].map(lambda c: m[c]["sensitivity"])
    df = df[["column", "type", "empty", "unique", "avg repetition", "description", "sensitivity", "values"]]
  return df

def timeit(func):
  now = datetime.datetime.now()
  func()
  after = datetime.datetime.now()
  print((after-now).seconds)
  return func()

