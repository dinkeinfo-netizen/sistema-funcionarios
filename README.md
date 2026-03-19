# 🏢 Sistema de Controle de Acesso de Funcionários

## 📋 Visão Geral

Sistema completo de controle de acesso de funcionários com autenticação facial, RFID, manual e relatórios em tempo real. Desenvolvido em Python/Flask com interface web moderna e responsiva.

## 🚀 Funcionalidades Principais

### ✅ Autenticação Múltipla
- **Acesso Facial**: Reconhecimento facial com OpenCV e face_recognition
- **Acesso RFID**: Leitura de cartões RFID
- **Acesso Manual**: Registro manual por número de funcionário

### ✅ Gestão de Funcionários
- Cadastro completo de funcionários
- Importação em massa via CSV/Excel
- Gestão de departamentos e cargos
- Status ativo/inativo

### ✅ Relatórios em Tempo Real
- **Relatório Online**: Dashboard em tempo real com atualização automática
- **Relatórios Diários**: Exportação em PDF, CSV e JSON
- **Relatórios por Funcionário**: Histórico individual detalhado

### ✅ Configurações Avançadas
- Horários de trabalho personalizados
- Feriados e exceções
- Tolerâncias de entrada/saída
- Configurações por departamento

## 🏗️ Arquitetura do Sistema

```
sistema-funcionarios/
├── sistema_acesso_funcionarios.py  # Aplicação principal Flask
├── docker-compose.yml              # Orquestração Docker
├── Dockerfile                      # Imagem Docker
├── Caddyfile                       # Proxy reverso HTTPS
├── requirements.txt                # Dependências Python
├── init.sql                        # Script de inicialização DB
├── templates/                      # Templates HTML
├── static/                         # Arquivos estáticos
├── certs/                          # Certificados SSL
├── logs/                           # Logs do sistema
└── venv/                          # Ambiente virtual Python
```

## 🛠️ Tecnologias Utilizadas

- **Backend**: Python 3.9, Flask 3.1.1
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5.3
- **Banco de Dados**: MySQL 8.0
- **Containerização**: Docker, Docker Compose
- **Proxy**: Caddy 2 (HTTPS automático)
- **Autenticação Facial**: OpenCV, face_recognition, dlib
- **Relatórios**: ReportLab (PDF), Pandas (CSV)

## 🚀 Instalação e Configuração

### Pré-requisitos
- Docker e Docker Compose
- 2GB RAM disponível
- Porta 8444 livre para HTTPS

### Instalação Rápida

```bash
# 1. Clone o repositório
git clone <repository-url>
cd sistema-funcionarios

# 2. Inicie o sistema
docker-compose up -d

# 3. Acesse o sistema
# URL: https://seu-ip:8444
# Admin: admin / admin123
```

### Configuração Manual

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Configurar banco de dados
mysql -u root -p < init.sql

# 3. Executar aplicação
python sistema_acesso_funcionarios.py
```

## 📊 Estrutura do Banco de Dados

### Tabelas Principais

#### `funcionarios`
- `id`: Chave primária
- `numero_registro`: Número único do funcionário
- `nome`: Nome completo
- `departamento`: Departamento
- `cargo`: Cargo/função
- `empresa`: Empresa
- `ativo`: Status ativo/inativo
- `data_cadastro`: Data de cadastro

#### `acessos_funcionarios`
- `id`: Chave primária
- `numero_registro`: FK para funcionário
- `tipo_acesso`: entrada/saída/almoco_entrada/almoco_saida
- `data_acesso`: Data do acesso
- `hora_acesso`: Hora do acesso
- `metodo_acesso`: facial/manual/rfid
- `ip_acesso`: IP do cliente
- `user_agent`: Navegador usado

#### `configuracoes_horarios`
- Configurações de horários por funcionário
- Tolerâncias de entrada/saída
- Horários específicos por dia da semana

## 🌐 Endpoints da API

### Autenticação
- `POST /admin/login` - Login administrativo
- `GET /admin/logout` - Logout

### Acesso de Funcionários
- `POST /registrar_acesso_funcionario` - Acesso manual
- `POST /registrar_acesso_facial` - Acesso facial
- `POST /api/detectar_face` - Detecção facial

### Gestão de Funcionários
- `GET /api/funcionarios` - Listar funcionários
- `POST /api/funcionarios` - Criar funcionário
- `PUT /api/funcionarios/<id>` - Atualizar funcionário
- `DELETE /api/funcionarios/<id>` - Excluir funcionário
- `POST /api/funcionarios/importar` - Importação em massa

### Relatórios
- `GET /api/relatorios/diario` - Relatório diário
- `GET /api/relatorios/funcionario` - Relatório por funcionário
- `GET /api/relatorio-presenca` - Dados de presença
- `GET /api/relatorio-online-data` - Dados para dashboard

### Configurações
- `GET /api/configuracoes/horarios` - Horários configurados
- `POST /api/configuracoes/horarios` - Salvar horários
- `GET /api/configuracoes/feriados` - Feriados configurados
- `POST /api/configuracoes/feriados` - Salvar feriados

## 📱 Páginas do Sistema

### Páginas Principais
- `/` - Página inicial
- `/admin` - Painel administrativo
- `/admin/login` - Login administrativo
- `/admin/funcionarios` - Gestão de funcionários
- `/admin/relatorios` - Relatórios
- `/admin/configuracoes` - Configurações

### Páginas de Acesso
- `/acesso-facial` - Acesso por reconhecimento facial
- `/acesso-manual` - Acesso manual por número
- `/acesso-rfid` - Acesso por RFID

### Relatórios
- `/relatorio-online-sistema-real` - Dashboard em tempo real

## 🔧 Configurações Avançadas

### Variáveis de Ambiente
```bash
MYSQL_HOST=acesso_mysql
MYSQL_USER=app_user
MYSQL_PASSWORD=app_password
MYSQL_DATABASE=acesso_funcionarios_db
SECRET_KEY=acesso_secret_key_2024
FLASK_HOST=0.0.0.0
FLASK_PORT=8082
```

### Portas Utilizadas
- **8444**: HTTPS (Caddy)
- **8081**: HTTP (Caddy)
- **3311**: MySQL
- **5009**: Flask (interno)

## 📊 Relatórios Disponíveis

### 1. Relatório Online (Tempo Real)
- **URL**: `/relatorio-online-sistema-real`
- **Funcionalidades**:
  - Dashboard em tempo real
  - Atualização automática a cada 30 segundos
  - Funcionários presentes e que saíram
  - Ordenação por colunas
  - Layout responsivo

### 2. Relatório Diário
- **URL**: `/admin/relatorios`
- **Funcionalidades**:
  - Seleção de período
  - Estatísticas gerais
  - Lista detalhada de acessos
  - Exportação em PDF, CSV, JSON

### 3. Relatório por Funcionário
- **Funcionalidades**:
  - Dados completos do funcionário
  - Histórico de acessos
  - Estatísticas individuais
  - Exportação em múltiplos formatos

## 🔐 Segurança

### Autenticação
- Login administrativo obrigatório
- Sessões seguras com Flask-Session
- Logout automático

### HTTPS
- Certificados SSL automáticos via Caddy
- Redirecionamento HTTP → HTTPS
- Headers de segurança configurados

### Rate Limiting
- Proteção contra spam de acessos faciais
- Limitação de tentativas de login
- Logs de segurança

## 📈 Monitoramento

### Logs
- Logs de acesso em `/logs/`
- Logs do Caddy em `/logs/caddy/`
- Logs de erro e debug

### Health Checks
- Verificação automática de saúde dos containers
- Monitoramento de conectividade com banco
- Alertas de falha

## 🚨 Troubleshooting

### Problemas Comuns

#### Sistema não inicia
```bash
# Verificar logs
docker-compose logs

# Reiniciar containers
docker-compose restart

# Reconstruir imagens
docker-compose build --no-cache
```

#### Erro de conexão com banco
```bash
# Verificar status do MySQL
docker-compose logs acesso_mysql

# Reiniciar apenas o MySQL
docker-compose restart acesso_mysql
```

#### Problemas com HTTPS
```bash
# Verificar certificados
ls -la certs/

# Reiniciar Caddy
docker-compose restart caddy_acesso
```

### Logs Importantes
- **Flask**: `docker-compose logs flask_acesso`
- **MySQL**: `docker-compose logs acesso_mysql`
- **Caddy**: `docker-compose logs caddy_acesso`

## 🔄 Manutenção

### Backup do Banco
```bash
# Backup completo
docker exec acesso_mysql mysqldump -u root -proot_password acesso_funcionarios_db > backup.sql

# Restaurar backup
docker exec -i acesso_mysql mysql -u root -proot_password acesso_funcionarios_db < backup.sql
```

### Atualização do Sistema
```bash
# Parar sistema
docker-compose down

# Atualizar código
git pull

# Reconstruir e iniciar
docker-compose build --no-cache
docker-compose up -d
```

### Limpeza de Logs
```bash
# Limpar logs antigos
find logs/ -name "*.log" -mtime +30 -delete
```

## 📞 Suporte

### Informações de Contato
- **Desenvolvedor**: Sistema de Controle de Acesso
- **Versão**: 1.0.0
- **Última Atualização**: Agosto 2025

### Recursos Adicionais
- Documentação técnica completa
- Guias de configuração
- Exemplos de uso
- Troubleshooting detalhado

---

## 🎯 Status do Sistema

✅ **Funcionalidades Implementadas**:
- Autenticação facial, RFID e manual
- Gestão completa de funcionários
- Relatórios em tempo real
- Configurações avançadas
- Interface web responsiva
- Sistema de logs e monitoramento

✅ **Sistema Funcionando**:
- Containers rodando normalmente
- Banco de dados operacional
- HTTPS configurado
- Relatórios online ativos

**Última verificação**: Agosto 2025 - Sistema 100% operacional 