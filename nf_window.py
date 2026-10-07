#/home/marcio/Desktop/projetos/lve_nf/nf_window.py
import tkinter as tk
from datetime import date
from decimal import Decimal, InvalidOperation
from tkinter import messagebox, ttk

from dialogs.ingredient_dialog import IngredientDialog
from dialogs.supplier_dialog import SupplierDialog


class ItemRow:
    def __init__(
        self,
        parent,
        ingredients,
        units,
        on_change,
        on_remove,
        on_new_ingredient,
    ):
        self.on_change = on_change
        self.on_remove = on_remove
        self.on_new_ingredient = on_new_ingredient
        self.units = units
        self.ingredients = ingredients

        self.frame = ttk.Frame(parent)
        self.frame.pack(fill="x", pady=2)

        # Combobox de insumo
        self.ingredient_var = tk.StringVar()
        self.ingredient_combo = ttk.Combobox(
            self.frame,
            textvariable=self.ingredient_var,
            state="readonly",
            width=28,
            values=self._ingredient_names(),
        )
        self.ingredient_combo.grid(row=0, column=0, padx=2)

        # Botão "+ Novo insumo"
        ttk.Button(
            self.frame,
            text="+ Novo insumo",
            command=self._new_ingredient,
        ).grid(row=0, column=1, padx=2)

        # Quantidade
        self.quantity_var = tk.StringVar()
        ttk.Entry(self.frame, textvariable=self.quantity_var, width=10).grid(
            row=0, column=2, padx=2
        )
        self.quantity_var.trace_add("write", lambda *a: self.on_change())

        # Unidade
        self.unit_var = tk.StringVar()
        self.unit_combo = ttk.Combobox(
            self.frame,
            textvariable=self.unit_var,
            state="readonly",
            width=16,
            values=self._unit_labels(),
        )
        self.unit_combo.grid(row=0, column=3, padx=2)

        # Total do item
        self.total_price_var = tk.StringVar()
        ttk.Entry(self.frame, textvariable=self.total_price_var, width=12).grid(
            row=0, column=4, padx=2
        )
        self.total_price_var.trace_add("write", lambda *a: self.on_change())

        # Remover
        ttk.Button(
            self.frame,
            text="X",
            width=3,
            command=lambda: self.on_remove(self),
        ).grid(row=0, column=5, padx=2)

    # ------------------------------------------------------------------ utils

    def _ingredient_names(self):
        return [i["food_ingredient"] for i in self.ingredients]

    def _unit_labels(self):
        return [f'{u["symbol"]} - {u["unit"]}' for u in self.units]

    def _ingredient_id_by_name(self):
        return {i["food_ingredient"]: i["id"] for i in self.ingredients}

    def _unit_id_by_label(self):
        return {f'{u["symbol"]} - {u["unit"]}': u["id"] for u in self.units}

    # ------------------------------------------------------------- callbacks

    def _new_ingredient(self):
        self.on_new_ingredient(self)

    # -------------------------------------------------------------- refresh

    def refresh_ingredients(self, ingredients):
        self.ingredients = ingredients
        self.ingredient_combo["values"] = self._ingredient_names()

    def refresh_units(self, units):
        self.units = units
        self.unit_combo["values"] = self._unit_labels()

    def select_ingredient_by_id(self, ingredient_id):
        for i in self.ingredients:
            if i["id"] == ingredient_id:
                self.ingredient_var.set(i["food_ingredient"])
                return

    # --------------------------------------------------------------- payload

    def get_payload(self):
        return {
            "food_ingredient": self._ingredient_id_by_name().get(
                self.ingredient_var.get()
            ),
            "quantity": self.quantity_var.get().strip(),
            "unit": self._unit_id_by_label().get(self.unit_var.get()),
            "total_price": self.total_price_var.get().strip(),
        }

    def get_total(self):
        try:
            return Decimal(self.total_price_var.get().strip() or "0")
        except InvalidOperation:
            return Decimal("0")

    def destroy(self):
        self.frame.destroy()


class NFWindow:
    def __init__(self, root, api, on_voltar=None):
        self.root = root
        self.api = api
        self.on_voltar = on_voltar
        self.items = []
        self.supplier_id_by_name = {}
        self.ingredients = []
        self.units = []

        self.root.title("LVE — Cadastro de NF")
        self.root.geometry("1000x560")

        self._load_data()
        self._build_ui()
        self._recalc_total()

    # ----------------------------------------------------------------- load

    def _load_data(self):
        try:
            suppliers = self.api.list_suppliers()
            self.ingredients = self.api.list_food_ingredients()
            self.units = self.api.list_units()
        except Exception as e:
            messagebox.showerror(
                "Erro", f"Não foi possível carregar dados:\n{e}"
            )
            self.root.destroy()
            raise SystemExit

        suppliers = [s for s in suppliers if s.get("active", True)]
        self.supplier_id_by_name = {s["supplier"]: s["id"] for s in suppliers}
        self.ingredients = [i for i in self.ingredients if i.get("active", True)]

    def _reload_suppliers(self):
        suppliers = [s for s in self.api.list_suppliers() if s.get("active", True)]
        self.supplier_id_by_name = {s["supplier"]: s["id"] for s in suppliers}

    def _reload_ingredients(self):
        self.ingredients = [
            i for i in self.api.list_food_ingredients() if i.get("active", True)
        ]

    # ------------------------------------------------------------------ ui

    def _build_ui(self):
        header = ttk.Frame(self.root, padding=10)
        header.pack(fill="x")

        ttk.Label(header, text="Data da NF:").grid(
            row=0, column=0, padx=4, sticky="w"
        )
        self.date_var = tk.StringVar(value=date.today().isoformat())
        ttk.Entry(header, textvariable=self.date_var, width=12).grid(
            row=0, column=1, padx=4
        )

        ttk.Label(header, text="Fornecedor da NF:").grid(
            row=0, column=2, padx=4, sticky="w"
        )
        self.supplier_var = tk.StringVar()
        self.supplier_combo = ttk.Combobox(
            header,
            textvariable=self.supplier_var,
            state="readonly",
            width=28,
            values=list(self.supplier_id_by_name.keys()),
        )
        self.supplier_combo.grid(row=0, column=3, padx=4)

        ttk.Button(
            header,
            text="+ Novo fornecedor",
            command=self.new_supplier_header,
        ).grid(row=0, column=4, padx=4)

        cols = ttk.Frame(self.root, padding=(10, 4))
        cols.pack(fill="x")
        ttk.Label(cols, text="Insumo", width=28).grid(
            row=0, column=0, padx=2, sticky="w"
        )
        ttk.Label(cols, text="", width=12).grid(row=0, column=1, padx=2)
        ttk.Label(cols, text="Quantidade", width=10).grid(
            row=0, column=2, padx=2, sticky="w"
        )
        ttk.Label(cols, text="Unidade", width=16).grid(
            row=0, column=3, padx=2, sticky="w"
        )
        ttk.Label(cols, text="Total item", width=12).grid(
            row=0, column=4, padx=2, sticky="w"
        )

        self.items_container = ttk.Frame(self.root, padding=(10, 0))
        self.items_container.pack(fill="both", expand=True)

        footer = ttk.Frame(self.root, padding=10)
        footer.pack(fill="x", side="bottom")

        if self.on_voltar:
            ttk.Button(
                footer, text="← Voltar", command=self.on_voltar,
            ).pack(side="left", padx=(0, 8))

        ttk.Button(
            footer, text="+ Adicionar item", command=self.add_item
        ).pack(side="left")

        ttk.Label(footer, text="Total da NF:").pack(side="left", padx=(24, 4))
        self.total_var = tk.StringVar(value="0.00")
        ttk.Label(
            footer, textvariable=self.total_var, font=("", 11, "bold")
        ).pack(side="left")

        ttk.Button(footer, text="Enviar NF", command=self.submit).pack(
            side="right"
        )

        self.add_item()

    # --------------------------------------------------------------- items

    def add_item(self):
        row = ItemRow(
            self.items_container,
            ingredients=self.ingredients,
            units=self.units,
            on_change=self._recalc_total,
            on_remove=self.remove_item,
            on_new_ingredient=self.new_ingredient_for_row,
        )
        self.items.append(row)
        self._recalc_total()

    def remove_item(self, row):
        if len(self.items) == 1:
            messagebox.showinfo(
                "Atenção", "A NF precisa ter pelo menos um item."
            )
            return
        row.destroy()
        self.items.remove(row)
        self._recalc_total()

    # ----------------------------------------------------------- novos cadastros

    def new_supplier_header(self):
        dlg = SupplierDialog(self.root, self.api)
        self.root.wait_window(dlg)
        if not dlg.created:
            return
        self._reload_suppliers()
        self.supplier_combo["values"] = list(self.supplier_id_by_name.keys())
        self.supplier_var.set(dlg.created["supplier"])

    def new_ingredient_for_row(self, row):
        """
        Abre o modal de insumo já pré-selecionando o fornecedor da NF
        (se houver). Ao criar, atualiza a lista em todas as linhas e
        seleciona o novo insumo na linha de origem.
        """
        supplier_id = self.supplier_id_by_name.get(self.supplier_var.get())
        dlg = IngredientDialog(
            self.root,
            self.api,
            suppliers=[
                {"id": v, "supplier": k}
                for k, v in self.supplier_id_by_name.items()
            ],
            units=self.units,
            preselected_supplier_id=supplier_id,
        )
        self.root.wait_window(dlg)
        if not dlg.created:
            return

        self._reload_ingredients()
        for r in self.items:
            r.refresh_ingredients(self.ingredients)
        row.select_ingredient_by_id(dlg.created["id"])

    # --------------------------------------------------------------- total

    def _recalc_total(self):
        total = sum((row.get_total() for row in self.items), Decimal("0"))
        self.total_var.set(f"{total:.2f}")

    # -------------------------------------------------------------- submit

    def submit(self):
        if not self.supplier_var.get().strip():
            messagebox.showwarning("Atenção", "Escolha o fornecedor.")
            return

        date_str = self.date_var.get().strip()
        try:
            date.fromisoformat(date_str)
        except ValueError:
            messagebox.showwarning(
                "Atenção", "Data inválida. Use AAAA-MM-DD."
            )
            return

        items_payload = []
        for idx, row in enumerate(self.items, start=1):
            p = row.get_payload()
            if not p["food_ingredient"]:
                messagebox.showwarning(
                    "Atenção", f"Item {idx}: escolha o insumo."
                )
                return
            if not p["unit"]:
                messagebox.showwarning(
                    "Atenção", f"Item {idx}: escolha a unidade."
                )
                return
            try:
                if Decimal(p["quantity"]) <= 0:
                    raise InvalidOperation
            except InvalidOperation:
                messagebox.showwarning(
                    "Atenção", f"Item {idx}: quantidade inválida."
                )
                return
            try:
                Decimal(p["total_price"])
            except InvalidOperation:
                messagebox.showwarning(
                    "Atenção", f"Item {idx}: total inválido."
                )
                return
            items_payload.append(p)

        total = sum(
            (Decimal(p["total_price"]) for p in items_payload),
            Decimal("0"),
        )

        payload = {
            "date": date_str,
            "supplier": self.supplier_id_by_name[self.supplier_var.get()],
            "total_value": f"{total:.2f}",
            "items": items_payload,
        }

        try:
            nf = self.api.create_nf(payload)
        except Exception as e:
            messagebox.showerror("Erro ao enviar NF", str(e))
            return

        messagebox.showinfo(
            "Sucesso",
            f"NF #{nf['id']} registrada.\nTotal: R$ {total:.2f}",
        )
        self._reset_form()

    def _reset_form(self):
        for row in self.items:
            row.destroy()
        self.items.clear()
        self.supplier_var.set("")
        self.date_var.set(date.today().isoformat())
        self.add_item()
        self._recalc_total()