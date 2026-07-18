# 🩺 ProntuDinamico

Sistema de prontuário eletrônico médico com **ficha clínica dinâmica por especialidade**, desenvolvido com Flask e MongoDB seguindo a arquitetura MVC.

---

## 💡 Sobre o Projeto

O diferencial do ProntuDinamico é que os campos do formulário de atendimento **não são fixos no código** — eles são carregados do banco de dados de acordo com a especialidade médica selecionada. Isso demonstra na prática o poder do MongoDB como banco de dados NoSQL orientado a documentos, onde cada atendimento pode ter uma estrutura completamente diferente.

### Funcionalidades

- Cadastro e autenticação de médicos com senha criptografada (bcrypt)
- Registro de atendimentos com ficha clínica dinâmica por especialidade
- Anexo de imagens de exames ao prontuário
- Busca por nome do paciente, CPF e filtro por especialidade
- Emissão de prescrição médica vinculada ao atendimento
- Trava de identidade: apenas o médico responsável pelo atendimento pode emitir a receita

### Especialidades disponíveis

| Especialidade | Campos clínicos |
|---|---|
| Psiquiatria | Relatório Comportamental e Emocional |
| Ortopedia | Membro Acometido, Nível de Dor, Histórico de Trauma |
| Dermatologia | Tipo de Lesão, Região do Corpo, Evolução e Conduta |
| Odontologia | Dente/Região, Procedimento, Plano de Tratamento |
| Oftalmologia | Acuidade Visual, Pressão Intraocular, Diagnóstico |
| Cardiologia | Pressão Arterial, Frequência Cardíaca, Laudo ECG |

---

## 🏗️ Arquitetura MVC

```
ProntuDinamico/
├── app.py                          # Ponto de entrada, registro dos Blueprints e filtros Jinja2
├── config/
│   └── database.py                 # Conexão com o MongoDB (lê MONGO_URI do ambiente)
├── models/
│   ├── prontuario_model.py         # Model: coleção atendimentos e especialidades
│   └── usuario_model.py            # Model: coleção usuarios (bcrypt)
├── controllers/
│   ├── auth_controller.py          # Blueprint: /login, /cadastro, /logout
│   ├── prontuario_controller.py    # Blueprint: / (listagem com busca), /novo
│   └── prescricao_controller.py    # Blueprint: /atendimento/<id>/prescricao
├── templates/
│   ├── login.html
│   ├── cadastro.html
│   ├── index.html                  # Listagem com busca por CPF/Nome e filtro por especialidade
│   ├── novo_prontuario.html        # Formulário com campos dinâmicos montados via JavaScript
│   └── nova_prescricao.html
├── static/
│   └── uploads/                    # Imagens de exames anexadas pelos médicos
├── data/                           # Dump das coleções MongoDB em JSON (usado pelo seed)
│   ├── especialidades.json
│   ├── atendimentos.json
│   ├── prescricoes.json
│   └── usuarios.json
├── seed.py                         # Popula o MongoDB automaticamente na primeira execução
├── Dockerfile                      # Imagem da aplicação Flask
├── docker-compose.yml              # Orquestra Flask + MongoDB + Seed
└── requirements.txt
```

---

## 🗄️ Banco de Dados — MongoDB (NoSQL)

Banco: `prontu_db` | 4 coleções

### `usuarios`
Médicos cadastrados no sistema.
```json
{
  "_id": "ObjectId",
  "nome": "Gabriel Soares Avelino",
  "crm": "123456/MG",
  "email": "medicoexemplo@gmail.com",
  "senha": "$2b$12$... (bcrypt hash)",
  "especialidade": "Psiquiatria"
}
```

### `especialidades`
Define os campos dinâmicos de cada especialidade. É aqui que o sistema decide quais inputs exibir no formulário de atendimento.
```json
{
  "nome": "Ortopedia",
  "campos": [
    { "nome_campo": "membro_afetado",   "rotulo": "Membro / Osso Acometido", "tipo": "text" },
    { "nome_campo": "nivel_dor",        "rotulo": "Nível de Dor (0 a 10)",   "tipo": "number" },
    { "nome_campo": "historico_trauma", "rotulo": "Houve Trauma ou Queda?",  "tipo": "text" }
  ]
}
```

### `atendimentos`
Documento polimórfico — o campo `anamnese_dinamica` muda de estrutura conforme a especialidade. Isso é o NoSQL em ação.
```json
{
  "_id": "ObjectId",
  "paciente_nome": "João da Silva",
  "paciente_cpf": "12345678900",
  "paciente_idade": "35",
  "paciente_genero": "Masculino",
  "paciente_contato": "(31) 99999-9999",
  "medico_id": "ObjectId do médico",
  "medico_nome": "Gabriel Soares Avelino",
  "especialidade": "Ortopedia",
  "data_consulta": "18/07/2025 14:30",
  "imagem_url": "/static/uploads/exame.jpg",
  "anamnese_dinamica": {
    "membro_afetado": "Joelho direito",
    "nivel_dor": "7",
    "historico_trauma": "Queda de bicicleta"
  }
}
```

### `prescricoes`
Receitas vinculadas a um atendimento específico.
```json
{
  "_id": "ObjectId",
  "atendimento_id": "ObjectId do atendimento",
  "data_emissao": "18/07/2025",
  "medicamentos": [
    { "nome": "Ibuprofeno 600mg", "posologia": "1 comprimido de 8 em 8 horas por 5 dias" }
  ]
}
```

---

## ▶️ Como Executar

Existem duas formas de rodar o projeto: com **Docker** (recomendado) ou **manualmente** com Python e MongoDB local.

---

## 🐳 Opção 1 — Docker (recomendado)

### Pré-requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado e rodando

### Passos

```bash
# 1. Clone o repositório
git clone https://github.com/soaresavelino/ProntuDinamico.git
cd ProntuDinamico

# 2. Suba tudo com um único comando
docker compose up --build
```

Acesse: **http://localhost:5000**

O que acontece nos bastidores:
1. **`mongo`** — sobe o MongoDB 7 e aguarda ficar saudável
2. **`seed`** — executa o `seed.py` que importa os 4 JSONs da pasta `/data` para o banco
3. **`app`** — constrói a imagem Flask e sobe a aplicação, já com banco populado

> Na primeira execução pode demorar ~30 segundos até o seed terminar. Aguarde e recarregue a página se necessário.

```bash
# Parar sem apagar os dados
docker compose down

# Parar e resetar o banco (próxima subida reimporta os JSONs)
docker compose down -v
```

---

## 🐍 Opção 2 — Execução Manual

### Pré-requisitos

- [Python 3.10+](https://www.python.org/downloads/)
- [MongoDB Community Server](https://www.mongodb.com/try/download/community) rodando na porta `27017`

### Passos

```bash
# 1. Clone o repositório
git clone https://github.com/soaresavelino/ProntuDinamico.git
cd ProntuDinamico

# 2. Crie e ative o ambiente virtual
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/macOS

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Popule o banco (importa os dados da pasta /data automaticamente)
python seed.py

# 5. Suba a aplicação
python app.py
```

Acesse: **http://localhost:5000**

---

## 🔑 Usuários de Teste

Os seguintes médicos já estão importados pelo seed. Use para testar o login:

| Nome | E-mail | Especialidade |
|---|---|---|
| Gabriel Soares Avelino | medicoexemplo@gmial.com | Psiquiatria |
| Ian Baptista | ianbaptista@gmail.com | Ortopedia |
| Kaua | kaua@gmail.com | Dermatologia |
| Michael Joseph Jackson | dr.michael@michaeljackson.med.br | Odontologia |
| Camille Silva Oliveira | draCamille@gmail.com | Cardiologia |

> As senhas são as cadastradas originalmente. Caso não lembre, crie um novo usuário em `/cadastro`.

---

## 🛠️ Tecnologias Utilizadas

| Tecnologia | Uso |
|---|---|
| Python 3 + Flask | Backend e roteamento via Blueprints |
| MongoDB 7 | Banco NoSQL com documentos polimórficos |
| PyMongo | Driver Python para MongoDB |
| bcrypt | Hash seguro de senhas |
| Docker + Compose | Containerização e orquestração dos serviços |
| Jinja2 | Engine de templates HTML |
| Bootstrap 5 | Interface responsiva |
| JavaScript | Montagem dinâmica dos campos do formulário |
