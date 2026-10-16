# LVE — Frontend (tkinter)

Aplicação desktop em **tkinter** que consome a API REST do backend
[`app_prod_lve`](../app_prod_lve). Cobre o cadastro, custeio, planejamento
de produção e geração de PDFs.

**Contato:** advmsuconic@gmail.com

---

## Sumário

1. [Visão geral](#visão-geral)
2. [Requisitos](#requisitos)
3. [Como rodar](#como-rodar)
4. [Estrutura de arquivos](#estrutura-de-arquivos)
5. [Telas disponíveis](#telas-disponíveis)
6. [Fluxo de uso](#fluxo-de-uso)
7. [Configuração](#configuração)
8. [Solução de problemas](#solução-de-problemas)

---

## Visão geral

O `lve_nf` é o **frontend** do sistema LVE. Ele:

- Faz **login** com token no backend (`http://127.0.0.1:8000`)
- Permite **cadastrar** insumos, NF, receitas, produtos, sub-produtos
- Calcula **custo e preço** de produtos
- Gera **fichas técnicas** e **listas de compras** em PDF
- Planeja **produções** (consolidação, cronograma, custo)

**É tkinter puro** — sem frameworks web, sem Node.js.

---

## Requisitos

- **Python 3.10+**
- **tkinter** (já vem com Python no Linux)
- **requests** (instalado via `pip`)
- **Backend `app_prod_lve` rodando** em `http://127.0.0.1:8000`

### Instalação (Linux/Arch)

```bash
# tkinter (geralmente já vem)
sudo pacman -S tk    # Arch
sudo apt install python3-tk   # Debian/Ubuntu

# requests
pip install requests
Como rodar
1. Backend precisa estar rodando
bash
cd ~/Desktop/projetos/app_prod_lve
source .venv/bin/activate
python manage.py runserver
Deixa esse terminal aberto.

2. Rodar o frontend
Em outro terminal:

bash
cd ~/Desktop/projetos/lve_nf
python main.py
Abre a tela de login.

3. Fazer login
Usuário: o superusuário do Django

Senha: a senha do superusuário

Estrutura de arquivos
text
lve_nf/
├── main.py                     # Ponto de entrada + menu
├── config.py                   # URL do backend
├── api.py                      # Cliente HTTP da API REST
├── login_window.py             # Tela de login
├── nf_window.py                # Cadastro de NF
├── recipe_window.py            # Cadastro de receita base
├── cost_window.py              # Custo da receita
├── product_cost_window.py      # Custo e preço do produto
├── product_window.py           # Cadastro de produto + composição + timing
├── category_window.py          # Categoria + subcategoria
├── subproduct_type_window.py   # Tipo + subtipo de sub-produto
├── subproduct_window.py        # Sub-produto
├── ingredient_window.py        # Insumos (com densidade)
├── machinery_window.py         # Maquinário
├── utensil_window.py           # Utensílio
├── schedule_window.py          # Cronograma de produção
├── production_pending_window.py # Tela 1 — Produções pendentes
├── production_plan_window.py   # Tela 2 — Planejar produção
└── dialogs/
    ├── ingredient_dialog.py    # Modal: insumo
    ├── supplier_dialog.py      # Modal: fornecedor
    ├── stage_dialog.py         # Modal: etapa
    ├── operation_dialog.py     # Modal: operação
    └── timeline_dialog.py      # Modal: linha do tempo
Telas disponíveis
Menu principal
text
┌──────────────────────────────────────┐
│ LVE — Produção                       │
├──────────────────────────────────────┤
│ [Nota Fiscal]                        │
│ [Receita Base]                       │
│ [Custo da Receita]                   │
│ [Custo e Preço do Produto]           │
│ [Categorias e Subcategorias]         │
│ [Tipos e Subtipos de Sub-Produto]    │
│ [Sub-produtos]                       │
│ [Produtos]                           │
│ [Insumos]                            │
│ [Maquinários]                        │
│ [Utensílios]                         │
│ [Cronograma de Produção]             │
│ [Produções Pendentes]                │
│ [Planejar Produção]                  │
│ [Sair]                               │
└──────────────────────────────────────┘
Descrição de cada tela
Tela	O que faz
Nota Fiscal	Cadastra NF de compra + itens + fornecedor. Cria insumos inline.
Receita Base	Cadastra receita com etapas, operações, insumos, tempos, temperatura, pH, incorporação.
Custo da Receita	Mostra custo detalhado (insumos + energia + mão de obra).
Custo e Preço do Produto	Custo unitário + markup + preço + gerar ficha técnica (PDF).
Categorias e Subcategorias	Categorias de produto (Salgados, Sobremesas) + subcategorias (com markup).
Tipos e Subtipos de Sub-Produto	Tipos de sub-produto (Massa, Molho) + subtipos.
Sub-produtos	Sub-produto vinculado a uma receita base + subtipo.
Produtos	Produto + composição (sub-produtos + %) + timing + capacidade + produção padrão.
Insumos	Insumos com densidade (volume) e porção.
Maquinários	Maquinário com potência, valor, código.
Utensílios	Utensílios com valor, código.
Cronograma de Produção	Calcula quando cada sub-produto começa/termina.
Produções Pendentes	Cria/lista produções pendentes. Ver itens. Ver plano salvo.
Planejar Produção	Seleciona itens + data/hora. Calcula plano. Salva como scheduled. Gera PDF da lista de compras.
Fluxo de uso
Cadastro (uma vez)
text
1. Menu → Insumos
   └── Cadastra insumos (com densidade se volume)

2. Menu → Categorias e Subcategorias
   └── Cadastra categorias (Salgados, Sobremesas)
   └── Cadastra subcategorias (com markup)

3. Menu → Tipos e Subtipos de Sub-Produto
   └── Cadastra tipos (Massa, Recheio)
   └── Cadastra subtipos

4. Menu → Sub-produtos
   └── Vincula sub-produto a uma receita base + subtipo

5. Menu → Receita Base
   └── Cadastra receita com etapas, operações, insumos

6. Menu → Produtos
   └── Cadastra produto + composição (sub-produtos + %)
   └── Define timing (at_start, at_finish, after_to)
   └── Define capacidade e produção padrão

7. Menu → Maquinários / Utensílios
   └── Cadastra recursos (opcional)

8. Menu → Nota Fiscal
   └── Cadastra NF de compra
Operação (recorrente)
text
1. Menu → Produções Pendentes
   └── Cria produção com produtos + quantidades
   └── (Quantidade sugerida pelo default_production do produto)

2. Menu → Planejar Produção
   └── Marca os itens a produzir
   └── Define data/hora de início
   └── Clica "Calcular plano"
   └── Vê o resultado (sub-produtos, cronograma, custo, lista de compras)
   └── Clica "Exportar lista de compras (PDF)"
   └── Clica "Confirmar e planejar"

3. Menu → Produções Pendentes
   └── Seleciona a produção planejada
   └── Clica "Ver plano"
   └── Vê o resultado salvo

4. Menu → Custo e Preço do Produto
   └── Gera ficha técnica em PDF
Configuração
URL do backend
Arquivo: config.py

python
API_BASE_URL = "http://127.0.0.1:8000"
Se o backend estiver em outra máquina, troca pelo IP:

python
API_BASE_URL = "http://192.168.1.100:8000"
Onde ficam os PDFs
Fichas técnicas:

text
../app_prod_lve/media/tech_sheets/
Listas de compras:

text
../app_prod_lve/media/shopping_lists/
Os PDFs são gerados pelo BACKEND (não pelo lve_nf). O lve_nf só dispara
o endpoint e abre o arquivo no visualizador padrão (xdg-open no Linux).

Visualizador de PDF
O sistema usa xdg-open para abrir os PDFs. No Arch, isso funciona
out-of-the-box (abre no evince, okular, zathura ou o que estiver
configurado como padrão).

Para trocar:

python
subprocess.Popen(["xdg-open", caminho_pdf])
Pode trocar por evince, okular, etc.

Solução de problemas
1. Erro "Não foi possível carregar dados"
Causa: backend fora do ar ou token expirado.

Solução:

Confere se o runserver está rodando.
Faz login de novo.
Confere a URL em config.py.
2. Erro 405 (Method Not Allowed)
Causa: o endpoint não aceita o método HTTP usado.

Solução: conferir o api.py — todos os métodos devem estar
implementados (_post com suporte a POST, PUT, PATCH, DELETE).

3. Erro 400 (Bad Request)
Causa: payload incorreto.

Solução: olhar o terminal do runserver — o Django imprime o
JSON do erro com o campo específico.

4. PDF não abre
Causa: xdg-open não configurado ou arquivo não gerado.

Solução:

Confere se o arquivo existe em ../app_prod_lve/media/...
Testa manualmente: xdg-open caminho/do/pdf.pdf
Confere se o endpoint devolveu 200.
5. "Port 8000 already in use"
Causa: runserver antigo ainda rodando.

Solução:

bash
fuser -k 8000/tcp
6. Combobox vazia
Causa: a API não devolveu dados ou o filtro ?active=true escondeu tudo.

Solução:

Testa o endpoint no Browsable API (http://127.0.0.1:8000/api/...)
Confere se tem dados cadastrados
Confere se os dados têm active=true
7. "Expecting value: line 1 column 1"
Causa: a API devolveu HTML (não JSON).

Solução: adicionar -H "Accept: application/json" no curl (se for teste
via terminal). No lve_nf, verificar se o _headers() está enviando
o token.

Notas técnicas
Cliente HTTP
O api.py implementa APIClient com:

login(username, password) → devolve token

_get(path) → GET simples

_get_paginated(path) → GET seguindo paginação

_post(path, payload, method) → POST/PUT/PATCH/DELETE

Métodos específicos: list_*, create_*, update_*, get_*

Token: guardado em self.token. Enviado em todas as requisições via header
Authorization: Token XXX.

Convenções de UI
*_window.py → telas principais (na raiz)

dialogs/*_dialog.py → modais

Cores: sem cor de fundo (economia de tinta ao imprimir)

Fonte: monospace para tabelas

Layout de tabela
As telas de cadastro seguem o padrão:

text
┌────────────────────────────────────────────┐
│ [Campo 1]  [Campo 2]  [Campo 3]            │
│ [Campo 4]  [Campo 5]                       │
├────────────────────────────────────────────┤
│ [Lista / Tabela]                           │
│                                            │
├────────────────────────────────────────────┤
│ [+ Novo] [Editar] [Desativar]              │
└────────────────────────────────────────────┘
Licença
Uso interno.

text

---

## Cola o arquivo

**Salva em `~/Desktop/projetos/lve_nf/README.md`.**

**Confirma que colou.**

## Depois disso

**A documentação está feita.** Você tem:

- ✅ `app_prod_lve/README.md`
- ✅ `lve_nf/README.md`
- ✅ `backup.sh`
- ✅ `.gitignore` atualizado

**O sistema está documentado e com backup.**

## Opcional: commit no Git

**Se quiser commitar:**

```bash
cd ~/Desktop/projetos/app_prod_lve
git add README.md backup.sh .gitignore
git commit -m "docs: adiciona README e script de backup"

cd ~/Desktop/projetos/lve_nf
git add README.md
git commit -m "docs: adiciona README do frontend"