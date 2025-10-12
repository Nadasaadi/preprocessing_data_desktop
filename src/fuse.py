# fuse.py
import pandas as pd
import os
from tkinter import messagebox

def fuse_datasets():
    try:
        df1 = pd.read_csv("data/Student Mental health.csv")
        df2 = pd.read_csv("data/Student Alcohol consumption.csv")

        df_merged = pd.concat([df1, df2], axis=0, ignore_index=True)
        df_merged.to_csv("data/fusion_result.csv", index=False)
        messagebox.showinfo("Fusion", "Les deux bases ont été fusionnées avec succès dans fusion_result.csv")
    except Exception as e:
        messagebox.showerror("Erreur", f"Erreur lors de la fusion : {e}")
