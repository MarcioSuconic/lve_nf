# lve_nf/subproduct_type_window.py
import tkinter as tk
from tkinter import messagebox, ttk


class SubProductTypeWindow:
    """
    Tela de Tipo + Subtipo de Sub-Produto (dois painéis).

    Painel esquerdo: lista de tipos.
    Painel direito: subtipos do tipo selecionado.
    """

    def __init__(self, root, api, on_voltar=None):
        self.root = root
        self.api = api
        self.on_voltar = on_voltar

        self.root.title("LVE — Tipos e Subtipos de Sub-Produto")
        self.root.geometry("1000x600")

        self.types = []
        self.subtypes = []
        self.current_type_id = None

        self._load_types()
        self._build_ui()
        self._refresh_types_tree()

    # ----------------------------------------------------------------- load
    def _load_types(self):
        try:
            self.types = self.api._get_paginated(
                "/api/sub-product-types/?active=true"
            )
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar tipos:\n{e}")
            self.root.destroy()
            raise SystemExit

    def _load_subtypes(self, type_id):
        try:
            self.subtypes = self.api._get_paginated(
                f"/api/sub-product-sub-types/?sub_product_type={type_id}&active=true"
            )
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar subtipos:\n{e}")
            self.subtypes = []

    # ------------------------------------------------------------------ ui
    def _build_ui(self):
        header = ttk.Frame(self.root, padding=10)
        header.pack(fill="x")

        ttk.Label(
            header, text="Tipos e Subtipos de Sub-Produto",
            font=("", 13, "bold"),
        ).pack(side="left")

        body = ttk.Frame(self.root, padding=10)
        body.pack(fill="both", expand=True)

        # -------- Painel esquerdo: tipos --------
        left = ttk.LabelFrame(body, text="Tipos", padding=8)
        left.pack(side="left", fill="both", expand=True, padx=(0, 5))

        cols_type = ("sub_product_type",)
        self.tree_type = ttk.Treeview(
            left, columns=cols_type, show="headings", height=18,
        )
        self.tree_type.heading("sub_product_type", text="Tipo")
        self.tree_type.column("sub_product_type", width=260)
        self.tree_type.pack(fill="both", expand=True)
        self.tree_type.bind("<<TreeviewSelect>>", self._on_type_select)

        btns_type = ttk.Frame(left)
        btns_type.pack(fill="x", pady=(6, 0))
        ttk.Button(
            btns_type, text="+ Novo tipo", command=self._new_type,
        ).pack(side="left", padx=2)
        ttk.Button(
            btns_type, text="Editar", command=self._edit_type,
        ).pack(side="left", padx=2)
        ttk.Button(
            btns_type, text="Desativar", command=self._deactivate_type,
        ).pack(side="left", padx=2)

        # -------- Painel direito: subtipos --------
        right = ttk.LabelFrame(body, text="Subtipos", padding=8)
        right.pack(side="left", fill="both", expand=True, padx=(5, 0))

        self.lbl_type_atual = ttk.Label(
            right, text="(selecione um tipo à esquerda)",
            foreground="#555",
        )
        self.lbl_type_atual.pack(anchor="w", pady=(0, 6))

        cols_sub = ("sub_product_sub_type",)
        self.tree_sub = ttk.Treeview(
            right, columns=cols_sub, show="headings", height=18,
        )
        self.tree_sub.heading("sub_product_sub_type", text="Subtipo")
        self.tree_sub.column("sub_product_sub_type", width=260)
        self.tree_sub.pack(fill="both", expand=True)

        btns_sub = ttk.Frame(right)
        btns_sub.pack(fill="x", pady=(6, 0))
        ttk.Button(
            btns_sub, text="+ Novo subtipo", command=self._new_subtype,
        ).pack(side="left", padx=2)
        ttk.Button(
            btns_sub, text="Editar", command=self._edit_subtype,
        ).pack(side="left", padx=2)
        ttk.Button(
            btns_sub, text="Desativar", command=self._deactivate_subtype,
        ).pack(side="left", padx=2)

        # -------- Rodapé --------
        footer = ttk.Frame(self.root, padding=10)
        footer.pack(fill="x", side="bottom")
        if self.on_voltar:
            ttk.Button(
                footer, text="← Voltar", command=self.on_voltar,
            ).pack(side="left")

    # ----------------------------------------------------------------- tree
    def _refresh_types_tree(self):
        for item in self.tree_type.get_children():
            self.tree_type.delete(item)
        for t in self.types:
            self.tree_type.insert("", "end", iid=str(t["id"]), values=(
                t["sub_product_type"],
            ))

    def _refresh_subtypes_tree(self):
        for item in self.tree_sub.get_children():
            self.tree_sub.delete(item)
        for s in self.subtypes:
            self.tree_sub.insert("", "end", iid=str(s["id"]), values=(
                s["sub_product_sub_type"],
            ))

    def _on_type_select(self, _event=None):
        sel = self.tree_type.selection()
        if not sel:
            return
        type_id = int(sel[0])
        self.current_type_id = type_id
        tipo = next((t for t in self.types if t["id"] == type_id), None)
        if tipo:
            self.lbl_type_atual.config(
                text=f"Tipo: {tipo['sub_product_type']}"
            )
        self._load_subtypes(type_id)
        self._refresh_subtypes_tree()

    # -------------------------------------------------------------- actions

    # ---- TIPO ----
    def _new_type(self):
        dlg = _TypeDialog(self.root, self.api, tipo=None)
        self.root.wait_window(dlg)
        if not dlg.saved:
            return
        self._load_types()
        self._refresh_types_tree()

    def _edit_type(self):
        sel = self.tree_type.selection()
        if not sel:
            messagebox.showinfo("Atenção", "Selecione um tipo.")
            return
        tipo = next(
            (t for t in self.types if t["id"] == int(sel[0])), None,
        )
        if not tipo:
            return
        dlg = _TypeDialog(self.root, self.api, tipo=tipo)
        self.root.wait_window(dlg)
        if not dlg.saved:
            return
        self._load_types()
        self._refresh_types_tree()

    def _deactivate_type(self):
        sel = self.tree_type.selection()
        if not sel:
            messagebox.showinfo("Atenção", "Selecione um tipo.")
            return
        type_id = int(sel[0])
        tipo = next((t for t in self.types if t["id"] == type_id), None)
        if not tipo:
            return
        if not messagebox.askyesno(
            "Confirmar",
            f"Desativar o tipo '{tipo['sub_product_type']}'?",
        ):
            return
        try:
            self.api._post(
                f"/api/sub-product-types/{type_id}/",
                {**tipo, "active": False},
                method="PATCH",
            )
        except Exception as e:
            messagebox.showerror("Erro", str(e))
            return
        self._load_types()
        self._refresh_types_tree()

    # ---- SUBTIPO ----
    def _new_subtype(self):
        if not self.current_type_id:
            messagebox.showinfo(
                "Atenção", "Selecione um tipo primeiro.",
            )
            return
        dlg = _SubTypeDialog(
            self.root, self.api,
            subtipo=None,
            type_id=self.current_type_id,
        )
        self.root.wait_window(dlg)
        if not dlg.saved:
            return
        self._load_subtypes(self.current_type_id)
        self._refresh_subtypes_tree()

    def _edit_subtype(self):
        sel = self.tree_sub.selection()
        if not sel:
            messagebox.showinfo("Atenção", "Selecione um subtipo.")
            return
        sub = next(
            (s for s in self.subtypes if s["id"] == int(sel[0])), None,
        )
        if not sub:
            return
        dlg = _SubTypeDialog(
            self.root, self.api,
            subtipo=sub,
            type_id=self.current_type_id,
        )
        self.root.wait_window(dlg)
        if not dlg.saved:
            return
        self._load_subtypes(self.current_type_id)
        self._refresh_subtypes_tree()

    def _deactivate_subtype(self):
        sel = self.tree_sub.selection()
        if not sel:
            messagebox.showinfo("Atenção", "Selecione um subtipo.")
            return
        sub_id = int(sel[0])
        sub = next((s for s in self.subtypes if s["id"] == sub_id), None)
        if not sub:
            return
        if not messagebox.askyesno(
            "Confirmar",
            f"Desativar o subtipo '{sub['sub_product_sub_type']}'?",
        ):
            return
        try:
            self.api._post(
                f"/api/sub-product-sub-types/{sub_id}/",
                {**sub, "active": False},
                method="PATCH",
            )
        except Exception as e:
            messagebox.showerror("Erro", str(e))
            return
        self._load_subtypes(self.current_type_id)
        self._refresh_subtypes_tree()


# =========================================================================
# Dialog: Tipo
# =========================================================================
class _TypeDialog(tk.Toplevel):
    def __init__(self, parent, api, tipo=None):
        super().__init__(parent)
        self.api = api
        self.tipo = tipo
        self.saved = False

        self.title("Editar tipo" if tipo else "Novo tipo")
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)

        frm = ttk.Frame(self, padding=16)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="Tipo:").grid(row=0, column=0, sticky="w", pady=4)
        self.name_var = tk.StringVar(
            value=(tipo or {}).get("sub_product_type", "")
        )
        entry = ttk.Entry(frm, textvariable=self.name_var, width=40)
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
        nome = self.name_var.get().strip()
        if not nome:
            messagebox.showwarning("Atenção", "Informe o tipo.", parent=self)
            return

        payload = {"sub_product_type": nome, "active": True}

        try:
            if self.tipo:
                self.api._post(
                    f"/api/sub-product-types/{self.tipo['id']}/",
                    payload, method="PUT",
                )
            else:
                self.api._post("/api/sub-product-types/", payload)
        except Exception as e:
            messagebox.showerror("Erro", str(e), parent=self)
            return

        self.saved = True
        self.destroy()


# =========================================================================
# Dialog: Subtipo
# =========================================================================
class _SubTypeDialog(tk.Toplevel):
    def __init__(self, parent, api, subtipo=None, type_id=None):
        super().__init__(parent)
        self.api = api
        self.subtipo = subtipo
        self.type_id = type_id
        self.saved = False

        self.title("Editar subtipo" if subtipo else "Novo subtipo")
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)

        frm = ttk.Frame(self, padding=16)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="Subtipo:").grid(
            row=0, column=0, sticky="w", pady=4,
        )
        self.name_var = tk.StringVar(
            value=(subtipo or {}).get("sub_product_sub_type", "")
        )
        entry = ttk.Entry(frm, textvariable=self.name_var, width=40)
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
        nome = self.name_var.get().strip()
        if not nome:
            messagebox.showwarning("Atenção", "Informe o subtipo.", parent=self)
            return

        payload = {
            "sub_product_sub_type": nome,
            "sub_product_type": self.type_id,
            "active": True,
        }

        try:
            if self.subtipo:
                self.api._post(
                    f"/api/sub-product-sub-types/{self.subtipo['id']}/",
                    payload, method="PUT",
                )
            else:
                self.api._post("/api/sub-product-sub-types/", payload)
        except Exception as e:
            messagebox.showerror("Erro", str(e), parent=self)
            return

        self.saved = True
        self.destroy()