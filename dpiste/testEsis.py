import sys
import requests 
from requests.auth import HTTPBasicAuth 
import xmltodict
import json
import re
from types import SimpleNamespace
import pandas 
import numpy
    
def read_response(r):
  if r.status_code == 200 : 
    if re.search("xml|html", r.headers["content-type"]) != None :
      resp_dict=xmltodict.parse(r.text)
      return json.loads(json.dumps(resp_dict), object_hook=lambda d: SimpleNamespace(**d))
    elif re.search("json", r.headers["content-type"]) != None :
      return r.json(object_hook=lambda d: SimpleNamespace(**d))
    else :
      raise NotImplementedError(f"Handling content type { r.headers['content-type'] } is not supported @epi")
  else :
    raise ConnectionError(f"Got status {r.status_code}\n {r.text}")

def voo_parse(value, d_type):
  if value == None :
    return None
  elif d_type == "string":
    return str(value)
  elif d_type == "integer":
    return int(value)
  elif d_type == "primary_key":
    return int(value)
  elif d_type == "fkey_dico":
    return int(value)
  elif d_type == "fkey_varset":
    return int(value)
  elif d_type == "fkey_dico_ext":
    return str(value)
  elif d_type == False:
    return str(value)
  elif d_type == "date":
    return numpy.datetime64(value)
  elif d_type == "datetime":
    return numpy.datetime64(value)
  else:
    raise NotImplementedError(f"Parsing {value} as {d_type} is not yet implemented")

def voo_type(columns):
  for (name, column) in columns.items():
    d_type = column.type
    if d_type == "string":
      yield (name, numpy.str)
    elif d_type == "integer":
      yield (name, "Int64")
    elif d_type == "primary_key":
      yield (name, "Int64")
    elif d_type == "fkey_dico":
      yield (name, "Int64")
    elif d_type == "fkey_varset":
      yield (name, "Int64")
    elif d_type == "fkey_dico_ext":
      yield (name, "string")
    elif d_type == False:
      yield (name, "string")
    elif d_type == "date":
      yield (name, numpy.datetime64)
    elif d_type == "datetime":
      yield (name, numpy.datetime64)
    else:
      raise NotImplementedError(f"Parsing type '{d_type}' is not yet implemented")

def generate_rows(rows, columns) : 
  for r in rows:
    yield [voo_parse(getattr(r, field), columns[field].type) for field in list(columns.keys())] 

def get_datasets(voo_url, login, password) :
  r = requests.get(f'{voo_url}/ws/dataset', auth = HTTPBasicAuth(login, password)) 
  # print datasets
  ds = read_response(r)
  for d in ds.root.response.dataset :
    print(f"{d.id}\t{d.resource_id}\t{d.name}")

voo_url = 'https://neoesis.preprod.voozanoo.net/neodemat'
login = 'f.orchard'

if len(sys.argv) == 2 :
  get_datasets(voo_url, login, sys.argv[1])
elif len(sys.argv) == 3 : 
  r = requests.get(f'{voo_url}/ws/dataset/id/{int(sys.argv[2])}/format/json', auth = HTTPBasicAuth(login, sys.argv[1])) 
  ds = read_response(r)
  columns = dict([(n, getattr(ds.metadata.fields,n )) for n in dir(ds.metadata.fields) if re.match("^__", n) == None])
  data = generate_rows(ds.rowdata, columns)
  df = pandas.DataFrame(data = data, columns = columns.keys()).astype(dict(voo_type(columns)))
  print(df)

  #print(ds) 
#id/'+ oItem.id +'/format/json/
