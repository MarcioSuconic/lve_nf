# lve_nf/machinery_window.py
import tkinter as tk
from tkinter import messagebox, ttk


class MachineryWindow:
    """Tela de cadastro de Maquinário."""

    def __init__(self, root, api, on_voltar=None):
        self.root = root
        self.api = api
        self.on_voltar = on_voltar

        self.root.title("LVE — Maquinários")
        self.root.geometry("1100x600")

        self.machineries = []
        self.stores = []
        self.units = []

        self._load_data()
        self._build_ui()
        self._refresh_tree()

    def _load_data(self):
        try:
            self.machineries = self.api._get_paginated(
                "/api/machineries/?active=true"
            )
            self.stores = self.api._get_paginated("/api/stores/?active=true")
            self.units = self.api.list_units()
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar dados:\n{e}")
            self.root.destroy()
            raise SystemExit

        self.stores = [s for s in self.stores if s.get("active", True)]
        self.units = [u for u in self.units if u.get("active", True)]

    def _reload_machineries(self):
        self.machineries = self.api._get_paginated(
            "/api/machineries/?active=true"
        )

    def _build_ui(self):
        header = ttk.Frame(self.root, padding=10)
        header.pack(fill="x")

        ttk.Label(
            header, text="Maquinários",
            font=("", 13, "bold"),
        ).pack(side="left")

        body = ttk.Frame(self.root, padding=10)
        body.pack(fill="both", expand=True)

        cols = ("code", "machinery", "power", "value", "store", "active")
        self.tree = ttk.Treeview(body, columns=cols, show="headings", height=16)
        for c, t, w in [
            ("code", "Código", 80),
            ("machinery", "Nome", 260),
            ("power", "Potência", 140),
            ("value", "Valor (R$)", 100),
            ("store", "Loja", 180),
            ("active", "Ativo", 60),
        ]:
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True)

        btns = ttk.Frame(body)
        btns.pack(fill="x", pady=(6, 0))
        ttk.Button(
            btns, text="+ Novo maquinário", command=self._new,
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
        for m in self.machineries:
            self.tree.insert("", "end", iid=str(m["id"]), values=(
                m["code"],
                m["machinery"],
                f'{m["qtde_power"]} {m.get("unit_power_symbol", "")}',
                m["value_machinery"],
                m.get("store_name", ""),
                "✓" if m.get("active") else "",
            ))

    def _new(self):
        if not self.stores:
            messagebox.showwarning(
                "Atenção", "Nenhuma loja cadastrada. Cadastre uma loja antes."
            )
            return
        dlg = _MachineryDialog(
            self.root, self.api,
            machinery=None,
            stores=self.stores,
            units=self.units,
        )
        self.root.wait_window(dlg)
        if not dlg.saved:
            return
        self._reload_machineries()
        self._refresh_tree()

    def _edit(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Atenção", "Selecione um maquinário.")
            return
        m = next(
            (x for x in self.machineries if x["id"] == int(sel[0])), None,
        )
        if not m:
            return
        dlg = _MachineryDialog(
            self.root, self.api,
            machinery=m,
            stores=self.stores,
            units=self.units,
        )
        self.root.wait_window(dlg)
        if not dlg.saved:
            return
        self._reload_machineries()
        self._refresh_tree()

    def _deactivate(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Atenção", "Selecione um maquinário.")
            return
        mid = int(sel[0])
        m = next((x for x in self.machineries if x["id"] == mid), None)
        if not m:
            return
        if not messagebox.askyesno(
            "Confirmar",
            f"Desativar '{m['machinery']}'?",
        ):
            return
        try:
            self.api._post(
                f"/api/machineries/{mid}/",
                {**m, "active": False},
                method="PATCH",
            )
        except Exception as e:
            messagebox.showerror("Erro", str(e))
            return
        self._reload_machineries()
        self._refresh_tree()


class _MachineryDialog(tk.Toplevel):
    def __init__(self, parent, api, machinery, stores, units):
        super().__init__(parent)
        self.api = api
        self.machinery = machinery
        self.saved = False

        # Só unidades de potência
        self.power_units = [
            u for u in units if u.get("physical_quantity_slug") == "potencia"
        ]
        self.unit_id_by_label = {
            f'{u["symbol"]} - {u["unit"]}': u["id"] for u in self.power_units
        }
        self.store_id_by_name = {s["name_store"]: s["id"] for s in stores}

        self.title("Editar maquinário" if machinery else "Novo maquinário")
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)

        frm = ttk.Frame(self, padding=16)
        frm.pack(fill="both", expand=True)

        row = 0

        ttk.Label(frm, text="Nome:").grid(row=row, column=0, sticky="w", pady=4)
        self.name_var = tk.StringVar(
            value=(machinery or {}).get("machinery", "")
        )
        entry = ttk.Entry(frm, textvariable=self.name_var, width=42)
        entry.grid(row=row, column=1, pady=4, columnspan=2, sticky="we")
        entry.focus_set()
        row += 1

        ttk.Label(frm, text="Descrição:").grid(row=row, column=0, sticky="w", pady=4)
        self.desc_var = tk.StringVar(
            value=(machinery or {}).get("description", "")
        )
        ttk.Entry(frm, textvariable=self.desc_var, width=42).grid(
            row=row, column=1, pady=4, columnspan=2, sticky="we",
        )
        row += 1

        ttk.Label(frm, text="Código (6 chars):").grid(
            row=row, column=0, sticky="w", pady=4,
        )
        self.code_var = tk.StringVar(
            value=(machinery or {}).get("code", "")
        )
        ttk.Entry(frm, textvariable=self.code_var, width=10).grid(
            row=row, column=1, pady=4, sticky="w",
        )
        row += 1

        ttk.Label(frm, text="Potência:").grid(row=row, column=0, sticky="w", pady=4)
        self.power_var = tk.StringVar(
            value=str((machinery or {}).get("qtde_power", ""))
        )
        ttk.Entry(frm, textvariable=self.power_var, width=12).grid(
            row=row, column=1, pady=4, sticky="w",
        )
        row += 1

        ttk.Label(frm, text="Unidade de potência:").grid(
            row=row, column=0, sticky="w", pady=4,
        )
        self.unit_var = tk.StringVar()
        self.unit_combo = ttk.Combobox(
            frm, textvariable=self.unit_var,
            state="readonly", width=24,
            values=list(self.unit_id_by_label.keys()),
        )
        self.unit_combo.grid(row=row, column=1, pady=4, sticky="w")
        if machinery:
            for u in self.power_units:
                if u["id"] == machinery.get("unit_power"):
                    self.unit_var.set(f'{u["symbol"]} - {u["unit"]}')
                    break
        row += 1

        ttk.Label(frm, text="Valor (R$):").grid(
            row=row, column=0, sticky="w", pady=4,
        )
        self.value_var = tk.StringVar(
            value=str((machinery or {}).get("value_machinery", ""))
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
        if machinery:
            for name, sid in self.store_id_by_name.items():
                if sid == machinery.get("store"):
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
        power = self.power_var.get().strip().replace(",", ".")
        value = self.value_var.get().strip().replace(",", ".")
        unit_id = self.unit_id_by_label.get(self.unit_var.get())
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
        if not power:
            messagebox.showwarning("Atenção", "Informe a potência.", parent=self)
            return
        if not unit_id:
            messagebox.showwarning(
                "Atenção", "Escolha a unidade de potência.", parent=self,
            )
            return
        if not value:
            messagebox.showwarning("Atenção", "Informe o valor.", parent=self)
            return
        if not store_id:
            messagebox.showwarning("Atenção", "Escolha a loja.", parent=self)
            return

        payload = {
            "machinery": nome,
            "description": desc,
            "code": code,
            "qtde_power": power,
            "unit_power": unit_id,
            "value_machinery": value,
            "store": store_id,
            "active": True,
        }

        try:
            if self.machinery:
                self.api._post(
                    f"/api/machineries/{self.machinery['id']}/",
                    payload, method="PUT",
                )
            else:
                self.api._post("/api/machineries/", payload)
        except Exception as e:
            messagebox.showerror("Erro", str(e), parent=self)
            return

        self.saved = True
        self.destroy()