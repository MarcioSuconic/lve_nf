# lve_nf/dialogs/timeline_dialog.py
import tkinter as tk
from tkinter import ttk


# Paleta de cores — uma por etapa, cicla se houver mais etapas que cores
CORES = [
    "#4e79a7",  # azul
    "#59a14f",  # verde
    "#f28e2b",  # laranja
    "#e15759",  # vermelho
    "#b07aa1",  # roxo
    "#76b7b2",  # turquesa
    "#edc948",  # amarelo
    "#ff9da7",  # rosa
]


class TimelineDialog(tk.Toplevel):
    """
    Popup da linha do tempo de uma receita.

    Recebe uma lista de passos com:
        {elapsed_min, execution_min, operacao, etapa, incorporado,
         insumo, ph, temperatura}

    Uso:
        dlg = TimelineDialog(parent, titulo="Pão de queijo", passos=passos)
        parent.wait_window(dlg)
    """

    def __init__(self, parent, titulo, passos):
        super().__init__(parent)
        self.passos = passos

        self.title(f"Linha do tempo — {titulo}")
        self.transient(parent)
        self.grab_set()
        self.resizable(True, True)

        # Ordena por elapsed
        self.passos.sort(key=lambda p: p["elapsed_min"])

        # Dimensões do desenho
        self.LARGURA_GANTT = 700            # área do gantt
        self.LARGURA_TABELA = 480           # coluna lateral com detalhes
        self.LARGURA = self.LARGURA_GANTT + self.LARGURA_TABELA
        self.ALTURA_BARRA = 26
        self.ESPACO_BARRA = 6
        self.MARGEM_ESQ = 60
        self.MARGEM_DIR = 30
        self.MARGEM_TOPO = 40

        n = len(self.passos)
        altura_gantt = (
            self.MARGEM_TOPO
            + n * (self.ALTURA_BARRA + self.ESPACO_BARRA)
            + 40
        )
        altura_total = max(altura_gantt, 200)

        self.canvas = tk.Canvas(
            self,
            width=self.LARGURA,
            height=altura_total,
            background="white",
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True, padx=10, pady=10)

        self._desenhar()

        # Botão fechar
        btns = ttk.Frame(self)
        btns.pack(fill="x", pady=(0, 10), padx=10)
        ttk.Button(btns, text="Fechar", command=self.destroy).pack(side="right")

        self.bind("<Escape>", lambda e: self.destroy())

    # ------------------------------------------------------------------
    def _desenhar(self):
        if not self.passos:
            self.canvas.create_text(
                self.LARGURA / 2, 60,
                text="Nenhum passo cadastrado.",
                fill="#888",
            )
            return

        # Linha vertical separando gantt da tabela
        x_div = self.LARGURA_GANTT + 20
        self.canvas.create_line(
            x_div, 10, x_div, self.canvas.winfo_reqheight() - 10,
            fill="#DDD",
        )

        # ---- Desenha o Gantt (à esquerda) ----
        self._desenhar_gantt()

        # ---- Desenha a tabela lateral (à direita) ----
        self._desenhar_tabela(x_div + 10)

    # ------------------------------------------------------------------
    def _desenhar_gantt(self):
        # Determina escala em minutos
        min_inicio = min(p["elapsed_min"] for p in self.passos)
        max_fim = max(
            p["elapsed_min"] + p["execution_min"] for p in self.passos
        )
        duracao = max(max_fim - min_inicio, 1)

        largura_util = self.LARGURA_GANTT - self.MARGEM_ESQ - self.MARGEM_DIR

        def x_para(minuto):
            return (
                self.MARGEM_ESQ
                + (minuto - min_inicio) / duracao * largura_util
            )

        # ---- Régua no topo ----
        passo_marcador = self._escolher_passo(duracao)
        marca = min_inicio
        while marca <= max_fim:
            x = x_para(marca)
            self.canvas.create_line(
                x, self.MARGEM_TOPO - 6,
                x, self.MARGEM_TOPO,
                fill="#999",
            )
            self.canvas.create_text(
                x, self.MARGEM_TOPO - 12,
                text=f"{int(marca)}",
                fill="#555",
                font=("", 8),
            )
            marca += passo_marcador

        self.canvas.create_line(
            self.MARGEM_ESQ, self.MARGEM_TOPO,
            self.LARGURA_GANTT - self.MARGEM_DIR, self.MARGEM_TOPO,
            fill="#ccc",
        )

        # ---- Barras ----
        etapas = sorted({p["etapa"] for p in self.passos})
        cor_por_etapa = {
            etapa: CORES[i % len(CORES)]
            for i, etapa in enumerate(etapas)
        }

        y = self.MARGEM_TOPO + 20
        for p in self.passos:
            x1 = x_para(p["elapsed_min"])
            x2 = x_para(p["elapsed_min"] + p["execution_min"])
            if x2 - x1 < 2:
                x2 = x1 + 2

            y1 = y
            y2 = y + self.ALTURA_BARRA

            cor = cor_por_etapa[p["etapa"]]
            if p["incorporado"]:
                self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill=cor, outline="",
                )
            else:
                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill="#eeeeee", outline=cor, width=2,
                )
                passo = 6
                xx = x1
                while xx < x2:
                    self.canvas.create_line(
                        xx, y2, xx + passo, y1,
                        fill=cor, width=1,
                    )
                    xx += passo * 2

            largura_barra = x2 - x1
            if largura_barra > 60:
                self.canvas.create_text(
                    (x1 + x2) / 2, (y1 + y2) / 2,
                    text=p["operacao"], fill="white", font=("", 9),
                )
            else:
                self.canvas.create_text(
                    x2 + 4, (y1 + y2) / 2,
                    text=p["operacao"], anchor="w",
                    fill="#333", font=("", 9),
                )

            # Rótulo da etapa à esquerda da barra
            self.canvas.create_text(
                self.MARGEM_ESQ - 6, (y1 + y2) / 2,
                text=p["etapa"][:10],
                anchor="e",
                fill="#666",
                font=("", 8),
            )

            y = y2 + self.ESPACO_BARRA

        # ---- Legenda ----
        leg_y = y + 10
        leg_x = self.MARGEM_ESQ
        for etapa in etapas:
            cor = cor_por_etapa[etapa]
            self.canvas.create_rectangle(
                leg_x, leg_y, leg_x + 12, leg_y + 12,
                fill=cor, outline="",
            )
            self.canvas.create_text(
                leg_x + 16, leg_y + 6,
                text=etapa, anchor="w",
                fill="#333", font=("", 9),
            )
            leg_x += 20 + len(etapa) * 7

    # ------------------------------------------------------------------
    def _desenhar_tabela(self, x0):
        """
        Desenha uma tabela textual à direita do Gantt, com:
        Etapa | Operação | Insumo | pH | Temp | Tempo
        """
        # Larguras das colunas
        colunas = [
            ("Etapa",      90),
            ("Operação",   90),
            ("Insumo",    130),
            ("pH",         45),
            ("Temp.",      50),
            ("Tempo",      55),
        ]
        largura_total = sum(w for _, w in colunas)

        x = x0
        y = self.MARGEM_TOPO - 12

        # Cabeçalho
        for titulo, largura in colunas:
            self.canvas.create_text(
                x + 4, y,
                text=titulo, anchor="w",
                fill="#333", font=("", 9, "bold"),
            )
            x += largura

        # Linha separadora
        self.canvas.create_line(
            x0, y + 12, x0 + largura_total, y + 12,
            fill="#999",
        )

        # Linhas
        y = self.MARGEM_TOPO + 20 + self.ALTURA_BARRA / 2
        for p in self.passos:
            insumo = p.get("insumo") or "—"
            # Trunca insumo longo
            if len(insumo) > 18:
                insumo = insumo[:17] + "…"

            x = x0
            for valor, (_, largura) in zip(
                [
                    p["etapa"][:14],
                    p["operacao"][:14],
                    insumo,
                    p.get("ph", "—"),
                    p.get("temperatura", "—"),
                    f'{p["execution_min"]:.1f} min',
                ],
                colunas,
            ):
                self.canvas.create_text(
                    x + 4, y,
                    text=valor, anchor="w",
                    fill="#222", font=("", 9),
                )
                x += largura

            y += self.ALTURA_BARRA + self.ESPACO_BARRA

    # ------------------------------------------------------------------
    @staticmethod
    def _escolher_passo(duracao):
        """Escolhe um passo de marcação 'bonito' conforme a duração total."""
        if duracao <= 10:
            return 1
        if duracao <= 30:
            return 5
        if duracao <= 120:
            return 15
        if duracao <= 300:
            return 30
        if duracao <= 600:
            return 60
        return 120