import pydicom
import os
import pandas as pd

from dpiste.p11_hdh_data_transfer import renew_sftp
from dpiste.p11_hdh_encryption import p11_decrypt_hdh

TAG = 0x00400316

def calculate_sum_given_tag(folder: str) -> int:
    """Reads all mammograms in a folder and calculate the sum of xray values"""
    s = 0
    for file in os.listdir(folder):
        fpath = os.path.join(folder, file)
        ds = pydicom.dcmread(fpath)
        try:
            s += ds[TAG].value
        except KeyError:
            print(f'All mammograms do not contains field {TAG}')
            s = -1
            break
    return s


def download_and_deciffer_screening(tmp_fol: str) -> pd.DataFrame:
   c, sftp = renew_sftp('procom2.front2', 'HDH_deeppiste')
   local_path = os.path.join(tmp_fol, '/screening.csv.gpg')
   sftp.get('dpiste/screening.csv.gpg', local_path)
   unenc_local_path, extension = os.path.splitext(local_path)
   p11_decrypt_hdh(local_path, unenc_local_path)


def evaluate_consistency(folder: str, tmp_fol: str) -> None:
    
    # studies = get_studies()
    # filtered_studies = filter_studies(studies)
    # download_studies(filtered_studies)

    screening = download_and_deciffer_screening()
    #filtered_screening = filter_studies(screening)
    #download_studies(filtered_screening())
    s1 = calculate_sum_given_tag(folder)
    print(f'sum : {s1}')
    return

if __name__ == '__main__':
    evaluate_consistency(
        '/space/Work/william2/deep.piste/home/data/input/dcm4chee/consistency_test/2.16.840.1.113669.632.20.1390549518.537038478.10002684028',
        '/space/Work/william2/deep.piste/home/data/input/dcm4chee/consistency_test/tmp'
    )