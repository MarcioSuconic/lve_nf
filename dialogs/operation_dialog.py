# lve_nf/dialogs/operation_dialog.py
import tkinter as tk
from tkinter import messagebox, ttk


class OperationDialog(tk.Toplevel):
    """
    Modal para cadastrar/editar operação (OperationBaseRecipe).

    Regra de mão de obra:
      - Vazio  → usa o tempo do passo (fallback)
      - 0      → ninguém trabalha (ex: descansar)
      - > 0    → tempo fixo (ex: fornear = 1)
    """

    def __init__(self, parent, api, operation=None):
        super().__init__(parent)
        self.api = api
        self.created = None
        self.operation = operation
        self.is_edit = operation is not None

        self.title("Editar operação" if self.is_edit else "Nova operação")
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)

        frm = ttk.Frame(self, padding=16)
        frm.pack(fill="both", expand=True)

        row = 0

        # Nome
        ttk.Label(frm, text="Nome da operação:").grid(
            row=row, column=0, sticky="w", pady=4,
        )
        self.name_var = tk.StringVar(
            value=(operation or {}).get("operation_base_recipe", "")
        )
        entry = ttk.Entry(frm, textvariable=self.name_var, width=34)
        entry.grid(row=row, column=1, pady=4)
        entry.focus_set()
        row += 1

        # Descrição
        ttk.Label(frm, text="Descrição:").grid(
            row=row, column=0, sticky="w", pady=4,
        )
        self.desc_var = tk.StringVar(
            value=(operation or {}).get("description", "") or ""
        )
        ttk.Entry(frm, textvariable=self.desc_var, width=34).grid(
            row=row, column=1, pady=4,
        )
        row += 1

        # Mão de obra
        ttk.Label(frm, text="Mão de obra (min):").grid(
            row=row, column=0, sticky="w", pady=4,
        )
        valor_inicial = (operation or {}).get("labor_minutes")
        self.labor_var = tk.StringVar(
            value="" if valor_inicial is None else str(valor_inicial),
        )
        ttk.Entry(frm, textvariable=self.labor_var, width=10).grid(
            row=row, column=1, pady=4, sticky="w",
        )
        row += 1

        # Legenda
        legenda = ttk.Frame(frm)
        legenda.grid(row=row, column=0, columnspan=2, sticky="w", pady=(0, 8))
        ttk.Label(
            legenda,
            text="Vazio = usa o tempo do passo   |   "
                 "0 = ninguém trabalha   |   "
                 "> 0 = tempo fixo",
            foreground="#666",
            font=("", 8),
        ).pack(anchor="w")
        row += 1

        # Botões
        btns = ttk.Frame(frm)
        btns.grid(row=row, column=0, columnspan=2, pady=(14, 0), sticky="e")
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

        # Mão de obra: pode ser vazia (None), 0 ou > 0
        labor_str = self.labor_var.get().strip().replace(",", ".")
        if not labor_str:
            labor_minutes = None
        else:
            try:
                labor_minutes = float(labor_str)
            except ValueError:
                messagebox.showwarning(
                    "Atenção", "Mão de obra inválida.", parent=self,
                )
                return

        payload = {
            "operation_base_recipe": name,
            "description": self.desc_var.get().strip() or None,
            "labor_minutes": labor_minutes,
            "active": True,
        }

        try:
            if self.is_edit:
                created = self.api._post(
                    f"/api/operation-base-recipes/{self.operation['id']}/",
                    payload, method="PUT",
                )
            else:
                created = self.api._post(
                    "/api/operation-base-recipes/", payload,
                )
        except Exception as e:
            messagebox.showerror("Erro", str(e), parent=self)
            return

        self.created = created
        self.destroy()