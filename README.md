# 🩺 ProntuDinamico

Sistema de prontuário eletrônico médico com **ficha clínica dinâmica por especialidade**, desenvolvido com Flask e MongoDB seguindo a arquitetura MVC.

---

## 💡 Sobre o Projeto

O diferencial do ProntuDinamico é que os campos do formulário de atendimento **não são fixos no código** — eles são carregados do banco de dados de acordo com a especialidade médica selecionada. Isso demonstra na prática o poder do MongoDB como banco de dados NoSQL orientado a documentos, onde cada atendimento pode ter uma estrutura diferente.

### Funcionalidades

- Cadastro e autenticação de médicos (senha criptografada com bcrypt)
- Registro de atendimentos com ficha clínica dinâmica por especialidade
- Anexo de imagens de exames
- Busca por nome do paciente, CPF e filtro por especialidade
- Emissão de prescrição médica vinculada ao atendimento
- Trava de identidade: apenas o médico responsável pode emitir a receita

---

## 🏗️ Arquitetura MVC

```
prontu_dinamico/
├── app.py                          # Ponto de entrada, registro dos Blueprints
├── config/
│   └── database.py                 # Conexão com o MongoDB
├── models/
│   ├── prontuario_model.py         # Model: coleção atendimentos e especialidades
│   └── usuario_model.py            # Model: coleção usuarios (bcrypt)
├── controllers/
│   ├── auth_controller.py          # Blueprint: /login, /cadastro, /logout
│   ├── prontuario_controller.py    # Blueprint: / (listagem), /novo
│   └── prescricao_controller.py    # Blueprint: /atendimento/<id>/prescricao
├── templates/
│   ├── login.html
│   ├── cadastro.html
│   ├── index.html                  # Listagem com busca e filtros
│   ├── novo_prontuario.html        # Formulário dinâmico via JS
│   └── nova_prescricao.html
├── static/
│   └── uploads/                    # Imagens de exames anexadas
└── requirements.txt
```

---

## 🗄️ Banco de Dados — MongoDB (NoSQL)

Banco: `prontu_db` | Porta padrão: `27017`

### Coleções

#### `usuarios`
Armazena os médicos cadastrados.
```json
{
  "_id": "ObjectId",
  "nome": "Gabriel Soares Avelino",
  "crm": "123456/MG",
  "email": "medico@email.com",
  "senha": "Binary (bcrypt hash)",
  "especialidade": "Ortopedia"
}
```

#### `especialidades`
Define os campos dinâmicos de cada especialidade. Populada manualmente via MongoDB Compass.
```json
{
  "nome": "Ortopedia",
  "campos": [
    { "nome_campo": "membro_afetado", "rotulo": "Membro Afetado", "tipo": "text" },
    { "nome_campo": "escala_dor",     "rotulo": "Escala de Dor (0-10)", "tipo": "number" },
    { "nome_campo": "diagnostico",    "rotulo": "Diagnóstico", "tipo": "textarea" }
  ]
}
```

#### `atendimentos`
Documento polimórfico — cada especialidade gera uma estrutura diferente em `anamnese_dinamica`.
```json
{
  "_id": "ObjectId",
  "paciente_nome": "João da Silva",
  "paciente_cpf": "12345678900",
  "paciente_idade": "35",
  "paciente_genero": "Masculino",
  "paciente_contato": "(31) 99999-9999",
  "medico_id": "ObjectId do médico",
  "medico_nome": "Dr. Gabriel",
  "especialidade": "Ortopedia",
  "data_consulta": "18/07/2025 14:30",
  "imagem_url": "/static/uploads/exame.jpg",
  "anamnese_dinamica": {
    "membro_afetado": "Joelho direito",
    "escala_dor": "7",
    "diagnostico": "Tendinite patelar"
  }
}
```

#### `prescricoes`
Receitas vinculadas a um atendimento.
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

### Pré-requisitos

- [Python 3.10+](https://www.python.org/downloads/)
- [MongoDB Community Server](https://www.mongodb.com/try/download/community) rodando localmente na porta `27017`
- [MongoDB Compass](https://www.mongodb.com/try/download/compass) (opcional, para visualizar os dados)

---

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/prontu_dinamico.git
cd prontu_dinamico
```

### 2. Crie e ative o ambiente virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Suba o MongoDB

Certifique-se de que o MongoDB está rodando. No Windows, ele geralmente sobe como serviço automaticamente. Para confirmar, abra o MongoDB Compass e conecte em `mongodb://localhost:27017`.

### 5. Popule as especialidades no banco

O sistema depende da coleção `especialidades` para funcionar. Crie o banco `prontu_db` no Compass e insira os documentos abaixo na coleção `especialidades`:

```json
[
  {
    "nome": "Ortopedia",
    "campos": [
      { "nome_campo": "membro_afetado", "rotulo": "Membro Afetado", "tipo": "text" },
      { "nome_campo": "escala_dor", "rotulo": "Escala de Dor (0-10)", "tipo": "number" },
      { "nome_campo": "diagnostico", "rotulo": "Diagnóstico", "tipo": "textarea" }
    ]
  },
  {
    "nome": "Cardiologia",
    "campos": [
      { "nome_campo": "pressao_arterial", "rotulo": "Pressão Arterial", "tipo": "text" },
      { "nome_campo": "frequencia_cardiaca", "rotulo": "Frequência Cardíaca (bpm)", "tipo": "number" },
      { "nome_campo": "sintomas", "rotulo": "Sintomas Relatados", "tipo": "textarea" }
    ]
  },
  {
    "nome": "Dermatologia",
    "campos": [
      { "nome_campo": "regiao_afetada", "rotulo": "Região Afetada", "tipo": "text" },
      { "nome_campo": "descricao_lesao", "rotulo": "Descrição da Lesão", "tipo": "textarea" },
      { "nome_campo": "tempo_evolucao", "rotulo": "Tempo de Evolução", "tipo": "text" }
    ]
  },
  {
    "nome": "Oftalmologia",
    "campos": [
      { "nome_campo": "acuidade_visual", "rotulo": "Acuidade Visual", "tipo": "text" },
      { "nome_campo": "olho_afetado", "rotulo": "Olho Afetado", "tipo": "text" },
      { "nome_campo": "queixa_principal", "rotulo": "Queixa Principal", "tipo": "textarea" }
    ]
  }
]
```

### 6. Execute a aplicação

```bash
python app.py
```

Acesse no navegador: **http://localhost:5000**

---

## 🔑 Primeiro Acesso

1. Acesse `/cadastro` e crie sua conta médica
2. Faça login com e-mail e senha
3. Registre um novo atendimento em `/novo`
4. Após o atendimento, emita uma prescrição médica

---

## 🛠️ Tecnologias Utilizadas

| Tecnologia | Uso |
|---|---|
| Python 3 + Flask | Backend e roteamento (Blueprints) |
| MongoDB | Banco de dados NoSQL orientado a documentos |
| PyMongo | Driver de conexão Python ↔ MongoDB |
| bcrypt | Hash de senhas |
| Jinja2 | Engine de templates |
| Bootstrap 5 | Interface responsiva |
| JavaScript | Montagem dinâmica dos campos no formulário |
