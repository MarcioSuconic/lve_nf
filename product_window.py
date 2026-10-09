# lve_nf/product_window.py
import tkinter as tk
from decimal import Decimal, InvalidOperation
from tkinter import messagebox, ttk


# ---------------------------------------------------------------------------
# Opções do combo "Ref. temporal"
# ---------------------------------------------------------------------------
REF_NENHUM = "nenhum (início da produção)"
REF_AT_START = "at_start (início do sub-produto)"
REF_AT_FINISH = "at_finish (fim do sub-produto)"
REF_AFTER_TO = "after_to (depois do fim)"


def minutos_para_duration(minutos: float) -> str:
    """15.5 → '00:15:30'"""
    total_segundos = int(round(minutos * 60))
    h = total_segundos // 3600
    m = (total_segundos % 3600) // 60
    s = total_segundos % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def duration_para_minutos(valor: str) -> float:
    """'00:15:30' → 15.5"""
    if not valor:
        return 0.0
    partes = valor.split(":")
    try:
        partes = [int(p) for p in partes]
    except ValueError:
        return 0.0
    if len(partes) == 3:
        h, m, s = partes
    elif len(partes) == 2:
        h, m = partes
        s = 0
    else:
        return 0.0
    return h * 60 + m + s / 60


class ProductWindow:
    """
    Tela de cadastro de Produto + Composição (sub-produtos) com timing.
    """

    def __init__(self, root, api, on_voltar=None):
        self.root = root
        self.api = api
        self.on_voltar = on_voltar

        self.root.title("LVE — Cadastro de Produto")
        self.root.geometry("1500x760")

        self.products = []
        self.stores = []
        self.subcategories = []
        self.subproducts = []
        self.units = []

        self.current_product_id = None
        self.composition_rows = []

        self._load_data()
        self._build_ui()
        self._refresh_products_combo()
        self.add_composition_row()

    # ----------------------------------------------------------------- load
    def _load_data(self):
        try:
            self.products = self.api._get_paginated(
                "/api/products/?active=true"
            )
            self.stores = self.api._get_paginated("/api/stores/?active=true")
            self.subcategories = self.api._get_paginated(
                "/api/product-sub-categories/?active=true"
            )
            self.subproducts = self.api._get_paginated(
                "/api/sub-products/?active=true"
            )
            self.units = self.api.list_units()
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar dados:\n{e}")
            self.root.destroy()
            raise SystemExit

        self.stores = [s for s in self.stores if s.get("active", True)]
        self.subcategories = [
            s for s in self.subcategories if s.get("active", True)
        ]
        self.subproducts = [
            s for s in self.subproducts if s.get("active", True)
        ]
        self.units = [u for u in self.units if u.get("active", True)]

    def _reload_products(self):
        self.products = self.api._get_paginated(
            "/api/products/?active=true"
        )

    # ------------------------------------------------------------------ ui
    def _build_ui(self):
        # ===== Cabeçalho =====
        header = ttk.LabelFrame(self.root, text="Dados do Produto", padding=10)
        header.pack(fill="x", padx=10, pady=(10, 4))

        row1 = ttk.Frame(header)
        row1.pack(fill="x")

        ttk.Label(row1, text="Produto:").pack(side="left")
        self.name_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self.name_var, width=42).pack(
            side="left", padx=(4, 12),
        )

        ttk.Label(row1, text="Nome no menu:").pack(side="left")
        self.menu_name_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self.menu_name_var, width=32).pack(
            side="left", padx=4,
        )

        row2 = ttk.Frame(header)
        row2.pack(fill="x", pady=(6, 0))

        ttk.Label(row2, text="Descrição do produto:").pack(side="left")
        self.desc_var = tk.StringVar()
        ttk.Entry(row2, textvariable=self.desc_var, width=80).pack(
            side="left", padx=4,
        )

        row3 = ttk.Frame(header)
        row3.pack(fill="x", pady=(6, 0))

        ttk.Label(row3, text="Descrição no menu:").pack(side="left")
        self.menu_desc_var = tk.StringVar()
        ttk.Entry(row3, textvariable=self.menu_desc_var, width=80).pack(
            side="left", padx=4,
        )

        row4 = ttk.Frame(header)
        row4.pack(fill="x", pady=(6, 0))

        ttk.Label(row4, text="Peso/Volume:").pack(side="left")
        self.weight_var = tk.StringVar()
        ttk.Entry(row4, textvariable=self.weight_var, width=12).pack(
            side="left", padx=(4, 12),
        )

        ttk.Label(row4, text="Unidade:").pack(side="left")
        self.unit_var = tk.StringVar()
        self.unit_combo = ttk.Combobox(
            row4, textvariable=self.unit_var,
            state="readonly", width=14,
            values=[f'{u["symbol"]} - {u["unit"]}' for u in self.units],
        )
        self.unit_combo.pack(side="left", padx=(4, 12))

        ttk.Label(row4, text="Loja:").pack(side="left")
        self.store_var = tk.StringVar()
        self.store_combo = ttk.Combobox(
            row4, textvariable=self.store_var,
            state="readonly", width=22,
            values=[s["name_store"] for s in self.stores],
        )
        self.store_combo.pack(side="left", padx=4)

        if self.stores:
            self.store_var.set(self.stores[0]["name_store"])

        row5 = ttk.Frame(header)
        row5.pack(fill="x", pady=(6, 0))

        ttk.Label(row5, text="Subcategoria:").pack(side="left")
        self.subcategory_var = tk.StringVar()
        self.subcategory_combo = ttk.Combobox(
            row5, textvariable=self.subcategory_var,
            state="readonly", width=42,
            values=[
                f'{s["sub_category"]} ({s.get("category_name", "?")})'
                for s in self.subcategories
            ],
        )
        self.subcategory_combo.pack(side="left", padx=4)

        # ===== Carregar produto =====
        load_frame = ttk.Frame(self.root, padding=(10, 4))
        load_frame.pack(fill="x")

        ttk.Label(load_frame, text="Carregar produto:").pack(side="left")
        self.product_combo_var = tk.StringVar()
        self.product_combo = ttk.Combobox(
            load_frame, textvariable=self.product_combo_var,
            state="readonly", width=42,
        )
        self.product_combo.pack(side="left", padx=4)
        self.product_combo.bind(
            "<<ComboboxSelected>>", self._on_product_selected,
        )

        ttk.Button(
            load_frame, text="Novo Produto", command=self._novo_produto,
        ).pack(side="left", padx=6)

        # ===== Composição =====
        comp_frame = ttk.LabelFrame(
            self.root, text="Composição (sub-produtos + timing)", padding=10,
        )
        comp_frame.pack(fill="both", expand=True, padx=10, pady=6)

        cols = ttk.Frame(comp_frame)
        cols.pack(fill="x")
        for texto, largura in [
            ("Sub-produto", 30),
            ("%", 10),
            ("Ref. temporal", 26),
            ("Relativo a", 26),
            ("Elapsed (min)", 12),
            ("Sinal", 6),
            ("", 3),
        ]:
            ttk.Label(cols, text=texto, width=largura).pack(
                side="left", padx=2,
            )

        self.rows_container = ttk.Frame(comp_frame)
        self.rows_container.pack(fill="both", expand=True)

        ttk.Button(
            comp_frame, text="+ Adicionar sub-produto",
            command=self.add_composition_row,
        ).pack(anchor="w", pady=(6, 0))

        self.total_pct_var = tk.StringVar(value="Total: 0.00%")
        self.lbl_total_pct = ttk.Label(
            comp_frame, textvariable=self.total_pct_var,
            font=("", 10, "bold"),
        )
        self.lbl_total_pct.pack(anchor="w", pady=(6, 0))

        # ===== Rodapé =====
        footer = ttk.Frame(self.root, padding=10)
        footer.pack(fill="x", side="bottom")

        if self.on_voltar:
            ttk.Button(
                footer, text="← Voltar", command=self.on_voltar,
            ).pack(side="left")

        ttk.Button(
            footer, text="Limpar", command=self._limpar,
        ).pack(side="left", padx=8)

        ttk.Button(
            footer, text="Salvar Produto", command=self._salvar,
        ).pack(side="right")

    # ---- combo de produtos ----
    def _refresh_products_combo(self):
        self.product_combo["values"] = [p["product"] for p in self.products]

    def _on_product_selected(self, _event=None):
        nome = self.product_combo_var.get()
        prod = next(
            (p for p in self.products if p["product"] == nome), None,
        )
        if not prod:
            return
        self._carregar_produto(prod["id"])

    # ---- composição ----
    def add_composition_row(self, data=None):
        row = _CompositionRow(
            self.rows_container,
            subproducts=self.subproducts,
            all_rows=self.composition_rows,
            on_change=self._recalc_total_pct,
            on_remove=self._remove_composition_row,
        )
        if data:
            row.preencher(data)
        self.composition_rows.append(row)
        self._recalc_total_pct()

    def _remove_composition_row(self, row):
        row.destroy()
        self.composition_rows.remove(row)
        self._recalc_total_pct()
        for r in self.composition_rows:
            r.refresh_relative_to()

    def _recalc_total_pct(self):
        total = Decimal("0")
        for row in self.composition_rows:
            try:
                total += Decimal(
                    row.pct_var.get().replace(",", ".") or "0"
                )
            except InvalidOperation:
                pass
        self.total_pct_var.set(f"Total: {total:.2f}%")

    # ---- carregar produto ----
    def _carregar_produto(self, product_id):
        try:
            prod = self.api._get(f"/api/products/{product_id}/")
            vinculos = self.api._get_paginated(
                f"/api/product-x-sub-products/"
                f"?product={product_id}&active=true"
            )
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar produto:\n{e}")
            return

        self.current_product_id = product_id
        self.name_var.set(prod["product"])
        self.menu_name_var.set(prod.get("name_menu", ""))
        self.desc_var.set(prod.get("description_product", ""))
        self.menu_desc_var.set(prod.get("description_menu", ""))
        self.weight_var.set(str(prod.get("product_weight_or_volume", "")))

        for u in self.units:
            if u["id"] == prod.get("unit_weight_or_volume"):
                self.unit_var.set(f'{u["symbol"]} - {u["unit"]}')
                break

        for s in self.stores:
            if s["id"] == prod.get("store"):
                self.store_var.set(s["name_store"])
                break

        for sc in self.subcategories:
            if sc["id"] == prod.get("sub_category"):
                self.subcategory_var.set(
                    f'{sc["sub_category"]} ({sc.get("category_name", "?")})'
                )
                break

        for row in self.composition_rows:
            row.destroy()
        self.composition_rows.clear()

        # Mapeia ID de vínculo → nome do sub-produto (pra resolver relative_to)
        id_vinculo_para_nome = {}
        for v in vinculos:
            # Busca o nome do sub-produto
            nome = v.get("sub_product_name", "")
            id_vinculo_para_nome[v["id"]] = nome

        for v in vinculos:
            # Converte relative_to (ID) em relative_to_name
            rel_id = v.get("relative_to")
            v["relative_to_name"] = id_vinculo_para_nome.get(rel_id)
            self.add_composition_row(data=v)

        if not vinculos:
            self.add_composition_row()

        # Atualiza os combos "Relativo a" (agora que temos todos os
        # sub-produtos da composição)
        for r in self.composition_rows:
            r.refresh_relative_to()

        # Agora preenche os "Relativo a" que estavam pendentes
        for r in self.composition_rows:
            r.aplicar_relative_pendente()

        self._recalc_total_pct()

    # ---- ações ----
    def _novo_produto(self):
        self.current_product_id = None
        self.name_var.set("")
        self.menu_name_var.set("")
        self.desc_var.set("")
        self.menu_desc_var.set("")
        self.weight_var.set("")
        self.unit_var.set("")
        self.subcategory_var.set("")
        self.product_combo_var.set("")
        if self.stores:
            self.store_var.set(self.stores[0]["name_store"])

        for row in self.composition_rows:
            row.destroy()
        self.composition_rows.clear()
        self.add_composition_row()

    def _limpar(self):
        self._novo_produto()

    def _salvar(self):
        # ---------- validações do cabeçalho ----------
        nome = self.name_var.get().strip()
        if not nome:
            messagebox.showwarning("Atenção", "Informe o nome do produto.")
            return
        menu_name = self.menu_name_var.get().strip()
        if not menu_name:
            messagebox.showwarning("Atenção", "Informe o nome no menu.")
            return
        desc = self.desc_var.get().strip()
        if not desc:
            messagebox.showwarning(
                "Atenção", "Informe a descrição do produto.",
            )
            return
        menu_desc = self.menu_desc_var.get().strip()
        if not menu_desc:
            messagebox.showwarning(
                "Atenção", "Informe a descrição no menu.",
            )
            return
        peso_str = self.weight_var.get().strip().replace(",", ".")
        if not peso_str:
            messagebox.showwarning("Atenção", "Informe o peso/volume.")
            return
        try:
            peso = float(peso_str)
        except ValueError:
            messagebox.showwarning("Atenção", "Peso/volume inválido.")
            return

        unit_id = None
        for u in self.units:
            if f'{u["symbol"]} - {u["unit"]}' == self.unit_var.get():
                unit_id = u["id"]
                break
        if not unit_id:
            messagebox.showwarning("Atenção", "Escolha a unidade.")
            return

        store_id = None
        for s in self.stores:
            if s["name_store"] == self.store_var.get():
                store_id = s["id"]
                break
        if not store_id:
            messagebox.showwarning("Atenção", "Escolha a loja.")
            return

        subcat_id = None
        for sc in self.subcategories:
            label = f'{sc["sub_category"]} ({sc.get("category_name", "?")})'
            if label == self.subcategory_var.get():
                subcat_id = sc["id"]
                break
        if not subcat_id:
            messagebox.showwarning("Atenção", "Escolha a subcategoria.")
            return

        # ---------- validações da composição ----------
        composicao = []
        for row in self.composition_rows:
            dados = row.get_payload()
            if not dados:
                continue
            composicao.append((row, dados))

        if not composicao:
            messagebox.showwarning(
                "Atenção", "Adicione pelo menos 1 sub-produto à composição."
            )
            return

        # Valida relative_to obrigatório quando tem booleano ativo
        for row, d in composicao:
            if (
                d["at_start"] or d["at_finish"] or d["after_to"]
            ) and not d["relative_to_nome"]:
                messagebox.showwarning(
                    "Atenção",
                    f"O sub-produto '{row.subproduct_var.get()}' tem "
                    f"referência temporal ativa mas não escolheu "
                    f"'Relativo a'.",
                )
                return

        # Valida after_to + sinal -
        for row, d in composicao:
            if d["after_to"] and d["elapsed_signal"] == "-":
                messagebox.showwarning(
                    "Atenção",
                    f"Sub-produto '{row.subproduct_var.get()}': "
                    f"after_to com sinal '-' não faz sentido.",
                )
                return

        total_pct = sum(
            (Decimal(d["composition_percentage"]) for _, d in composicao),
            Decimal("0"),
        )
        if total_pct != Decimal("100"):
            ok = messagebox.askyesno(
                "Aviso",
                f"A soma dos percentuais é {total_pct:.2f}% "
                f"(deveria ser 100%).\n\nDeseja salvar mesmo assim?",
            )
            if not ok:
                return

        # ---------- salva produto ----------
        payload = {
            "product": nome,
            "description_product": desc,
            "name_menu": menu_name,
            "description_menu": menu_desc,
            "product_weight_or_volume": f"{peso:.4f}",
            "unit_weight_or_volume": unit_id,
            "store": store_id,
            "sub_category": subcat_id,
            "active": True,
        }

        try:
            if self.current_product_id:
                self.api._post(
                    f"/api/products/{self.current_product_id}/",
                    payload, method="PUT",
                )
                product_id = self.current_product_id
                # Apaga vínculos antigos
                import requests
                antigos = self.api._get_paginated(
                    f"/api/product-x-sub-products/?product={product_id}"
                )
                for v in antigos:
                    requests.delete(
                        f"{self.api.base_url}/api/product-x-sub-products/"
                        f"{v['id']}/",
                        headers=self.api._headers(),
                        timeout=10,
                    )
            else:
                prod = self.api._post("/api/products/", payload)
                product_id = prod["id"]
        except Exception as e:
            messagebox.showerror("Erro ao salvar produto", str(e))
            return

        # ---------- cria vínculos em ordem de dependência ----------
        try:
            self._criar_vinculos_ordenados(product_id, composicao)
        except Exception as e:
            messagebox.showerror("Erro ao salvar composição", str(e))
            return

        messagebox.showinfo("Sucesso", f"Produto '{nome}' salvo.")
        self._reload_products()
        self._refresh_products_combo()
        self.product_combo_var.set(nome)
        self.current_product_id = product_id

    def _criar_vinculos_ordenados(self, product_id, composicao):
        """
        Cria os vínculos em ordem de dependência:
          - Primeiro os sem relative_to
          - Depois os que dependem dos já criados
          - Repete até acabar
        """
        # Mapa nome_do_subproduto -> (row, dados)
        por_nome = {}
        for row, d in composicao:
            nome = row.subproduct_var.get()
            por_nome[nome] = (row, d)

        pendentes = set(por_nome.keys())
        id_por_nome = {}  # nome -> ID do vínculo criado

        while pendentes:
            progrediu = False
            for nome in list(pendentes):
                row, d = por_nome[nome]
                rel_nome = d.get("relative_to_nome") or ""

                # Se tem relative_to, precisa do ID do relativo
                if rel_nome:
                    if rel_nome not in id_por_nome:
                        # Ainda não criado, pula
                        continue
                    rel_id = id_por_nome[rel_nome]
                else:
                    rel_id = None

                # Cria o vínculo
                payload = {
                    "product": product_id,
                    "sub_product": d["sub_product"],
                    "composition_percentage": d["composition_percentage"],
                    "at_start": d["at_start"],
                    "at_finish": d["at_finish"],
                    "after_to": d["after_to"],
                    "relative_to": rel_id,
                    "elapsed_time": d["elapsed_time"],
                    "elapsed_signal": d["elapsed_signal"],
                    "active": True,
                }
                criado = self.api._post(
                    "/api/product-x-sub-products/", payload,
                )
                id_por_nome[nome] = criado["id"]
                pendentes.remove(nome)
                progrediu = True

            if not progrediu:
                # Ciclo ou referência a sub-produto inexistente
                raise ValueError(
                    "Não foi possível criar todos os vínculos. "
                    f"Verifique dependências circulares: {pendentes}"
                )


# =========================================================================
# Linha da composição (com timing)
# =========================================================================
class _CompositionRow:
    def __init__(
        self, parent, subproducts, all_rows, on_change, on_remove,
    ):
        self.subproducts = subproducts
        self.all_rows = all_rows
        self.on_change = on_change
        self.on_remove = on_remove

        self.id_by_name = {
            f'{s["sub_product"]}': s["id"] for s in subproducts
        }
        self._relative_to_pendente = None  # usado no preencher()

        self.frame = ttk.Frame(parent)
        self.frame.pack(fill="x", pady=2)

        # Sub-produto
        self.subproduct_var = tk.StringVar()
        self.subproduct_combo = ttk.Combobox(
            self.frame, textvariable=self.subproduct_var,
            state="readonly", width=30,
            values=list(self.id_by_name.keys()),
        )
        self.subproduct_combo.grid(row=0, column=0, padx=2)
        self.subproduct_combo.bind(
            "<<ComboboxSelected>>", lambda e: self._refresh_all_relatives(),
        )

        # %
        self.pct_var = tk.StringVar(value="100.00")
        ttk.Entry(
            self.frame, textvariable=self.pct_var, width=10,
        ).grid(row=0, column=1, padx=2)
        self.pct_var.trace_add("write", lambda *a: self.on_change())

        # Ref. temporal
        self.ref_var = tk.StringVar(value=REF_NENHUM)
        self.ref_combo = ttk.Combobox(
            self.frame, textvariable=self.ref_var,
            state="readonly", width=26,
            values=[REF_NENHUM, REF_AT_START, REF_AT_FINISH, REF_AFTER_TO],
        )
        self.ref_combo.grid(row=0, column=2, padx=2)
        self.ref_combo.bind(
            "<<ComboboxSelected>>", self._on_ref_change,
        )

        # Relativo a
        self.relative_var = tk.StringVar()
        self.relative_combo = ttk.Combobox(
            self.frame, textvariable=self.relative_var,
            state="disabled", width=26, values=[],
        )
        self.relative_combo.grid(row=0, column=3, padx=2)

        # Elapsed (min)
        self.elapsed_var = tk.StringVar(value="0")
        self.elapsed_entry = ttk.Entry(
            self.frame, textvariable=self.elapsed_var, width=10,
            state="disabled",
        )
        self.elapsed_entry.grid(row=0, column=4, padx=2)

        # Sinal
        self.signal_var = tk.StringVar(value="+")
        self.signal_combo = ttk.Combobox(
            self.frame, textvariable=self.signal_var,
            state="disabled", width=4, values=["+", "-"],
        )
        self.signal_combo.grid(row=0, column=5, padx=2)

        # Remover
        ttk.Button(
            self.frame, text="X", width=3,
            command=lambda: self.on_remove(self),
        ).grid(row=0, column=6, padx=2)

    # ---- callbacks ----
    def _refresh_all_relatives(self):
        """Quando muda o sub-produto, atualiza os combos 'Relativo a'
        de todas as linhas (porque o nome mudou)."""
        for r in self.all_rows:
            r.refresh_relative_to()

    def _on_ref_change(self, _event=None):
        if self.ref_var.get() == REF_NENHUM:
            self.relative_combo.config(state="disabled")
            self.relative_var.set("")
            self.elapsed_entry.config(state="normal")
            self.signal_combo.config(state="disabled")
            self.signal_var.set("+")
        else:
            self.relative_combo.config(state="readonly")
            self.elapsed_entry.config(state="normal")
            self.signal_combo.config(state="readonly")
            self.refresh_relative_to()

    # ---- refresh ----
    def refresh_relative_to(self):
        """Atualiza as opções do combo 'Relativo a' com os outros
        sub-produtos da composição."""
        opcoes = []
        for r in self.all_rows:
            if r is self:
                continue
            nome = r.subproduct_var.get()
            if nome:
                opcoes.append(nome)
        self.relative_combo["values"] = opcoes
        if self.relative_var.get() and self.relative_var.get() not in opcoes:
            self.relative_var.set("")

    # ---- payload ----
    def preencher(self, v):
        """v = vínculo vindo da API."""
        for name, id_ in self.id_by_name.items():
            if id_ == v["sub_product"]:
                self.subproduct_var.set(name)
                break

        self.pct_var.set(str(v["composition_percentage"]))

        if v.get("at_start"):
            self.ref_var.set(REF_AT_START)
        elif v.get("at_finish"):
            self.ref_var.set(REF_AT_FINISH)
        elif v.get("after_to"):
            self.ref_var.set(REF_AFTER_TO)
        else:
            self.ref_var.set(REF_NENHUM)

        # Usa o nome do relativo (não o ID)
        rel_nome = v.get("relative_to_name")
        if rel_nome:
            self.relative_var.set(rel_nome)

        minutos = duration_para_minutos(v.get("elapsed_time", "0:00:00"))
        self.elapsed_var.set(f"{minutos:.2f}".rstrip("0").rstrip(".") or "0")

        self.signal_var.set(v.get("elapsed_signal", "+"))
        self._on_ref_change()

    def aplicar_relative_pendente(self):
        """
        Aplica o `relative_to` que veio da API, depois que todos os
        combos foram preenchidos.
        """
        if self._relative_to_pendente is None:
            return
        # Procura o sub-produto cujo ID é _relative_to_pendente
        # Como o combo guarda NOME, e não temos o ID dos outros vínculos,
        # precisamos de outra abordagem: o backend devolve `relative_to`
        # como ID de vínculo. Mas no `lve_nf`, só temos os dados do
        # próprio vínculo. Então usamos `relative_to_name` (do serializer).
        # Esse método é substituído pelo `_carregar_produto` que vai
        # preencher direto pelo nome.

        # Solução: o `_carregar_produto` passa o `relative_to_name` no
        # `preencher`, em vez do `relative_to` (ID).
        pass

    def get_payload(self):
        sub_id = self.id_by_name.get(self.subproduct_var.get())
        if not sub_id:
            return None
        try:
            pct = Decimal(self.pct_var.get().replace(",", ".") or "0")
        except InvalidOperation:
            pct = Decimal("0")

        ref = self.ref_var.get()
        at_start = ref == REF_AT_START
        at_finish = ref == REF_AT_FINISH
        after_to = ref == REF_AFTER_TO

        try:
            minutos = float(self.elapsed_var.get().replace(",", ".") or "0")
        except ValueError:
            minutos = 0.0

        return {
            "sub_product": sub_id,
            "composition_percentage": f"{pct:.6f}",
            "at_start": at_start,
            "at_finish": at_finish,
            "after_to": after_to,
            "relative_to_nome": self.relative_var.get(),
            "elapsed_time": minutos_para_duration(minutos),
            "elapsed_signal": self.signal_var.get(),
            "active": True,
        }

    def destroy(self):
        self.frame.destroy()