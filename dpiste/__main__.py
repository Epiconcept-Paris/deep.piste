import sys
import argparse
from tkinter import Tk
from tkinter.filedialog import askopenfilename
from .p02_initial_extraction import *
from . import utils

def main(a):
  # Base argument parser
  parser = argparse.ArgumentParser()
  subs = parser.add_subparsers()
  
  # extract command
  extract_parser = subs.add_parser("extract", help = "Invoke initial extractions commands") 
  extract_subs = extract_parser.add_subparsers()

  # extract neoscope command
  neoextract_parser = extract_subs.add_parser("neoscope", help = "Invoke neoscope extractions commands") 
  neoextract_subs = neoextract_parser.add_subparsers()

  # -- get neoscope key to clipboard
  neokey2clipboard_parser = neoextract_subs.add_parser("readkey", aliases=['key'], help = "Copy the neoscope extraction key from qrcode to clipboard")
  neokey2clipboard_parser.set_defaults(func = do_neokey2clipboard)

  # -- encrypt neoscope extractions
  encrypt_neoextract_parser = neoextract_subs.add_parser("encrypt", help = "Encrypt neoscope extractions")
  encrypt_neoextract_parser.add_argument("-e", "--extractions", required=False, help="Path to a file containing the extraction files to be encryped. If not provided it will be prompted")
  encrypt_neoextract_parser.add_argument("-w", "--webcam", required=False, help="Flag to establish that system webcam will be used to get password", action = "store_true", default = False)
  encrypt_neoextract_parser.add_argument("-c", "--clipboard", required=False, help="Flag to establish that system clipboard will be used to get password", action = "store_true", default = True)
  encrypt_neoextract_parser.set_defaults(func = do_encrypt_neoscope_extractions)

  # -- upload encrypted files to epifiles
  neoextract2epifiles_parser = neoextract_subs.add_parser(
    "push2epifiles", 
    aliases=["push"], 
    help = "Push neoscope extractions to epifiles. Password will be requested or can be set on environmant variable DP_PWD_EPI_FILES"
  )
  neoextract2epifiles_parser.add_argument(
    "-e", 
    "--epifiles-host", 
    required=False, 
    help="epifiles base host, default = epifiles.voozanoo.net", 
    default = "epifiles.voozanoo.net"
  )
  neoextract2epifiles_parser.add_argument(
    "-r", 
    "--maven-repo", 
    required=False, 
    help="maven repository to use to download sparkly and dependencies, default = https://repo1.maven.org/maven2", 
    default = "https://repo1.maven.org/maven2"
  )
  neoextract2epifiles_parser.add_argument("-u", "--epi-user", required=True, help="login for connecting to epifiles")
  neoextract2epifiles_parser.set_defaults(func = do_neoextract2epifiles)

  # -- download encrypted files from epifiles
  epifiles2neoextract_parser = neoextract_subs.add_parser("pull2bigdata", aliases=["pull"], help = "Pull neoscope extractions from epifiles to big data infrastructure")
  epifiles2neoextract_parser.add_argument(
    "-e", 
    "--epifiles-host", 
    required=False, 
    help="epifiles base host, default = epifiles.voozanoo.net", 
    default = "epifiles.voozanoo.net"
  )
  epifiles2neoextract_parser.add_argument(
    "-r", 
    "--maven-repo", 
    required=False, 
    help="maven repository to use to download sparkly and dependencies, default = https://repo1.maven.org/maven2", 
    default = "https://repo1.maven.org/maven2"
  )
  epifiles2neoextract_parser.add_argument("-u", "--epi-user", required=True, help="login for connecting to epifiles")
  epifiles2neoextract_parser.set_defaults(func = do_epifiles2bigdata)
  
  # -- decrypt neoscope extractions
  decrypt_neoextract_parser = neoextract_subs.add_parser("decrypt", help = "Decrypt neoscope extractions")
  decrypt_neoextract_parser.set_defaults(func = do_decrypt_neoscope_extractions)
   
  # extract esis command
  esis_parser = extract_subs.add_parser("esis", help = "Invoke esis command") 
  esis_subs = esis_parser.add_subparsers()

  # -- get esis data dicom ids
  esis_get_guid = esis_subs.add_parser("dicom-guid", aliases=['guid'], help = "Get the list of dicom guids. Password will be requested or can be set on environmant variable DP_PWD_ESIS")
  esis_get_guid.add_argument(
    "-e", 
    "--esis-host", 
    required=False, 
    help="esis application host, default = https://neoesis.preprod.voozanoo.net/neodemat", 
    default = "https://neoesis.preprod.voozanoo.net/neodemat"
  )
  esis_get_guid.add_argument(
    "-n", 
    "--data-query", 
    required=False, 
    help="name or id of the data query to extract the guids", 
    default = "deep-piste-extract"
  )
  esis_get_guid.add_argument("-u", "--esis-user", required=True, help="login for connecting to esis")
  esis_get_guid.add_argument("-b", "--batch-size", required=False, help="batch size for data query pooling")
  esis_get_guid.add_argument("-r", "--remote-dest", required=False, help="remote destination if file has to sent to a remote server via ssh")
  esis_get_guid.set_defaults(func = do_get_dicom_guid)
  
  # -- analyse esis dicom ids
  esis_reports = esis_subs.add_parser("report", help = "Produce a set of aggregation to manually validate de soundness of esis DICOM id validations")
  esis_reports.set_defaults(func = do_esis_report)

  # extract dcm4chee command
  dcm4chee_parser = extract_subs.add_parser("dcm4chee", help = "Invoke dcm4chee extractions commands") 
  dcm4chee_subs = dcm4chee_parser.add_subparsers()

  # -- get dicom parser
  get_dicom_parser = dcm4chee_subs.add_parser("dicom", help = "Get dicom files from dcm4chee")
  get_dicom_parser.add_argument("-s", "--server", required=True, help="Path to a file containing the extraction files to be encryped. If not provided it will be prompted")
  get_dicom_parser.add_argument("-p", "--port", required=False, help="Flag to establish that system webcam will be used to get password", default = 11112)
  get_dicom_parser.set_defaults(func = do_get_dicom)
  
  #calling handlers
  func = None
  try:
    args = parser.parse_args()
    func = args.func
  except AttributeError:
    parser.print_help()
  if func != None:
    args.func(args, parser)
  

# handlers
def do_neokey2clipboard(args, *other):
  p02_002_neoscope_key_to_clipboard()

def do_encrypt_neoscope_extractions(args, *other):
  get_home()
  if args.extractions == None:
    print("Please chose the file to crypt")
    Tk().withdraw()
    filename = askopenfilename()
  else:
    filename = args.extractions
  p02_003_encrypt_neoscope_extractions(source = filename, webcam_pwd = args.webcam, clipboard_pwd = args.clipbord)   

def do_neoextract2epifiles(args, *other):
  utils.prepare_sparkly(repo = args.maven_repo)
  p02_004_send_neoscope_extractions_to_epifiles(
    epifiles = args.epifiles_host, 
    login=args.epi_user, 
    password=utils.get_password(f"epifiles", f"Password for {args.epi_user}")
  )
def do_epifiles2bigdata(args, *other):
  utils.prepare_sparkly(repo = args.maven_repo)
  p02_005_get_neoscope_extractions_from_epifiles(
    epifiles = args.epifiles_host, 
    login=args.epi_user, 
    password=utils.get_password(f"epifiles", f"Password for {args.epi_user}")
  )
def do_decrypt_neoscope_extractions(args, *other):
  p02_006_decrypt_neoscope_extractions(key = utils.get_password(f"neo_decrypt", f"Key for Neoscope extractions"))   

def do_get_dicom_guid(args, *other):
  p02_007_get_dicom_guid(
    esis_host = args.esis_host, 
    dataquery = args.data_query, 
    login=args.esis_user, 
    password = utils.get_password(f"esis", f"Esis password for getting dicom guid queries"), 
    batch_size = args.batch_size,
    remote_dest = args.remote_dest
  )   
def do_get_dicom(args, *other):
  p02_008_get_dicom(server = args.server, port = args.port)

def do_esis_report(args, *other):
  p02_010_dicom_guid_report() 

if __name__ == "__main__":
  main(sys.argv[1] if len(sys.argv)>1 else None)


