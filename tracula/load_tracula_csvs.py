import os
import pandas as pd
from glob import glob

os.chdir("/Volumes/lhab_public/04_DataAnalysis/04-MRI/02-DTI/tracula_output/tracula_collect_tracts/out_overall/")

df = pd.DataFrame([])


for f in glob("*csv"):

    df_=pd.read_csv(f, sep=";")

    df_["tract"] = df_.columns[0]
    df_["sub_id"]=df_.ix[:,0].str.slice(stop=12)
    df_["ses_id"]=df_.ix[:,0].str.slice(start=17, stop=20)
    df = df.append(df_)

    df = df.set_index(df.sub_id)
