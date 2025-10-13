import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import os

from preprocessing import handle_missing_data, normalize_data, standardize_data , variance_threshold_filter
from fuse import fuse_datasets
from visualize import visualize_interactive
from smart_preprocessing import analyze_dataset
from auto_analysis import run_auto_analysis  # <-- module de YData Profiling


DATA_DIR = "data"


# -----------------------------------------------------
#   FENÊTRE PRINCIPALE
# -----------------------------------------------------
def launch_main_window():
    os.makedirs(DATA_DIR, exist_ok=True)
    root = tk.Tk()
    root.title("Gestion de Base de Données - Analyse Étudiante")
    root.geometry("1100x650")
    root.minsize(900, 550)

    # --- BARRE DE MENU ---
    menubar = tk.Menu(root)
    root.config(menu=menubar)

    # --- MENU : FICHIER ---
    file_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Fichier", menu=file_menu)
    file_menu.add_command(label="Charger un CSV", command=lambda: import_csv(tree))
    file_menu.add_command(label="Supprimer un CSV", command=lambda: delete_csv(tree))
    file_menu.add_separator()
    file_menu.add_command(label="Quitter", command=root.destroy)

    # --- MENU : PRÉTRAITEMENT ---
    pre_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Prétraitement", menu=pre_menu)
    pre_menu.add_command(label="Gestion des valeurs manquantes", command=lambda: apply_preprocessing(tree, "missing"))
    pre_menu.add_command(label="Standardisation", command=lambda: apply_preprocessing(tree, "standardize"))
    pre_menu.add_command(label="Normalisation", command=lambda: apply_preprocessing(tree, "normalize"))
    pre_menu.add_command(label="Filtrage par variance", command=lambda: apply_preprocessing(tree, "variance"))


    pre_menu.add_separator()
    pre_menu.add_command(label="Analyse intelligente (auto)", command=lambda: open_smart_analysis(tree))
    pre_menu.add_command(label="Profiling avancé (YData)", command=lambda: open_auto_profiling(tree))  # <-- ajouté ici

    # --- MENU : VISUALISATION ---
    vis_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Visualisation", menu=vis_menu)

    vis_types = [
        "Histogramme",
        "Diagramme en barres (catégoriel)",
        "Boxplot (catégorie ↔ numérique)",
        "Nuage de points (2 numériques)",
        "Heatmap de catégories",
        "Comparaison groupée (2 catégories)",
        "Matrice de corrélation"
    ]
    for vis in vis_types:
        vis_menu.add_command(label=vis, command=lambda v=vis: open_visualization(tree, v))

    # --- MENU : FUSION ---
    fuse_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Fusion", menu=fuse_menu)
    fuse_menu.add_command(label="Fusionner les deux bases", command=fuse_datasets)

    # --- BARRE D’OUTILS ---
    toolbar = tk.Frame(root, relief="raised", bd=2, bg="#f0f0f0")
    toolbar.pack(side="top", fill="x")

    ttk.Button(toolbar, text="Importer CSV", command=lambda: import_csv(tree)).pack(side="left", padx=5, pady=3)
    ttk.Button(toolbar, text="Prétraiter", command=lambda: apply_preprocessing(tree, "missing")).pack(side="left", padx=5, pady=3)
    ttk.Button(toolbar, text="Visualiser", command=lambda: open_visualization(tree, "Histogramme")).pack(side="left", padx=5, pady=3)
    ttk.Button(toolbar, text="Fusionner", command=fuse_datasets).pack(side="left", padx=5, pady=3)
    ttk.Button(toolbar, text="Quitter", command=root.destroy).pack(side="right", padx=5, pady=3)

    # --- ZONE CENTRALE ---
    frame = ttk.Frame(root, padding=10)
    frame.pack(expand=True, fill="both")

    ttk.Label(frame, text="Bases de données disponibles :", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 8))

    global tree
    tree = ttk.Treeview(frame, columns=("Nom", "Taille (Ko)"), show="headings", height=10)
    tree.heading("Nom", text="Nom du fichier")
    tree.heading("Taille (Ko)", text="Taille (Ko)")
    tree.pack(expand=True, fill="both")
    tree.bind("<Double-1>", lambda e: open_dataset(tree))

    # --- BARRE D’ÉTAT ---
    status = tk.Label(root, text="Prêt", anchor="w", relief="sunken", bd=1)
    status.pack(side="bottom", fill="x")

    show_databases(tree)
    root.mainloop()


# -----------------------------------------------------
#   GESTION DES FICHIERS CSV
# -----------------------------------------------------
def show_databases(tree):
    tree.delete(*tree.get_children())
    if not os.path.exists(DATA_DIR):
        return
    files = [f for f in os.listdir(DATA_DIR) if f.lower().endswith(".csv")]
    for f in sorted(files):
        size_kb = round(os.path.getsize(os.path.join(DATA_DIR, f)) / 1024, 1)
        tree.insert("", "end", values=(f, size_kb))


def import_csv(tree):
    path = filedialog.askopenfilename(title="Sélectionner un fichier CSV", filetypes=[("CSV files", "*.csv")])
    if not path:
        return
    dest = os.path.join(DATA_DIR, os.path.basename(path))
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(path, "rb") as src, open(dest, "wb") as dst:
        dst.write(src.read())
    messagebox.showinfo("Importation", f"Fichier importé : {os.path.basename(path)}")
    show_databases(tree)


def delete_csv(tree):
    item = tree.selection()
    if not item:
        messagebox.showwarning("Attention", "Sélectionnez une base de données à supprimer.")
        return

    filename = tree.item(item, "values")[0]
    path = os.path.join(DATA_DIR, filename)

    confirm = messagebox.askyesno(
        "Confirmation",
        f"Êtes-vous sûr de vouloir supprimer la base de données :\n\n{filename} ?",
        icon="warning"
    )
    if not confirm:
        return

    try:
        os.remove(path)
        show_databases(tree)
        messagebox.showinfo("Supprimé", f"Le fichier '{filename}' a été supprimé avec succès.")
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible de supprimer le fichier : {e}")


# -----------------------------------------------------
#   OUVERTURE & PRÉTRAITEMENT
# -----------------------------------------------------
def open_dataset(tree):
    item = tree.selection()
    if not item:
        return
    filename = tree.item(item, "values")[0]
    path = os.path.join(DATA_DIR, filename)
    df = pd.read_csv(path)

    win = tk.Toplevel()
    win.title(f"Aperçu - {filename}")
    win.geometry("900x600")

    text = tk.Text(win, wrap="none", font=("Consolas", 10))
    text.pack(expand=True, fill="both")

    text.insert("end", f"--- {filename} ---\n\n")
    text.insert("end", f"Lignes : {df.shape[0]}, Colonnes : {df.shape[1]}\n\n")
    text.insert("end", str(df.head(8)))
    text.config(state="disabled")


def apply_preprocessing(tree, action):
    item = tree.selection()
    if not item:
        messagebox.showwarning("Attention", "Sélectionnez un fichier CSV.")
        return

    filename = tree.item(item, "values")[0]
    path = os.path.join(DATA_DIR, filename)
    df = pd.read_csv(path)

    if action == "missing":
        df_new, changed = handle_missing_data(df)
        if not changed:
            messagebox.showinfo(
                "Information",
                "Le dataset ne contient aucune valeur manquante. Aucun prétraitement nécessaire."
            )
            return
    elif action == "normalize":
        df_new = normalize_data(df)
    elif action == "standardize":
        df_new = standardize_data(df)
    elif action == "variance":
        df_new = variance_threshold_filter(df, threshold=0.01)
        messagebox.showinfo("Filtrage par variance", "Les colonnes à faible variance ont été supprimées.")
        
    
    else:
        messagebox.showerror("Erreur", "Action inconnue.")
        return

    out_name = f"{os.path.splitext(filename)[0]}_{action}.csv"
    df_new.to_csv(os.path.join(DATA_DIR, out_name), index=False)
    messagebox.showinfo("Succès", f"Prétraitement '{action}' appliqué → {out_name}")
    show_databases(tree)


# -----------------------------------------------------
#   VISUALISATION
# -----------------------------------------------------
def open_visualization(tree, vis_type):
    item = tree.selection()
    if not item:
        messagebox.showwarning("Attention", "Sélectionnez un fichier CSV.")
        return

    filename = tree.item(item, "values")[0]
    path = os.path.join(DATA_DIR, filename)

    try:
        df = pd.read_csv(path)
        visualize_interactive(df, parent=None, default_vis=vis_type)
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible de charger le dataset : {e}")


# -----------------------------------------------------
#   ANALYSE INTELLIGENTE DU PRÉTRAITEMENT
# -----------------------------------------------------
def open_smart_analysis(tree):
    """
    Analyse automatique d’un dataset et affichage des recommandations.
    """
    item = tree.selection()
    if not item:
        messagebox.showwarning("Attention", "Sélectionnez un fichier CSV.")
        return

    filename = tree.item(item, "values")[0]
    path = os.path.join(DATA_DIR, filename)
    df = pd.read_csv(path)

    suggestions, summary = analyze_dataset(df)

    win = tk.Toplevel()
    win.title("Analyse intelligente du prétraitement")
    win.geometry("700x500")

    ttk.Label(win, text=f"🔍 Analyse automatique de '{filename}'",
              font=("Segoe UI", 13, "bold")).pack(pady=10)

    frame = ttk.Frame(win, padding=10)
    frame.pack(expand=True, fill="both")

    treeview = ttk.Treeview(frame, columns=("type", "action", "reason"), show="headings", height=10)
    treeview.heading("type", text="Type de traitement")
    treeview.heading("action", text="Action recommandée")
    treeview.heading("reason", text="Raison")
    treeview.column("type", width=180)
    treeview.column("action", width=200)
    treeview.column("reason", width=320)
    treeview.pack(expand=True, fill="both")

    for s in suggestions:
        treeview.insert("", "end", values=(s["type"], s["action"], s["reason"]))

    ttk.Button(win, text="Appliquer automatiquement",
               command=lambda: apply_suggestions(df, suggestions, filename, win)).pack(pady=10)


def apply_suggestions(df, suggestions, filename, win):
    from preprocessing import handle_missing_data, normalize_data, standardize_data
    from sklearn.preprocessing import LabelEncoder, OneHotEncoder

    df_new = df.copy()

    for s in suggestions:
        t = s["type"].lower()

        if "manquantes" in t:
            df_new, changed = handle_missing_data(df_new)
            if not changed:
                messagebox.showinfo(
                    "Information",
                    "Le dataset ne contient aucune valeur manquante. Aucun prétraitement nécessaire."
                )
                continue  # passe au traitement suivant

            

        elif "standardisation" in t:
            df_new = standardize_data(df_new)

        elif "normalisation" in t and "aucune" not in s["action"].lower():
            df_new = normalize_data(df_new)

        elif "encodage" in t:
            # --- Encodage automatique des variables catégorielles ---
            cat_cols = df_new.select_dtypes(include=["object", "category"]).columns
            if len(cat_cols) == 0:
                continue

            # Choix du mode d’encodage selon le nombre de catégories
            for col in cat_cols:
                n_unique = df_new[col].nunique()
                if n_unique <= 10:
                    # Encodage One-Hot
                    onehot = pd.get_dummies(df_new[col], prefix=col)
                    df_new = pd.concat([df_new.drop(columns=[col]), onehot], axis=1)
                else:
                    # Label encoding si trop de modalités
                    le = LabelEncoder()
                    df_new[col] = le.fit_transform(df_new[col].astype(str))

    out_name = f"{os.path.splitext(filename)[0]}_smart.csv"
    df_new.to_csv(os.path.join(DATA_DIR, out_name), index=False)

    messagebox.showinfo(
        "Succès",
        f"Prétraitement intelligent appliqué → {out_name}\n"
        f"Les encodages catégoriels ont été générés automatiquement."
    )

    win.destroy()


# -----------------------------------------------------
#   PROFILING AVANCÉ (YData Profiling)
# -----------------------------------------------------
def open_auto_profiling(tree):
    """
    Génère une analyse automatique complète via YData Profiling.
    """
    item = tree.selection()
    if not item:
        messagebox.showwarning("Attention", "Sélectionnez un fichier CSV à analyser.")
        return

    filename = tree.item(item, "values")[0]
    path = os.path.join(DATA_DIR, filename)

    try:
        run_auto_analysis(path)
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible d’exécuter l’analyse automatique : {e}")
