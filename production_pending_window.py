# lve_nf/production_pending_window.py
import tkinter as tk
from tkinter import messagebox, ttk


class ProductionPendingWindow:
    """
    Tela 1 — Cadastro e listagem de produções pendentes.

    - Cria produções (agrupando N produtos + quantidades)
    - Lista as produções com status 'pending' e 'scheduled'
    - Permite editar itens, apagar produção
    """

    def __init__(self, root, api, on_voltar=None):
        self.root = root
        self.api = api
        self.on_voltar = on_voltar

        self.root.title("LVE — Produções Pendentes")
        self.root.geometry("1100x680")

        self.productions = []
        self.products = []
        self.units = []
        self.stores = []

        self._load_data()
        self._build_ui()
        self._refresh_tree()

    # ----------------------------------------------------------------- load
    def _load_data(self):
        try:
            self.productions = self.api._get_paginated(
                "/api/pending-productions/?status=pending"
            )
            # Também pega as agendadas (para exibir na lista)
            agendadas = self.api._get_paginated(
                "/api/pending-productions/?status=scheduled"
            )
            self.productions.extend(agendadas)

            self.products = self.api._get_paginated(
                "/api/products/?active=true"
            )
            self.units = self.api.list_units()
            self.stores = self.api._get_paginated(
                "/api/stores/?active=true"
            )
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar dados:\n{e}")
            self.root.destroy()
            raise SystemExit

        self.products = [p for p in self.products if p.get("active", True)]
        self.units = [u for u in self.units if u.get("active", True)]
        self.stores = [s for s in self.stores if s.get("active", True)]

        # Ordena por data decrescente
        self.productions.sort(
            key=lambda x: x.get("created_at", ""), reverse=True,
        )

    def _reload_productions(self):
        pendentes = self.api._get_paginated(
            "/api/pending-productions/?status=pending"
        )
        agendadas = self.api._get_paginated(
            "/api/pending-productions/?status=scheduled"
        )
        self.productions = pendentes + agendadas
        self.productions.sort(
            key=lambda x: x.get("created_at", ""), reverse=True,
        )

    # ------------------------------------------------------------------ ui
    def _build_ui(self):
        header = ttk.Frame(self.root, padding=10)
        header.pack(fill="x")

        ttk.Label(
            header, text="Produções Pendentes",
            font=("", 13, "bold"),
        ).pack(side="left")

        ttk.Button(
            header, text="+ Nova produção",
            command=self._nova_producao,
        ).pack(side="right", padx=4)

        # ---- Lista ----
        body = ttk.LabelFrame(
            self.root, text="Produções em espera", padding=10,
        )
        body.pack(fill="both", expand=True, padx=10, pady=6)

        cols = ("id", "items", "status", "scheduled_start", "created_at")
        self.tree = ttk.Treeview(body, columns=cols, show="headings", height=18)
        for c, t, w in [
            ("id", "ID", 60),
            ("items", "Itens", 500),
            ("status", "Status", 120),
            ("scheduled_start", "Início planejado", 180),
            ("created_at", "Criada em", 160),
        ]:
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True)

        btns = ttk.Frame(body)
        btns.pack(fill="x", pady=(6, 0))
        ttk.Button(
            btns, text="Ver itens", command=self._ver_itens,
        ).pack(side="left", padx=2)
        ttk.Button(
            btns, text="Adicionar item", command=self._adicionar_item,
        ).pack(side="left", padx=2)
        ttk.Button(
            btns, text="Apagar produção", command=self._apagar_producao,
        ).pack(side="left", padx=2)

        # ---- Rodapé ----
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

        for p in self.productions:
            # Busca os itens
            try:
                itens = self.api._get_paginated(
                    f"/api/production-x-products/?production={p['id']}&active=true"
                )
            except Exception:
                itens = []

            resumo = " | ".join(
                f"{i['product_name']} ({i['quantity']} {i['unit_symbol']})"
                for i in itens
            ) or "(sem itens)"

            status_display = p.get("status_display", p["status"])

            self.tree.insert("", "end", iid=str(p["id"]), values=(
                f"#{p['id']}",
                resumo,
                status_display,
                p.get("scheduled_start") or "—",
                p.get("created_at", "")[:16].replace("T", " "),
            ))

    # -------------------------------------------------------------- actions
    def _nova_producao(self):
        if not self.products:
            messagebox.showwarning(
                "Atenção", "Nenhum produto cadastrado."
            )
            return
        if not self.stores:
            messagebox.showwarning(
                "Atenção", "Nenhuma loja cadastrada."
            )
            return

        dlg = _NewProductionDialog(
            self.root, self.api,
            products=self.products,
            units=self.units,
            stores=self.stores,
        )
        self.root.wait_window(dlg)
        if not dlg.created:
            return
        self._reload_productions()
        self._refresh_tree()

    def _ver_itens(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Atenção", "Selecione uma produção.")
            return
        prod_id = int(sel[0])
        prod = next(
            (p for p in self.productions if p["id"] == prod_id), None,
        )
        if not prod:
            return

        try:
            itens = self.api._get_paginated(
                f"/api/production-x-products/?production={prod_id}&active=true"
            )
        except Exception as e:
            messagebox.showerror("Erro", str(e))
            return

        _ItemsDialog(self.root, prod, itens)

    def _adicionar_item(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Atenção", "Selecione uma produção.")
            return
        prod_id = int(sel[0])
        prod = next(
            (p for p in self.productions if p["id"] == prod_id), None,
        )
        if not prod:
            return

        if prod["status"] != "pending":
            messagebox.showinfo(
                "Atenção",
                "Só é possível adicionar itens em produções pendentes.",
            )
            return

        dlg = _AddItemDialog(
            self.root, self.api,
            production_id=prod_id,
            products=self.products,
            units=self.units,
        )
        self.root.wait_window(dlg)
        if not dlg.created:
            return
        self._reload_productions()
        self._refresh_tree()

    def _apagar_producao(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Atenção", "Selecione uma produção.")
            return
        prod_id = int(sel[0])
        prod = next(
            (p for p in self.productions if p["id"] == prod_id), None,
        )
        if not prod:
            return

        if not messagebox.askyesno(
            "Confirmar",
            f"Apagar a produção #{prod_id}?\n\n"
            "Todos os itens vinculados serão apagados.",
        ):
            return

        try:
            self.api._post(
                f"/api/pending-productions/{prod_id}/",
                {}, method="DELETE",
            )
        except Exception as e:
            messagebox.showerror("Erro", str(e))
            return

        self._reload_productions()
        self._refresh_tree()


# =========================================================================
# Dialog: Nova produção
# =========================================================================
class _NewProductionDialog(tk.Toplevel):
    """Modal pra criar uma produção com N itens."""

    def __init__(self, parent, api, products, units, stores):
        super().__init__(parent)
        self.api = api
        self.created = None
        self.products = products
        self.units = units
        self.stores = stores

        self.product_id_by_name = {
            p["product"]: p["id"] for p in products
        }
        self.unit_id_by_label = {
            f'{u["symbol"]} - {u["unit"]}': u["id"] for u in units
        }
        self.store_id_by_name = {
            s["name_store"]: s["id"] for s in stores
        }

        self.items = []  # list of _ItemRow

        self.title("Nova produção")
        self.transient(parent)
        self.grab_set()
        self.geometry("900x600")

        frm = ttk.Frame(self, padding=16)
        frm.pack(fill="both", expand=True)

        # ---- Loja ----
        row = ttk.Frame(frm)
        row.pack(fill="x", pady=4)
        ttk.Label(row, text="Loja:").pack(side="left")
        self.store_var = tk.StringVar()
        store_combo = ttk.Combobox(
            row, textvariable=self.store_var,
            state="readonly", width=30,
            values=list(self.store_id_by_name.keys()),
        )
        store_combo.pack(side="left", padx=4)
        if stores:
            self.store_var.set(stores[0]["name_store"])

        # ---- Notas ----
        row = ttk.Frame(frm)
        row.pack(fill="x", pady=4)
        ttk.Label(row, text="Observações:").pack(side="left")
        self.notes_var = tk.StringVar()
        ttk.Entry(row, textvariable=self.notes_var, width=70).pack(
            side="left", padx=4,
        )

        # ---- Itens ----
        ttk.Label(
            frm, text="Itens da produção:", font=("", 10, "bold"),
        ).pack(anchor="w", pady=(10, 4))

        cols_frame = ttk.Frame(frm)
        cols_frame.pack(fill="x")
        ttk.Label(cols_frame, text="Produto", width=40).pack(side="left", padx=2)
        ttk.Label(cols_frame, text="Qtde", width=12).pack(side="left", padx=2)
        ttk.Label(cols_frame, text="Unidade", width=18).pack(side="left", padx=2)

        self.items_container = ttk.Frame(frm)
        self.items_container.pack(fill="both", expand=True)

        ttk.Button(
            frm, text="+ Adicionar item",
            command=self._add_item,
        ).pack(anchor="w", pady=(6, 0))

        # ---- Botões ----
        btns = ttk.Frame(frm)
        btns.pack(fill="x", pady=(14, 0))
        ttk.Button(
            btns, text="Cancelar", command=self.destroy,
        ).pack(side="right", padx=4)
        ttk.Button(
            btns, text="Salvar produção", command=self.save,
        ).pack(side="right")

        self._add_item()  # começa com 1 linha

        self.bind("<Escape>", lambda e: self.destroy())

    def _add_item(self):
        row = _ItemRow(
            self.items_container,
            products=self.products,
            units=self.units,
            on_remove=self._remove_item,
        )
        self.items.append(row)

    def _remove_item(self, row):
        if len(self.items) == 1:
            messagebox.showinfo(
                "Atenção", "A produção precisa ter pelo menos 1 item.",
                parent=self,
            )
            return
        row.destroy()
        self.items.remove(row)

    def save(self):
        store_id = self.store_id_by_name.get(self.store_var.get())
        if not store_id:
            messagebox.showwarning(
                "Atenção", "Escolha a loja.", parent=self,
            )
            return

        items_payload = []
        for idx, row in enumerate(self.items, start=1):
            item = row.get_payload()
            if not item:
                continue
            if not item["product"]:
                messagebox.showwarning(
                    "Atenção", f"Item {idx}: escolha o produto.",
                    parent=self,
                )
                return
            if not item["unit"]:
                messagebox.showwarning(
                    "Atenção", f"Item {idx}: escolha a unidade.",
                    parent=self,
                )
                return
            try:
                if float(item["quantity"]) <= 0:
                    raise ValueError
            except (ValueError, TypeError):
                messagebox.showwarning(
                    "Atenção", f"Item {idx}: quantidade inválida.",
                    parent=self,
                )
                return
            items_payload.append(item)

        if not items_payload:
            messagebox.showwarning(
                "Atenção", "Adicione pelo menos 1 item.", parent=self,
            )
            return

        payload = {
            "store": store_id,
            "notes": self.notes_var.get().strip(),
            "items": items_payload,
        }

        try:
            created = self.api._post(
                "/api/pending-productions/", payload,
            )
        except Exception as e:
            messagebox.showerror("Erro", str(e), parent=self)
            return

        self.created = created
        self.destroy()


class _ItemRow:
    """Uma linha de item no dialog de nova produção."""

    def __init__(self, parent, products, units, on_remove):
        self.on_remove = on_remove
        self.products = products
        self.units = units

        self.product_id_by_name = {
            p["product"]: p["id"] for p in products
        }
        self.unit_id_by_label = {
            f'{u["symbol"]} - {u["unit"]}': u["id"] for u in units
        }

        self.frame = ttk.Frame(parent)
        self.frame.pack(fill="x", pady=2)

        # Produto
        self.product_var = tk.StringVar()
        ttk.Combobox(
            self.frame, textvariable=self.product_var,
            state="readonly", width=38,
            values=list(self.product_id_by_name.keys()),
        ).grid(row=0, column=0, padx=2)

        # Qtde
        self.qtde_var = tk.StringVar(value="1")
        ttk.Entry(
            self.frame, textvariable=self.qtde_var, width=12,
        ).grid(row=0, column=1, padx=2)

        # Unidade
        self.unit_var = tk.StringVar()
        ttk.Combobox(
            self.frame, textvariable=self.unit_var,
            state="readonly", width=16,
            values=list(self.unit_id_by_label.keys()),
        ).grid(row=0, column=2, padx=2)

        # Remover
        ttk.Button(
            self.frame, text="X", width=3,
            command=lambda: self.on_remove(self),
        ).grid(row=0, column=3, padx=2)

    def get_payload(self):
        prod_id = self.product_id_by_name.get(self.product_var.get())
        unit_id = self.unit_id_by_label.get(self.unit_var.get())
        if not prod_id and not unit_id:
            return None
        return {
            "product": prod_id,
            "quantity": self.qtde_var.get().strip(),
            "unit": unit_id,
        }

    def destroy(self):
        self.frame.destroy()


# =========================================================================
# Dialog: Ver itens
# =========================================================================
class _ItemsDialog(tk.Toplevel):
    def __init__(self, parent, production, itens):
        super().__init__(parent)
        self.title(f"Produção #{production['id']} — Itens")
        self.transient(parent)
        self.grab_set()
        self.geometry("700x400")

        frm = ttk.Frame(self, padding=16)
        frm.pack(fill="both", expand=True)

        ttk.Label(
            frm, text=f"Status: {production.get('status_display', '?')}",
            font=("", 10, "bold"),
        ).pack(anchor="w", pady=(0, 8))

        cols = ("product", "quantity", "unit")
        tree = ttk.Treeview(frm, columns=cols, show="headings", height=12)
        for c, t, w in [
            ("product", "Produto", 400),
            ("quantity", "Quantidade", 120),
            ("unit", "Unidade", 100),
        ]:
            tree.heading(c, text=t)
            tree.column(c, width=w, anchor="w")
        tree.pack(fill="both", expand=True)

        for i in itens:
            tree.insert("", "end", values=(
                i["product_name"],
                i["quantity"],
                i["unit_symbol"],
            ))

        ttk.Button(frm, text="Fechar", command=self.destroy).pack(
            side="right", pady=(10, 0),
        )

        self.bind("<Escape>", lambda e: self.destroy())


# =========================================================================
# Dialog: Adicionar item a produção existente
# =========================================================================
class _AddItemDialog(tk.Toplevel):
    def __init__(self, parent, api, production_id, products, units):
        super().__init__(parent)
        self.api = api
        self.created = None
        self.production_id = production_id

        self.product_id_by_name = {
            p["product"]: p["id"] for p in products
        }
        self.unit_id_by_label = {
            f'{u["symbol"]} - {u["unit"]}': u["id"] for u in units
        }

        self.title(f"Adicionar item à produção #{production_id}")
        self.transient(parent)
        self.grab_set()
        self.geometry("500x250")

        frm = ttk.Frame(self, padding=16)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="Produto:").grid(row=0, column=0, sticky="w", pady=4)
        self.product_var = tk.StringVar()
        ttk.Combobox(
            frm, textvariable=self.product_var,
            state="readonly", width=40,
            values=list(self.product_id_by_name.keys()),
        ).grid(row=0, column=1, pady=4)

        ttk.Label(frm, text="Quantidade:").grid(row=1, column=0, sticky="w", pady=4)
        self.qtde_var = tk.StringVar(value="1")
        ttk.Entry(frm, textvariable=self.qtde_var, width=12).grid(
            row=1, column=1, pady=4, sticky="w",
        )

        ttk.Label(frm, text="Unidade:").grid(row=2, column=0, sticky="w", pady=4)
        self.unit_var = tk.StringVar()
        ttk.Combobox(
            frm, textvariable=self.unit_var,
            state="readonly", width=20,
            values=list(self.unit_id_by_label.keys()),
        ).grid(row=2, column=1, pady=4, sticky="w")

        btns = ttk.Frame(frm)
        btns.grid(row=3, column=0, columnspan=2, pady=(14, 0), sticky="e")
        ttk.Button(btns, text="Cancelar", command=self.destroy).pack(
            side="right", padx=4,
        )
        ttk.Button(btns, text="Adicionar", command=self.save).pack(side="right")

        self.bind("<Escape>", lambda e: self.destroy())

    def save(self):
        prod_id = self.product_id_by_name.get(self.product_var.get())
        unit_id = self.unit_id_by_label.get(self.unit_var.get())

        if not prod_id:
            messagebox.showwarning("Atenção", "Escolha o produto.", parent=self)
            return
        if not unit_id:
            messagebox.showwarning("Atenção", "Escolha a unidade.", parent=self)
            return

        try:
            if float(self.qtde_var.get().strip()) <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Atenção", "Quantidade inválida.", parent=self)
            return

        payload = {
            "product": prod_id,
            "quantity": self.qtde_var.get().strip(),
            "unit": unit_id,
        }

        try:
            created = self.api._post(
                f"/api/pending-productions/{self.production_id}/add-item/",
                payload,
            )
        except Exception as e:
            messagebox.showerror("Erro", str(e), parent=self)
            return

        self.created = created
        self.destroy()