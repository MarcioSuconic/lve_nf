# lve_nf/main.py
import tkinter as tk
from tkinter import ttk

from api import APIClient
from config import API_BASE_URL
from cost_window import CostWindow
from login_window import LoginWindow
from nf_window import NFWindow
from product_cost_window import ProductCostWindow
from recipe_window import RecipeWindow
from category_window import CategoryWindow
from subproduct_type_window import SubProductTypeWindow
from subproduct_window import SubProductWindow
from product_window import ProductWindow
from schedule_window import ScheduleWindow


def _limpar(root):
    """Remove todos os widgets do root, para trocar de tela."""
    for child in root.winfo_children():
        child.destroy()


def _tela_menu(root, api):
    _limpar(root)
    root.title("LVE — Menu")
    root.geometry("420x520")

    frame = ttk.Frame(root, padding=30)
    frame.pack(fill="both", expand=True)

    ttk.Label(
        frame, text="LVE — Produção",
        font=("", 14, "bold"),
    ).pack(pady=(0, 20))

    ttk.Button(
        frame, text="Nota Fiscal",
        command=lambda: _tela_nf(root, api),
    ).pack(fill="x", pady=6)

    ttk.Button(
        frame, text="Receita Base",
        command=lambda: _tela_receita(root, api),
    ).pack(fill="x", pady=6)

    ttk.Button(
        frame, text="Custo da Receita Base",
        command=lambda: _tela_custo(root, api),
    ).pack(fill="x", pady=6)

    ttk.Button(
        frame, text="Custo e Preço do Produto",
        command=lambda: _tela_custo_produto(root, api),
    ).pack(fill="x", pady=6)
    
    ttk.Button(
        frame, text="Categorias e Subcategorias",
        command=lambda: _tela_categorias(root, api),
    ).pack(fill="x", pady=6)
    
    ttk.Button(
        frame, text="Tipos e Subtipos de Sub-Produto",
        command=lambda: _tela_subproduct_types(root, api),
    ).pack(fill="x", pady=6)
    
    ttk.Button(
        frame, text="Sub-produtos",
        command=lambda: _tela_subproducts(root, api),
    ).pack(fill="x", pady=6)
    
    ttk.Button(
        frame, text="Produtos",
        command=lambda: _tela_products(root, api),
    ).pack(fill="x", pady=6)
    
    ttk.Button(
        frame, text="Cronograma de Produção",
        command=lambda: _tela_schedule(root, api),
    ).pack(fill="x", pady=6)

    ttk.Button(
        frame, text="Sair",
        command=root.destroy,
    ).pack(fill="x", pady=(20, 0))


def _tela_nf(root, api):
    _limpar(root)
    NFWindow(root, api, on_voltar=lambda: _tela_menu(root, api))


def _tela_receita(root, api):
    _limpar(root)
    RecipeWindow(root, api, on_voltar=lambda: _tela_menu(root, api))


def _tela_custo(root, api):
    _limpar(root)
    CostWindow(root, api, on_voltar=lambda: _tela_menu(root, api))


def _tela_custo_produto(root, api):
    _limpar(root)
    ProductCostWindow(root, api, on_voltar=lambda: _tela_menu(root, api))
    
def _tela_categorias(root, api):
    _limpar(root)
    CategoryWindow(root, api, on_voltar=lambda: _tela_menu(root, api))

def _tela_subproduct_types(root, api):
    _limpar(root)
    SubProductTypeWindow(root, api, on_voltar=lambda: _tela_menu(root, api))
    
def _tela_subproducts(root, api):
    _limpar(root)
    SubProductWindow(root, api, on_voltar=lambda: _tela_menu(root, api))
    
def _tela_products(root, api):
    _limpar(root)
    ProductWindow(root, api, on_voltar=lambda: _tela_menu(root, api))
    
def _tela_schedule(root, api):
    _limpar(root)
    ScheduleWindow(root, api, on_voltar=lambda: _tela_menu(root, api))

def main():
    api = APIClient(API_BASE_URL)

    root = tk.Tk()
    root.withdraw()

    login = tk.Toplevel(root)
    login.title("LVE — Login")

    logged_in = {"ok": False}

    def on_success():
        logged_in["ok"] = True
        login.destroy()

    LoginWindow(login, api, on_success=on_success)
    root.wait_window(login)

    if not logged_in["ok"]:
        root.destroy()
        return

    _tela_menu(root, api)
    root.deiconify()
    root.mainloop()


if __name__ == "__main__":
    main()