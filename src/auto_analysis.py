import pandas as pd
from ydata_profiling import ProfileReport
import os
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox


def run_auto_analysis(csv_path: str):
    """
    Génère une analyse automatique complète via YData Profiling.
    Crée un rapport HTML interactif et propose de l’ouvrir.
    """
    try:
        # --- Chargement du dataset ---
        df = pd.read_csv(csv_path)

        # Vérification de base
        if df.empty:
            messagebox.showwarning("Avertissement", "Le fichier CSV est vide.")
            return

        # --- Génération du rapport ---
        profile = ProfileReport(
            df,
            title=f"Analyse automatique de {os.path.basename(csv_path)}",
            explorative=True,
            minimal=False,
            correlations={"auto": {"calculate": True}},
        )

        # --- Enregistrement ---
        report_path = os.path.splitext(csv_path)[0] + "_report.html"
        profile.to_file(report_path)

        # --- Fenêtre de résumé ---
        show_summary_window(report_path, df)

    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible d’exécuter l’analyse automatique :\n{e}")


def show_summary_window(report_path: str, df: pd.DataFrame):
    """
    Affiche un résumé de l’analyse et propose d’ouvrir le rapport HTML.
    """
    win = tk.Toplevel()
    win.title("Rapport automatique - YData Profiling")
    win.geometry("500x350")

    ttk.Label(
        win,
        text="📊 Rapport d’analyse automatique généré avec succès",
        font=("Segoe UI", 12, "bold"),
        wraplength=450
    ).pack(pady=15)

    # Statistiques rapides
    stats_frame = ttk.Frame(win)
    stats_frame.pack(pady=10)

    ttk.Label(stats_frame, text=f"Nombre de lignes : {df.shape[0]}").pack(anchor="w", pady=2)
    ttk.Label(stats_frame, text=f"Nombre de colonnes : {df.shape[1]}").pack(anchor="w", pady=2)

    num_cols = df.select_dtypes(include=["int64", "float64"]).columns
    cat_cols = df.select_dtypes(include=["object", "category"]).columns
    ttk.Label(stats_frame, text=f"Variables numériques : {len(num_cols)}").pack(anchor="w", pady=2)
    ttk.Label(stats_frame, text=f"Variables catégorielles : {len(cat_cols)}").pack(anchor="w", pady=2)

    ttk.Label(
        win,
        text="Le rapport complet contient les statistiques, corrélations,\nvaleurs manquantes et détection d’outliers.",
        wraplength=460,
        justify="center"
    ).pack(pady=15)

    ttk.Button(
        win,
        text="Ouvrir le rapport HTML",
        command=lambda: webbrowser.open(f"file://{os.path.abspath(report_path)}")
    ).pack(pady=5)

    ttk.Button(win, text="Fermer", command=win.destroy).pack(pady=5)
