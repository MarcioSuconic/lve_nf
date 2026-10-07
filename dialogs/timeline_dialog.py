#/home/marcio/Desktop/projetos/lve_nf/dialogs/timeline_dialog.py
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
        {elapsed_min, execution_min, operacao, etapa, incorporado}

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
        self.LARGURA = 900
        self.ALTURA_BARRA = 26
        self.ESPACO_BARRA = 6
        self.MARGEM_ESQ = 60
        self.MARGEM_DIR = 30
        self.MARGEM_TOPO = 40

        n = len(self.passos)
        altura_total = (
            self.MARGEM_TOPO
            + n * (self.ALTURA_BARRA + self.ESPACO_BARRA)
            + 40
        )
        altura_total = max(altura_total, 200)

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

    def _desenhar(self):
        if not self.passos:
            self.canvas.create_text(
                self.LARGURA / 2, 60,
                text="Nenhum passo cadastrado.",
                fill="#888",
            )
            return

        # Determina escala em minutos
        min_inicio = min(p["elapsed_min"] for p in self.passos)
        max_fim = max(
            p["elapsed_min"] + p["execution_min"] for p in self.passos
        )
        duracao = max(max_fim - min_inicio, 1)  # evita divisão por zero

        largura_util = self.LARGURA - self.MARGEM_ESQ - self.MARGEM_DIR

        def x_para(minuto):
            return (
                self.MARGEM_ESQ
                + (minuto - min_inicio) / duracao * largura_util
            )

        # ---- Régua no topo ----
        # Passo do marcador (escolhe um passo "bonito")
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

        # Linha base da régua
        self.canvas.create_line(
            self.MARGEM_ESQ, self.MARGEM_TOPO,
            self.LARGURA - self.MARGEM_DIR, self.MARGEM_TOPO,
            fill="#ccc",
        )

        # ---- Barras ----
        # Mapeia etapa -> cor (cicla na paleta)
        etapas = sorted({p["etapa"] for p in self.passos})
        cor_por_etapa = {
            etapa: CORES[i % len(CORES)]
            for i, etapa in enumerate(etapas)
        }

        y = self.MARGEM_TOPO + 20
        for p in self.passos:
            x1 = x_para(p["elapsed_min"])
            x2 = x_para(p["elapsed_min"] + p["execution_min"])

            # Garante largura mínima visível
            if x2 - x1 < 2:
                x2 = x1 + 2

            y1 = y
            y2 = y + self.ALTURA_BARRA

            cor = cor_por_etapa[p["etapa"]]
            if p["incorporado"]:
                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=cor, outline="",
                )
            else:
                # Textura listrada — desenha linhas diagonais
                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill="#eeeeee", outline=cor, width=2,
                )
                # Listras
                passo = 6
                xx = x1
                while xx < x2:
                    self.canvas.create_line(
                        xx, y2, xx + passo, y1,
                        fill=cor, width=1,
                    )
                    xx += passo * 2

            # Nome da operação dentro da barra, se couber
            largura_barra = x2 - x1
            texto = p["operacao"]
            if largura_barra > 60:
                self.canvas.create_text(
                    (x1 + x2) / 2, (y1 + y2) / 2,
                    text=texto, fill="white", font=("", 9),
                )
            else:
                # Não cabe: coloca ao lado
                self.canvas.create_text(
                    x2 + 4, (y1 + y2) / 2,
                    text=texto, anchor="w",
                    fill="#333", font=("", 9),
                )

            # Rótulo da etapa (à esquerda da barra)
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