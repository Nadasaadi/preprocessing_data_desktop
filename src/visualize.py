import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import seaborn as sns
import pandas as pd

# --- STYLE GLOBAL ---
plt.style.use("seaborn-v0_8-muted")
sns.set_palette("deep")


# --------------------------------------------------
#  FONCTIONS UTILITAIRES
# --------------------------------------------------
def _numeric_columns(df: pd.DataFrame):
    """Retourne les colonnes numériques."""
    return df.select_dtypes(include=["float64", "int64"]).columns.tolist()


def _categorical_columns(df: pd.DataFrame):
    """Retourne les colonnes catégorielles (texte)."""
    return df.select_dtypes(include=["object", "category"]).columns.tolist()


# --------------------------------------------------
#  FENÊTRE PRINCIPALE DE VISUALISATION
# --------------------------------------------------
def visualize_interactive(df: pd.DataFrame, parent=None, default_vis="Histogramme"):
    """
    Ouvre une fenêtre Tkinter interactive avec adaptation IHM :
    - désactive les choix inutiles selon le type de graphique
    - gère les variables numériques et catégorielles
    - accepte un type de visualisation par défaut
    """
    num_cols = _numeric_columns(df)
    cat_cols = _categorical_columns(df)
    all_cols = cat_cols + num_cols

    if not all_cols:
        messagebox.showwarning("Aucune donnée", "Aucune colonne exploitable détectée.")
        return

    # --- FENÊTRE ---
    win = tk.Toplevel(parent)
    win.title("Visualisation des données")
    win.geometry("950x750")
    win.configure(bg="#f9fafc")

    # --- CADRE SUPERIEUR ---
    options_frame = ttk.LabelFrame(win, text=" Paramètres de visualisation ", padding=10)
    options_frame.pack(side="top", fill="x", padx=10, pady=10)

    ttk.Label(options_frame, text="Type de graphique :", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky="w")

    vis_types = [
        "Histogramme",
        "Diagramme en barres (catégoriel)",
        "Boxplot (catégorie ↔ numérique)",
        "Nuage de points (2 numériques)",
        "Heatmap de catégories",
        "Comparaison groupée (2 catégories)",
        "Matrice de corrélation"
    ]
    selected_vis = tk.StringVar(value=default_vis)  # 👈 par défaut, celui choisi dans le menu
    vis_menu = ttk.Combobox(options_frame, textvariable=selected_vis, values=vis_types, state="readonly", width=35)
    vis_menu.grid(row=0, column=1, padx=8, pady=5)

    ttk.Label(options_frame, text="Variable X :", font=("Segoe UI", 10, "bold")).grid(row=1, column=0, padx=5, pady=5, sticky="w")
    selected_x = tk.StringVar(value=all_cols[0])
    x_menu = ttk.Combobox(options_frame, textvariable=selected_x, values=all_cols, state="readonly", width=30)
    x_menu.grid(row=1, column=1, padx=8, pady=5)

    ttk.Label(options_frame, text="Variable Y :", font=("Segoe UI", 10, "bold")).grid(row=1, column=2, padx=5, pady=5, sticky="w")
    selected_y = tk.StringVar(value=all_cols[1] if len(all_cols) > 1 else all_cols[0])
    y_menu = ttk.Combobox(options_frame, textvariable=selected_y, values=all_cols, state="readonly", width=30)
    y_menu.grid(row=1, column=3, padx=8, pady=5)

    # --- BOUTON D’AFFICHAGE ---
    ttk.Button(
        options_frame,
        text="Afficher le graphique",
        command=lambda: _plot_selected(df, selected_vis.get(), selected_x.get(), selected_y.get(), canvas_frame),
        style="Accent.TButton"
    ).grid(row=2, column=0, columnspan=4, pady=10)

    # --- CADRE DU GRAPHIQUE ---
    canvas_frame = ttk.Frame(win)
    canvas_frame.pack(fill="both", expand=True, padx=10, pady=10)
    ttk.Label(canvas_frame, text="Sélectionnez un type et les variables, puis cliquez sur 'Afficher le graphique'.",
              font=("Segoe UI", 10, "italic"), foreground="#666").pack(pady=50)

    # --- STYLE BOUTONS ---
    style = ttk.Style()
    style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), padding=6)

    # --- MISE À JOUR IHM DYNAMIQUE ---
    def update_ui(event=None):
        """Adapte dynamiquement les menus selon le type de graphique choisi."""
        vis = selected_vis.get()
        x_menu.config(state="readonly")
        y_menu.config(state="readonly")

        if vis in ["Histogramme", "Diagramme en barres (catégoriel)"]:
            x_menu.config(values=all_cols)
            y_menu.set("")
            y_menu.config(state="disabled")

        elif vis == "Boxplot (catégorie ↔ numérique)":
            x_menu.config(values=cat_cols)
            y_menu.config(values=num_cols)
            x_menu.config(state="readonly")
            y_menu.config(state="readonly")

        elif vis == "Nuage de points (2 numériques)":
            x_menu.config(values=num_cols)
            y_menu.config(values=num_cols)
            x_menu.config(state="readonly")
            y_menu.config(state="readonly")

        elif vis in ["Heatmap de catégories", "Comparaison groupée (2 catégories)"]:
            x_menu.config(values=cat_cols)
            y_menu.config(values=cat_cols)
            x_menu.config(state="readonly")
            y_menu.config(state="readonly")

        elif vis == "Matrice de corrélation":
            x_menu.set("")
            y_menu.set("")
            x_menu.config(state="disabled")
            y_menu.config(state="disabled")

    vis_menu.bind("<<ComboboxSelected>>", update_ui)
    update_ui()  # initialisation correcte selon le type choisi

    # --- AUTO-AFFICHAGE DU GRAPHIQUE PAR DÉFAUT ---
    _plot_selected(df, default_vis, selected_x.get(), selected_y.get(), canvas_frame)


# --------------------------------------------------
#  FONCTION DE TRAÇAGE
# --------------------------------------------------
def _plot_selected(df: pd.DataFrame, vis_type: str, x_col: str, y_col: str, frame):
    """Trace le graphique choisi par l'utilisateur."""
    for widget in frame.winfo_children():
        widget.destroy()

    fig, ax = plt.subplots(figsize=(8, 5.5))

    try:
        if vis_type == "Histogramme":
            if x_col in _numeric_columns(df):
                sns.histplot(df[x_col].dropna(), bins=20, kde=True, ax=ax, color="#4ea8de")
                ax.set_title(f"Distribution de '{x_col}'")
            else:
                counts = df[x_col].value_counts()
                sns.barplot(x=counts.index, y=counts.values, ax=ax, color="#4ea8de")
                ax.set_title(f"Répartition de '{x_col}' (catégoriel)")
                ax.tick_params(axis='x', rotation=45)

        elif vis_type == "Diagramme en barres (catégoriel)":
            counts = df[x_col].value_counts().sort_values(ascending=False)
            sns.barplot(x=counts.index, y=counts.values, ax=ax, color="#4ea8de")
            ax.set_title(f"Diagramme en barres : '{x_col}'")
            ax.tick_params(axis='x', rotation=45)
            ax.set_ylabel("Fréquence")

        elif vis_type == "Boxplot (catégorie ↔ numérique)":
            if x_col in _categorical_columns(df) and y_col in _numeric_columns(df):
                sns.boxplot(x=df[x_col], y=df[y_col], ax=ax, palette="Set2")
                ax.set_title(f"Boxplot : {y_col} par {x_col}")
                ax.tick_params(axis='x', rotation=45)
            else:
                messagebox.showinfo("Info", "Choisissez une variable catégorielle pour X et une numérique pour Y.")
                return

        elif vis_type == "Nuage de points (2 numériques)":
            if x_col == y_col:
                messagebox.showinfo("Information", "Choisissez deux variables différentes pour le nuage de points.")
                return
            sns.scatterplot(data=df, x=x_col, y=y_col, ax=ax, color="#ff595e", edgecolor="black")
            ax.set_title(f"Nuage de points : {x_col} vs {y_col}")

        elif vis_type == "Heatmap de catégories":
            if x_col not in _categorical_columns(df) or y_col not in _categorical_columns(df):
                messagebox.showinfo("Info", "Les deux variables doivent être catégorielles.")
                return
            cross = pd.crosstab(df[x_col], df[y_col])
            sns.heatmap(cross, annot=True, cmap="YlGnBu", ax=ax)
            ax.set_title(f"Heatmap : {x_col} vs {y_col}")

        elif vis_type == "Comparaison groupée (2 catégories)":
            if x_col not in _categorical_columns(df) or y_col not in _categorical_columns(df):
                messagebox.showinfo("Info", "Les deux variables doivent être catégorielles.")
                return
            sns.countplot(x=x_col, hue=y_col, data=df, ax=ax, palette="husl")
            ax.set_title(f"Comparaison groupée : {x_col} vs {y_col}")
            ax.tick_params(axis='x', rotation=45)

        elif vis_type == "Matrice de corrélation":
            num_cols = _numeric_columns(df)
            if len(num_cols) < 2:
                messagebox.showinfo("Info", "Pas assez de colonnes numériques pour une matrice de corrélation.")
                return
            corr = df[num_cols].corr()
            sns.heatmap(corr, annot=True, cmap="coolwarm", ax=ax)
            ax.set_title("Matrice de corrélation")

        # --- Style global ---
        ax.set_xlabel(x_col)
        ax.grid(alpha=0.3)
        plt.tight_layout()

        # --- Intégration Tkinter ---
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible d'afficher la visualisation : {e}")
