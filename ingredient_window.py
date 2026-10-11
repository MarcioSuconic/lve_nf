# lve_nf/ingredient_window.py
import tkinter as tk
from tkinter import messagebox, ttk

from dialogs.ingredient_dialog import IngredientDialog


class IngredientWindow:
    """
    Tela de cadastro de Insumos.

    Lista, cria, edita e desativa insumos (FoodIngredient).
    """

    def __init__(self, root, api, on_voltar=None):
        self.root = root
        self.api = api
        self.on_voltar = on_voltar

        self.root.title("LVE — Insumos")
        self.root.geometry("1200x640")

        self.ingredients = []
        self.suppliers = []
        self.units = []
        self.densities_cache = {}  # {ingredient_id: [densidades]}

        self.mostrar_inativos_var = tk.BooleanVar(value=False)

        self._load_data()
        self._build_ui()
        self._refresh_tree()

    # ----------------------------------------------------------------- load
    def _load_data(self):
        try:
            self.ingredients = self.api._get_paginated(
                "/api/food-ingredients/"
            )
            self.suppliers = self.api._get_paginated("/api/suppliers/")
            self.units = self.api.list_units()
            # Carrega as densidades de uma vez
            todas_densidades = self.api._get_paginated(
                "/api/food-ingredient-densities/"
            )
            for d in todas_densidades:
                iid = d["food_ingredient"]
                self.densities_cache.setdefault(iid, []).append(d)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar dados:\n{e}")
            self.root.destroy()
            raise SystemExit

        self.suppliers = [s for s in self.suppliers if s.get("active", True)]
        self.units = [u for u in self.units if u.get("active", True)]

    def _reload_ingredients(self):
        self.ingredients = self.api._get_paginated("/api/food-ingredients/")
        # Recarrega densidades
        self.densities_cache = {}
        todas_densidades = self.api._get_paginated(
            "/api/food-ingredient-densities/"
        )
        for d in todas_densidades:
            iid = d["food_ingredient"]
            self.densities_cache.setdefault(iid, []).append(d)

    # ------------------------------------------------------------------ ui
    def _build_ui(self):
        header = ttk.Frame(self.root, padding=10)
        header.pack(fill="x")

        ttk.Label(
            header, text="Insumos",
            font=("", 13, "bold"),
        ).pack(side="left")

        ttk.Checkbutton(
            header,
            text="Mostrar inativos",
            variable=self.mostrar_inativos_var,
            command=self._refresh_tree,
        ).pack(side="right")

        body = ttk.Frame(self.root, padding=10)
        body.pack(fill="both", expand=True)

        cols = ("name", "unit", "supplier", "density", "active")
        self.tree = ttk.Treeview(body, columns=cols, show="headings", height=18)
        for c, t, w in [
            ("name", "Nome", 300),
            ("unit", "Unidade", 100),
            ("supplier", "Fornecedor", 220),
            ("density", "Densidade", 220),
            ("active", "Ativo", 60),
        ]:
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True)

        btns = ttk.Frame(body)
        btns.pack(fill="x", pady=(6, 0))
        ttk.Button(
            btns, text="+ Novo insumo", command=self._new,
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

    # ----------------------------------------------------------------- tree
    def _refresh_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        mostrar_inativos = self.mostrar_inativos_var.get()

        for ing in self.ingredients:
            if not mostrar_inativos and not ing.get("active", True):
                continue

            # Unidade
            unit_label = ""
            for u in self.units:
                if u["id"] == ing.get("unit"):
                    unit_label = u["symbol"]
                    break

            # Densidade
            dens_str = "—"
            densidades = self.densities_cache.get(ing["id"], [])
            if densidades:
                d = densidades[0]  # mais recente
                dens_str = (
                    f'{d["density"]} '
                    f'{d.get("mass_unit_symbol", "")}/'
                    f'{d.get("volume_unit_symbol", "")}'
                )

            self.tree.insert("", "end", iid=str(ing["id"]), values=(
                ing["food_ingredient"],
                unit_label,
                ing.get("main_supplier_name", ""),
                dens_str,
                "✓" if ing.get("active") else "",
            ))

    # -------------------------------------------------------------- actions
    def _new(self):
        if not self.suppliers:
            messagebox.showwarning(
                "Atenção",
                "Nenhum fornecedor cadastrado. Cadastre um fornecedor antes.",
            )
            return

        dlg = IngredientDialog(
            self.root,
            self.api,
            suppliers=[
                {"id": s["id"], "supplier": s["supplier"]}
                for s in self.suppliers
            ],
            units=self.units,
            ingredient=None,
        )
        self.root.wait_window(dlg)
        if not dlg.created:
            return
        self._reload_ingredients()
        self._refresh_tree()

    def _edit(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Atenção", "Selecione um insumo.")
            return
        ing = next(
            (x for x in self.ingredients if x["id"] == int(sel[0])), None,
        )
        if not ing:
            return

        dlg = IngredientDialog(
            self.root,
            self.api,
            suppliers=[
                {"id": s["id"], "supplier": s["supplier"]}
                for s in self.suppliers
            ],
            units=self.units,
            ingredient=ing,
        )
        self.root.wait_window(dlg)
        if not dlg.created:
            return
        self._reload_ingredients()
        self._refresh_tree()

    def _deactivate(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Atenção", "Selecione um insumo.")
            return
        iid = int(sel[0])
        ing = next((x for x in self.ingredients if x["id"] == iid), None)
        if not ing:
            return
        if not ing.get("active", True):
            messagebox.showinfo(
                "Atenção", "Esse insumo já está inativo.",
            )
            return
        if not messagebox.askyesno(
            "Confirmar",
            f"Desativar o insumo '{ing['food_ingredient']}'?",
        ):
            return
        try:
            self.api._post(
                f"/api/food-ingredients/{iid}/",
                {**ing, "active": False},
                method="PATCH",
            )
        except Exception as e:
            messagebox.showerror("Erro", str(e))
            return
        self._reload_ingredients()
        self._refresh_tree()