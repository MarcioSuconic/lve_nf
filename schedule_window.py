# lve_nf/schedule_window.py
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk


class ScheduleWindow:
    """
    Tela de cronograma de produção.

    Escolhe um produto, uma data/hora de início, e mostra o cronograma
    calculado pelo backend.
    """

    def __init__(self, root, api, on_voltar=None):
        self.root = root
        self.api = api
        self.on_voltar = on_voltar

        self.root.title("LVE — Cronograma de Produção")
        self.root.geometry("1300x700")

        self.products = []
        self.resultado = None

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

        ttk.Label(header, text="Início:").pack(side="left", padx=(12, 4))
        self.start_var = tk.StringVar(
            value=datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        )
        ttk.Entry(header, textvariable=self.start_var, width=22).pack(
            side="left", padx=4,
        )

        ttk.Button(
            header, text="Calcular", command=self._calcular,
        ).pack(side="left", padx=8)

        # ---- resumo ----
        self.lbl_resumo = ttk.Label(
            self.root, text="", font=("", 11, "bold"), padding=(10, 4),
        )
        self.lbl_resumo.pack(fill="x")

        # ---- tabela ----
        box = ttk.LabelFrame(self.root, text="Cronograma", padding=8)
        box.pack(fill="both", expand=True, padx=10, pady=6)

        cols = (
            "sub_product", "duracao", "inicio", "fim",
            "at_start", "at_finish", "after_to",
            "relative_to", "elapsed",
        )
        headings = (
            ("sub_product", "Sub-produto"),
            ("duracao", "Duração (h)"),
            ("inicio", "Início"),
            ("fim", "Fim"),
            ("at_start", "at_start"),
            ("at_finish", "at_finish"),
            ("after_to", "after_to"),
            ("relative_to", "Relativo a"),
            ("elapsed", "Elapsed"),
        )
        widths = (180, 90, 140, 140, 70, 70, 70, 140, 90)

        self.tree = ttk.Treeview(box, columns=cols, show="headings", height=15)
        for (c, t), w in zip(headings, widths):
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True)

        # ---- rodapé ----
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
            self.resultado = self.api._get(
                f"/api/products/{produto['id']}/schedule/"
                f"?start={start_str}"
            )
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao calcular:\n{e}")
            return

        self._preencher()

    def _preencher(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        r = self.resultado
        self.lbl_resumo.config(
            text=(
                f"Produto: {r.get('product_id')} | "
                f"Início: {r['data_inicio']} | "
                f"Fim: {r['data_fim']} | "
                f"Duração total: {float(r['duracao_total_h']):.2f} h"
            )
        )

        def fmt_dt(s):
            try:
                dt = datetime.fromisoformat(s)
                return dt.strftime("%d/%m %H:%M")
            except Exception:
                return s

        def fmt_bool(b):
            return "✓" if b else ""

        def fmt_elapsed(signal, valor_h):
            h = float(valor_h)
            if h == 0:
                return "0"
            return f"{signal}{h:.2f}h"

        for p in r["passos"]:
            self.tree.insert("", "end", values=(
                p["sub_product"],
                f'{float(p["duracao_h"]):.2f}',
                fmt_dt(p["inicio"]),
                fmt_dt(p["fim"]),
                fmt_bool(p["at_start"]),
                fmt_bool(p["at_finish"]),
                fmt_bool(p["after_to"]),
                p["relative_to"] or "—",
                fmt_elapsed(p["elapsed_signal"], p["elapsed_time"]),
            ))