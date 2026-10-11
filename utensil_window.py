# lve_nf/utensil_window.py
import tkinter as tk
from tkinter import messagebox, ttk


class UtensilWindow:
    """Tela de cadastro de Utensílio."""

    def __init__(self, root, api, on_voltar=None):
        self.root = root
        self.api = api
        self.on_voltar = on_voltar

        self.root.title("LVE — Utensílios")
        self.root.geometry("1100x600")

        self.utensils = []
        self.stores = []

        self._load_data()
        self._build_ui()
        self._refresh_tree()

    def _load_data(self):
        try:
            self.utensils = self.api._get_paginated(
                "/api/utensils/?active=true"
            )
            self.stores = self.api._get_paginated("/api/stores/?active=true")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar dados:\n{e}")
            self.root.destroy()
            raise SystemExit

        self.stores = [s for s in self.stores if s.get("active", True)]

    def _reload_utensils(self):
        self.utensils = self.api._get_paginated(
            "/api/utensils/?active=true"
        )

    def _build_ui(self):
        header = ttk.Frame(self.root, padding=10)
        header.pack(fill="x")

        ttk.Label(
            header, text="Utensílios",
            font=("", 13, "bold"),
        ).pack(side="left")

        body = ttk.Frame(self.root, padding=10)
        body.pack(fill="both", expand=True)

        cols = ("code", "utensil", "value", "store", "active")
        self.tree = ttk.Treeview(body, columns=cols, show="headings", height=16)
        for c, t, w in [
            ("code", "Código", 80),
            ("utensil", "Nome", 300),
            ("value", "Valor (R$)", 120),
            ("store", "Loja", 200),
            ("active", "Ativo", 60),
        ]:
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True)

        btns = ttk.Frame(body)
        btns.pack(fill="x", pady=(6, 0))
        ttk.Button(
            btns, text="+ Novo utensílio", command=self._new,
        ).pack(side="left", padx=2)
        ttk.Button(
            btns, text="Editar", command=self._edit,
        ).pack(side="left", padx=2)
        ttk.Button(
            btns, text="Desativar", command=self._deactivate,
        ).pack(side="left", padx=2)

        footer = ttk.Frame(self.root, padding=10)
        footer.pack(fill="x", side="bottom")
        if self.on_voltar:
            ttk.Button(
                footer, text="← Voltar", command=self.on_voltar,
            ).pack(side="left")

    def _refresh_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for u in self.utensils:
            self.tree.insert("", "end", iid=str(u["id"]), values=(
                u["code"],
                u["utensil"],
                u["value_utensil"],
                u.get("store_name", ""),
                "✓" if u.get("active") else "",
            ))

    def _new(self):
        if not self.stores:
            messagebox.showwarning(
                "Atenção", "Nenhuma loja cadastrada."
            )
            return
        dlg = _UtensilDialog(
            self.root, self.api, utensil=None, stores=self.stores,
        )
        self.root.wait_window(dlg)
        if not dlg.saved:
            return
        self._reload_utensils()
        self._refresh_tree()

    def _edit(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Atenção", "Selecione um utensílio.")
            return
        u = next(
            (x for x in self.utensils if x["id"] == int(sel[0])), None,
        )
        if not u:
            return
        dlg = _UtensilDialog(
            self.root, self.api, utensil=u, stores=self.stores,
        )
        self.root.wait_window(dlg)
        if not dlg.saved:
            return
        self._reload_utensils()
        self._refresh_tree()

    def _deactivate(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Atenção", "Selecione um utensílio.")
            return
        uid = int(sel[0])
        u = next((x for x in self.utensils if x["id"] == uid), None)
        if not u:
            return
        if not messagebox.askyesno(
            "Confirmar",
            f"Desativar '{u['utensil']}'?",
        ):
            return
        try:
            self.api._post(
                f"/api/utensils/{uid}/",
                {**u, "active": False},
                method="PATCH",
            )
        except Exception as e:
            messagebox.showerror("Erro", str(e))
            return
        self._reload_utensils()
        self._refresh_tree()


class _UtensilDialog(tk.Toplevel):
    def __init__(self, parent, api, utensil, stores):
        super().__init__(parent)
        self.api = api
        self.utensil = utensil
        self.saved = False

        self.store_id_by_name = {s["name_store"]: s["id"] for s in stores}

        self.title("Editar utensílio" if utensil else "Novo utensílio")
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)

        frm = ttk.Frame(self, padding=16)
        frm.pack(fill="both", expand=True)

        row = 0

        ttk.Label(frm, text="Nome:").grid(row=row, column=0, sticky="w", pady=4)
        self.name_var = tk.StringVar(
            value=(utensil or {}).get("utensil", "")
        )
        entry = ttk.Entry(frm, textvariable=self.name_var, width=42)
        entry.grid(row=row, column=1, pady=4, columnspan=2, sticky="we")
        entry.focus_set()
        row += 1

        ttk.Label(frm, text="Descrição:").grid(row=row, column=0, sticky="w", pady=4)
        self.desc_var = tk.StringVar(
            value=(utensil or {}).get("description", "")
        )
        ttk.Entry(frm, textvariable=self.desc_var, width=42).grid(
            row=row, column=1, pady=4, columnspan=2, sticky="we",
        )
        row += 1

        ttk.Label(frm, text="Código (6 chars):").grid(
            row=row, column=0, sticky="w", pady=4,
        )
        self.code_var = tk.StringVar(
            value=(utensil or {}).get("code", "")
        )
        ttk.Entry(frm, textvariable=self.code_var, width=10).grid(
            row=row, column=1, pady=4, sticky="w",
        )
        row += 1

        ttk.Label(frm, text="Valor (R$):").grid(
            row=row, column=0, sticky="w", pady=4,
        )
        self.value_var = tk.StringVar(
            value=str((utensil or {}).get("value_utensil", ""))
        )
        ttk.Entry(frm, textvariable=self.value_var, width=14).grid(
            row=row, column=1, pady=4, sticky="w",
        )
        row += 1

        ttk.Label(frm, text="Loja:").grid(row=row, column=0, sticky="w", pady=4)
        self.store_var = tk.StringVar()
        self.store_combo = ttk.Combobox(
            frm, textvariable=self.store_var,
            state="readonly", width=24,
            values=list(self.store_id_by_name.keys()),
        )
        self.store_combo.grid(row=row, column=1, pady=4, sticky="w")
        if utensil:
            for name, sid in self.store_id_by_name.items():
                if sid == utensil.get("store"):
                    self.store_var.set(name)
                    break
        elif self.store_id_by_name:
            self.store_var.set(list(self.store_id_by_name.keys())[0])
        row += 1

        btns = ttk.Frame(frm)
        btns.grid(row=row, column=0, columnspan=3, pady=(16, 0), sticky="e")
        ttk.Button(btns, text="Cancelar", command=self.destroy).pack(
            side="right", padx=4,
        )
        ttk.Button(btns, text="Salvar", command=self.save).pack(side="right")

        entry.bind("<Return>", lambda e: self.save())
        self.bind("<Escape>", lambda e: self.destroy())

    def save(self):
        nome = self.name_var.get().strip()
        desc = self.desc_var.get().strip()
        code = self.code_var.get().strip().upper()
        value = self.value_var.get().strip().replace(",", ".")
        store_id = self.store_id_by_name.get(self.store_var.get())

        if not nome:
            messagebox.showwarning("Atenção", "Informe o nome.", parent=self)
            return
        if not desc:
            messagebox.showwarning("Atenção", "Informe a descrição.", parent=self)
            return
        if not code or len(code) > 6:
            messagebox.showwarning(
                "Atenção", "Código obrigatório, máx. 6 caracteres.", parent=self,
            )
            return
        if not value:
            messagebox.showwarning("Atenção", "Informe o valor.", parent=self)
            return
        if not store_id:
            messagebox.showwarning("Atenção", "Escolha a loja.", parent=self)
            return

        payload = {
            "utensil": nome,
            "description": desc,
            "code": code,
            "value_utensil": value,
            "store": store_id,
            "active": True,
        }

        try:
            if self.utensil:
                self.api._post(
                    f"/api/utensils/{self.utensil['id']}/",
                    payload, method="PUT",
                )
            else:
                self.api._post("/api/utensils/", payload)
        except Exception as e:
            messagebox.showerror("Erro", str(e), parent=self)
            return

        self.saved = True
        self.destroy()