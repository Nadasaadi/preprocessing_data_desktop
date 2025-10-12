import tkinter as tk
import os
import re
from auth_db import add_user, user_exists, verify_user


class AuthWindow:
    def __init__(self, master):
        self.master = master
        self.master.title("Gestion de Base de Données - Authentification")
        self.master.geometry("420x480")
        self.master.resizable(False, False)
        self.master.configure(bg="#f8f9fa")

        self.attempts = 0
        self.mode = "login"  # login ou register

        # --- TITRE ---
        tk.Label(
            master,
            text="Gestion de Base de Données",
            font=("Segoe UI", 16, "bold"),
            bg="#f8f9fa",
            fg="#2c3e50"
        ).pack(pady=(30, 12))

        # --- Nom d'utilisateur ---
        tk.Label(master, text="Nom d'utilisateur :", bg="#f8f9fa", font=("Segoe UI", 11)).pack()
        self.username_entry = tk.Entry(master, font=("Segoe UI", 11), width=32)
        self.username_entry.pack(pady=6)

        # --- Mot de passe ---
        tk.Label(master, text="Mot de passe :", bg="#f8f9fa", font=("Segoe UI", 11)).pack()
        self.password_entry = tk.Entry(master, show="*", font=("Segoe UI", 11), width=32)
        self.password_entry.pack(pady=6)

        # --- Afficher mot de passe ---
        self.show_pw_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            master,
            text="Afficher le mot de passe",
            variable=self.show_pw_var,
            bg="#f8f9fa",
            font=("Segoe UI", 9),
            command=self.toggle_password_visibility
        ).pack(pady=(0, 6))

        # --- Label d’erreur ---
        self.error_label = tk.Label(master, text="", bg="#f8f9fa", fg="red", font=("Segoe UI", 10))
        self.error_label.pack(pady=(6, 0))

        # --- Bouton principal ---
        self.action_button = tk.Button(
            master,
            text="Se connecter",
            command=self.login,
            bg="#3498db",
            fg="white",
            font=("Segoe UI", 11, "bold"),
            width=18,
            relief="flat",
            cursor="hand2"
        )
        self.action_button.pack(pady=12)

        # --- Lien bascule login/register ---
        self.toggle_link = tk.Label(
            master,
            text="Pas encore de compte ? S'inscrire",
            fg="#2980b9",
            bg="#f8f9fa",
            cursor="hand2",
            font=("Segoe UI", 10, "underline")
        )
        self.toggle_link.pack()
        self.toggle_link.bind("<Button-1>", self.toggle_mode)

        # --- Indicateur de force du mot de passe ---
        self.pw_hint = tk.Label(master, text="", bg="#f8f9fa", fg="#555", font=("Segoe UI", 9))
        self.pw_hint.pack(pady=(8, 0))

        self.password_entry.bind("<KeyRelease>", self.update_pw_hint)

    # --- FONCTIONS ---

    def toggle_password_visibility(self):
        if self.show_pw_var.get():
            self.password_entry.config(show="")
        else:
            self.password_entry.config(show="*")

    def toggle_mode(self, event=None):
        if self.mode == "login":
            self.mode = "register"
            self.action_button.config(text="S'inscrire", bg="#27ae60", command=self.register)
            self.toggle_link.config(text="Déjà un compte ? Se connecter")
            self.error_label.config(text="")
            self.pw_hint.config(text="")
        else:
            self.mode = "login"
            self.action_button.config(text="Se connecter", bg="#3498db", command=self.login)
            self.toggle_link.config(text="Pas encore de compte ? S'inscrire")
            self.error_label.config(text="")
            self.pw_hint.config(text="")

    def update_pw_hint(self, event=None):
        if self.mode != "register":
            self.pw_hint.config(text="")
            return
        pw = self.password_entry.get()
        ok, errs = self.check_password_strength(pw)
        if ok:
            self.pw_hint.config(text="Mot de passe conforme.", fg="#1e7e34")
        else:
            self.pw_hint.config(text="Exigences: " + ", ".join(errs[:3]), fg="#c0392b")

    def check_password_strength(self, pw):
        errors = []
        if len(pw) < 8: errors.append("Longueur minimale de 8 caractères")
        if not re.search(r'[A-Z]', pw): errors.append("une majuscule")
        if not re.search(r'[a-z]', pw): errors.append("une minuscule")
        if not re.search(r'\d', pw): errors.append("un chiffre")
        if not re.search(r'[\W_]', pw): errors.append("un symbole")
        return (len(errors) == 0), errors

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        self.error_label.config(text="")

        if not username or not password:
            self.error_label.config(text="Veuillez remplir tous les champs.")
            return

        if verify_user(username, password):
            self.master.destroy()
            import main_window
            main_window.launch_main_window()
        else:
            self.attempts += 1
            remaining = max(0, 3 - self.attempts)
            self.error_label.config(text=f"Identifiants invalides. Tentatives restantes : {remaining}")
            if self.attempts >= 3:
                self.master.destroy()
                os._exit(0)

    def register(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        self.error_label.config(text="")

        if not username or not password:
            self.error_label.config(text="Veuillez remplir tous les champs.")
            return

        ok, errs = self.check_password_strength(password)
        if not ok:
            self.error_label.config(text="Mot de passe faible : " + ", ".join(errs))
            return

        if user_exists(username):
            self.error_label.config(text="Ce nom d'utilisateur existe déjà.")
            return

        try:
            add_user(username, password)
            self.master.destroy()
            import main_window
            main_window.launch_main_window()
        except Exception as e:
            self.error_label.config(text=f"Erreur SQL : {e}")
