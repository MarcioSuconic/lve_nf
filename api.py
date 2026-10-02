import requests


class APIError(Exception):
    pass


class APIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.token = None

    def _headers(self):
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Token {self.token}"
        return headers

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

    def list_suppliers(self):
        return self._get_paginated("/api/suppliers/")

    def list_food_ingredients(self):
        return self._get_paginated("/api/food-ingredients/")

    def list_units(self):
        return self._get_paginated("/api/units/")

    def create_nf(self, payload: dict):
        try:
            r = requests.post(
                f"{self.base_url}/api/nf-purchases/",
                json=payload,
                headers=self._headers(),
                timeout=15,
            )
        except requests.RequestException as e:
            raise APIError(f"Erro de conexão: {e}")
        if r.status_code == 201:
            return r.json()
        try:
            detail = r.json()
        except Exception:
            detail = r.text
        raise APIError(f"Erro {r.status_code}: {detail}")
    
    def create_supplier(self, payload: dict):
        return self._post("/api/suppliers/", payload)

    def create_food_ingredient(self, payload: dict):
        return self._post("/api/food-ingredients/", payload)

    def _post(self, path: str, payload: dict):
        try:
            r = requests.post(
                f"{self.base_url}{path}",
                json=payload,
                headers=self._headers(),
                timeout=15,
            )
        except requests.RequestException as e:
            raise APIError(f"Erro de conexão: {e}")
        if r.status_code in (200, 201):
            return r.json()
        try:
            detail = r.json()
        except Exception:
            detail = r.text
        raise APIError(f"Erro {r.status_code}: {detail}")