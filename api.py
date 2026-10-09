#/home/marcio/Desktop/projetos/lve_nf/api.py
import requests


class APIError(Exception):
    pass


class APIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.token = None

    # ------------------------------------------------------------------ infra

    def _headers(self):
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Token {self.token}"
        return headers

    def _get(self, path: str):
        try:
            r = requests.get(
                f"{self.base_url}{path}",
                headers=self._headers(),
                timeout=10,
            )
        except requests.RequestException as e:
            raise APIError(f"Erro de conexão: {e}")
        if r.status_code != 200:
            raise APIError(f"Erro {r.status_code} ao buscar {path}")
        return r.json()

    def _get_paginated(self, path: str):
        results = []
        url = f"{self.base_url}{path}"
        while url:
            try:
                r = requests.get(url, headers=self._headers(), timeout=10)
            except requests.RequestException as e:
                raise APIError(f"Erro de conexão: {e}")
            if r.status_code != 200:
                raise APIError(f"Erro {r.status_code} ao buscar {path}")
            data = r.json()
            if isinstance(data, dict) and "results" in data:
                results.extend(data["results"])
                url = data.get("next")
            else:
                results.extend(data)
                url = None
        return results

    def _post(self, path: str, payload: dict, method: str = "POST"):
        """Faz POST, PUT ou PATCH em `path` com `payload`."""
        url = f"{self.base_url}{path}"
        try:
            if method == "PUT":
                r = requests.put(
                    url, json=payload, headers=self._headers(), timeout=15,
                )
            elif method == "PATCH":
                r = requests.patch(
                    url, json=payload, headers=self._headers(), timeout=15,
                )
            else:
                r = requests.post(
                    url, json=payload, headers=self._headers(), timeout=15,
                )
        except requests.RequestException as e:
            raise APIError(f"Erro de conexão: {e}")
        if r.status_code in (200, 201, 204):
            try:
                return r.json()
            except Exception:
                return {}
        try:
            detail = r.json()
        except Exception:
            detail = r.text
        raise APIError(f"Erro {r.status_code}: {detail}")

    # ------------------------------------------------------------------ login

    def login(self, username: str, password: str):
        try:
            r = requests.post(
                f"{self.base_url}/api/api-token-auth/",
                json={"username": username, "password": password},
                timeout=10,
            )
        except requests.RequestException as e:
            raise APIError(f"Erro de conexão: {e}")
        if r.status_code != 200:
            raise APIError("Usuário ou senha inválidos.")
        self.token = r.json()["token"]
        return self.token

    # ------------------------------------------------------------------ list

    def list_suppliers(self):
        return self._get_paginated("/api/suppliers/")

    def list_food_ingredients(self):
        return self._get_paginated("/api/food-ingredients/")

    def list_units(self):
        return self._get_paginated("/api/units/")

    def list_stages(self):
        return self._get_paginated("/api/stage-base-recipes/")

    def list_operations(self):
        return self._get_paginated("/api/operation-base-recipes/")

    def list_machineries(self):
        return self._get_paginated("/api/machineries/")

    def list_utensils(self):
        return self._get_paginated("/api/utensils/")

    def list_base_recipes(self):
        return self._get_paginated("/api/base-recipes/")

    def get_base_recipe_detail(self, recipe_id: int):
        return self._get(f"/api/base-recipes/{recipe_id}/")

    def list_executions_by_recipe(self, recipe_id: int):
        return self._get_paginated(
            f"/api/execution-operation-base-recipes/?base_recipe={recipe_id}"
        )

    # ------------------------------------------------------------------ create

    def create_nf(self, payload: dict):
        return self._post("/api/nf-purchases/", payload)

    def create_supplier(self, payload: dict):
        return self._post("/api/suppliers/", payload)

    def create_food_ingredient(self, payload: dict):
        return self._post("/api/food-ingredients/", payload)

    def create_base_recipe(self, payload: dict):
        """
        Cria uma BaseRecipe completa (cabeçalho + execuções).
        O endpoint aceita o campo `executions` no mesmo POST.
        """
        return self._post("/api/base-recipes/", payload)

    def replace_executions(self, recipe_id: int, payload: dict):
        return self._post(
            f"/api/base-recipes/{recipe_id}/replace-executions/",
            payload,
        )
        
    def get_recipe_cost(self, recipe_id: int):
        return self._get(f"/api/base-recipes/{recipe_id}/cost/")
    
    def get_product_unit_cost(self, product_id: int, data: str | None = None):
        path = f"/api/products/{product_id}/unit-cost/"
        if data:
            path += f"?data={data}"
        return self._get(path)
    

    def generate_tech_sheet(self, product_id: int):
        """POST /api/products/{id}/tech-sheet/ — gera nova versão."""
        return self._post(
            f"/api/products/{product_id}/tech-sheet/", {},
        )

    def get_tech_sheet_url(self, product_id: int, version: int | None = None) -> str:
        path = f"/api/products/{product_id}/tech-sheet/download/"
        if version:
            path += f"?version={version}"
        return f"{self.base_url}{path}"
    
    def update_base_recipe(self, recipe_id: int, payload: dict):
        """PATCH /api/base-recipes/{id}/ — atualiza só o cabeçalho."""
        return self._post(
            f"/api/base-recipes/{recipe_id}/",
            payload,
            method="PATCH",
        )

    def create_base_recipe_only_header(self, payload: dict):
        """POST /api/base-recipes/ com executions=[] (receita vazia)."""
        payload = {**payload, "executions": []}
        return self._post("/api/base-recipes/", payload)