# smart_preprocessing.py
import pandas as pd
import numpy as np
import re

def analyze_dataset(df: pd.DataFrame):
    """
    Analyse intelligente du dataset.
    Ignore les colonnes identifiants et applique des seuils souples.
    Retourne une liste de suggestions justifiées.
    """

    suggestions = []
    summary = {}

    # --- 0️⃣ Filtrage des colonnes identifiants ---
    id_like = [
        col for col in df.columns
        if re.search(r'\b(id|code|num|index|identifiant)\b', col.lower())
        or df[col].is_unique
    ]
    df = df.drop(columns=id_like, errors="ignore")

    if id_like:
        suggestions.append({
            "type": "Filtrage",
            "action": f"Ignoré {len(id_like)} colonne(s) identifiant",
            "reason": f"Colonnes identifiées comme ID : {', '.join(id_like)}",
            "justification": "Les identifiants ne nécessitent pas de prétraitement statistique."
        })

    # --- 1️⃣ Valeurs manquantes ---
    missing_rate = df.isna().mean()
    high_missing = missing_rate[missing_rate > 0.10]  # plus tolérant (10%)
    summary["missing_rate"] = missing_rate.to_dict()

    if not high_missing.empty:
        suggestions.append({
            "type": "Gestion des valeurs manquantes",
            "action": "Imputation moyenne/mode ou suppression",
            "reason": f"{len(high_missing)} colonnes >10% de NaN (max {high_missing.max():.1%})",
            "justification": "Un fort taux de valeurs manquantes peut fausser les analyses."
        })

    # --- 2️⃣ Variables numériques ---
    num_df = df.select_dtypes(include=["float64", "int64"])
    if not num_df.empty:
        summary["numeric_cols"] = num_df.columns.tolist()

        # Dispersion d'échelle
        stds = num_df.std()
        std_ratio = stds.max() / (stds.min() + 1e-9)

        if std_ratio > 10:  # plus tolérant (au lieu de 5)
            suggestions.append({
                "type": "Standardisation",
                "action": "StandardScaler()",
                "reason": f"Les échelles varient beaucoup (ratio std = {std_ratio:.1f})",
                "justification": "Recommandé pour équilibrer les variables de grande amplitude."
            })

        # Vérification normalisation
        min_val, max_val = num_df.min().min(), num_df.max().max()
        if min_val >= 0 and max_val > 1.5:
            suggestions.append({
                "type": "Normalisation",
                "action": "MinMaxScaler()",
                "reason": f"Les valeurs sont positives et non bornées (max = {max_val:.2f})",
                "justification": "Utile pour homogénéiser les variables positives."
            })
        elif min_val >= 0 and max_val <= 1.5:
            suggestions.append({
                "type": "Aucune normalisation nécessaire",
                "action": "Données déjà sur [0,1]",
                "reason": "Les données semblent déjà normalisées",
                "justification": "Pas besoin de retransformer les valeurs."
            })

    # --- 3️⃣ Variables catégorielles ---
    cat_df = df.select_dtypes(include=["object", "category"])
    if not cat_df.empty:
        summary["categorical_cols"] = cat_df.columns.tolist()
        suggestions.append({
            "type": "Encodage catégoriel",
            "action": "OneHotEncoder ou LabelEncoder",
            "reason": f"{len(cat_df.columns)} colonnes catégorielles détectées",
            "justification": "Les modèles statistiques nécessitent des données numériques."
        })

    # --- 4️⃣ Outliers ---
    if not num_df.empty:
        q1, q3 = num_df.quantile(0.25), num_df.quantile(0.75)
        iqr = q3 - q1
        outlier_mask = (num_df < (q1 - 1.5 * iqr)) | (num_df > (q3 + 1.5 * iqr))
        outlier_rate = outlier_mask.mean().mean()
        summary["outlier_rate"] = outlier_rate

        if outlier_rate > 0.10:  # 10% = seuil raisonnable
            suggestions.append({
                "type": "Nettoyage d’outliers",
                "action": "Suppression ou Winsorisation",
                "reason": f"{outlier_rate:.1%} de valeurs extrêmes détectées",
                "justification": "Les outliers influencent les moyennes et les modèles sensibles."
            })

    # --- 5️⃣ Dataset propre ---
    if len(suggestions) == 0:
        suggestions.append({
            "type": "Aucun prétraitement nécessaire",
            "action": "Aucune",
            "reason": "Aucune anomalie détectée",
            "justification": "Le dataset est déjà propre et équilibré."
        })

    return suggestions, summary
