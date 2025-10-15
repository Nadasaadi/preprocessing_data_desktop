# main_gui.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import os
import threading
import time

# Import des fonctions externes (assure-toi que ces modules existent)
from preprocessing import (
    handle_missing_data,
    normalize_data,
    standardize_data,
    variance_threshold_filter,
    encode_categorical,
    label_encode_categorical,
)
from fuse import fuse_datasets_interactive
from visualize import visualize_interactive
from smart_preprocessing import analyze_dataset
from auto_analysis import run_auto_analysis  # module YData Profiling
from preprocessing import handle_outliers

DATA_DIR = "data"


# ---------------------------
# Utilitaires
# ---------------------------
def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


# ---------------------------
# Fenêtre principale
# ---------------------------
def launch_main_window():
    ensure_data_dir()
    root = tk.Tk()
    root.title("Gestion de Base de Données ")
    root.geometry("1100x650")
    root.minsize(900, 550)
    root._icons = {}

    # --- BARRE DE MENU ---
    menubar = tk.Menu(root)
    root.config(menu=menubar)

    # --- MENU : Fichier ---
    file_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Fichier", menu=file_menu)
    file_menu.add_command(label="Charger un CSV", command=lambda: import_csv(tree))
    file_menu.add_command(label="Supprimer un CSV", command=lambda: delete_csv(tree))
    file_menu.add_separator()
    file_menu.add_command(label="Quitter", command=root.destroy)

    # --- MENU : Prétraitement ---
    pre_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Prétraitement", menu=pre_menu)
    encode_menu = tk.Menu(pre_menu, tearoff=0)
    pre_menu.add_cascade(label="Encodage", menu=encode_menu)
    encode_menu.add_command(label="One-Hot Encoding", command=lambda: run_with_progress(tree, "onehot", root))
    encode_menu.add_command(label="Label Encoding", command=lambda: run_with_progress(tree, "label", root))
    pre_menu.add_command(label="Gestion des valeurs manquantes", command=lambda: run_with_progress(tree, "missing", root))
    pre_menu.add_command(label="Standardisation", command=lambda: run_with_progress(tree, "standardize", root))
    pre_menu.add_command(label="Normalisation", command=lambda: run_with_progress(tree, "normalize", root))
    pre_menu.add_command(label="Filtrage par variance", command=lambda: run_with_progress(tree, "variance", root))
    pre_menu.add_separator()
    pre_menu.add_command(label="Analyse intelligente (auto)", command=lambda: open_smart_analysis(tree))
    pre_menu.add_command(label="Profiling avancé (YData)", command=lambda: open_auto_profiling(tree))

    # --- MENU : Visualisation ---
    vis_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Visualisation", menu=vis_menu)
    vis_types = [
        "Histogramme",
        "Diagramme en barres (catégoriel)",
        "Boxplot (catégorie ↔ numérique)",
        "Nuage de points (2 numériques)",
        "Heatmap de catégories",
        "Comparaison groupée (2 catégories)",
        "Matrice de corrélation",
    ]
    for vis in vis_types:
        vis_menu.add_command(label=vis, command=lambda v=vis: open_visualization(tree, v))

    # --- MENU : Fusion ---
    menubar.add_command(label="Fusion", command=fuse_datasets_interactive)

    # --- MENU : Aide ---
    help_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Aide", menu=help_menu)
    help_menu.add_command(label="Guide d’utilisation", command=show_help)
    help_menu.add_command(label="À propos", command=show_about)

    # -------------------------------------------------
    # ✅ BARRE D'OUTILS (placée sous la barre de menu)
    # -------------------------------------------------
    toolbar = tk.Frame(root, relief="raised", bd=2, bg="#f0f0f0")
    toolbar.pack(side="top", fill="x")

    # Chargement et redimensionnement des icônes
    icon_files = {
        "import": "icons/importer.png",
        "process": "icons/procession.png",
        "visual": "icons/vision.png",
        "fuse": "icons/combiner-des-carres.png",
        "refresh": "icons/fleches-rotatives.png",
        "quit": "icons/porte.png",
    }

    try:
        from PIL import Image, ImageTk
        USE_PIL = True
    except ImportError:
        USE_PIL = False

    for key, path in icon_files.items():
        try:
            if os.path.exists(path):
                if USE_PIL:
                    img = Image.open(path).resize((20, 20), Image.LANCZOS)
                    img = ImageTk.PhotoImage(img)
                else:
                    img = tk.PhotoImage(file=path).subsample(3, 3)
            else:
                img = tk.PhotoImage(width=1, height=1)
        except Exception:
            img = tk.PhotoImage(width=1, height=1)
        root._icons[key] = img

    style = {"compound": "left", "padding": (4, 2)}
    ttk.Button(toolbar, image=root._icons["import"], command=lambda: import_csv(tree), **style).pack(side="left", padx=4, pady=3)
    ttk.Button(toolbar, image=root._icons["process"], command=lambda: run_with_progress(tree, "missing", root), **style).pack(side="left", padx=4, pady=3)
    ttk.Button(toolbar, image=root._icons["visual"], command=lambda: open_visualization(tree, "Histogramme"), **style).pack(side="left", padx=4, pady=3)
    ttk.Button(toolbar, image=root._icons["fuse"], command=fuse_datasets_interactive, **style).pack(side="left", padx=4, pady=3)
    ttk.Button(toolbar, image=root._icons["refresh"], command=lambda: show_databases(tree), **style).pack(side="left", padx=4, pady=3)
    ttk.Button(toolbar, image=root._icons["quit"], command=root.destroy, **style).pack(side="right", padx=4, pady=3)

    # -------------------------------------------------
    # ✅ ZONE CENTRALE (table des fichiers)
    # -------------------------------------------------
    frame = ttk.Frame(root, padding=10)
    frame.pack(expand=True, fill="both")

    ttk.Label(frame, text="Bases de données disponibles :", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 8))
    tree = ttk.Treeview(frame, columns=("Nom", "Taille (Ko)"), show="headings", height=12)
    tree.heading("Nom", text="Nom du fichier")
    tree.heading("Taille (Ko)", text="Taille (Ko)")
    tree.pack(expand=True, fill="both")
    tree.bind("<Double-1>", lambda e: open_dataset(tree))

    # Barre d’état
    status = tk.Label(root, text="Prêt", anchor="w", relief="sunken", bd=1)
    status.pack(side="bottom", fill="x")

    # Chargement initial
    show_databases(tree)
    root._tree = tree
    root._status = status
    root.mainloop()

# ---------------------------
# Gestion fichiers CSV
# ---------------------------
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
    try:
        with open(path, "rb") as src, open(dest, "wb") as dst:
            dst.write(src.read())
        messagebox.showinfo("Importation", f"Fichier importé : {os.path.basename(path)}")
        show_databases(tree)
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible d'importer le fichier : {e}")


def delete_csv(tree):
    item = tree.selection()
    if not item:
        messagebox.showwarning("Attention", "Sélectionnez une base de données à supprimer.")
        return

    filename = tree.item(item, "values")[0]
    path = os.path.join(DATA_DIR, filename)

    confirm = messagebox.askyesno("Confirmation", f"Êtes-vous sûr de vouloir supprimer :\n\n{filename} ?", icon="warning")
    if not confirm:
        return

    try:
        os.remove(path)
        show_databases(tree)
        messagebox.showinfo("Supprimé", f"Le fichier '{filename}' a été supprimé avec succès.")
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible de supprimer le fichier : {e}")


# ---------------------------
# Ouverture & preview dataset
# ---------------------------
def open_dataset(tree):
    item = tree.selection()
    if not item:
        return
    filename = tree.item(item, "values")[0]
    path = os.path.join(DATA_DIR, filename)
    try:
        df = pd.read_csv(path)
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible de lire le fichier : {e}")
        return

    win = tk.Toplevel()
    win.title(f"Aperçu - {filename}")
    win.geometry("900x600")

    top_label = ttk.Label(win, text=f"--- {filename} ---    Lignes : {df.shape[0]}    Colonnes : {df.shape[1]}")
    top_label.pack(anchor="w", padx=8, pady=6)

    text = tk.Text(win, wrap="none", font=("Consolas", 10))
    text.pack(expand=True, fill="both")

    # affichage des premières lignes
    text.insert("end", str(df.head(12)))
    text.config(state="disabled")


def apply_preprocessing(tree, action):
    item = tree.selection()
    if not item:
        messagebox.showwarning("Attention", "Sélectionnez un fichier CSV.")
        return

    filename = tree.item(item, "values")[0]
    path = os.path.join(DATA_DIR, filename)
    df = pd.read_csv(path)

    # --- Appliquer le prétraitement ---
    if action == "missing":
        df_new, changed = handle_missing_data(df)
        if not changed:
            messagebox.showinfo(
                "Information",
                "Le dataset ne contient aucune valeur manquante. Aucun prétraitement nécessaire."
            )
            return

    elif action == "onehot":
        df_new = encode_categorical(df)

    elif action == "label":
        df_new = label_encode_categorical(df)

    elif action == "normalize":
        df_new = normalize_data(df)

    elif action == "standardize":
        df_new = standardize_data(df)

    elif action == "variance":
        df_new = variance_threshold_filter(df, threshold=0.01)

    else:
        messagebox.showerror("Erreur", "Action inconnue.")
        return

    # --- Générer un nouveau nom de fichier pour ne pas écraser l'original ---
    base, ext = os.path.splitext(filename)
    new_filename = f"{base}_{action}{ext}"  # ex: "data_missing.csv"
    new_path = os.path.join(DATA_DIR, new_filename)

    # --- Sauvegarder le DataFrame prétraité ---
    df_new.to_csv(new_path, index=False)
    messagebox.showinfo("Terminé", f"Le prétraitement '{action}' a été appliqué.\nFichier enregistré : {new_filename}")

# ---------------------------
# Prétraitement & sauvegarde
# ---------------------------
def apply_suggestions(df, suggestions, filename, win):
    

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
            df_new = label_encode_categorical(df_new)


        elif "outliers":
            df_new = handle_outliers(df)

    out_name = f"{os.path.splitext(filename)[0]}_smart.csv"
    df_new.to_csv(os.path.join(DATA_DIR, out_name), index=False)

    messagebox.showinfo(
        "Succès",
        f"Prétraitement intelligent appliqué → {out_name}\n"
        f"Les encodages catégoriels ont été générés automatiquement."
    )

    win.destroy()

# ---------------------------
# Progress / threading wrapper
# ---------------------------
def run_with_progress(tree, action, parent_root=None):
    """
    Ouvre une petite fenêtre avec barre de progression indéterminée
    et exécute apply_preprocessing dans un thread.
    """
    progress_win = tk.Toplevel(parent_root) if parent_root else tk.Toplevel()
    progress_win.title("Traitement en cours...")
    progress_win.geometry("420x110")
    progress_win.resizable(False, False)

    ttk.Label(progress_win, text=f"Application du prétraitement : {action}", anchor="center").pack(pady=(12, 6))

    pb = ttk.Progressbar(progress_win, mode="indeterminate", length=360)
    pb.pack(pady=(0, 12))
    pb.start(12)

    # Désactiver la fenêtre principale si parent_root donné (optionnel)
    if parent_root:
        try:
            parent_root.attributes("-disabled", True)
        except Exception:
            pass

    def task():
        try:
            # Petite pause pour laisser l'UI répondre
            time.sleep(0.2)
            apply_preprocessing(tree, action)
        finally:
            # arrêt de la progressbar et fermeture
            try:
                pb.stop()
                progress_win.destroy()
                if parent_root:
                    parent_root.attributes("-disabled", False)
            except Exception:
                pass

    threading.Thread(target=task, daemon=True).start()


# ---------------------------
# Visualisation
# ---------------------------
def open_visualization(tree, vis_type):
    item = tree.selection()
    if not item:
        messagebox.showwarning("Attention", "Sélectionnez un fichier CSV.")
        return

    filename = tree.item(item, "values")[0]
    path = os.path.join(DATA_DIR, filename)

    try:
        df = pd.read_csv(path)
        # visualise dans une nouvelle fenêtre via la fonction externe
        visualize_interactive(df, parent=None, default_vis=vis_type)
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible de charger le dataset : {e}")


# ---------------------------
# Analyse intelligente (smart)
# ---------------------------
def open_smart_analysis(tree):
    item = tree.selection()
    if not item:
        messagebox.showwarning("Attention", "Sélectionnez un fichier CSV.")
        return

    filename = tree.item(item, "values")[0]
    path = os.path.join(DATA_DIR, filename)
    try:
        df = pd.read_csv(path)
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible de lire le fichier : {e}")
        return

    suggestions, summary = analyze_dataset(df)  # attend une liste de dicts

    win = tk.Toplevel()
    win.title("Analyse intelligente du prétraitement")
    win.geometry("700x500")

    ttk.Label(win, text=f"🔍 Analyse automatique de '{filename}'", font=("Segoe UI", 12, "bold")).pack(pady=8)

    frame = ttk.Frame(win, padding=8)
    frame.pack(expand=True, fill="both")

    treeview = ttk.Treeview(frame, columns=("type", "action", "reason"), show="headings", height=12)
    treeview.heading("type", text="Type de traitement")
    treeview.heading("action", text="Action recommandée")
    treeview.heading("reason", text="Raison")
    treeview.column("type", width=180)
    treeview.column("action", width=200)
    treeview.column("reason", width=320)
    treeview.pack(expand=True, fill="both")

    for s in suggestions:
        # assure que les clés existent
        t = s.get("type", "")
        a = s.get("action", "")
        r = s.get("reason", "")
        treeview.insert("", "end", values=(t, a, r))

    ttk.Button(win, text="Appliquer automatiquement", command=lambda: apply_suggestions(df, suggestions, filename, win)).pack(pady=8)


def apply_suggestions(df, suggestions, filename, win):
    from sklearn.preprocessing import LabelEncoder

    df_new = df.copy()

    for s in suggestions:
        t = s.get("type", "").lower()
        action = s.get("action", "").lower()

        try:
            if "manquantes" in t or "missing" in t:
                df_new, changed = handle_missing_data(df_new)
                if isinstance(changed, bool) and not changed:
                    continue

            elif "standardisation" in t or "standardize" in t:
                df_new = standardize_data(df_new)

            elif "normalisation" in t or "normalize" in t:
                if "aucune" not in action:
                    df_new = normalize_data(df_new)

            elif "encodage" in t or "encoding" in t:
                cat_cols = df_new.select_dtypes(include=["object", "category"]).columns
                if len(cat_cols) == 0:
                    continue
                for col in cat_cols:
                    n_unique = df_new[col].nunique()
                    if n_unique <= 10:
                        onehot = pd.get_dummies(df_new[col], prefix=col)
                        df_new = pd.concat([df_new.drop(columns=[col]), onehot], axis=1)
                    else:
                        le = LabelEncoder()
                        df_new[col] = le.fit_transform(df_new[col].astype(str))
        except Exception as e:
            # log minimal, mais on continue
            print("Erreur apply_suggestions:", e)

    out_name = f"{os.path.splitext(filename)[0]}_smart.csv"
    df_new.to_csv(os.path.join(DATA_DIR, out_name), index=False)

    messagebox.showinfo("Succès", f"Prétraitement intelligent appliqué → {out_name}")
    win.destroy()
    # refresh liste
    # si une fenêtre principale existe, on peut déclencher show_databases via root._tree
    # mais ici on laisse l'utilisateur rafraîchir manuellement (bouton Rafraîchir).


# ---------------------------
# Profiling avancé (YData)
# ---------------------------
def open_auto_profiling(tree):
    item = tree.selection()
    if not item:
        messagebox.showwarning("Attention", "Sélectionnez un fichier CSV à analyser.")
        return

    filename = tree.item(item, "values")[0]
    path = os.path.join(DATA_DIR, filename)

    # exécuter run_auto_analysis dans un thread — peut ouvrir un rapport HTML
    def task():
        try:
            run_auto_analysis(path)
            messagebox.showinfo("Profiling", "Analyse automatique terminée (vérifiez le dossier de sortie).")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d’exécuter l’analyse automatique : {e}")

    threading.Thread(target=task, daemon=True).start()


# ---------------------------
# Menu Aide
# ---------------------------
def show_help():
    messagebox.showinfo(
        "Aide",
        "🛈 Guide d’utilisation :\n\n"
        "- Importer : charger vos fichiers CSV\n"
        "- Prétraitement : nettoyer, encoder, normaliser vos données\n"
        "- Visualisation : explorer vos données\n"
        "- Fusion : combiner deux bases\n\n"
        "Heuristiques ergonomiques respectées :\n"
        "✔ Feedback (barre de progression)\n"
        "✔ Contrôle/confirmation (suppression)\n"
        "✔ Cohérence et reconnaissance (icônes + menus)\n"
        "✔ Visibilité de l'état (barre de status)"
    )


def show_about():
    messagebox.showinfo(
        "À propos",
        "Gestion de Base de Données - Analyse Étudiante\n"
        "Version 2.0 – Interface ergonomique Tkinter\n"
        "Développé par Nada Saadi et Chahd Necib © 2025",
    )
