# smart_preprocessing.py
import pandas as pd
import numpy as np

def analyze_dataset(df: pd.DataFrame):
    """
    Analyse la base et propose des recommandations de prétraitement
    selon des heuristiques statistiques simples.
    """
    suggestions = []
    summary = {}

    # --- 1️⃣ Données manquantes ---
    missing_rate = df.isna().mean()
    high_missing = missing_rate[missing_rate > 0.05]
    summary["missing_cols"] = high_missing.to_dict()
    if not high_missing.empty:
        suggestions.append({
            "type": "Gestion des valeurs manquantes",
            "action": "Imputation moyenne/mode",
            "reason": f"{len(high_missing)} colonnes contiennent plus de 5% de valeurs manquantes."
        })

    # --- 2️⃣ Données numériques ---
    num_df = df.select_dtypes(include=["float64", "int64"])
    if not num_df.empty:
        std_ratio = num_df.std().max() / max(num_df.std().min(), 1e-9)
        if std_ratio > 5:
            suggestions.append({
                "type": "Standardisation",
                "action": "StandardScaler()",
                "reason": "Les échelles des variables numériques sont très différentes."
            })
        elif num_df.min().min() >= 0 and num_df.max().max() <= 1:
            suggestions.append({
                "type": "Normalisation",
                "action": "Aucune (données déjà sur [0,1])",
                "reason": "Les données semblent déjà normalisées."
            })
        else:
            suggestions.append({
                "type": "Normalisation",
                "action": "MinMaxScaler()",
                "reason": "Les valeurs ne sont pas sur la même échelle."
            })

    # --- 3️⃣ Données catégorielles ---
    cat_df = df.select_dtypes(include=["object", "category"])
    if not cat_df.empty:
        suggestions.append({
            "type": "Encodage catégoriel",
            "action": "OneHot ou Label Encoding",
            "reason": f"{len(cat_df.columns)} colonnes catégorielles détectées."
        })

    # --- 4️⃣ Outliers ---
    if not num_df.empty:
        q1 = num_df.quantile(0.25)
        q3 = num_df.quantile(0.75)
        iqr = q3 - q1
        outlier_mask = ((num_df < (q1 - 1.5 * iqr)) | (num_df > (q3 + 1.5 * iqr)))
        outlier_rate = outlier_mask.mean().mean()
        if outlier_rate > 0.05:
            suggestions.append({
                "type": "Nettoyage d’outliers",
                "action": "Suppression ou winsorisation",
                "reason": f"{outlier_rate:.1%} de valeurs extrêmes détectées."
            })

    if not suggestions:
        suggestions.append({
            "type": "Aucun prétraitement nécessaire",
            "action": "Aucune",
            "reason": "Le dataset semble propre et bien formaté."
        })

    return suggestions, summary
