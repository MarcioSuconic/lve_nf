import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk


class IngredientDialog(tk.Toplevel):
    def __init__(
        self,
        parent,
        api,
        suppliers,
        units,
        preselected_supplier_id=None,   # NOVO
    ):
        super().__init__(parent)
        self.api = api
        self.created = None

        self.supplier_id_by_name = {s["supplier"]: s["id"] for s in suppliers}
        self.unit_id_by_label = {
            f'{u["symbol"]} - {u["unit"]}': u for u in units
        }
        self.units = units

        self.title("Novo insumo")
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)

        frm = ttk.Frame(self, padding=16)
        frm.pack(fill="both", expand=True)

        row = 0

        # Nome
        ttk.Label(frm, text="Nome:").grid(row=row, column=0, sticky="w", pady=4)
        self.name_var = tk.StringVar()
        ttk.Entry(frm, textvariable=self.name_var, width=40).grid(
            row=row, column=1, pady=4, columnspan=2, sticky="we",
        )
        row += 1

        # Descrição
        ttk.Label(frm, text="Descrição:").grid(row=row, column=0, sticky="w", pady=4)
        self.desc_var = tk.StringVar()
        ttk.Entry(frm, textvariable=self.desc_var, width=40).grid(
            row=row, column=1, pady=4, columnspan=2, sticky="we",
        )
        row += 1

        # Quantidade padrão
        ttk.Label(frm, text="Qtde padrão:").grid(row=row, column=0, sticky="w", pady=4)
        self.qtde_var = tk.StringVar(value="1.00")
        ttk.Entry(frm, textvariable=self.qtde_var, width=12).grid(
            row=row, column=1, pady=4, sticky="w",
        )
        row += 1

        # Unidade
        ttk.Label(frm, text="Unidade:").grid(row=row, column=0, sticky="w", pady=4)
        self.unit_var = tk.StringVar()
        self.unit_combo = ttk.Combobox(
            frm, textvariable=self.unit_var, state="readonly", width=30,
            values=list(self.unit_id_by_label.keys()),
        )
        self.unit_combo.grid(row=row, column=1, pady=4, sticky="w")
        self.unit_combo.bind("<<ComboboxSelected>>", self._on_unit_change)
        row += 1

        # Fornecedor principal
        ttk.Label(frm, text="Fornecedor principal:").grid(
            row=row, column=0, sticky="w", pady=4,
        )
        self.supplier_var = tk.StringVar()
        self.supplier_combo = ttk.Combobox(
            frm, textvariable=self.supplier_var, state="readonly", width=30,
            values=list(self.supplier_id_by_name.keys()),
        )
        self.supplier_combo.grid(row=row, column=1, pady=4, sticky="w")
        row += 1

        # NOVO: pré-seleciona o fornecedor, se veio do contexto
        if preselected_supplier_id is not None:
            for name, sid in self.supplier_id_by_name.items():
                if sid == preselected_supplier_id:
                    self.supplier_var.set(name)
                    break

        # Bloco de densidade (visível só quando volume)
        self.density_frame = ttk.LabelFrame(frm, text="Densidade", padding=10)
        self.density_frame.grid(
            row=row, column=0, columnspan=3, pady=(12, 0), sticky="we",
        )
        row += 1

        d = 0
        ttk.Label(self.density_frame, text="Densidade:").grid(
            row=d, column=0, sticky="w", pady=4,
        )
        self.density_var = tk.StringVar()
        ttk.Entry(self.density_frame, textvariable=self.density_var, width=14).grid(
            row=d, column=1, pady=4, sticky="w",
        )
        d += 1

        ttk.Label(self.density_frame, text="Unidade de massa:").grid(
            row=d, column=0, sticky="w", pady=4,
        )
        self.mass_unit_var = tk.StringVar()
        ttk.Combobox(
            self.density_frame, textvariable=self.mass_unit_var,
            state="readonly", width=28,
            values=self._unit_labels_by_slug("massa"),
        ).grid(row=d, column=1, pady=4, sticky="w")
        d += 1

        ttk.Label(self.density_frame, text="Unidade de volume:").grid(
            row=d, column=0, sticky="w", pady=4,
        )
        self.volume_unit_var = tk.StringVar()
        ttk.Combobox(
            self.density_frame, textvariable=self.volume_unit_var,
            state="readonly", width=28,
            values=self._unit_labels_by_slug("volume"),
        ).grid(row=d, column=1, pady=4, sticky="w")
        d += 1

        ttk.Label(self.density_frame, text="Temp. referência (°C):").grid(
            row=d, column=0, sticky="w", pady=4,
        )
        self.temp_var = tk.StringVar(value="20")
        ttk.Entry(self.density_frame, textvariable=self.temp_var, width=10).grid(
            row=d, column=1, pady=4, sticky="w",
        )
        d += 1

        ttk.Label(self.density_frame, text="Data da medição:").grid(
            row=d, column=0, sticky="w", pady=4,
        )
        self.density_date_var = tk.StringVar(value=date.today().isoformat())
        ttk.Entry(
            self.density_frame, textvariable=self.density_date_var, width=12,
        ).grid(row=d, column=1, pady=4, sticky="w")

        self.density_frame.grid_remove()

        # Botões
        btns = ttk.Frame(frm)
        btns.grid(row=row, column=0, columnspan=3, pady=(16, 0), sticky="e")
        ttk.Button(btns, text="Cancelar", command=self.destroy).pack(
            side="right", padx=4,
        )
        ttk.Button(btns, text="Salvar", command=self.save).pack(side="right")

        self.bind("<Escape>", lambda e: self.destroy())

    def _unit_labels_by_slug(self, slug):
        return [
            f'{u["symbol"]} - {u["unit"]}'
            for u in self.units
            if u.get("physical_quantity_slug") == slug
        ]

    def _on_unit_change(self, _event=None):
        unit = self.unit_id_by_label.get(self.unit_var.get())
        if not unit:
            return
        if unit.get("physical_quantity_slug") == "volume":
            self.density_frame.grid()
        else:
            self.density_frame.grid_remove()

    def save(self):
        name = self.name_var.get().strip()
        desc = self.desc_var.get().strip()
        qtde = self.qtde_var.get().strip()
        unit = self.unit_id_by_label.get(self.unit_var.get())
        supplier_id = self.supplier_id_by_name.get(self.supplier_var.get())

        if not name:
            messagebox.showwarning("Atenção", "Informe o nome.", parent=self)
            return
        if not desc:
            messagebox.showwarning("Atenção", "Informe a descrição.", parent=self)
            return
        if not qtde:
            messagebox.showwarning("Atenção", "Informe a quantidade padrão.", parent=self)
            return
        if not unit:
            messagebox.showwarning("Atenção", "Escolha a unidade.", parent=self)
            return
        if not supplier_id:
            messagebox.showwarning("Atenção", "Escolha o fornecedor.", parent=self)
            return

        payload = {
            "food_ingredient": name,
            "description": desc,
            "qtde_default_shopping": qtde,
            "unit": unit["id"],
            "main_supplier": supplier_id,
            "active": True,
        }

        if unit.get("physical_quantity_slug") == "volume":
            density = self.density_var.get().strip()
            mass = self.unit_id_by_label.get(self.mass_unit_var.get())
            vol = self.unit_id_by_label.get(self.volume_unit_var.get())
            temp = self.temp_var.get().strip()
            ddate = self.density_date_var.get().strip()

            if not density:
                messagebox.showwarning("Atenção", "Informe a densidade.", parent=self)
                return
            if not mass:
                messagebox.showwarning("Atenção", "Escolha a unidade de massa.", parent=self)
                return
            if not vol:
                messagebox.showwarning("Atenção", "Escolha a unidade de volume.", parent=self)
                return
            if not ddate:
                messagebox.showwarning("Atenção", "Informe a data da medição.", parent=self)
                return

            payload["density"] = density
            payload["mass_unit"] = mass["id"]
            payload["volume_unit"] = vol["id"]
            payload["reference_temperature_celsius"] = temp or "20"
            payload["density_date"] = ddate

        try:
            created = self.api.create_food_ingredient(payload)
        except Exception as e:
            messagebox.showerror("Erro", str(e), parent=self)
            return
        self.created = created
        self.destroy()