import os
import stat
from tkinter import Tk
from tkinter import filedialog
from typing import Union
from paramiko.sftp_client import SFTPClient
import datetime
import pandas as pd
from kskit import java
from kskit import password

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

def recursive_count_files(dir: str) -> int:
  return sum(len(files) for _, _, files in os.walk(dir))

def cleandir(dirlist: Union[str, list], deldir=False) -> None:
  if type(dirlist) == str:
    dirlist = [dirlist]
  for repository in dirlist:
    for root, dirs, files in os.walk(repository):
      for file in files:
        os.remove(os.path.join(root, file))
    for root, dirs, files in os.walk(repository):
      for d in dirs:
        os.rmdir(os.path.join(root, d))
    os.rmdir(repository) if deldir else None

def avg_mammogram_size(dirpath: str) -> float:
  """Calculate the avg size of a mammogram (in bytes) based on a folder of studies"""
  s, nb_files = do_calculate_avg_file_size(dirpath, '.png')
  return round(s / nb_files, 2)

def do_calculate_avg_file_size(dirpath: str, extension: str = '') -> tuple:
  s, nb_files = 0, 0
  for file in os.listdir(dirpath):
    filepath = os.path.join(dirpath, file)
    if not os.path.isdir(filepath) and filepath.endswith(extension):
      s += os.stat(filepath).st_size
      nb_files += 1
    elif os.path.isdir(filepath):
      res = do_calculate_avg_file_size(filepath)
      s += res[0]
      nb_files += res[1]
  return s, nb_files

def sftp_recursive_count_files(path: str, sftp: SFTPClient) -> int:
  items = sftp.listdir(path)
  nb = 0
  for i in items:
     nb += len(sftp.listdir(os.path.join(path, i)))
  return nb

def sftp_reset(sftp: SFTPClient, path: str = None) -> None:
  """Clean an entire SFTP server from root"""
  path = '.' if path is None else path
  for file in sftp.listdir_attr(path):
    filepath = os.path.join(path, file.filename)
    if not stat.S_ISDIR(file.st_mode):
      sftp.remove(filepath)
    else:
      sftp_reset(sftp, path=filepath)
      sftp.rmdir(filepath)
  return

def sftp_cleandir(sftp: SFTPClient, dirpath: str, deldir=False) -> None:
  """Clean an entire SFTP folder including its subfolders"""
  for file in sftp.listdir_attr(dirpath):
    filepath = os.path.join(dirpath, file.filename)
    if not stat.S_ISDIR(file.st_mode):
      sftp.remove(filepath)
    else:
      sftp_cleandir(sftp, filepath, deldir=True)
  sftp.rmdir(dirpath) if deldir else None

def sftp_calculate_size(sftp: SFTPClient, dirpath: str = '.') -> int:
  """Calculate the size of a SFTP folder including all of its subdirectories"""
  sftp_size = 0
  for file in sftp.listdir_attr(dirpath):
    filepath = os.path.join(dirpath, file.filename)
    if not stat.S_ISDIR(file.st_mode):
      sftp_size += file.st_size
    else:
      sftp_size += sftp_calculate_size(sftp, filepath)
  return sftp_size
