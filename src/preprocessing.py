# preprocess.py
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.feature_selection import VarianceThreshold


def handle_missing_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Traite les valeurs manquantes d'un DataFrame.
    Ne modifie le dataset que si des valeurs manquantes existent.
    Gère maintenant aussi les colonnes de type datetime.
    """
    df = df.copy()

    # --- Étape 1 : Normaliser les valeurs manquantes non standard ---
    df.replace(["?", "", " "], np.nan, inplace=True)

    # --- Vérifier s'il y a réellement des valeurs manquantes ---
    if df.isnull().sum().sum() == 0:
        return df, False  # pas de valeurs manquantes

    # --- Étape 2 : Supprimer les colonnes avec trop de valeurs manquantes ---
    threshold_col = 0.5  # si plus de 50% des valeurs sont manquantes
    df = df.loc[:, df.isnull().mean() < threshold_col]

    # --- Étape 3 : Remplir les valeurs manquantes ---
    for col in df.columns:
        if df[col].isnull().any():
            if pd.api.types.is_numeric_dtype(df[col]):
                df[col].fillna(df[col].mean(), inplace=True)
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col].fillna(df[col].median(), inplace=True)
            else:
                df[col].fillna(df[col].mode()[0], inplace=True)

    # --- Étape 4 : Supprimer les lignes restantes avec NaN ---
    df.dropna(inplace=True)

    return df, True


def normalize_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applique une normalisation Min-Max sur les colonnes numériques.
    """
    df = df.copy()
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
    if len(numeric_cols) > 0:
        scaler = MinMaxScaler()
        df[numeric_cols] = scaler.fit_transform(df[numeric_cols])
    return df


def standardize_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applique une standardisation (Z-score) sur les colonnes numériques.
    """
    df = df.copy()
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
    if len(numeric_cols) > 0:
        scaler = StandardScaler()
        df[numeric_cols] = scaler.fit_transform(df[numeric_cols])
    return df


def variance_threshold_filter(df: pd.DataFrame, threshold: float = 0.01) -> pd.DataFrame:
    """
    Supprime les colonnes dont la variance est inférieure au seuil spécifié.
    Utile pour réduire les features redondantes ou quasi constantes.

    Paramètres :
    - df : DataFrame d'entrée
    - threshold : seuil minimal de variance (par défaut 0.01)
    """
    df = df.copy()
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns

    if len(numeric_cols) == 0:
        return df  # rien à filtrer

    selector = VarianceThreshold(threshold=threshold)
    reduced_data = selector.fit_transform(df[numeric_cols])

    kept_features = [col for col, keep in zip(numeric_cols, selector.get_support()) if keep]
    df = df[kept_features + [col for col in df.columns if col not in numeric_cols]]

    return df
