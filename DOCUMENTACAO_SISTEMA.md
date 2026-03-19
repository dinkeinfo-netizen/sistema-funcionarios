# 📋 Sistema de Controle de Acesso de Funcionários - Documentação Completa

## 📖 Índice

1. [Visão Geral](#visão-geral)
2. [Arquitetura do Sistema](#arquitetura-do-sistema)
3. [Funcionalidades](#funcionalidades)
4. [Instalação e Configuração](#instalação-e-configuração)
5. [Uso do Sistema](#uso-do-sistema)
6. [APIs e Endpoints](#apis-e-endpoints)
7. [Banco de Dados](#banco-de-dados)
8. [Segurança](#segurança)
9. [Manutenção e Suporte](#manutenção-e-suporte)
10. [Troubleshooting](#troubleshooting)

---

## 🎯 Visão Geral

O **Sistema de Controle de Acesso de Funcionários** é uma solução completa e robusta para gerenciar o controle de acesso de colaboradores em empresas. O sistema oferece múltiplas formas de autenticação, incluindo reconhecimento facial, RFID, QR Code e acesso manual, proporcionando flexibilidade e segurança para diferentes cenários empresariais.

### 🎯 Objetivos do Sistema

- **Controle de Acesso**: Gerenciar entrada e saída de funcionários
- **Múltiplas Autenticações**: Suporte a facial, RFID, QR Code e manual
- **Relatórios**: Geração de relatórios detalhados de presença
- **Dashboard**: Visualização em tempo real do status dos funcionários
- **Gestão de Funcionários**: Cadastro e administração de colaboradores
- **Configurações Flexíveis**: Horários de trabalho e feriados personalizáveis

### 🏢 Casos de Uso

- **Empresas com controle de ponto eletrônico**
- **Edifícios corporativos com controle de acesso**
- **Fábricas e indústrias**
- **Escritórios e centros comerciais**
- **Instituições educacionais**

---

## 🏗️ Arquitetura do Sistema

### 🔧 Stack Tecnológica

- **Backend**: Python 3.12 + Flask 3.1.1
- **Banco de Dados**: MySQL 8.0
- **Frontend**: HTML5 + CSS3 + JavaScript (Vanilla)
- **Containerização**: Docker + Docker Compose
- **Proxy Reverso**: Caddy 2
- **Processamento de Imagem**: OpenCV + face_recognition
- **Autenticação**: Sistema próprio com hash PBKDF2

### 🏛️ Estrutura de Arquivos

```
/sistema-funcionarios/
├── sistema_acesso_funcionarios.py    # Aplicação principal Flask
├── docker-compose.yml                # Configuração Docker
├── Dockerfile                        # Imagem Docker da aplicação
├── requirements.txt                  # Dependências Python
├── Caddyfile                         # Configuração do proxy reverso
├── init.sql                          # Script de inicialização do banco
├── templates/                        # Templates HTML
├── static/                           # Arquivos estáticos
├── logs/                             # Logs do sistema
├── certs/                            # Certificados SSL
└── venv/                             # Ambiente virtual Python
```

---

## ⚡ Funcionalidades

### 🔐 Métodos de Autenticação

#### 1. **Reconhecimento Facial**
- **Tecnologia**: OpenCV + face_recognition
- **Processamento**: Normalização de iluminação com CLAHE
- **Segurança**: Confiança mínima configurável (padrão: 60%)
- **Performance**: Cache de encodings faciais
- **Rate Limiting**: Proteção contra spam de requisições

#### 2. **Acesso RFID**
- **Suporte**: Cartões, tags e chaveiros RFID
- **Cadastro**: Interface administrativa para registro
- **Validação**: Verificação de cartão ativo e funcionário válido

#### 3. **Acesso Manual**
- **Entrada**: Número de registro + validação
- **Interface**: Simples e intuitiva
- **Validação**: Verificação de status do funcionário

#### 4. **QR Code**
- **Geração**: QR codes únicos por funcionário
- **Validação**: Leitura e verificação automática
- **Segurança**: Códigos com expiração configurável

### 📊 Dashboard e Relatórios

#### **Dashboard em Tempo Real**
- **Funcionários Presentes**: Contagem atual
- **Acessos do Dia**: Estatísticas em tempo real
- **Gráficos Interativos**: Acessos por hora, departamento
- **Alertas**: Notificações de eventos importantes
- **Atividade Recente**: Últimos 10 acessos

#### **Relatórios Disponíveis**
- **Relatório Diário**: Acessos por data específica
- **Relatório por Funcionário**: Histórico individual
- **Relatório por Departamento**: Análise por área
- **Exportação**: CSV e PDF
- **Filtros**: Por período, tipo de acesso, método

---

## 🚀 Instalação e Configuração

### 📋 Pré-requisitos

- **Sistema Operacional**: Linux (Ubuntu 20.04+ recomendado)
- **Docker**: Versão 20.10+
- **Docker Compose**: Versão 2.0+
- **Memória RAM**: Mínimo 4GB (8GB recomendado)
- **Armazenamento**: Mínimo 20GB livre
- **Câmera**: Para funcionalidade facial (USB ou integrada)

### 🔧 Instalação Rápida

#### **1. Clone do Repositório**
```bash
git clone <url-do-repositorio>
cd sistema-funcionarios
```

#### **2. Execução com Docker**
```bash
# Construir e iniciar serviços
docker-compose up -d --build

# Verificar status
docker-compose ps

# Visualizar logs
docker-compose logs -f flask_acesso
```

#### **3. Acesso ao Sistema**
- **Interface Principal**: http://localhost:8081
- **Painel Admin**: http://localhost:8081/admin
- **API**: http://localhost:8081/api/

---

## 💻 Uso do Sistema

### 👤 Acesso de Funcionários

#### **Reconhecimento Facial**
1. **Acessar**: `/acesso-facial`
2. **Posicionar**: Face centralizada na câmera
3. **Aguardar**: Processamento automático
4. **Confirmação**: Mensagem de sucesso ou erro

#### **Acesso RFID**
1. **Acessar**: `/acesso-rfid`
2. **Aproximar**: Cartão/tag do leitor
3. **Validação**: Verificação automática
4. **Confirmação**: Feedback visual e sonoro

#### **Acesso Manual**
1. **Acessar**: `/acesso-manual`
2. **Inserir**: Número de registro
3. **Confirmar**: Tipo de acesso (entrada/saída)
4. **Validação**: Verificação de permissões

### 👨‍💼 Painel Administrativo

#### **Login Administrativo**
1. **Acessar**: `/admin`
2. **Credenciais**: Usuário e senha admin
3. **Autenticação**: Sistema de sessão segura
4. **Acesso**: Painel completo de controle

---

## 🔌 APIs e Endpoints

### 📡 Endpoints Principais

#### **Autenticação e Acesso**
```http
POST /registrar_acesso_funcionario
POST /registrar_acesso_facial
POST /api/detectar_face
POST /api/detectar_tipo_acesso
```

#### **Dashboard e Relatórios**
```http
GET /api/dashboard-data
GET /api/relatorios/diario
GET /api/relatorios/funcionario
GET /api/relatorio-presenca
```

#### **Gestão de Funcionários**
```http
GET /api/funcionarios
POST /api/funcionarios
PUT /api/funcionarios/{id}
DELETE /api/funcionarios/{id}
```

---

## 🗄️ Banco de Dados

### 🏗️ Estrutura das Tabelas

#### **Tabela Principal: funcionarios**
```sql
CREATE TABLE funcionarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    numero_registro VARCHAR(20) UNIQUE NOT NULL,
    nome VARCHAR(100) NOT NULL,
    cpf VARCHAR(14) UNIQUE,
    departamento VARCHAR(50) NOT NULL,
    cargo VARCHAR(50) NOT NULL,
    empresa VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'ativo',
    ativo BOOLEAN DEFAULT TRUE,
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **Tabela de Acessos: acessos_funcionarios**
```sql
CREATE TABLE acessos_funcionarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    numero_registro VARCHAR(20) NOT NULL,
    tipo_acesso VARCHAR(20) NOT NULL,
    data_acesso DATE NOT NULL,
    hora_acesso TIME NOT NULL,
    metodo_acesso VARCHAR(20) DEFAULT 'manual',
    FOREIGN KEY (numero_registro) REFERENCES funcionarios(numero_registro)
);
```

---

## 🔒 Segurança

### 🛡️ Medidas de Segurança Implementadas

#### **Autenticação e Autorização**
- **Hash de Senhas**: PBKDF2 com salt único
- **Sessões Seguras**: Cookies HTTPOnly e SameSite
- **Rate Limiting**: Proteção contra ataques de força bruta
- **Validação de Entrada**: Sanitização de dados
- **Controle de Acesso**: Decorators para rotas protegidas

#### **Proteção de Dados**
- **Criptografia**: Senhas e dados sensíveis
- **Validação**: Verificação de permissões por funcionalidade
- **Logs de Auditoria**: Registro de todas as ações
- **Timeouts**: Sessões com expiração automática

---

## 🛠️ Manutenção e Suporte

### 📅 Tarefas de Manutenção

#### **Diárias**
- **Verificar Logs**: Análise de erros e alertas
- **Backup**: Verificação de integridade dos dados
- **Monitoramento**: Status dos serviços Docker

#### **Semanais**
- **Limpeza de Logs**: Remoção de logs antigos
- **Análise de Performance**: Verificação de consultas lentas
- **Atualizações**: Verificação de atualizações de segurança

### 🔧 Comandos de Manutenção

#### **Verificação de Status**
```bash
# Status dos serviços
docker-compose ps

# Logs em tempo real
docker-compose logs -f flask_acesso

# Verificar uso de recursos
docker stats
```

#### **Backup do Banco**
```bash
# Backup completo
docker exec acesso_mysql mysqldump -u root -proot_password acesso_funcionarios_db > backup_$(date +%Y%m%d_%H%M%S).sql
```

---

## 🚨 Troubleshooting

### ❌ Problemas Comuns e Soluções

#### **1. Sistema Não Inicia**

**Sintomas:**
- Erro ao executar `docker-compose up`
- Aplicação não responde na porta configurada

**Soluções:**
```bash
# Verificar logs
docker-compose logs flask_acesso

# Verificar portas em uso
sudo netstat -tulpn | grep :8081

# Reiniciar serviços
docker-compose down
docker-compose up -d
```

#### **2. Erro de Conexão com Banco**

**Sintomas:**
- Erro "Can't connect to MySQL server"
- Aplicação não consegue acessar dados

**Soluções:**
```bash
# Verificar status do MySQL
docker-compose ps acesso_mysql

# Verificar logs do MySQL
docker-compose logs acesso_mysql
```

#### **3. Reconhecimento Facial Não Funciona**

**Sintomas:**
- Erro "Nenhuma face detectada"
- Sistema não reconhece funcionários cadastrados

**Soluções:**
```bash
# Verificar permissões da câmera
ls -la /dev/video*

# Verificar dependências Python
pip list | grep face-recognition
```

---

## 🎉 Conclusão

O **Sistema de Controle de Acesso de Funcionários** representa uma solução completa e profissional para o controle de acesso empresarial. Com sua arquitetura robusta, múltiplas formas de autenticação e interface intuitiva, o sistema atende às necessidades de empresas de diversos portes e setores.

### 🌟 Principais Vantagens

- **Flexibilidade**: Múltiplos métodos de autenticação
- **Confiabilidade**: Sistema robusto e estável
- **Escalabilidade**: Suporte a grandes volumes de usuários
- **Segurança**: Múltiplas camadas de proteção
- **Facilidade de Uso**: Interface intuitiva e responsiva

---

**Versão da Documentação**: 1.0  
**Data de Atualização**: Dezembro 2024  
**Sistema**: Sistema de Controle de Acesso de Funcionários v1.0
