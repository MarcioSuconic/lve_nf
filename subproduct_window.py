# lve_nf/subproduct_window.py
import tkinter as tk
from tkinter import messagebox, ttk


class SubProductWindow:
    """
    Tela de cadastro de Sub-produtos.

    Lista simples (nome, receita base, subtipo) com botões de ação.
    """

    def __init__(self, root, api, on_voltar=None):
        self.root = root
        self.api = api
        self.on_voltar = on_voltar

        self.root.title("LVE — Sub-produtos")
        self.root.geometry("1000x600")

        self.subproducts = []
        self.recipes = []
        self.subtypes = []

        self._load_all()
        self._build_ui()
        self._refresh_tree()

    # ----------------------------------------------------------------- load
    def _load_all(self):
        try:
            self.subproducts = self.api._get_paginated(
                "/api/sub-products/?active=true"
            )
            self.recipes = self.api.list_base_recipes()
            self.subtypes = self.api._get_paginated(
                "/api/sub-product-sub-types/?active=true"
            )
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar dados:\n{e}")
            self.root.destroy()
            raise SystemExit

        # Filtra ativos
        self.recipes = [r for r in self.recipes if r.get("active", True)]
        self.subtypes = [s for s in self.subtypes if s.get("active", True)]

    def _reload_subproducts(self):
        self.subproducts = self.api._get_paginated(
            "/api/sub-products/?active=true"
        )

    # ------------------------------------------------------------------ ui
    def _build_ui(self):
        header = ttk.Frame(self.root, padding=10)
        header.pack(fill="x")

        ttk.Label(
            header, text="Sub-produtos",
            font=("", 13, "bold"),
        ).pack(side="left")

        body = ttk.Frame(self.root, padding=10)
        body.pack(fill="both", expand=True)

        cols = ("sub_product", "base_recipe_name", "sub_product_sub_type_name")
        self.tree = ttk.Treeview(body, columns=cols, show="headings", height=18)
        self.tree.heading("sub_product", text="Sub-produto")
        self.tree.heading("base_recipe_name", text="Receita base")
        self.tree.heading(
            "sub_product_sub_type_name", text="Subtipo do sub-produto",
        )
        self.tree.column("sub_product", width=320)
        self.tree.column("base_recipe_name", width=320)
        self.tree.column("sub_product_sub_type_name", width=280)
        self.tree.pack(fill="both", expand=True)

        btns = ttk.Frame(body)
        btns.pack(fill="x", pady=(6, 0))
        ttk.Button(
            btns, text="+ Novo sub-produto", command=self._new_subproduct,
        ).pack(side="left", padx=2)
        ttk.Button(
            btns, text="Editar", command=self._edit_subproduct,
        ).pack(side="left", padx=2)
        ttk.Button(
            btns, text="Desativar", command=self._deactivate_subproduct,
        ).pack(side="left", padx=2)

        # Rodapé
        footer = ttk.Frame(self.root, padding=10)
        footer.pack(fill="x", side="bottom")
        if self.on_voltar:
            ttk.Button(
                footer, text="← Voltar", command=self.on_voltar,
            ).pack(side="left")

    # ----------------------------------------------------------------- tree
    def _refresh_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for s in self.subproducts:
            self.tree.insert("", "end", iid=str(s["id"]), values=(
                s["sub_product"],
                s.get("base_recipe_name", ""),
                s.get("sub_product_sub_type_name", ""),
            ))

    # -------------------------------------------------------------- actions
    def _new_subproduct(self):
        if not self.recipes:
            messagebox.showwarning(
                "Atenção",
                "Nenhuma receita base cadastrada. Cadastre uma receita antes.",
            )
            return
        if not self.subtypes:
            messagebox.showwarning(
                "Atenção",
                "Nenhum subtipo cadastrado. Cadastre um subtipo antes.",
            )
            return

        dlg = _SubProductDialog(
            self.root, self.api,
            subproduct=None,
            recipes=self.recipes,
            subtypes=self.subtypes,
        )
        self.root.wait_window(dlg)
        if not dlg.saved:
            return
        self._reload_subproducts()
        self._refresh_tree()

    def _edit_subproduct(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Atenção", "Selecione um sub-produto.")
            return
        sub = next(
            (s for s in self.subproducts if s["id"] == int(sel[0])), None,
        )
        if not sub:
            return
        dlg = _SubProductDialog(
            self.root, self.api,
            subproduct=sub,
            recipes=self.recipes,
            subtypes=self.subtypes,
        )
        self.root.wait_window(dlg)
        if not dlg.saved:
            return
        self._reload_subproducts()
        self._refresh_tree()

    def _deactivate_subproduct(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Atenção", "Selecione um sub-produto.")
            return
        sub_id = int(sel[0])
        sub = next((s for s in self.subproducts if s["id"] == sub_id), None)
        if not sub:
            return
        if not messagebox.askyesno(
            "Confirmar",
            f"Desativar '{sub['sub_product']}'?",
        ):
            return
        try:
            self.api._post(
                f"/api/sub-products/{sub_id}/",
                {**sub, "active": False},
                method="PATCH",
            )
        except Exception as e:
            messagebox.showerror("Erro", str(e))
            return
        self._reload_subproducts()
        self._refresh_tree()


# =========================================================================
# Dialog: Sub-produto
# =========================================================================
class _SubProductDialog(tk.Toplevel):
    def __init__(self, parent, api, subproduct, recipes, subtypes):
        super().__init__(parent)
        self.api = api
        self.subproduct = subproduct
        self.recipes = recipes
        self.subtypes = subtypes
        self.saved = False

        # Mapas nome → id
        self.recipe_id_by_label = {
            f'{r["base_recipe"]} (id {r["id"]})': r["id"] for r in recipes
        }
        self.subtype_id_by_label = {
            f'{s["sub_product_sub_type"]} '
            f'({s.get("sub_product_type_name", "?")})': s["id"]
            for s in subtypes
        }

        self.title(
            "Editar sub-produto" if subproduct else "Novo sub-produto"
        )
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)

        frm = ttk.Frame(self, padding=16)
        frm.pack(fill="both", expand=True)

        # Nome
        ttk.Label(frm, text="Nome:").grid(row=0, column=0, sticky="w", pady=4)
        self.name_var = tk.StringVar(
            value=(subproduct or {}).get("sub_product", "")
        )
        entry = ttk.Entry(frm, textvariable=self.name_var, width=42)
        entry.grid(row=0, column=1, pady=4)
        entry.focus_set()

        # Receita base
        ttk.Label(frm, text="Receita base:").grid(
            row=1, column=0, sticky="w", pady=4,
        )
        self.recipe_var = tk.StringVar()
        recipe_combo = ttk.Combobox(
            frm, textvariable=self.recipe_var,
            state="readonly", width=40,
            values=list(self.recipe_id_by_label.keys()),
        )
        recipe_combo.grid(row=1, column=1, pady=4)

        # Subtipo
        ttk.Label(frm, text="Subtipo:").grid(
            row=2, column=0, sticky="w", pady=4,
        )
        self.subtype_var = tk.StringVar()
        subtype_combo = ttk.Combobox(
            frm, textvariable=self.subtype_var,
            state="readonly", width=40,
            values=list(self.subtype_id_by_label.keys()),
        )
        subtype_combo.grid(row=2, column=1, pady=4)

        # Pré-seleciona se for edição
        if subproduct:
            rid = subproduct.get("base_recipe")
            for label, id_ in self.recipe_id_by_label.items():
                if id_ == rid:
                    self.recipe_var.set(label)
                    break
            sid = subproduct.get("sub_product_sub_type")
            for label, id_ in self.subtype_id_by_label.items():
                if id_ == sid:
                    self.subtype_var.set(label)
                    break

        # Botões
        btns = ttk.Frame(frm)
        btns.grid(row=3, column=0, columnspan=2, pady=(14, 0), sticky="e")
        ttk.Button(btns, text="Cancelar", command=self.destroy).pack(
            side="right", padx=4,
        )
        ttk.Button(btns, text="Salvar", command=self.save).pack(side="right")

        entry.bind("<Return>", lambda e: self.save())
        self.bind("<Escape>", lambda e: self.destroy())

    def save(self):
        nome = self.name_var.get().strip()
        if not nome:
            messagebox.showwarning("Atenção", "Informe o nome.", parent=self)
            return
        recipe_id = self.recipe_id_by_label.get(self.recipe_var.get())
        if not recipe_id:
            messagebox.showwarning(
                "Atenção", "Escolha a receita base.", parent=self,
            )
            return
        subtype_id = self.subtype_id_by_label.get(self.subtype_var.get())
        if not subtype_id:
            messagebox.showwarning(
                "Atenção", "Escolha o subtipo.", parent=self,
            )
            return

        payload = {
            "sub_product": nome,
            "base_recipe": recipe_id,
            "sub_product_sub_type": subtype_id,
            "active": True,
        }

        try:
            if self.subproduct:
                self.api._post(
                    f"/api/sub-products/{self.subproduct['id']}/",
                    payload, method="PUT",
                )
            else:
                self.api._post("/api/sub-products/", payload)
        except Exception as e:
            messagebox.showerror("Erro", str(e), parent=self)
            return

        self.saved = True
        self.destroy()