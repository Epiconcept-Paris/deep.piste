import os
import pandas as pd

root_path = "/space/Work/william2/deep.piste/home/data/local_test/final"
studies_df_path = os.path.join(root_path, "studies.csv")

studies_df = pd.read_csv(studies_df_path)

matching_studies, total = 0, 0
for file in os.listdir(root_path):
    if not os.path.isdir(os.path.join(root_path, file)):
        continue
    
    study_id = file
    total += 1
    if len(studies_df[studies_df["study_pseudo_id"] == study_id]) != 0:
        matching_studies += 1

print(f"{matching_studies}/{total}")
