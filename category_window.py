# lve_nf/category_window.py
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk


class CategoryWindow:
    """
    Tela de Categoria + Subcategoria (dois painéis).

    Painel esquerdo: lista de categorias.
    Painel direito: subcategorias da categoria selecionada.
    """

    def __init__(self, root, api, on_voltar=None):
        self.root = root
        self.api = api
        self.on_voltar = on_voltar

        self.root.title("LVE — Categorias e Subcategorias")
        self.root.geometry("1000x600")

        self.categories = []
        self.subcategories = []
        self.current_category_id = None

        self._load_categories()
        self._build_ui()
        self._refresh_categories_tree()

    # ----------------------------------------------------------------- load
    def _load_categories(self):
        try:
            self.categories = self.api._get_paginated(
                "/api/product-categories/?active=true"
            )
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar categorias:\n{e}")
            self.root.destroy()
            raise SystemExit

    def _load_subcategories(self, category_id):
        try:
            self.subcategories = self.api._get_paginated(
                f"/api/product-sub-categories/?category={category_id}&active=true"
            )
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar subcategorias:\n{e}")
            self.subcategories = []

    # ------------------------------------------------------------------ ui
    def _build_ui(self):
        header = ttk.Frame(self.root, padding=10)
        header.pack(fill="x")

        ttk.Label(
            header, text="Categorias e Subcategorias",
            font=("", 13, "bold"),
        ).pack(side="left")

        # Dois painéis lado a lado
        body = ttk.Frame(self.root, padding=10)
        body.pack(fill="both", expand=True)

        # -------- Painel esquerdo: categorias --------
        left = ttk.LabelFrame(body, text="Categorias", padding=8)
        left.pack(side="left", fill="both", expand=True, padx=(0, 5))

        cols_cat = ("category", "description_menu")
        self.tree_cat = ttk.Treeview(
            left, columns=cols_cat, show="headings", height=18,
        )
        self.tree_cat.heading("category", text="Categoria")
        self.tree_cat.heading("description_menu", text="Descrição menu")
        self.tree_cat.column("category", width=180)
        self.tree_cat.column("description_menu", width=220)
        self.tree_cat.pack(fill="both", expand=True)
        self.tree_cat.bind("<<TreeviewSelect>>", self._on_category_select)

        btns_cat = ttk.Frame(left)
        btns_cat.pack(fill="x", pady=(6, 0))
        ttk.Button(
            btns_cat, text="+ Nova categoria", command=self._new_category,
        ).pack(side="left", padx=2)
        ttk.Button(
            btns_cat, text="Editar", command=self._edit_category,
        ).pack(side="left", padx=2)
        ttk.Button(
            btns_cat, text="Desativar", command=self._deactivate_category,
        ).pack(side="left", padx=2)

        # -------- Painel direito: subcategorias --------
        right = ttk.LabelFrame(body, text="Subcategorias", padding=8)
        right.pack(side="left", fill="both", expand=True, padx=(5, 0))

        self.lbl_cat_atual = ttk.Label(
            right, text="(selecione uma categoria à esquerda)",
            foreground="#555",
        )
        self.lbl_cat_atual.pack(anchor="w", pady=(0, 6))

        cols_sub = ("sub_category", "description_menu", "markup_default")
        self.tree_sub = ttk.Treeview(
            right, columns=cols_sub, show="headings", height=18,
        )
        self.tree_sub.heading("sub_category", text="Subcategoria")
        self.tree_sub.heading("description_menu", text="Descrição menu")
        self.tree_sub.heading("markup_default", text="Markup %")
        self.tree_sub.column("sub_category", width=180)
        self.tree_sub.column("description_menu", width=200)
        self.tree_sub.column("markup_default", width=80, anchor="e")
        self.tree_sub.pack(fill="both", expand=True)

        btns_sub = ttk.Frame(right)
        btns_sub.pack(fill="x", pady=(6, 0))
        ttk.Button(
            btns_sub, text="+ Nova subcategoria", command=self._new_subcategory,
        ).pack(side="left", padx=2)
        ttk.Button(
            btns_sub, text="Editar", command=self._edit_subcategory,
        ).pack(side="left", padx=2)
        ttk.Button(
            btns_sub, text="Desativar", command=self._deactivate_subcategory,
        ).pack(side="left", padx=2)

        # -------- Rodapé --------
        footer = ttk.Frame(self.root, padding=10)
        footer.pack(fill="x", side="bottom")
        if self.on_voltar:
            ttk.Button(
                footer, text="← Voltar", command=self.on_voltar,
            ).pack(side="left")

    # ----------------------------------------------------------------- tree
    def _refresh_categories_tree(self):
        for item in self.tree_cat.get_children():
            self.tree_cat.delete(item)
        for c in self.categories:
            self.tree_cat.insert("", "end", iid=str(c["id"]), values=(
                c["category"],
                c.get("description_menu", ""),
            ))

    def _refresh_subcategories_tree(self):
        for item in self.tree_sub.get_children():
            self.tree_sub.delete(item)
        for s in self.subcategories:
            self.tree_sub.insert("", "end", iid=str(s["id"]), values=(
                s["sub_category"],
                s.get("description_menu", ""),
                f'{s["markup_default"]}',
            ))

    def _on_category_select(self, _event=None):
        sel = self.tree_cat.selection()
        if not sel:
            return
        cat_id = int(sel[0])
        self.current_category_id = cat_id
        cat = next((c for c in self.categories if c["id"] == cat_id), None)
        if cat:
            self.lbl_cat_atual.config(
                text=f"Categoria: {cat['category']}"
            )
        self._load_subcategories(cat_id)
        self._refresh_subcategories_tree()

    # -------------------------------------------------------------- actions

    # ---- CATEGORIA ----
    def _new_category(self):
        dlg = _CategoryDialog(self.root, self.api, category=None)
        self.root.wait_window(dlg)
        if not dlg.saved:
            return
        self._load_categories()
        self._refresh_categories_tree()

    def _edit_category(self):
        sel = self.tree_cat.selection()
        if not sel:
            messagebox.showinfo("Atenção", "Selecione uma categoria.")
            return
        cat = next(
            (c for c in self.categories if c["id"] == int(sel[0])), None,
        )
        if not cat:
            return
        dlg = _CategoryDialog(self.root, self.api, category=cat)
        self.root.wait_window(dlg)
        if not dlg.saved:
            return
        self._load_categories()
        self._refresh_categories_tree()

    def _deactivate_category(self):
        sel = self.tree_cat.selection()
        if not sel:
            messagebox.showinfo("Atenção", "Selecione uma categoria.")
            return
        cat_id = int(sel[0])
        cat = next((c for c in self.categories if c["id"] == cat_id), None)
        if not cat:
            return
        if not messagebox.askyesno(
            "Confirmar",
            f"Desativar a categoria '{cat['category']}'?\n\n"
            "(As subcategorias continuam no banco, mas somem da lista.)",
        ):
            return
        try:
            self.api._post(
                f"/api/product-categories/{cat_id}/",
                {**cat, "active": False},
                method="PATCH",
            )
        except Exception as e:
            messagebox.showerror("Erro", str(e))
            return
        self._load_categories()
        self._refresh_categories_tree()

    # ---- SUBCATEGORIA ----
    def _new_subcategory(self):
        if not self.current_category_id:
            messagebox.showinfo(
                "Atenção", "Selecione uma categoria primeiro.",
            )
            return
        dlg = _SubCategoryDialog(
            self.root, self.api,
            subcategory=None,
            category_id=self.current_category_id,
        )
        self.root.wait_window(dlg)
        if not dlg.saved:
            return
        self._load_subcategories(self.current_category_id)
        self._refresh_subcategories_tree()

    def _edit_subcategory(self):
        sel = self.tree_sub.selection()
        if not sel:
            messagebox.showinfo("Atenção", "Selecione uma subcategoria.")
            return
        sub = next(
            (s for s in self.subcategories if s["id"] == int(sel[0])), None,
        )
        if not sub:
            return
        dlg = _SubCategoryDialog(
            self.root, self.api,
            subcategory=sub,
            category_id=self.current_category_id,
        )
        self.root.wait_window(dlg)
        if not dlg.saved:
            return
        self._load_subcategories(self.current_category_id)
        self._refresh_subcategories_tree()

    def _deactivate_subcategory(self):
        sel = self.tree_sub.selection()
        if not sel:
            messagebox.showinfo("Atenção", "Selecione uma subcategoria.")
            return
        sub_id = int(sel[0])
        sub = next((s for s in self.subcategories if s["id"] == sub_id), None)
        if not sub:
            return
        if not messagebox.askyesno(
            "Confirmar",
            f"Desativar a subcategoria '{sub['sub_category']}'?",
        ):
            return
        try:
            self.api._post(
                f"/api/product-sub-categories/{sub_id}/",
                {**sub, "active": False},
                method="PATCH",
            )
        except Exception as e:
            messagebox.showerror("Erro", str(e))
            return
        self._load_subcategories(self.current_category_id)
        self._refresh_subcategories_tree()


# =========================================================================
# Dialog: Categoria
# =========================================================================
class _CategoryDialog(tk.Toplevel):
    def __init__(self, parent, api, category=None):
        super().__init__(parent)
        self.api = api
        self.category = category
        self.saved = False

        self.title("Editar categoria" if category else "Nova categoria")
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)

        frm = ttk.Frame(self, padding=16)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="Categoria:").grid(row=0, column=0, sticky="w", pady=4)
        self.name_var = tk.StringVar(
            value=(category or {}).get("category", "")
        )
        entry = ttk.Entry(frm, textvariable=self.name_var, width=40)
        entry.grid(row=0, column=1, pady=4)
        entry.focus_set()

        ttk.Label(frm, text="Descrição menu:").grid(row=1, column=0, sticky="w", pady=4)
        self.desc_var = tk.StringVar(
            value=(category or {}).get("description_menu", "")
        )
        ttk.Entry(frm, textvariable=self.desc_var, width=40).grid(
            row=1, column=1, pady=4,
        )

        btns = ttk.Frame(frm)
        btns.grid(row=2, column=0, columnspan=2, pady=(14, 0), sticky="e")
        ttk.Button(btns, text="Cancelar", command=self.destroy).pack(
            side="right", padx=4,
        )
        ttk.Button(btns, text="Salvar", command=self.save).pack(side="right")

        entry.bind("<Return>", lambda e: self.save())
        self.bind("<Escape>", lambda e: self.destroy())

    def save(self):
        nome = self.name_var.get().strip()
        desc = self.desc_var.get().strip()
        if not nome:
            messagebox.showwarning("Atenção", "Informe a categoria.", parent=self)
            return
        if not desc:
            messagebox.showwarning("Atenção", "Informe a descrição.", parent=self)
            return

        payload = {
            "category": nome,
            "description_menu": desc,
            "active": True,
        }

        try:
            if self.category:
                self.api._post(
                    f"/api/product-categories/{self.category['id']}/",
                    payload, method="PUT",
                )
            else:
                self.api._post("/api/product-categories/", payload)
        except Exception as e:
            messagebox.showerror("Erro", str(e), parent=self)
            return

        self.saved = True
        self.destroy()


# =========================================================================
# Dialog: Subcategoria
# =========================================================================
class _SubCategoryDialog(tk.Toplevel):
    def __init__(self, parent, api, subcategory=None, category_id=None):
        super().__init__(parent)
        self.api = api
        self.subcategory = subcategory
        self.category_id = category_id
        self.saved = False

        self.title(
            "Editar subcategoria" if subcategory else "Nova subcategoria"
        )
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)

        frm = ttk.Frame(self, padding=16)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="Subcategoria:").grid(
            row=0, column=0, sticky="w", pady=4,
        )
        self.name_var = tk.StringVar(
            value=(subcategory or {}).get("sub_category", "")
        )
        entry = ttk.Entry(frm, textvariable=self.name_var, width=40)
        entry.grid(row=0, column=1, pady=4)
        entry.focus_set()

        ttk.Label(frm, text="Descrição menu:").grid(
            row=1, column=0, sticky="w", pady=4,
        )
        self.desc_var = tk.StringVar(
            value=(subcategory or {}).get("description_menu", "")
        )
        ttk.Entry(frm, textvariable=self.desc_var, width=40).grid(
            row=1, column=1, pady=4,
        )

        ttk.Label(frm, text="Markup padrão (%):").grid(
            row=2, column=0, sticky="w", pady=4,
        )
        self.markup_var = tk.StringVar(
            value=str((subcategory or {}).get("markup_default", "200.0000"))
        )
        ttk.Entry(frm, textvariable=self.markup_var, width=12).grid(
            row=2, column=1, pady=4, sticky="w",
        )

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
        desc = self.desc_var.get().strip()
        markup = self.markup_var.get().strip().replace(",", ".")

        if not nome:
            messagebox.showwarning("Atenção", "Informe a subcategoria.", parent=self)
            return
        if not desc:
            messagebox.showwarning("Atenção", "Informe a descrição.", parent=self)
            return
        try:
            float(markup)
        except ValueError:
            messagebox.showwarning("Atenção", "Markup inválido.", parent=self)
            return

        payload = {
            "category": self.category_id,
            "sub_category": nome,
            "description_menu": desc,
            "markup_default": markup,
            "active": True,
        }

        try:
            if self.subcategory:
                self.api._post(
                    f"/api/product-sub-categories/{self.subcategory['id']}/",
                    payload, method="PUT",
                )
            else:
                self.api._post("/api/product-sub-categories/", payload)
        except Exception as e:
            messagebox.showerror("Erro", str(e), parent=self)
            return

        self.saved = True
        self.destroy()