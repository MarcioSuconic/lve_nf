# lve_nf/recipe_window.py
import tkinter as tk
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from tkinter import messagebox, ttk

from dialogs.operation_dialog import OperationDialog
from dialogs.stage_dialog import StageDialog
from dialogs.timeline_dialog import TimelineDialog


# ---------------------------------------------------------------------------
# Grade de colunas de passos — referência única para cabeçalho e campos
# ---------------------------------------------------------------------------
STEP_COLUMNS = [
    ("Operação", 0),
    ("", 1),            # botão "+"
    ("Descrição", 2),
    ("Tempo", 3),
    ("Elapsed", 4),
    ("Insumo", 5),
    ("Qtde", 6),
    ("Un", 7),
    ("Maquinário", 8),
    ("Utensílio", 9),
    ("Incorp.", 10),
    ("Temp.", 11),
    ("pH", 12),
    ("", 13),           # botão "X"
]

STEP_COLUMN_WIDTHS = {
    0: 130, 1: 40, 2: 200, 3: 70, 4: 70, 5: 150, 6: 80,
    7: 100, 8: 130, 9: 130, 10: 70, 11: 60, 12: 55, 13: 40,
}

STEP_PADX = (0, 8)


def minutos_para_duration(minutos: float) -> str:
    total_segundos = int(round(minutos * 60))
    h = total_segundos // 3600
    m = (total_segundos % 3600) // 60
    s = total_segundos % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def duration_para_minutos(valor: str) -> float:
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


class StepRow:
    def __init__(
        self,
        parent,
        ingredients,
        units,
        machineries,
        utensils,
        operations,
        on_change,
        on_remove,
        on_new_operation,
    ):
        self.on_change = on_change
        self.on_remove = on_remove
        self.on_new_operation = on_new_operation

        self.ingredients = ingredients
        self.units = units
        self.machineries = machineries
        self.utensils = utensils
        self.operations = operations

        self.frame = ttk.Frame(parent)
        self.frame.pack(fill="x", pady=1)

        for col, largura in STEP_COLUMN_WIDTHS.items():
            self.frame.grid_columnconfigure(col, minsize=largura)

        # Operação
        self.operation_var = tk.StringVar()
        self.operation_combo = ttk.Combobox(
            self.frame, textvariable=self.operation_var,
            state="readonly", width=14,
            values=self._operation_names(),
        )
        self.operation_combo.grid(
            row=0, column=0, padx=STEP_PADX, sticky="w",
        )

        # Botão "+"
        ttk.Button(
            self.frame, text="+", width=2, command=self._nova_operacao,
        ).grid(row=0, column=1, padx=STEP_PADX, sticky="w")

        # Descrição
        self.description_var = tk.StringVar()
        ttk.Entry(
            self.frame, textvariable=self.description_var, width=22,
        ).grid(row=0, column=2, padx=STEP_PADX, sticky="w")

        # Tempo
        self.execution_var = tk.StringVar()
        ttk.Entry(
            self.frame, textvariable=self.execution_var, width=6,
        ).grid(row=0, column=3, padx=STEP_PADX, sticky="w")
        self.execution_var.trace_add("write", lambda *a: self.on_change())

        # Elapsed
        self.elapsed_var = tk.StringVar()
        ttk.Entry(
            self.frame, textvariable=self.elapsed_var, width=6,
        ).grid(row=0, column=4, padx=STEP_PADX, sticky="w")
        self.elapsed_var.trace_add("write", lambda *a: self.on_change())

        # Insumo
        self.ingredient_var = tk.StringVar()
        self.ingredient_combo = ttk.Combobox(
            self.frame, textvariable=self.ingredient_var,
            state="readonly", width=16,
            values=self._ingredient_names(),
        )
        self.ingredient_combo.grid(
            row=0, column=5, padx=STEP_PADX, sticky="w",
        )

        # Quantidade
        self.qtde_var = tk.StringVar()
        ttk.Entry(
            self.frame, textvariable=self.qtde_var, width=8,
        ).grid(row=0, column=6, padx=STEP_PADX, sticky="w")

        # Unidade
        self.unit_var = tk.StringVar()
        self.unit_combo = ttk.Combobox(
            self.frame, textvariable=self.unit_var,
            state="readonly", width=10,
            values=self._unit_labels(),
        )
        self.unit_combo.grid(row=0, column=7, padx=STEP_PADX, sticky="w")

        # Maquinário
        self.machinery_var = tk.StringVar()
        self.machinery_combo = ttk.Combobox(
            self.frame, textvariable=self.machinery_var,
            state="readonly", width=14,
            values=self._machinery_names(),
        )
        self.machinery_combo.grid(
            row=0, column=8, padx=STEP_PADX, sticky="w",
        )

        # Utensílio
        self.utensil_var = tk.StringVar()
        self.utensil_combo = ttk.Combobox(
            self.frame, textvariable=self.utensil_var,
            state="readonly", width=14,
            values=self._utensil_names(),
        )
        self.utensil_combo.grid(
            row=0, column=9, padx=STEP_PADX, sticky="w",
        )

        # Incorporação (%)
        self.incorporation_var = tk.StringVar(value="100")
        ttk.Entry(
            self.frame, textvariable=self.incorporation_var, width=6,
        ).grid(row=0, column=10, padx=STEP_PADX, sticky="w")

        # Temperatura (°C)
        self.temperature_var = tk.StringVar(value="20.0")
        ttk.Entry(
            self.frame, textvariable=self.temperature_var, width=6,
        ).grid(row=0, column=11, padx=STEP_PADX, sticky="w")

        # pH
        self.ph_var = tk.StringVar(value="7.00")
        ttk.Entry(
            self.frame, textvariable=self.ph_var, width=6,
        ).grid(row=0, column=12, padx=STEP_PADX, sticky="w")

        # Remover
        ttk.Button(
            self.frame, text="X", width=2,
            command=lambda: self.on_remove(self),
        ).grid(row=0, column=13, padx=STEP_PADX, sticky="w")

    # ---- helpers ----
    def _operation_names(self):
        return [o["operation_base_recipe"] for o in self.operations]

    def _operation_id_by_name(self):
        return {o["operation_base_recipe"]: o["id"] for o in self.operations}

    def _ingredient_names(self):
        return [i["food_ingredient"] for i in self.ingredients]

    def _ingredient_id_by_name(self):
        return {i["food_ingredient"]: i["id"] for i in self.ingredients}

    def _unit_labels(self):
        return [f'{u["symbol"]} - {u["unit"]}' for u in self.units]

    def _unit_id_by_label(self):
        return {f'{u["symbol"]} - {u["unit"]}': u["id"] for u in self.units}

    def _machinery_names(self):
        return [""] + [m["machinery"] for m in self.machineries]

    def _machinery_id_by_name(self):
        return {m["machinery"]: m["id"] for m in self.machineries}

    def _utensil_names(self):
        return [""] + [u["utensil"] for u in self.utensils]

    def _utensil_id_by_name(self):
        return {u["utensil"]: u["id"] for u in self.utensils}

    def _nova_operacao(self):
        self.on_new_operation(self)

    # ---- refresh ----
    def refresh_operations(self, operations):
        self.operations = operations
        self.operation_combo["values"] = self._operation_names()

    def refresh_ingredients(self, ingredients):
        self.ingredients = ingredients
        self.ingredient_combo["values"] = self._ingredient_names()

    def refresh_machineries(self, machineries):
        self.machineries = machineries
        self.machinery_combo["values"] = self._machinery_names()

    def refresh_utensils(self, utensils):
        self.utensils = utensils
        self.utensil_combo["values"] = self._utensil_names()

    def select_operation_by_id(self, operation_id):
        for o in self.operations:
            if o["id"] == operation_id:
                self.operation_var.set(o["operation_base_recipe"])
                return

    # ---- leitura ----
    def get_execution_min(self) -> float:
        try:
            return float(self.execution_var.get().replace(",", "."))
        except ValueError:
            return 0.0

    def get_elapsed_min(self) -> float:
        try:
            return float(self.elapsed_var.get().replace(",", "."))
        except ValueError:
            return 0.0

    def get_incorporation(self) -> str:
        valor = self.incorporation_var.get().strip().replace(",", ".")
        if not valor:
            return "100.00"
        try:
            d = Decimal(valor)
            if d < 0:
                d = Decimal("0")
            if d > 100:
                d = Decimal("100")
            return f"{d:.2f}"
        except InvalidOperation:
            return "100.00"

    def get_temperature(self) -> str:
        valor = self.temperature_var.get().strip().replace(",", ".")
        if not valor:
            return "20.0"
        try:
            return f"{Decimal(valor):.1f}"
        except InvalidOperation:
            return "20.0"

    def get_ph(self) -> str:
        valor = self.ph_var.get().strip().replace(",", ".")
        if not valor:
            return "7.00"
        try:
            return f"{Decimal(valor):.2f}"
        except InvalidOperation:
            return "7.00"

    def set_elapsed_min(self, minutos: float):
        self.elapsed_var.set(f"{minutos:.2f}")

    def get_payload(self):
        stage_id = getattr(self, "stage_id", None)
        return {
            "stage_execution": stage_id,
            "operation_execution": self._operation_id_by_name().get(
                self.operation_var.get()
            ),
            "description_execution": self.description_var.get().strip(),
            "food_ingredient": self._ingredient_id_by_name().get(
                self.ingredient_var.get()
            ),
            "qtde_food_ingredient": self.qtde_var.get().strip() or None,
            "unidade_qtde_food_ingredient": self._unit_id_by_label().get(
                self.unit_var.get()
            ),
            "incorporation_percentage": self.get_incorporation(),
            "temperature": self.get_temperature(),
            "pH": self.get_ph(),
            "execution_time": minutos_para_duration(self.get_execution_min()),
            "elapsed_time": minutos_para_duration(self.get_elapsed_min()),
            "machinery": self._machinery_id_by_name().get(
                self.machinery_var.get()
            ),
            "utensils": self._utensil_id_by_name().get(
                self.utensil_var.get()
            ),
        }

    def destroy(self):
        self.frame.destroy()


class StageBlock:
    def __init__(
        self,
        parent,
        stages,
        ingredients,
        units,
        machineries,
        utensils,
        operations,
        on_change,
        on_remove_block,
        on_new_stage,
        on_new_operation,
        on_move_up=None,
        on_move_down=None,
    ):
        self.stages = stages
        self.ingredients = ingredients
        self.units = units
        self.machineries = machineries
        self.utensils = utensils
        self.operations = operations
        self.on_change = on_change
        self.on_remove_block = on_remove_block
        self.on_new_stage = on_new_stage
        self.on_new_operation = on_new_operation
        self.on_move_up = on_move_up
        self.on_move_down = on_move_down

        self.steps = []

        self.frame = ttk.LabelFrame(parent, padding=6)
        self.frame.pack(fill="x", pady=4, padx=2)

        # Cabeçalho do bloco (etapa + botões)
        header = ttk.Frame(self.frame)
        header.pack(fill="x")

        ttk.Label(header, text="Etapa:").pack(side="left", padx=(0, 4))

        self.stage_var = tk.StringVar()
        self.stage_combo = ttk.Combobox(
            header, textvariable=self.stage_var,
            state="readonly", width=20,
            values=self._stage_names(),
        )
        self.stage_combo.pack(side="left", padx=2)
        self.stage_var.trace_add("write", lambda *a: self._on_stage_change())

        ttk.Button(
            header, text="+ Nova etapa", command=self._nova_etapa,
        ).pack(side="left", padx=4)

        # Botões ↑↓ e Remover (à direita)
        ttk.Button(
            header, text="Remover etapa",
            command=lambda: self.on_remove_block(self),
        ).pack(side="right", padx=2)

        if self.on_move_down:
            ttk.Button(
                header, text="↓", width=3,
                command=lambda: self.on_move_down(self),
            ).pack(side="right", padx=2)

        if self.on_move_up:
            ttk.Button(
                header, text="↑", width=3,
                command=lambda: self.on_move_up(self),
            ).pack(side="right", padx=2)

        # ---- Cabeçalho das colunas (grid alinhado ao StepRow) ----
        cols = ttk.Frame(self.frame)
        cols.pack(fill="x", pady=(6, 0))

        for col, largura in STEP_COLUMN_WIDTHS.items():
            cols.grid_columnconfigure(col, minsize=largura)

        for texto, col in STEP_COLUMNS:
            ttk.Label(cols, text=texto).grid(
                row=0, column=col, padx=STEP_PADX, sticky="w",
            )

        # Container de passos
        self.steps_container = ttk.Frame(self.frame)
        self.steps_container.pack(fill="x")

        ttk.Button(
            self.frame, text="+ Adicionar passo", command=self.add_step,
        ).pack(anchor="w", pady=(4, 0))

    def _on_stage_change(self):
        for step in self.steps:
            self._apply_stage_to_step(step)

    def _stage_names(self):
        return [s["stage_base_recipe"] for s in self.stages]

    def _stage_id_by_name(self):
        return {s["stage_base_recipe"]: s["id"] for s in self.stages}

    def _nova_etapa(self):
        self.on_new_stage(self)

    def add_step(self):
        step = StepRow(
            self.steps_container,
            ingredients=self.ingredients,
            units=self.units,
            machineries=self.machineries,
            utensils=self.utensils,
            operations=self.operations,
            on_change=self.on_change,
            on_remove=self.remove_step,
            on_new_operation=self.on_new_operation,
        )
        self._apply_stage_to_step(step)
        self.steps.append(step)
        self.on_change()

    def remove_step(self, step):
        step.destroy()
        self.steps.remove(step)
        self.on_change()

    def _apply_stage_to_step(self, step):
        stage_id = self._stage_id_by_name().get(self.stage_var.get())
        step.stage_id = stage_id

    def refresh_stages(self, stages):
        self.stages = stages
        self.stage_combo["values"] = self._stage_names()

    def refresh_operations(self, operations):
        self.operations = operations
        for step in self.steps:
            step.refresh_operations(operations)

    def refresh_ingredients(self, ingredients):
        self.ingredients = ingredients
        for step in self.steps:
            step.refresh_ingredients(ingredients)

    def refresh_machineries(self, machineries):
        self.machineries = machineries
        for step in self.steps:
            step.refresh_machineries(machineries)

    def refresh_utensils(self, utensils):
        self.utensils = utensils
        for step in self.steps:
            step.refresh_utensils(utensils)

    def select_stage_by_id(self, stage_id):
        for s in self.stages:
            if s["id"] == stage_id:
                self.stage_var.set(s["stage_base_recipe"])
                for step in self.steps:
                    self._apply_stage_to_step(step)
                return

    def get_stage_id(self):
        return self._stage_id_by_name().get(self.stage_var.get())

    def get_steps_payload(self):
        payload = []
        for step in self.steps:
            payload.append(step.get_payload())
        return payload

    def destroy(self):
        for step in self.steps:
            step.destroy()
        self.steps.clear()
        self.frame.destroy()


class RecipeWindow:
    def __init__(self, root, api, on_voltar=None):
        self.root = root
        self.api = api
        self.on_voltar = on_voltar

        self.stages = []
        self.ingredients = []
        self.units = []
        self.machineries = []
        self.utensils = []
        self.operations = []
        self.base_recipes = []

        self.current_recipe_id = None
        self.blocks = []

        self.root.title("LVE — Cadastro de Receita Base")
        self.root.geometry("1600x720")

        self._load_data()
        self._build_ui()
        self._refresh_recipes_combo()
        self.add_block()

    def _load_data(self):
        try:
            self.stages = self.api.list_stages()
            self.ingredients = self.api.list_food_ingredients()
            self.units = self.api.list_units()
            self.machineries = self.api.list_machineries()
            self.utensils = self.api.list_utensils()
            self.operations = self.api.list_operations()
            self.base_recipes = self.api.list_base_recipes()
        except Exception as e:
            messagebox.showerror(
                "Erro", f"Não foi possível carregar dados:\n{e}"
            )
            self.root.destroy()
            raise SystemExit

        self.ingredients = [i for i in self.ingredients if i.get("active", True)]
        self.machineries = [m for m in self.machineries if m.get("active", True)]
        self.utensils = [u for u in self.utensils if u.get("active", True)]
        self.operations = [o for o in self.operations if o.get("active", True)]
        self.stages = [s for s in self.stages if s.get("active", True)]

    def _reload(self, attr):
        reloaders = {
            "stages": self.api.list_stages,
            "ingredients": self.api.list_food_ingredients,
            "units": self.api.list_units,
            "machineries": self.api.list_machineries,
            "utensils": self.api.list_utensils,
            "operations": self.api.list_operations,
        }
        data = reloaders[attr]()
        setattr(self, attr, [d for d in data if d.get("active", True)])

    def _build_ui(self):
        header = ttk.LabelFrame(self.root, text="Receita Base", padding=8)
        header.pack(fill="x", padx=10, pady=(10, 4))

        row1 = ttk.Frame(header)
        row1.pack(fill="x")

        ttk.Label(row1, text="Nome:").pack(side="left")
        self.name_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self.name_var, width=40).pack(
            side="left", padx=(4, 12),
        )

        ttk.Label(row1, text="Tamanho:").pack(side="left")
        self.size_var = tk.StringVar(value="1.00")
        ttk.Entry(row1, textvariable=self.size_var, width=10).pack(
            side="left", padx=(4, 8),
        )

        ttk.Label(row1, text="Unidade:").pack(side="left")
        self.unit_size_var = tk.StringVar()
        self.unit_size_combo = ttk.Combobox(
            row1, textvariable=self.unit_size_var,
            state="readonly", width=14,
            values=[f'{u["symbol"]} - {u["unit"]}' for u in self.units],
        )
        self.unit_size_combo.pack(side="left", padx=4)

        row2 = ttk.Frame(header)
        row2.pack(fill="x", pady=(6, 0))

        ttk.Label(row2, text="Descrição:").pack(side="left")
        self.description_var = tk.StringVar()
        ttk.Entry(row2, textvariable=self.description_var, width=90).pack(
            side="left", padx=4,
        )

        row3 = ttk.Frame(header)
        row3.pack(fill="x", pady=(6, 0))

        ttk.Label(row3, text="Carregar receita:").pack(side="left")
        self.recipe_combo_var = tk.StringVar()
        self.recipe_combo = ttk.Combobox(
            row3, textvariable=self.recipe_combo_var,
            state="readonly", width=40,
        )
        self.recipe_combo.pack(side="left", padx=4)
        self.recipe_combo.bind(
            "<<ComboboxSelected>>", self._on_recipe_selected,
        )

        ttk.Button(
            row3, text="Nova receita", command=self._nova_receita,
        ).pack(side="left", padx=8)

        container = ttk.Frame(self.root)
        container.pack(fill="both", expand=True, padx=10, pady=4)

        self.canvas = tk.Canvas(container, background="white", highlightthickness=0)
        scroll = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scroll.set)

        scroll.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.blocks_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.blocks_frame, anchor="nw")

        self.blocks_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        footer = ttk.Frame(self.root)
        footer.pack(fill="x", padx=10, pady=(4, 10))

        if self.on_voltar:
            ttk.Button(
                footer, text="← Voltar", command=self.on_voltar,
            ).pack(side="left", padx=(0, 8))

        ttk.Button(
            footer, text="+ Adicionar etapa", command=self.add_block,
        ).pack(side="left")

        ttk.Button(
            footer, text="Recalcular sequência",
            command=self._recalcular_sequencia,
        ).pack(side="left", padx=8)

        self.total_var = tk.StringVar(value="Total: 0.00 min")
        ttk.Label(
            footer, textvariable=self.total_var, font=("", 11, "bold"),
        ).pack(side="left", padx=20)

        ttk.Button(
            footer, text="Ver linha do tempo", command=self._abrir_timeline,
        ).pack(side="right", padx=4)

        ttk.Button(
            footer, text="Salvar tudo", command=self._salvar_tudo,
        ).pack(side="right")

    def add_block(self):
        block = StageBlock(
            self.blocks_frame,
            stages=self.stages,
            ingredients=self.ingredients,
            units=self.units,
            machineries=self.machineries,
            utensils=self.utensils,
            operations=self.operations,
            on_change=self._recalc_total,
            on_remove_block=self._remove_block,
            on_new_stage=self._nova_etapa,
            on_new_operation=self._nova_operacao,
            on_move_up=self._mover_bloco_acima,
            on_move_down=self._mover_bloco_abaixo,
        )
        self.blocks.append(block)
        self._recalc_total()

    def _remove_block(self, block):
        if len(self.blocks) == 1:
            messagebox.showinfo(
                "Atenção", "A receita precisa ter pelo menos uma etapa."
            )
            return
        block.destroy()
        self.blocks.remove(block)
        self._recalc_total()

    # ---- mover blocos ↑↓ ----
    def _mover_bloco_acima(self, block):
        idx = self.blocks.index(block)
        if idx == 0:
            return
        self.blocks[idx], self.blocks[idx - 1] = (
            self.blocks[idx - 1], self.blocks[idx],
        )
        self._repack_blocks()
        self._recalc_total()

    def _mover_bloco_abaixo(self, block):
        idx = self.blocks.index(block)
        if idx == len(self.blocks) - 1:
            return
        self.blocks[idx], self.blocks[idx + 1] = (
            self.blocks[idx + 1], self.blocks[idx],
        )
        self._repack_blocks()
        self._recalc_total()

    def _repack_blocks(self):
        """Reposiciona os frames dos blocos na ordem atual de self.blocks."""
        for b in self.blocks:
            b.frame.pack_forget()
        for b in self.blocks:
            b.frame.pack(fill="x", pady=4, padx=2)

    def _nova_etapa(self, block):
        dlg = StageDialog(self.root, self.api)
        self.root.wait_window(dlg)
        if not dlg.created:
            return
        self._reload("stages")
        for b in self.blocks:
            b.refresh_stages(self.stages)
        block.select_stage_by_id(dlg.created["id"])

    def _nova_operacao(self, step_row):
        dlg = OperationDialog(self.root, self.api)
        self.root.wait_window(dlg)
        if not dlg.created:
            return
        self._reload("operations")
        for b in self.blocks:
            b.refresh_operations(self.operations)
        step_row.select_operation_by_id(dlg.created["id"])

    def _recalc_total(self):
        total = 0.0
        for block in self.blocks:
            for step in block.steps:
                elapsed = step.get_elapsed_min()
                execution = step.get_execution_min()
                fim = elapsed + execution
                if fim > total:
                    total = fim
        self.total_var.set(f"Total: {total:.2f} min")

    def _recalcular_sequencia(self):
        acumulado = 0.0
        for block in self.blocks:
            for step in block.steps:
                step.set_elapsed_min(acumulado)
                acumulado += step.get_execution_min()
        self._recalc_total()

    def _abrir_timeline(self):
        passos = []
        for block in self.blocks:
            etapa_nome = block.stage_var.get() or "?"
            for step in block.steps:
                try:
                    pct = Decimal(step.incorporation_var.get() or "100")
                except InvalidOperation:
                    pct = Decimal("100")
                passos.append({
                    "elapsed_min": step.get_elapsed_min(),
                    "execution_min": step.get_execution_min(),
                    "operacao": step.operation_var.get() or "?",
                    "etapa": etapa_nome,
                    "incorporado": pct > 0,
                })
        TimelineDialog(
            self.root,
            titulo=self.name_var.get() or "Receita",
            passos=passos,
        )

    def _refresh_recipes_combo(self):
        self.base_recipes = self.api.list_base_recipes()
        self.recipe_combo["values"] = [
            r["base_recipe"] for r in self.base_recipes
        ]

    def _on_recipe_selected(self, _event=None):
        nome = self.recipe_combo_var.get()
        receita = next(
            (r for r in self.base_recipes if r["base_recipe"] == nome),
            None,
        )
        if not receita:
            return
        self._carregar_receita(receita["id"])

    def _carregar_receita(self, recipe_id):
        try:
            dados = self.api.get_base_recipe_detail(recipe_id)
            execucoes = self.api.list_executions_by_recipe(recipe_id)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar:\n{e}")
            return

        for block in self.blocks:
            block.destroy()
        self.blocks.clear()

        self.current_recipe_id = recipe_id
        self.name_var.set(dados["base_recipe"])
        self.description_var.set(dados.get("description", ""))
        self.size_var.set(str(dados["size"]))
        for u in self.units:
            if u["id"] == dados["unit_size"]:
                self.unit_size_var.set(f'{u["symbol"]} - {u["unit"]}')
                break

        # Agrupa execuções por etapa
        grupos = {}
        for ex in execucoes:
            grupos.setdefault(ex["stage_execution"], []).append(ex)

        # Ordena os grupos pelo menor elapsed_time de cada um
        grupos_ordenados = sorted(
            grupos.items(),
            key=lambda kv: min(
                duration_para_minutos(e["elapsed_time"]) for e in kv[1]
            ),
        )

        for stage_id, execs in grupos_ordenados:
            execs.sort(key=lambda e: duration_para_minutos(e["elapsed_time"]))
            block = StageBlock(
                self.blocks_frame,
                stages=self.stages,
                ingredients=self.ingredients,
                units=self.units,
                machineries=self.machineries,
                utensils=self.utensils,
                operations=self.operations,
                on_change=self._recalc_total,
                on_remove_block=self._remove_block,
                on_new_stage=self._nova_etapa,
                on_new_operation=self._nova_operacao,
                on_move_up=self._mover_bloco_acima,
                on_move_down=self._mover_bloco_abaixo,
            )
            block.select_stage_by_id(stage_id)
            self.blocks.append(block)

            for ex in execs:
                block.add_step()
                step = block.steps[-1]
                step.description_var.set(ex.get("description_execution", ""))
                step.execution_var.set(
                    f"{duration_para_minutos(ex['execution_time']):.2f}"
                )
                step.elapsed_var.set(
                    f"{duration_para_minutos(ex['elapsed_time']):.2f}"
                )
                for o in self.operations:
                    if o["id"] == ex["operation_execution"]:
                        step.operation_var.set(o["operation_base_recipe"])
                        break
                if ex.get("food_ingredient"):
                    for i in self.ingredients:
                        if i["id"] == ex["food_ingredient"]:
                            step.ingredient_var.set(i["food_ingredient"])
                            break
                if ex.get("qtde_food_ingredient"):
                    step.qtde_var.set(str(ex["qtde_food_ingredient"]))
                if ex.get("unidade_qtde_food_ingredient"):
                    for u in self.units:
                        if u["id"] == ex["unidade_qtde_food_ingredient"]:
                            step.unit_var.set(f'{u["symbol"]} - {u["unit"]}')
                            break
                if ex.get("machinery"):
                    for m in self.machineries:
                        if m["id"] == ex["machinery"]:
                            step.machinery_var.set(m["machinery"])
                            break
                if ex.get("utensils"):
                    for u in self.utensils:
                        if u["id"] == ex["utensils"]:
                            step.utensil_var.set(u["utensil"])
                            break
                # Incorporação
                inc = ex.get("incorporation_percentage")
                if inc is None:
                    inc = "0" if ex.get("unincorporated_ingredient") else "100"
                try:
                    inc_str = f"{Decimal(str(inc)):.2f}"
                except (InvalidOperation, TypeError):
                    inc_str = "100.00"
                step.incorporation_var.set(inc_str)

                # Temperatura
                temp = ex.get("temperature", "20.0")
                try:
                    temp_str = f"{Decimal(str(temp)):.1f}"   # ← 1 casa
                except (InvalidOperation, TypeError):
                    temp_str = "20.0"
                step.temperature_var.set(temp_str)

                # pH
                ph = ex.get("pH", "7.00")
                try:
                    ph_str = f"{Decimal(str(ph)):.2f}"
                except (InvalidOperation, TypeError):
                    ph_str = "7.00"
                step.ph_var.set(ph_str)

        self._recalc_total()

    def _nova_receita(self):
        for block in self.blocks:
            block.destroy()
        self.blocks.clear()
        self.current_recipe_id = None
        self.name_var.set("")
        self.description_var.set("")
        self.size_var.set("1.00")
        self.unit_size_var.set("")
        self.recipe_combo_var.set("")
        self.add_block()

    def _salvar_tudo(self):
        nome = self.name_var.get().strip()
        if not nome:
            messagebox.showwarning("Atenção", "Informe o nome da receita.")
            return

        try:
            size = float(self.size_var.get().replace(",", "."))
        except ValueError:
            messagebox.showwarning("Atenção", "Tamanho inválido.")
            return

        unit_size_id = None
        for u in self.units:
            if f'{u["symbol"]} - {u["unit"]}' == self.unit_size_var.get():
                unit_size_id = u["id"]
                break
        if not unit_size_id:
            messagebox.showwarning("Atenção", "Escolha a unidade do tamanho.")
            return

        execucoes = []
        for block in self.blocks:
            stage_id = block.get_stage_id()
            if not stage_id:
                messagebox.showwarning(
                    "Atenção", "Cada bloco precisa ter uma etapa escolhida."
                )
                return
            for step in block.steps:
                payload = step.get_payload()
                if not payload["operation_execution"]:
                    messagebox.showwarning(
                        "Atenção", "Cada passo precisa ter uma operação."
                    )
                    return
                if step.get_execution_min() < 0.1:
                    messagebox.showwarning(
                        "Atenção",
                        "O tempo de cada passo deve ser pelo menos 0,1 min.",
                    )
                    return
                payload["stage_execution"] = stage_id
                execucoes.append(payload)

        if not execucoes:
            messagebox.showwarning(
                "Atenção", "A receita precisa ter pelo menos um passo."
            )
            return

        if self.current_recipe_id:
            ok = messagebox.askyesno(
                "Confirmar",
                "Isso vai apagar todas as execuções salvas desta receita "
                "e recriar as novas. Continuar?",
            )
            if not ok:
                return

        payload = {
            "base_recipe": nome,
            "description": self.description_var.get().strip(),
            "size": f"{size:.2f}",
            "unit_size": unit_size_id,
            "active": True,
            "executions": execucoes,
        }

        try:
            if self.current_recipe_id:
                receita = self.api.replace_executions(
                    self.current_recipe_id, payload,
                )
            else:
                receita = self.api.create_base_recipe(payload)
                self.current_recipe_id = receita["id"]
        except Exception as e:
            messagebox.showerror("Erro ao salvar", str(e))
            return

        messagebox.showinfo(
            "Sucesso",
            f"Receita '{receita['base_recipe']}' salva.",
        )
        self._refresh_recipes_combo()