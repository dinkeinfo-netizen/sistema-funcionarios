# 🚀 Guia de Uso Rápido - Sistema de Controle de Acesso

## ⚡ Início Rápido

### 🐳 Com Docker (Recomendado)

```bash
# 1. Baixar o projeto
git clone <url-do-repositorio>
cd sistema-funcionarios

# 2. Iniciar o sistema
docker-compose up -d

# 3. Acessar o sistema
# Abrir no navegador: http://localhost:8081
```

### 🐍 Sem Docker

```bash
# 1. Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Configurar banco MySQL
# 4. Executar aplicação
python sistema_acesso_funcionarios.py
```

---

## 🎯 Funcionalidades Principais

### 👤 **Acesso de Funcionários**

#### **Reconhecimento Facial** 📸
- Acesse: `/acesso-facial`
- Posicione sua face na câmera
- Sistema reconhece automaticamente
- Confirma acesso com som e mensagem

#### **Acesso RFID** 🆔
- Acesse: `/acesso-rfid`
- Aproxime cartão/tag do leitor
- Validação automática
- Feedback visual e sonoro

#### **Acesso Manual** ⌨️
- Acesse: `/acesso-manual`
- Digite seu número de registro
- Escolha tipo de acesso
- Confirmação imediata

### 👨‍💼 **Painel Administrativo**

#### **Dashboard** 📊
- Visão geral em tempo real
- Funcionários presentes
- Acessos do dia
- Gráficos interativos

#### **Gestão de Funcionários** 👥
- Cadastrar novos funcionários
- Editar informações
- Ativar/desativar
- Configurar horários

#### **Relatórios** 📋
- Relatórios diários
- Histórico por funcionário
- Exportação CSV/PDF
- Filtros por período

---

## 🔧 Configurações Importantes

### ⏰ **Horários de Trabalho**

```python
# Configuração padrão
HORARIOS_PADRAO = {
    'entrada': '08:00',
    'saida': '18:00',
    'almoco_inicio': '12:00',
    'almoco_fim': '13:00',
    'tolerancia_entrada': 15,  # minutos
    'tolerancia_saida': 15      # minutos
}
```

### 🔐 **Segurança**

```python
# Configurações de sessão
app.config.update(
    SESSION_COOKIE_SECURE=True,      # HTTPS obrigatório
    SESSION_COOKIE_HTTPONLY=True,    # Sem acesso JavaScript
    SESSION_COOKIE_SAMESITE='Strict', # Proteção CSRF
    PERMANENT_SESSION_LIFETIME=timedelta(hours=2)  # Expiração
)
```

### 📷 **Reconhecimento Facial**

```python
# Configurações de performance
OPTIMIZATION_CONFIG = {
    'max_image_size': (640, 480),    # Tamanho máximo
    'use_cache': True,               # Cache de encodings
    'cache_ttl': 300,                # 5 minutos
    'min_confidence': 0.65,          # Confiança mínima
    'max_processing_time': 3         # 3 segundos máximo
}
```

---

## 📱 Interfaces do Sistema

### 🏠 **Página Principal** (`/`)
- Menu de acesso rápido
- Status do sistema
- Links para todas as funcionalidades

### 📸 **Acesso Facial** (`/acesso-facial`)
- Câmera em tempo real
- Detecção automática de face
- Feedback visual e sonoro
- Processamento otimizado

### 🆔 **Acesso RFID** (`/acesso-rfid`)
- Interface para leitor
- Validação de cartões
- Histórico de acessos
- Configurações de leitor

### ⌨️ **Acesso Manual** (`/acesso-manual`)
- Campo de número de registro
- Seleção de tipo de acesso
- Validação em tempo real
- Mensagens de confirmação

### 👨‍💼 **Admin** (`/admin`)
- Login administrativo
- Dashboard completo
- Gestão de funcionários
- Configurações do sistema

---

## 🔌 APIs Principais

### 📡 **Endpoints de Acesso**

```http
# Registrar acesso manual
POST /registrar_acesso_funcionario
{
    "numero_registro": "12345",
    "tipo_acesso": "entrada",
    "metodo_acesso": "manual"
}

# Registrar acesso facial
POST /registrar_acesso_facial
{
    "imagem": "base64_encoded_image"
}

# Detectar face na imagem
POST /api/detectar_face
{
    "imagem": "base64_encoded_image"
}
```

### 📊 **Endpoints de Dados**

```http
# Dados do dashboard
GET /api/dashboard-data

# Relatório diário
GET /api/relatorios/diario?data_inicio=2024-12-01&data_fim=2024-12-01

# Lista de funcionários
GET /api/funcionarios

# Status do sistema
GET /api/status-sistema
```

---

## 🗄️ Banco de Dados

### 🏗️ **Tabelas Principais**

#### **funcionarios**
- Dados pessoais e profissionais
- Status e horários
- Configurações individuais

#### **acessos_funcionarios**
- Histórico de todos os acessos
- Método de autenticação
- Timestamps e IPs

#### **funcionarios_facial**
- Encodings faciais
- Imagens de referência
- Configurações de confiança

#### **cartoes_rfid**
- Códigos dos cartões
- Associação com funcionários
- Status de ativação

### 🔍 **Consultas Úteis**

```sql
-- Funcionários presentes agora
SELECT f.nome, f.departamento, MAX(a.hora_acesso) as ultima_entrada
FROM funcionarios f
JOIN acessos_funcionarios a ON f.numero_registro = a.numero_registro
WHERE DATE(a.data_acesso) = CURDATE()
AND a.tipo_acesso = 'entrada'
GROUP BY f.numero_registro
HAVING NOT EXISTS (
    SELECT 1 FROM acessos_funcionarios a2
    WHERE a2.numero_registro = f.numero_registro
    AND DATE(a2.data_acesso) = CURDATE()
    AND a2.tipo_acesso = 'saida'
    AND a2.hora_acesso > MAX(a.hora_acesso)
);

-- Acessos por hora hoje
SELECT HOUR(hora_acesso) as hora, COUNT(*) as total
FROM acessos_funcionarios
WHERE DATE(data_acesso) = CURDATE()
GROUP BY HOUR(hora_acesso)
ORDER BY hora;
```

---

## 🛠️ Manutenção

### 📅 **Tarefas Diárias**

```bash
# Verificar status dos serviços
docker-compose ps

# Ver logs em tempo real
docker-compose logs -f flask_acesso

# Verificar uso de recursos
docker stats
```

### 📅 **Tarefas Semanais**

```bash
# Backup do banco
docker exec acesso_mysql mysqldump -u root -proot_password \
  acesso_funcionarios_db > backup_$(date +%Y%m%d).sql

# Limpar logs antigos
find ./logs -name "*.log" -mtime +7 -delete

# Verificar atualizações
docker-compose pull
```

### 📅 **Tarefas Mensais**

```bash
# Backup completo
tar -czf backup_completo_$(date +%Y%m).tar.gz \
  --exclude=venv --exclude=logs/*.log .

# Análise de performance
# Verificar consultas lentas no MySQL
# Revisar logs de erro
```

---

## 🚨 Troubleshooting

### ❌ **Problemas Comuns**

#### **Sistema não inicia**
```bash
# Verificar logs
docker-compose logs flask_acesso

# Verificar portas
sudo netstat -tulpn | grep :8081

# Reiniciar
docker-compose down && docker-compose up -d
```

#### **Erro de banco de dados**
```bash
# Verificar MySQL
docker-compose ps acesso_mysql

# Testar conexão
docker exec -it acesso_mysql mysql -u app_user -papp_password

# Ver logs
docker-compose logs acesso_mysql
```

#### **Reconhecimento facial não funciona**
```bash
# Verificar câmera
ls -la /dev/video*

# Verificar dependências
pip list | grep face-recognition

# Testar câmera
python -c "import cv2; cap = cv2.VideoCapture(0); print('OK' if cap.isOpened() else 'ERRO')"
```

### 🔧 **Comandos de Diagnóstico**

```bash
# Status geral
curl http://localhost:8081/api/status-sistema

# Verificar saúde dos serviços
docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

# Ver uso de recursos
docker stats --no-stream

# Ver logs de erro
docker-compose logs --tail=100 flask_acesso | grep ERROR
```

---

## 📚 Recursos Adicionais

### 🔗 **Links Úteis**

- **Documentação Flask**: https://flask.palletsprojects.com/
- **MySQL Documentation**: https://dev.mysql.com/doc/
- **Docker Documentation**: https://docs.docker.com/
- **OpenCV Documentation**: https://docs.opencv.org/

### 📖 **Arquivos Importantes**

- `sistema_acesso_funcionarios.py` - Aplicação principal
- `docker-compose.yml` - Configuração Docker
- `requirements.txt` - Dependências Python
- `Caddyfile` - Configuração proxy reverso
- `init.sql` - Inicialização do banco

### 🆘 **Suporte**

- **Logs**: Sempre verifique os logs primeiro
- **Documentação**: Esta documentação e comentários no código
- **Issues**: Reporte problemas no repositório
- **Comunidade**: Stack Overflow e fóruns Python

---

## 🎉 Próximos Passos

1. **Teste o sistema** com alguns funcionários
2. **Configure horários** específicos da sua empresa
3. **Cadastre funcionários** e configure acessos
4. **Teste todos os métodos** de autenticação
5. **Configure relatórios** conforme suas necessidades
6. **Treine usuários** e administradores
7. **Monitore performance** e ajuste configurações

---

**🎯 Dica**: Comece com o básico e vá adicionando funcionalidades conforme necessário. O sistema é flexível e pode ser adaptado para diferentes cenários empresariais.

**📞 Suporte**: Para dúvidas técnicas, consulte os logs e esta documentação. Em caso de problemas específicos, verifique a seção de troubleshooting. 