# lve_nf/production_plan_window.py
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import messagebox, ttk


class ProductionPlanWindow:
    """
    Tela 2 — Planejamento de produção.

    1. Lê todas as produções com status 'pending'
    2. Lista os itens com checkbox
    3. Usuário seleciona itens + define data/hora de início
    4. Clica em "Calcular plano"
    5. Vê o resultado (sub-produtos, cronograma, custo, lista de compras)
    6. Clica em "Confirmar e planejar"
    """

    def __init__(self, root, api, on_voltar=None):
        self.root = root
        self.api = api
        self.on_voltar = on_voltar

        self.root.title("LVE — Planejar Produção")
        self.root.geometry("1300x800")

        self.productions = []
        self.items_by_prod = {}
        self.check_vars = {}
        self.item_index = {}
        self.current_plan = None
        self.current_plan_production_id = None

        self._load_data()
        self._build_ui()
        self._refresh_items()

    # ----------------------------------------------------------------- load
    def _load_data(self):
        try:
            self.productions = self.api._get_paginated(
                "/api/pending-productions/?status=pending"
            )
            for p in self.productions:
                itens = self.api._get_paginated(
                    f"/api/production-x-products/?production={p['id']}&active=true"
                )
                self.items_by_prod[p["id"]] = itens
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar dados:\n{e}")
            self.root.destroy()
            raise SystemExit

    def _reload_items(self):
        self.productions = self.api._get_paginated(
            "/api/pending-productions/?status=pending"
        )
        self.items_by_prod = {}
        for p in self.productions:
            itens = self.api._get_paginated(
                f"/api/production-x-products/?production={p['id']}&active=true"
            )
            self.items_by_prod[p["id"]] = itens

    # ------------------------------------------------------------------ ui
    def _build_ui(self):
        # ---- Header ----
        header = ttk.Frame(self.root, padding=10)
        header.pack(fill="x")

        ttk.Label(header, text="Data/hora início:").pack(side="left")

        default = (datetime.now() + timedelta(hours=1)).replace(
            second=0, microsecond=0,
        )
        self.start_var = tk.StringVar(
            value=default.strftime("%Y-%m-%dT%H:%M:%S"),
        )
        ttk.Entry(
            header, textvariable=self.start_var, width=22,
        ).pack(side="left", padx=4)

        ttk.Button(
            header, text="Recarregar", command=self._reload_all,
        ).pack(side="right", padx=4)

        # ---- Itens ----
        items_box = ttk.LabelFrame(
            self.root, text="Itens pendentes", padding=10,
        )
        items_box.pack(fill="both", expand=True, padx=10, pady=6)

        cols = ("sel", "product", "quantity", "production", "created")
        self.tree = ttk.Treeview(
            items_box, columns=cols, show="headings", height=10,
        )
        for c, t, w in [
            ("sel", "☑", 40),
            ("product", "Produto", 350),
            ("quantity", "Qtde", 120),
            ("production", "Produção", 100),
            ("created", "Criada em", 160),
        ]:
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True)

        self.tree.bind("<Button-1>", self._on_tree_click)

        btns1 = ttk.Frame(items_box)
        btns1.pack(fill="x", pady=(6, 0))
        ttk.Button(
            btns1, text="Marcar todos", command=self._select_all,
        ).pack(side="left", padx=2)
        ttk.Button(
            btns1, text="Desmarcar todos", command=self._deselect_all,
        ).pack(side="left", padx=2)
        ttk.Button(
            btns1, text="Calcular plano", command=self._calcular,
        ).pack(side="right", padx=2)

        # ---- Resultado ----
        self.result_box = ttk.LabelFrame(
            self.root, text="Resultado do plano", padding=10,
        )
        self.result_box.pack(fill="both", expand=True, padx=10, pady=6)

        self.result_text = tk.Text(
            self.result_box, height=18, wrap="word",
            font=("monospace", 9),
        )
        self.result_text.pack(fill="both", expand=True)

        # ---- Rodapé ----
        footer = ttk.Frame(self.root, padding=10)
        footer.pack(fill="x", side="bottom")
        if self.on_voltar:
            ttk.Button(
                footer, text="← Voltar", command=self.on_voltar,
            ).pack(side="left")

        ttk.Button(
            footer, text="Exportar lista de compras (PDF)",
            command=self._exportar_pdf,
        ).pack(side="right", padx=4)

        self.btn_confirmar = ttk.Button(
            footer, text="Confirmar e planejar",
            command=self._confirmar,
            state="disabled",
        )
        self.btn_confirmar.pack(side="right", padx=4)

    # ----------------------------------------------------------------- tree
    def _refresh_items(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.check_vars = {}
        self.item_index = {}

        for p in self.productions:
            itens = self.items_by_prod.get(p["id"], [])
            for it in itens:
                item_id = it["id"]
                self.check_vars[item_id] = tk.BooleanVar(value=False)
                self.item_index[item_id] = (p, it)

                self.tree.insert("", "end", iid=str(item_id), values=(
                    "☐",
                    it["product_name"],
                    f'{it["quantity"]} {it["unit_symbol"]}',
                    f"#{p['id']}",
                    p.get("created_at", "")[:16].replace("T", " "),
                ))

    def _on_tree_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell":
            return
        col = self.tree.identify_column(event.x)
        if col != "#1":
            return
        item_id_str = self.tree.identify_row(event.y)
        if not item_id_str:
            return
        item_id = int(item_id_str)
        if item_id not in self.check_vars:
            return
        self.check_vars[item_id].set(not self.check_vars[item_id].get())
        self._update_check_marker(item_id)

    def _update_check_marker(self, item_id):
        var = self.check_vars.get(item_id)
        if var is None:
            return
        marker = "☑" if var.get() else "☐"
        values = list(self.tree.item(str(item_id), "values"))
        values[0] = marker
        self.tree.item(str(item_id), values=values)

    def _select_all(self):
        for item_id in self.check_vars:
            self.check_vars[item_id].set(True)
            self._update_check_marker(item_id)

    def _deselect_all(self):
        for item_id in self.check_vars:
            self.check_vars[item_id].set(False)
            self._update_check_marker(item_id)

    def _reload_all(self):
        self._reload_items()
        self._refresh_items()
        self.result_text.delete("1.0", "end")
        self.current_plan = None
        self.current_plan_production_id = None
        self.btn_confirmar.config(state="disabled")

    # -------------------------------------------------------------- calcular
    def _calcular(self):
        selecionados = [
            (prod, it) for item_id, var in self.check_vars.items()
            if var.get()
            for prod, it in [self.item_index[item_id]]
        ]
        if not selecionados:
            messagebox.showinfo("Atenção", "Selecione pelo menos 1 item.")
            return

        start_str = self.start_var.get().strip()
        try:
            datetime.fromisoformat(start_str)
        except ValueError:
            messagebox.showwarning(
                "Atenção",
                "Data/hora inválida. Use AAAA-MM-DDTHH:MM:SS.",
            )
            return

        try:
            new_prod = self._criar_producao_consolidada(
                selecionados, start_str,
            )
        except Exception as e:
            messagebox.showerror("Erro", str(e))
            return

        try:
            plano = self.api._post(
                f"/api/pending-productions/{new_prod['id']}/plan/",
                {"scheduled_start": start_str},
            )
        except Exception as e:
            messagebox.showerror("Erro ao planejar", str(e))
            return

        self.current_plan = plano
        self.current_plan_production_id = new_prod["id"]
        self._mostrar_resultado(plano)
        self.btn_confirmar.config(state="normal")

        # Marca as produções originais como 'cancelled'
        orig_ids = {p["id"] for p, _ in selecionados}
        for pid in orig_ids:
            try:
                self.api._post(
                    f"/api/pending-productions/{pid}/",
                    {"status": "cancelled"},
                    method="PATCH",
                )
            except Exception:
                pass

        # Recarrega SÓ a lista (não apaga o resultado)
        self._reload_items()
        self._refresh_items()

        messagebox.showinfo(
            "Plano calculado",
            f"Produção #{new_prod['id']} criada e planejada.\n\n"
            "As produções originais foram marcadas como 'canceladas'.\n\n"
            "O resultado está abaixo.",
        )

    def _criar_producao_consolidada(self, selecionados, start_str):
        consolidado = {}
        for prod, it in selecionados:
            key = (it["product"], it["unit"])
            if key not in consolidado:
                consolidado[key] = {
                    "product": it["product"],
                    "unit": it["unit"],
                    "quantity": 0.0,
                }
            consolidado[key]["quantity"] += float(it["quantity"])

        store_id = selecionados[0][0]["store"]

        payload = {
            "store": store_id,
            "notes": (
                "Consolidada de: "
                + ", ".join(f"#{p['id']}" for p, _ in selecionados)
            ),
            "items": [
                {
                    "product": v["product"],
                    "quantity": f'{v["quantity"]:.3f}',
                    "unit": v["unit"],
                }
                for v in consolidado.values()
            ],
        }

        return self.api._post("/api/pending-productions/", payload)

    def _mostrar_resultado(self, plano):
        self.result_text.delete("1.0", "end")

        avisos = plano.get("avisos", [])
        if avisos:
            self.result_text.insert("end", "⚠️  AVISOS:\n")
            for a in avisos:
                self.result_text.insert("end", f"  - {a}\n")
            self.result_text.insert("end", "\n")
        else:
            self.result_text.insert("end", "✅ Sem avisos.\n\n")

        self.result_text.insert("end", "SUB-PRODUTOS A PRODUZIR:\n")
        for sp in plano.get("sub_produtos", []):
            ajustado = " ⚠️" if sp["ajustado"] else ""
            self.result_text.insert(
                "end",
                f"  {sp['sub_product']}: "
                f"{sp['quantity_final']} {sp['unit']}"
                f" (fator {sp['fator'][:6]}){ajustado}\n",
            )
        self.result_text.insert("end", "\n")

        self.result_text.insert("end", "CRONOGRAMA:\n")
        for c in plano.get("cronograma", []):
            self.result_text.insert(
                "end",
                f"  {c['sub_product']}: "
                f"{c['inicio'][:16].replace('T', ' ')} → "
                f"{c['fim'][:16].replace('T', ' ')} "
                f"({c['duracao_h'][:5]} h)\n",
            )
        self.result_text.insert("end", "\n")

        custo = plano.get("custo", {})
        self.result_text.insert(
            "end",
            f"CUSTO TOTAL: R$ {self._fmt(custo.get('total', '0'))}\n",
        )
        self.result_text.insert(
            "end",
            f"  Insumos:     R$ {self._fmt(custo.get('insumos', '0'))}\n",
        )
        self.result_text.insert(
            "end",
            f"  Energia:     R$ {self._fmt(custo.get('energia', '0'))}\n",
        )
        self.result_text.insert(
            "end",
            f"  Mão de obra: R$ {self._fmt(custo.get('mao_de_obra', '0'))}\n",
        )
        self.result_text.insert("end", "\n")

        self.result_text.insert("end", "LISTA DE COMPRAS:\n")
        for lc in plano.get("lista_compras", []):
            flag = " [NÃO-PROP]" if lc.get("not_proportional") else ""
            self.result_text.insert(
                "end",
                f"  {lc['food_ingredient']}: "
                f"{self._fmt(lc['quantity'], 4)} {lc['unit']} "
                f"→ R$ {self._fmt(lc['custo'])}{flag}\n",
            )

    @staticmethod
    def _fmt(valor, casas=2):
        try:
            v = float(str(valor))
        except (ValueError, TypeError):
            return str(valor)
        s = f"{v:,.{casas}f}"
        return s.replace(",", "X").replace(".", ",").replace("X", ".")

    # -------------------------------------------------------------- confirmar
    def _confirmar(self):
        if not self.current_plan:
            messagebox.showinfo("Atenção", "Calcule o plano primeiro.")
            return

        messagebox.showinfo(
            "Confirmado",
            f"Produção #{self.current_plan_production_id} está planejada.\n\n"
            "Você pode vê-la em 'Produções Pendentes'.",
        )
        self.current_plan = None
        self.current_plan_production_id = None
        self.btn_confirmar.config(state="disabled")

    # ------------------------------------------------------------- exportar
    def _exportar_pdf(self):
        if not self.current_plan_production_id:
            messagebox.showinfo("Atenção", "Calcule o plano primeiro.")
            return

        import subprocess
        import tempfile
        import urllib.request

        url = self.api.get_shopping_list_pdf_url(
            self.current_plan_production_id,
        )

        try:
            req = urllib.request.Request(url, method="POST")
            if self.api.token:
                req.add_header("Authorization", f"Token {self.api.token}")
            with urllib.request.urlopen(req) as resp:
                pdf_bytes = resp.read()

            tmp = tempfile.NamedTemporaryFile(
                suffix=".pdf", delete=False,
                prefix=f"lista_producao_{self.current_plan_production_id}_",
            )
            tmp.write(pdf_bytes)
            tmp.close()

            subprocess.Popen(["xdg-open", tmp.name])
        except Exception as e:
            messagebox.showerror(
                "Erro ao abrir", f"Falha ao gerar PDF:\n{e}",
            )