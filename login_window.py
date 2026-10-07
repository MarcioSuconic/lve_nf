#/home/marcio/Desktop/projetos/lve_nf/login_window.py
import tkinter as tk
from tkinter import ttk


class LoginWindow:
    def __init__(self, parent, api, on_success):
        self.parent = parent
        self.api = api
        self.on_success = on_success

        self.parent.geometry("360x220")
        self.parent.resizable(False, False)

        frm = ttk.Frame(self.parent, padding=20)
        frm.pack(fill="both", expand=True)

        ttk.Label(
            frm, text="LVE — Cadastro de NF", font=("", 12, "bold"),
        ).grid(row=0, column=0, columnspan=2, pady=(0, 14), sticky="w")

        ttk.Label(frm, text="Usuário:").grid(row=1, column=0, sticky="w", pady=4)
        self.username_var = tk.StringVar()
        entry_user = ttk.Entry(frm, textvariable=self.username_var, width=28)
        entry_user.grid(row=1, column=1, pady=4)

        ttk.Label(frm, text="Senha:").grid(row=2, column=0, sticky="w", pady=4)
        self.password_var = tk.StringVar()
        entry_pwd = ttk.Entry(
            frm, textvariable=self.password_var, show="*", width=28,
        )
        entry_pwd.grid(row=2, column=1, pady=4)

        self.status_var = tk.StringVar()
        ttk.Label(
            frm, textvariable=self.status_var, foreground="red",
        ).grid(row=3, column=0, columnspan=2, pady=(6, 0), sticky="w")

        self.login_btn = ttk.Button(frm, text="Entrar", command=self.do_login)
        self.login_btn.grid(row=4, column=0, columnspan=2, pady=(14, 0), sticky="ew")

        entry_user.focus_set()
        entry_pwd.bind("<Return>", lambda e: self.do_login())

    def do_login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get()
        if not username or not password:
            self.status_var.set("Preencha usuário e senha.")
            return

        self.login_btn.config(state="disabled")
        self.status_var.set("Entrando...")
        self.parent.update_idletasks()

        try:
            self.api.login(username, password)
        except Exception as e:
            self.status_var.set(str(e))
            self.login_btn.config(state="normal")
            return

        self.on_success()