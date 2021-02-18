import sys
import os
from pathlib import Path
from .utils import *
import jupytext
from nbconvert.preprocessors import ExecutePreprocessor
from nbconvert.exporters import HTMLExporter
from traitlets.config import Config


# Configure and run out exporter


def generate(source = None, dest = None, report = None):
  """
  generate jypyter HTML reports from a folder with markdown files
  python blocs can be evaluated with the the follwing syntax
  ```python
  print("hello")
  ```
  source: de folder containing the st files to transform into html files
  dest: the destination folder to store destination HTML files 
  """
  #ensuring source & destination folder exists 
  pkg_dir, this_filename = os.path.split(__file__)
  source = os.path.join(pkg_dir, "data/reports") if source == None else source 
  dest = os.path.join(get_home(), "reports") if dest == None else dest
  Path(source).mkdir(parents=False, exist_ok=True)
  Path(dest).mkdir(parents=False, exist_ok=True)

  #setting up the jupyter kernel name
  ep = ExecutePreprocessor(timeout=600, kernel_name='python3')
  c = Config()

  # Configure our tag removal
  c.TagRemovePreprocessor.remove_cell_tags = ("hide-cell",)
  c.TagRemovePreprocessor.remove_all_outputs_tags = ('hide-output',)
  c.TagRemovePreprocessor.remove_input_tags = ('hide-input',)
  c.HTMLExporter.preprocessors = ["nbconvert.preprocessors.TagRemovePreprocessor"]

  html_exporter = HTMLExporter(config=c)
  #html_exporter.template_name = 'classic'
  
  #iterating over all reports
  for path in os.listdir(source):
    if path.endswith('.md'):
      report_name = path[0:len(path)-3]
      if report == None or report_name == report:
        print(f"generating report {report_name}")
        nb = jupytext.read(os.path.join(source, path))   
        ep.preprocess(nb)             
        (body, resources) = html_exporter.from_notebook_node(nb)
        with open(os.path.join(dest, f"{report_name}.html"), 'w') as out:
          out.write(body)
  
  exec_env = {} 

