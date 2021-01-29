import os
from tkinter import Tk
from tkinter import filedialog
from kskit import java
from kskit import password
def get_home():
  if os.environ.get('DP_HOME') == None :
    print("Please select the deep.piste home folder")
    os.environ['DP_HOME'] = filedialog.askdirectory()
    print(f"you have set  {os.environ.get('DP_HOME')} as epi home")
  return os.environ.get('DP_HOME')

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
