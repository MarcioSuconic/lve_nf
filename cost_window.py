# lve_nf/cost_window.py
import tkinter as tk
from decimal import Decimal, ROUND_HALF_UP
from tkinter import messagebox, ttk


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

        self.root.title("LVE — Custo da Receita Base")
        self.root.geometry("1100x650")

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
        box = ttk.LabelFrame(self.root, text="Custo detalhado", padding=10)
        box.pack(fill="both", expand=True, padx=10, pady=10)

        cols = ("etapa", "operacao", "tempo", "maquinario",
                "insumo", "qtde", "custo_insumo",
                "custo_energia", "custo_mao_obra")
        headings = (
            ("etapa", "Etapa"),
            ("operacao", "Operação"),
            ("tempo", "Tempo (h)"),
            ("maquinario", "Maquinário"),
            ("insumo", "Insumo"),
            ("qtde", "Qtde"),
            ("custo_insumo", "Custo insumo"),
            ("custo_energia", "Custo energia"),
            ("custo_mao_obra", "Custo mão de obra"),
        )
        widths = (110, 100, 70, 130, 130, 90, 100, 100, 110)
        self.tree = ttk.Treeview(box, columns=cols, show="headings", height=14)
        for (c, t), w in zip(headings, widths):
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True)

        # ---- Totais ----
        totals = ttk.LabelFrame(self.root, text="Totais", padding=10)
        totals.pack(fill="x", padx=10, pady=6)

        self.lbl_insumos = ttk.Label(totals, text="Insumos: R$ 0,00")
        self.lbl_insumos.pack(side="left", padx=10)
        self.lbl_energia = ttk.Label(totals, text="Energia: R$ 0,00")
        self.lbl_energia.pack(side="left", padx=10)
        self.lbl_mao = ttk.Label(totals, text="Mão de obra: R$ 0,00")
        self.lbl_mao.pack(side="left", padx=10)
        self.lbl_total = ttk.Label(
            totals, text="CUSTO TOTAL: R$ 0,00", font=("", 12, "bold"),
        )
        self.lbl_total.pack(side="left", padx=20)

        # ---- Informação de tamanho/rendimento ----
        info = ttk.Frame(self.root, padding=(10, 0))
        info.pack(fill="x")
        self.lbl_size = ttk.Label(info, text="", foreground="#555")
        self.lbl_size.pack(side="left")

        # ---- Rodapé ----
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
            if insumo.get("erro"):
                nome_insumo = f'{insumo.get("food_ingredient", "?")} (sem compra)'
            qtde = insumo.get("qtde_receita", "")
            unidade = insumo.get("unidade_receita", "")
            qtde_str = f"{qtde} {unidade}".strip() or "—"

            self.tree.insert("", "end", values=(
                p["etapa"],
                p["operacao"],
                fmt(p["tempo_h"], 3),
                p.get("maquinario") or "—",
                nome_insumo,
                qtde_str,
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
        self.lbl_size.config(
            text=f"Tamanho da receita: {fmt(c['size'], 2)} {c['unit_size']}"
        )