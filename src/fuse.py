# fuse.py
import pandas as pd
import os
from tkinter import filedialog, messagebox
from datetime import datetime  # <-- pour créer un nom unique
import random

def detect_common_keys(df1: pd.DataFrame, df2: pd.DataFrame):
    """
    Détecte les colonnes communes entre deux DataFrames.
    Retourne une liste de colonnes communes potentielles.
    """
    return list(set(df1.columns).intersection(set(df2.columns)))


def fuse_datasets_interactive():
    """
    Ouvre deux fichiers CSV et fusionne automatiquement :
    - Si les colonnes sont identiques → concaténation verticale
    - Si une colonne clé commune est détectée → jointure horizontale
    """
    try:
        # --- Sélection des fichiers à fusionner ---
        file1_path = filedialog.askopenfilename(title="Sélectionner le premier dataset", filetypes=[("CSV Files", "*.csv")])
        if not file1_path:
            return

        file2_path = filedialog.askopenfilename(title="Sélectionner le second dataset", filetypes=[("CSV Files", "*.csv")])
        if not file2_path:
            return

        # --- Chargement des fichiers ---
        df1 = pd.read_csv(file1_path)
        df2 = pd.read_csv(file2_path)

        # --- Détection automatique du type de fusion ---
        common_cols = detect_common_keys(df1, df2)

        if set(df1.columns) == set(df2.columns):
            # 🔹 Fusion verticale
            df_final = pd.concat([df1, df2], ignore_index=True)
            fusion_type = "verticale (concaténation)"
        elif len(common_cols) > 0:
            # 🔹 Fusion horizontale (clé commune)
            key = common_cols[0]
            df_final = pd.merge(df1, df2, on=key, how="inner")
            fusion_type = f"horizontale (clé commune : {key})"
        else:
            messagebox.showerror("Erreur de fusion", "Aucune colonne commune trouvée entre les deux fichiers.")
            return

        # --- Nettoyage de base ---
        df_final.drop_duplicates(inplace=True)
        df_final.reset_index(drop=True, inplace=True)

        # --- Génération d'un nom de fichier unique ---
        os.makedirs("data", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_id = random.randint(1000, 9999)
        output_name = f"fused_dataset_{timestamp}_{random_id}.csv"
        output_path = os.path.join("data", output_name)

        # --- Sauvegarde du résultat ---
        df_final.to_csv(output_path, index=False)

        messagebox.showinfo(
            "Fusion réussie",
            f"✅ Fusion {fusion_type} réalisée avec succès.\n\n"
            f"Fichier fusionné : {output_name}\n"
            f"Dimensions finales : {df_final.shape[0]} lignes × {df_final.shape[1]} colonnes"
        )

        return df_final

    except Exception as e:
        messagebox.showerror("Erreur", f"Une erreur est survenue pendant la fusion :\n{e}")
 