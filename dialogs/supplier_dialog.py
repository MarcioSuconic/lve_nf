#/home/marcio/Desktop/projetos/lve_nf/dialogs/supplier_dialog.py
import tkinter as tk
from tkinter import messagebox, ttk


class SupplierDialog(tk.Toplevel):
    def __init__(self, parent, api):
        super().__init__(parent)
        self.api = api
        self.created = None

        self.title("Novo fornecedor")
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)

        frm = ttk.Frame(self, padding=16)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="Nome do fornecedor:").grid(
            row=0, column=0, sticky="w", pady=4
        )
        self.name_var = tk.StringVar()
        entry = ttk.Entry(frm, textvariable=self.name_var, width=34)
        entry.grid(row=0, column=1, pady=4)
        entry.focus_set()

        btns = ttk.Frame(frm)
        btns.grid(row=1, column=0, columnspan=2, pady=(14, 0), sticky="e")
        ttk.Button(btns, text="Cancelar", command=self.destroy).pack(
            side="right", padx=4,
        )
        ttk.Button(btns, text="Salvar", command=self.save).pack(side="right")

        entry.bind("<Return>", lambda e: self.save())
        self.bind("<Escape>", lambda e: self.destroy())

    def save(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("Atenção", "Informe o nome.", parent=self)
            return
        try:
            created = self.api.create_supplier({"supplier": name, "active": True})
        except Exception as e:
            messagebox.showerror("Erro", str(e), parent=self)
            return
        self.created = created
        self.destroy()