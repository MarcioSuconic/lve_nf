# lve_nf/product_cost_window.py
import subprocess
import tempfile
import tkinter as tk
import urllib.request
from decimal import Decimal
from tkinter import messagebox, ttk


def _fmt(valor, casas=2):
    """Formata Decimal/str para exibição brasileira: 1234.56 → 1.234,56"""
    if valor is None:
        return "—"
    d = Decimal(str(valor))
    s = f"{d:,.{casas}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


class ProductCostWindow:
    def __init__(self, root, api, on_voltar=None):
        self.root = root
        self.api = api
        self.on_voltar = on_voltar

        self.root.title("LVE — Custo e Preço do Produto")
        self.root.geometry("1150x720")

        self.products = []
        self.current = None

        self._load_products()
        self._build_ui()

    def _load_products(self):
        try:
            self.products = self.api._get_paginated("/api/products/?active=true")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar produtos:\n{e}")
            self.root.destroy()
            raise SystemExit

    def _build_ui(self):
        header = ttk.Frame(self.root, padding=10)
        header.pack(fill="x")

        ttk.Label(header, text="Produto:").pack(side="left")
        self.product_var = tk.StringVar()
        self.product_combo = ttk.Combobox(
            header, textvariable=self.product_var,
            state="readonly", width=42,
            values=[p["product"] for p in self.products],
        )
        self.product_combo.pack(side="left", padx=4)

        ttk.Button(
            header, text="Calcular", command=self._calcular,
        ).pack(side="left", padx=8)

        # ---- sub-produtos ----
        box = ttk.LabelFrame(self.root, text="Composição do produto", padding=8)
        box.pack(fill="both", expand=True, padx=10, pady=6)

        cols = ("sub", "receita", "pct", "qtd", "custo_receita", "custo_no_produto")
        self.tree = ttk.Treeview(box, columns=cols, show="headings", height=8)
        headings = (
            ("sub", "Sub-produto"),
            ("receita", "Receita base"),
            ("pct", "%"),
            ("qtd", "Qtd no produto"),
            ("custo_receita", "Custo da receita"),
            ("custo_no_produto", "Custo no produto"),
        )
        widths = (190, 180, 70, 130, 140, 140)
        for (col, title), w in zip(headings, widths):
            self.tree.heading(col, text=title)
            self.tree.column(col, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True)

        # ---- totais ----
        totals = ttk.LabelFrame(self.root, text="Totais", padding=10)
        totals.pack(fill="x", padx=10, pady=6)

        self.lbl_custo = ttk.Label(totals, text="Custo do produto: R$ 0,00")
        self.lbl_custo.pack(side="left", padx=10)

        self.lbl_markup = ttk.Label(totals, text="Markup: 0%")
        self.lbl_markup.pack(side="left", padx=10)

        self.lbl_bruto = ttk.Label(totals, text="Preço bruto: R$ 0,00")
        self.lbl_bruto.pack(side="left", padx=10)

        self.lbl_preco = ttk.Label(
            totals, text="PREÇO DE VENDA: R$ 0,00", font=("", 13, "bold"),
        )
        self.lbl_preco.pack(side="left", padx=20)

        # Botão de ficha técnica à direita
        ttk.Button(
            totals, text="Gerar Ficha Técnica",
            command=self._gerar_ficha,
        ).pack(side="right", padx=10)

        # ---- footer ----
        footer = ttk.Frame(self.root, padding=10)
        footer.pack(fill="x", side="bottom")
        if self.on_voltar:
            ttk.Button(
                footer, text="← Voltar", command=self.on_voltar,
            ).pack(side="left")

    def _calcular(self):
        nome = self.product_var.get()
        produto = next(
            (p for p in self.products if p["product"] == nome), None,
        )
        if not produto:
            messagebox.showwarning("Atenção", "Escolha um produto.")
            return

        try:
            self.current = self.api.get_product_unit_cost(produto["id"])
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao calcular:\n{e}")
            return

        self._preencher()

    def _preencher(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for s in self.current["sub_products"]:
            self.tree.insert("", "end", values=(
                s["sub_product"],
                s["base_recipe"],
                _fmt(s["composition_percentage"], 2),
                f'{_fmt(s["quantity_in_product"], 4)} {s["unit_in_product"]}',
                f'R$ {_fmt(s["recipe_cost_total"])}',
                f'R$ {_fmt(s["cost_in_product"])}',
            ))

        c = self.current
        self.lbl_custo.config(
            text=f"Custo do produto: R$ {_fmt(c['custo_produto'])}"
        )
        self.lbl_markup.config(
            text=f"Markup: {_fmt(c['markup_default'], 2)}%"
        )
        self.lbl_bruto.config(
            text=f"Preço bruto: R$ {_fmt(c['preco_bruto'])}"
        )
        self.lbl_preco.config(
            text=f"PREÇO DE VENDA: R$ {_fmt(c['preco_sugerido'])}"
        )

    def _gerar_ficha(self):
        if not self.current:
            messagebox.showwarning("Atenção", "Calcule o custo primeiro.")
            return

        try:
            info = self.api.generate_tech_sheet(self.current["product_id"])
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao gerar ficha:\n{e}")
            return

        url = self.api.get_tech_sheet_url(
            self.current["product_id"], version=info["version"],
        )

        try:
            req = urllib.request.Request(url)
            if self.api.token:
                req.add_header("Authorization", f"Token {self.api.token}")
            with urllib.request.urlopen(req) as resp:
                pdf_bytes = resp.read()

            tmp = tempfile.NamedTemporaryFile(
                suffix=".pdf", delete=False,
                prefix=f"ficha_{info['version']}_",
            )
            tmp.write(pdf_bytes)
            tmp.close()

            subprocess.Popen(["xdg-open", tmp.name])
            messagebox.showinfo(
                "Ficha gerada",
                f"Versão {info['version']} gerada e aberta no visualizador.",
            )
        except Exception as e:
            messagebox.showerror(
                "Erro ao abrir",
                f"PDF gerado em:\n{info['file']}\n\n"
                f"Mas falhou ao abrir:\n{e}",
            )