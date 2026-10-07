# lve_nf/cost_window.py
import tkinter as tk
from decimal import Decimal, ROUND_HALF_UP
from tkinter import messagebox, ttk

from api import APIError


def fmt(valor, casas=2):
    if valor is None:
        return "—"
    return str(Decimal(str(valor)).quantize(
        Decimal(f"0.{'0'*casas}"), rounding=ROUND_HALF_UP
    ))


class CostWindow:
    def __init__(self, root, api, on_voltar=None):
        self.root = root
        self.api = api
        self.on_voltar = on_voltar

        self.root.title("LVE — Custo e Preço")
        self.root.geometry("1000x650")

        self.recipes = []
        self.current_cost = None

        self._load_recipes()
        self._build_ui()

    def _load_recipes(self):
        try:
            self.recipes = self.api.list_base_recipes()
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar receitas:\n{e}")
            self.root.destroy()
            raise SystemExit

    def _build_ui(self):
        # ---- Header ----
        header = ttk.Frame(self.root, padding=10)
        header.pack(fill="x")

        ttk.Label(header, text="Receita:").pack(side="left")
        self.recipe_var = tk.StringVar()
        self.recipe_combo = ttk.Combobox(
            header, textvariable=self.recipe_var,
            state="readonly", width=40,
            values=[r["base_recipe"] for r in self.recipes],
        )
        self.recipe_combo.pack(side="left", padx=4)

        ttk.Button(
            header, text="Calcular", command=self._calcular,
        ).pack(side="left", padx=8)

        # ---- Resultado ----
        self.result_frame = ttk.LabelFrame(
            self.root, text="Custo detalhado", padding=10,
        )
        self.result_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Treeview dos passos
        cols = ("etapa", "operacao", "tempo", "maquinario",
                "insumo", "qtde", "custo_insumo",
                "custo_energia", "custo_mao_obra")
        self.tree = ttk.Treeview(
            self.result_frame, columns=cols, show="headings", height=12,
        )
        for c, w in zip(cols, (100, 90, 60, 120, 120, 80, 90, 90, 100)):
            self.tree.heading(c, text=c.replace("_", " ").title())
            self.tree.column(c, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True)

        # Totais
        totais = ttk.Frame(self.root, padding=10)
        totais.pack(fill="x")

        self.lbl_insumos = ttk.Label(totais, text="Insumos: R$ 0,00")
        self.lbl_insumos.pack(side="left", padx=8)
        self.lbl_energia = ttk.Label(totais, text="Energia: R$ 0,00")
        self.lbl_energia.pack(side="left", padx=8)
        self.lbl_mao = ttk.Label(totais, text="Mão de obra: R$ 0,00")
        self.lbl_mao.pack(side="left", padx=8)
        self.lbl_total = ttk.Label(
            totais, text="CUSTO TOTAL: R$ 0,00", font=("", 11, "bold"),
        )
        self.lbl_total.pack(side="left", padx=20)

        # Margem e preço
        precos = ttk.LabelFrame(self.root, text="Preço de venda", padding=10)
        precos.pack(fill="x", padx=10, pady=(0, 10))

        ttk.Label(precos, text="Margem desejada (%):").pack(side="left")
        self.margem_var = tk.StringVar(value="60")
        ttk.Entry(precos, textvariable=self.margem_var, width=8).pack(
            side="left", padx=4,
        )
        ttk.Button(
            precos, text="Calcular preço", command=self._calcular_preco,
        ).pack(side="left", padx=8)

        self.lbl_preco = ttk.Label(
            precos, text="Preço sugerido: —", font=("", 12, "bold"),
        )
        self.lbl_preco.pack(side="left", padx=20)

        # Rodapé
        footer = ttk.Frame(self.root, padding=10)
        footer.pack(fill="x", side="bottom")
        if self.on_voltar:
            ttk.Button(
                footer, text="← Voltar", command=self.on_voltar,
            ).pack(side="left")

    def _calcular(self):
        nome = self.recipe_var.get()
        receita = next(
            (r for r in self.recipes if r["base_recipe"] == nome), None,
        )
        if not receita:
            messagebox.showwarning("Atenção", "Escolha uma receita.")
            return

        try:
            self.current_cost = self.api.get_recipe_cost(receita["id"])
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao calcular:\n{e}")
            return

        self._preencher_tree()
        self._preencher_totais()

    def _preencher_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for p in self.current_cost["passos"]:
            insumo = p.get("insumo") or {}
            nome_insumo = insumo.get("food_ingredient", "—")
            qtde = insumo.get("qtde_receita", "—")
            unidade = insumo.get("unidade_receita", "")
            self.tree.insert("", "end", values=(
                p["etapa"],
                p["operacao"],
                fmt(p["tempo_h"], 2),
                p.get("maquinario") or "—",
                nome_insumo,
                f"{qtde} {unidade}".strip(),
                fmt(p["custo_insumo"]),
                fmt(p["custo_energia"]),
                fmt(p["custo_mao_obra"]),
            ))

    def _preencher_totais(self):
        c = self.current_cost
        self.lbl_insumos.config(text=f"Insumos: R$ {fmt(c['total_insumos'])}")
        self.lbl_energia.config(text=f"Energia: R$ {fmt(c['total_energia'])}")
        self.lbl_mao.config(text=f"Mão de obra: R$ {fmt(c['total_mao_obra'])}")
        self.lbl_total.config(
            text=f"CUSTO TOTAL: R$ {fmt(c['custo_total'])}"
        )
        self.lbl_preco.config(text="Preço sugerido: —")

    def _calcular_preco(self):
        if not self.current_cost:
            messagebox.showwarning("Atenção", "Calcule o custo primeiro.")
            return
        try:
            margem = Decimal(self.margem_var.get().replace(",", ".")) / 100
        except Exception:
            messagebox.showwarning("Atenção", "Margem inválida.")
            return

        if margem <= 0 or margem >= 1:
            messagebox.showwarning("Atenção", "Margem deve estar entre 0 e 100.")
            return

        custo = Decimal(self.current_cost["custo_total"])
        preco = custo / (1 - margem)   # margem sobre preço
        self.lbl_preco.config(text=f"Preço sugerido: R$ {fmt(preco)}")