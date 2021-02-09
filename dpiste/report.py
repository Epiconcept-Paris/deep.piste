from docutils import nodes, utils, core
from io import StringIO
from docutils.parsers.rst import roles
import sys
import os
from pathlib import Path
from .utils import *

exec_env = {}

def execute_role(role, rawtext, text, lineno, inliner,options={}, content=[]):
  out0, err0 = sys.stdout, sys.stderr
  output, err = StringIO(), StringIO()
  
  sys.stdout = output
  sys.stderr = err
  try:
    exec(text, exec_env)
  finally:
    sys.stdout = out0
    sys.stderr = err0

  results = list()
  results.append(output.getvalue())
  results.append(err.getvalue())
  results = ''.join(results)
  node = nodes.Text(results, results)
  return [node], []
  
def generate(source = None, dest = None, env = None):
  """
  generate HTML reports from a folder with structured text files
  python blocs can be evaluated with the :python:`print("hello")` syntax
  other docutils roles are also supported
  source: de folder containing the st files to transform into html files
  dest: the destination folder to store destination HTML files 
  """
  #ensuring source & destination folder exists 
  pkg_dir, this_filename = os.path.split(__file__)
  source = os.path.join(pkg_dir, "data/reports") if source == None else source 
  dest = os.path.join(get_home(), "reports") if dest == None else dest
  Path(source).mkdir(parents=False, exist_ok=True)
  Path(dest).mkdir(parents=False, exist_ok=True)

  #registering the python role if first call
  roles.register_local_role("python", execute_role)
  
  #setting environment if provided
  if env != None: 
    exec_env = env
  else:
    exec_env = {}

  #iterating over all reports
  for path in os.listdir(source):
    if path.endswith('.rst'):
      report_name = path[0:len(path)-4]
      print(f"generating report {report_name}")
      with open(os.path.join(source, path)) as f:
        st = f.read() 
        doc = core.publish_parts(st, writer_name='html')
      with open(os.path.join(dest, f"{report_name}.html"), 'w') as out:
        out.write(doc['whole'])
  
  exec_env = {} 

