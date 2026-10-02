import tkinter as tk

from api import APIClient
from config import API_BASE_URL
from login_window import LoginWindow
from nf_window import NFWindow


def main():
    api = APIClient(API_BASE_URL)

    root = tk.Tk()
    root.withdraw()  # esconde enquanto a autenticação não passa

    login = tk.Toplevel(root)
    login.title("LVE — Login")

    logged_in = {"ok": False}

    def on_success():
        logged_in["ok"] = True
        login.destroy()

    LoginWindow(login, api, on_success=on_success)
    root.wait_window(login)  # trava até a janela de login fechar

    if not logged_in["ok"]:
        root.destroy()
        return

    NFWindow(root, api)
    root.deiconify()
    root.mainloop()


if __name__ == "__main__":
    main()