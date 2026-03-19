# ⚙️ Configuração Técnica Detalhada - Sistema de Controle de Acesso

## 🔧 Configurações do Sistema

### 📊 Configurações de Performance

#### **Rate Limiting para Processamento Facial**
```python
PROCESSAMENTO_FACIAL_LIMITS = {
    'max_requests_per_minute': 120,  # Máximo 120 requisições/min
    'max_processing_time': 5,        # 5 segundos máximo
    'cooldown_period': 30            # 30 segundos de cooldown
}
```

#### **Cache de Encodings Faciais**
```python
# Cache para encodings faciais (otimização de performance)
facial_encodings_cache = {}
CACHE_EXPIRY = 300  # 5 minutos

# Configurações de otimização
OPTIMIZATION_CONFIG = {
    'max_image_size': (640, 480),    # Tamanho máximo da imagem
    'use_cache': True,               # Usar cache de encodings
    'cache_ttl': 300,                # TTL do cache em segundos
    'min_confidence': 0.65,          # Confiança mínima
    'max_processing_time': 3         # Tempo máximo de processamento
}
```

### 🔐 Configurações de Segurança

#### **Sessões Seguras**
```python
# Configurações de sessão segura
app.config.update(
    SESSION_COOKIE_SECURE=False,      # False para desenvolvimento
    SESSION_COOKIE_HTTPONLY=True,     # Sem acesso via JavaScript
    SESSION_COOKIE_SAMESITE='Lax',    # Proteção CSRF
    PERMANENT_SESSION_LIFETIME=timedelta(hours=2)  # 2 horas
)
```

#### **Hash de Senhas**
```python
def hash_password(password):
    """Cria hash seguro da senha usando PBKDF2"""
    salt = secrets.token_hex(32)
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), 
                                  salt.encode('utf-8'), 100000)
    return salt + pwdhash.hex()

def verify_password(stored_password, provided_password):
    """Verifica se a senha está correta"""
    try:
        # Para desenvolvimento, aceitar senhas simples
        if stored_password == provided_password:
            return True
        
        # Verificação PBKDF2 (para produção)
        if len(stored_password) > 64:
            salt = stored_password[:64]
            stored_pwdhash = stored_password[64:]
            pwdhash = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), 
                                          salt.encode('utf-8'), 100000)
            return pwdhash.hex() == stored_pwdhash
        
        return False
    except Exception as e:
        print(f"Erro ao verificar senha: {e}")
        return False
```

### 🌍 Configurações de Timezone

```python
# Configurar timezone para Brasil
import os
os.environ['TZ'] = 'America/Sao_Paulo'

def get_data_atual():
    """Retorna a data atual no timezone do Brasil"""
    from datetime import datetime
    import pytz
    
    # Definir timezone do Brasil
    tz_brasil = pytz.timezone('America/Sao_Paulo')
    agora = datetime.now(tz_brasil)
    return agora.date()
```

---

## 🗄️ Configurações do Banco de Dados

### 🔌 Conexão MySQL

#### **Função de Conexão**
```python
def get_simple_connection():
    """Conexão simples sem pool"""
    try:
        conn = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            user=os.getenv('MYSQL_USER', 'app_user'),
            password=os.getenv('MYSQL_PASSWORD', 'app_password'),
            database=os.getenv('MYSQL_DATABASE', 'acesso_funcionarios_db'),
            autocommit=True,
            connect_timeout=30,
            charset='utf8'
        )
        return conn
    except Exception as e:
        print(f"Erro conexão: {e}")
        raise
```

#### **Variáveis de Ambiente**
```bash
# Configurações do banco de dados
MYSQL_HOST=localhost          # ou IP do servidor MySQL
MYSQL_USER=app_user          # usuário do banco
MYSQL_PASSWORD=app_password  # senha do banco
MYSQL_DATABASE=acesso_funcionarios_db  # nome do banco
```

### 🏗️ Estrutura das Tabelas

#### **Tabela de Funcionários**
```sql
CREATE TABLE funcionarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    numero_registro VARCHAR(20) UNIQUE NOT NULL,
    nome VARCHAR(100) NOT NULL,
    cpf VARCHAR(14) UNIQUE,
    rg VARCHAR(20),
    departamento VARCHAR(50) NOT NULL,
    cargo VARCHAR(50) NOT NULL,
    empresa VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'ativo' COMMENT 'ativo, inativo, ferias, licenca, demitido',
    data_admissao DATE,
    data_demissao DATE NULL,
    horario_entrada TIME DEFAULT '08:00:00',
    horario_saida TIME DEFAULT '18:00:00',
    tolerancia_entrada INT DEFAULT 15 COMMENT 'Tolerância em minutos para entrada',
    tolerancia_saida INT DEFAULT 15 COMMENT 'Tolerância em minutos para saída',
    ativo BOOLEAN DEFAULT TRUE,
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Índices para performance
    INDEX idx_numero_registro (numero_registro),
    INDEX idx_cpf (cpf),
    INDEX idx_status (status),
    INDEX idx_empresa (empresa),
    INDEX idx_departamento (departamento),
    INDEX idx_ativo (ativo),
    INDEX idx_data_admissao (data_admissao)
);
```

#### **Tabela de Acessos**
```sql
CREATE TABLE acessos_funcionarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    numero_registro VARCHAR(20) NOT NULL,
    nome_funcionario VARCHAR(100) NOT NULL,
    departamento VARCHAR(50) NOT NULL,
    cargo VARCHAR(50) NOT NULL,
    empresa VARCHAR(50) NOT NULL,
    tipo_acesso VARCHAR(20) NOT NULL COMMENT 'entrada, saida, almoco_entrada, almoco_saida, etc.',
    data_acesso DATE NOT NULL,
    hora_acesso TIME NOT NULL,
    timestamp_acesso TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metodo_acesso VARCHAR(20) DEFAULT 'manual' COMMENT 'manual, rfid, qrcode, facial',
    observacao TEXT NULL,
    ip_acesso VARCHAR(45) NULL,
    user_agent TEXT NULL,
    
    -- Chave estrangeira
    FOREIGN KEY (numero_registro) REFERENCES funcionarios(numero_registro) ON UPDATE CASCADE,
    
    -- Índices para performance
    INDEX idx_data_acesso (data_acesso),
    INDEX idx_numero_registro (numero_registro),
    INDEX idx_timestamp (timestamp_acesso),
    INDEX idx_tipo_acesso (tipo_acesso),
    INDEX idx_empresa (empresa),
    INDEX idx_departamento (departamento),
    INDEX idx_metodo_acesso (metodo_acesso),
    INDEX idx_data_tipo (data_acesso, tipo_acesso),
    INDEX idx_funcionario_data (numero_registro, data_acesso)
);
```

#### **Tabela de Reconhecimento Facial**
```sql
CREATE TABLE funcionarios_facial (
    id INT AUTO_INCREMENT PRIMARY KEY,
    numero_registro VARCHAR(20) NOT NULL,
    encoding_facial LONGTEXT NOT NULL COMMENT 'JSON com encoding da face',
    imagem_referencia LONGTEXT NULL COMMENT 'Base64 da imagem de referência',
    ativo BOOLEAN DEFAULT TRUE,
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultimo_uso TIMESTAMP NULL,
    confianca_minima DECIMAL(3,2) DEFAULT 0.60 COMMENT 'Limite de confiança para reconhecimento',
    
    -- Chave estrangeira
    FOREIGN KEY (numero_registro) REFERENCES funcionarios(numero_registro) ON UPDATE CASCADE ON DELETE CASCADE,
    
    -- Índices para performance
    INDEX idx_numero_registro (numero_registro),
    INDEX idx_ativo (ativo),
    INDEX idx_ultimo_uso (ultimo_uso)
);
```

---

## 📷 Configurações de Reconhecimento Facial

### 🎯 Processamento de Imagem

#### **Normalização de Iluminação**
```python
def normalizar_iluminacao(imagem_rgb):
    """
    Normaliza a iluminação da imagem usando CLAHE
    Melhora significativamente o reconhecimento facial em condições ruins
    """
    try:
        # Converter RGB para LAB (melhor para processamento de iluminação)
        lab = cv2.cvtColor(imagem_rgb, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        
        # Aplicar CLAHE apenas no canal L (luminância)
        clahe = cv2.createCLAHE(
            clipLimit=2.0,        # Limite de contraste (2.0 é um bom equilíbrio)
            tileGridSize=(8, 8)   # Tamanho da grade (8x8 é eficiente)
        )
        l_normalizado = clahe.apply(l)
        
        # Reunir os canais
        lab_normalizado = cv2.merge([l_normalizado, a, b])
        
        # Converter de volta para RGB
        imagem_normalizada = cv2.cvtColor(lab_normalizado, cv2.COLOR_LAB2RGB)
        
        return imagem_normalizada
        
    except Exception as e:
        print(f"⚠️ Erro na normalização de iluminação: {e}")
        return imagem_rgb  # Retorna imagem original em caso de erro
```

#### **Cálculo de Qualidade da Imagem**
```python
def calcular_qualidade_imagem(imagem_rgb):
    """
    Calcula métricas de qualidade da imagem para otimizar o processamento
    Retorna um score de 0.0 a 1.0
    """
    try:
        # Converter para escala de cinza para análises
        gray = cv2.cvtColor(imagem_rgb, cv2.COLOR_RGB2GRAY)
        
        # 1. Análise de contraste (usando desvio padrão)
        contraste = np.std(gray) / 255.0
        
        # 2. Análise de nitidez (usando variância do Laplaciano)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        nitidez = np.var(laplacian) / 10000.0  # Normalizar
        
        # 3. Análise de brilho (evitar muito escuro ou muito claro)
        brilho_medio = np.mean(gray) / 255.0
        score_brilho = 1.0 - abs(brilho_medio - 0.5) * 2  # Ideal é 0.5 (127)
        
        # 4. Distribuição de histograma (evitar imagens muito uniformes)
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        hist_normalizado = hist / hist.sum()
        entropia = -np.sum(hist_normalizado * np.log2(hist_normalizado + 1e-10))
        score_entropia = min(entropia / 8.0, 1.0)  # Normalizar entropia
        
        # Score final (média ponderada)
        score_final = (
            contraste * 0.25 +
            min(nitidez, 1.0) * 0.25 +
            score_brilho * 0.25 +
            score_entropia * 0.25
        )
        
        return min(score_final, 1.0)
        
    except Exception as e:
        print(f"⚠️ Erro no cálculo de qualidade: {e}")
        return 0.5  # Retorna valor médio em caso de erro
```

### 🔍 Detecção de Face

#### **Configurações de Detecção**
```python
# Detecção de faces otimizada
face_locations = face_recognition.face_locations(
    imagem_final, 
    model="hog",                    # Modelo HOG (mais rápido)
    number_of_times_to_upsample=1   # Upsample mínimo para performance
)

# Extrair encoding facial com configuração otimizada
face_encodings = face_recognition.face_encodings(
    imagem_final, 
    face_locations, 
    num_jitters=1,  # Para performance
    model="small"   # Modelo rápido
)
```

---

## 🐳 Configurações Docker

### 📦 Docker Compose

#### **Serviço MySQL**
```yaml
acesso_mysql:
  image: mysql:8.0
  container_name: acesso_mysql
  restart: unless-stopped
  environment:
    MYSQL_ROOT_PASSWORD: root_password
    MYSQL_DATABASE: acesso_funcionarios_db
    MYSQL_USER: app_user
    MYSQL_PASSWORD: app_password
    TZ: America/Sao_Paulo
  ports:
    - "3311:3306"
  volumes:
    - mysql_acesso_data:/var/lib/mysql
    - ./init.sql:/docker-entrypoint-initdb.d/init.sql
  networks:
    - acesso_network
  healthcheck:
    test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
    timeout: 20s
    retries: 10
```

#### **Serviço Flask**
```yaml
flask_acesso:
  build:
    context: .
    dockerfile: Dockerfile
  container_name: acesso_flask
  restart: unless-stopped
  environment:
    MYSQL_HOST: acesso_mysql
    MYSQL_USER: app_user
    MYSQL_PASSWORD: app_password
    MYSQL_DATABASE: acesso_funcionarios_db
    SECRET_KEY: acesso_secret_key_2024
    TZ: America/Sao_Paulo
  ports:
    - "5009:8081"
  volumes:
    - ./templates:/app/templates
    - ./static:/app/static
    - ./logs:/app/logs
  depends_on:
    acesso_mysql:
      condition: service_healthy
  networks:
    - acesso_network
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:5009/"]
    interval: 30s
    timeout: 10s
    retries: 3
```

#### **Serviço Caddy (Proxy Reverso)**
```yaml
caddy_acesso:
  image: caddy:2-alpine
  container_name: acesso_caddy
  restart: unless-stopped
  ports:
    - "8081:80"
    - "8444:443"
  volumes:
    - ./Caddyfile:/etc/caddy/Caddyfile
    - ./certs:/etc/caddy/certs
    - caddy_acesso_data:/data
    - caddy_acesso_config:/config
    - ./logs/caddy:/var/log/caddy
  environment:
    - ACME_AGREE=true
  depends_on:
    - flask_acesso
  networks:
    - acesso_network
```

### 🐋 Dockerfile

```dockerfile
FROM python:3.12-slim

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgthread-2.0-0 \
    libgtk-3-0 \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libatlas-base-dev \
    gfortran \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Definir diretório de trabalho
WORKDIR /app

# Copiar arquivos de dependências
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Expor porta
EXPOSE 8081

# Comando para executar a aplicação
CMD ["python", "sistema_acesso_funcionarios.py"]
```

---

## 🔌 Configurações de API

### 📡 Endpoints de Acesso

#### **Registro de Acesso Manual**
```python
@app.route('/registrar_acesso_funcionario', methods=['POST'])
def registrar_acesso_funcionario():
    """Registra acesso de funcionário"""
    # Verificar se os dados vieram via JSON ou form
    if request.is_json:
        data = request.get_json()
        numero_registro = data.get('numero_registro', '').strip()
        tipo_acesso = data.get('tipo_acesso', '')
        observacao = data.get('observacao', '')
        metodo_acesso = data.get('metodo_acesso', 'manual')
    else:
        numero_registro = request.form.get('numero_registro', '').strip()
        tipo_acesso = request.form.get('tipo_acesso', '')
        observacao = request.form.get('observacao', '')
        metodo_acesso = request.form.get('metodo_acesso', 'manual')
    
    # Se não especificou tipo, determinar automaticamente
    if not tipo_acesso:
        tipo_acesso = determinar_tipo_acesso_automatico(numero_registro)
    
    # ... resto da implementação
```

#### **Registro de Acesso Facial**
```python
@app.route('/registrar_acesso_facial', methods=['POST'])
def registrar_acesso_facial():
    """Registra acesso via reconhecimento facial"""
    try:
        imagem_base64 = request.json.get('imagem', '')
        
        if not imagem_base64:
            return jsonify({'success': False, 'message': 'Imagem obrigatória'})
        
        # Buscar funcionário por face
        funcionario, erro = buscar_funcionario_por_facial(imagem_base64)
        
        if erro:
            return jsonify({
                'success': False, 
                'message': erro,
                'tipo': 'face_nao_reconhecida'
            })
        
        # ... resto da implementação
```

### 📊 Endpoints de Dados

#### **Dashboard Data**
```python
@app.route('/api/dashboard-data')
@login_required
def dashboard_data():
    """API para fornecer dados do dashboard"""
    try:
        conn = get_simple_connection()
        cursor = conn.cursor()
        
        # Estatísticas básicas
        stats = {}
        
        # Total de funcionários
        cursor.execute("SELECT COUNT(*) FROM funcionarios WHERE ativo = TRUE")
        stats['total_funcionarios'] = cursor.fetchone()[0]
        
        # Acessos hoje
        cursor.execute("""
            SELECT COUNT(*) FROM acessos_funcionarios 
            WHERE DATE(data_acesso) = CURDATE()
        """)
        stats['acessos_hoje'] = cursor.fetchone()[0]
        
        # ... resto da implementação
```

---

## ⚙️ Configurações de Horários

### 🕐 Sistema de Horários

#### **Configuração Padrão**
```python
# Horários padrão de trabalho
HORARIOS_PADRAO = {
    'entrada': '08:00',
    'saida': '18:00',
    'almoco_inicio': '12:00',
    'almoco_fim': '13:00',
    'intervalo_inicio': '15:00',
    'intervalo_fim': '15:15'
}

# Tipos de acesso
TIPOS_ACESSO = {
    'entrada': 'Entrada',
    'saida': 'Saída',
    'almoco_entrada': 'Entrada Almoço',
    'almoco_saida': 'Saída Almoço',
    'intervalo_entrada': 'Entrada Intervalo',
    'intervalo_saida': 'Saída Intervalo'
}
```

#### **Determinação Automática de Horário**
```python
def determinar_horario_aplicavel(numero_registro, hora_atual, dia_semana):
    """Determina qual configuração de horário aplicar baseado em múltiplas regras"""
    try:
        conn = get_simple_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Buscar todas as configurações de horário ativas
        cursor.execute("""
            SELECT * FROM configuracoes_horarios 
            WHERE ativo = TRUE 
            ORDER BY nome_config
        """)
        
        configuracoes = cursor.fetchall()
        
        # ... lógica de determinação de horário
        
    except Exception as e:
        print(f"Erro ao determinar horário aplicável: {e}")
        return {
            'hora_entrada': '08:00:00',
            'hora_saida': '18:00:00',
            'tolerancia_entrada': 15,
            'tolerancia_saida': 15,
            'nome_config': 'Padrão (Erro)'
        }
```

---

## 📝 Configurações de Log

### 📋 Sistema de Logs

#### **Função de Log**
```python
def log_acesso(tipo_evento, descricao, dados_extras=None):
    """Registra evento no log do sistema de acesso"""
    try:
        conn = get_simple_connection()
        cursor = conn.cursor()
        
        usuario_admin = session.get('admin_nome', session.get('admin_username', None))
        dados_json = json.dumps(dados_extras) if dados_extras else None
        ip_origem = request.remote_addr if request else None
        
        cursor.execute("""
            INSERT INTO logs_acesso (tipo_evento, descricao, usuario_admin, dados_extras, ip_origem)
            VALUES (%s, %s, %s, %s, %s)
        """, (tipo_evento, descricao, usuario_admin, dados_json, ip_origem))
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Erro ao registrar log: {e}")
```

#### **Tabela de Logs**
```sql
CREATE TABLE logs_acesso (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp_log TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tipo_evento VARCHAR(50) NOT NULL,
    descricao TEXT NOT NULL,
    usuario_admin VARCHAR(50) NULL,
    dados_extras JSON NULL,
    ip_origem VARCHAR(45) NULL,
    
    -- Índices
    INDEX idx_timestamp (timestamp_log),
    INDEX idx_tipo (tipo_evento),
    INDEX idx_ip_origem (ip_origem)
);
```

---

## 🔧 Configurações de Desenvolvimento

### 🚀 Configurações de Debug

#### **Modo de Desenvolvimento**
```python
if __name__ == '__main__':
    print("Iniciando Sistema de Controle de Acesso de Funcionários...")
    
    # Criar tabelas se não existirem
    try:
        criar_tabelas_acesso_funcionarios()
        criar_tabelas_facial()
        criar_tabelas_rfid()
        criar_tabelas_configuracoes()
        print("Tabelas criadas/verificadas com sucesso!")
    except Exception as e:
        print(f"Erro ao criar tabelas: {e}")
    
    # Configurar host e porta
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 8082))
    
    print(f"Sistema iniciado em http://{host}:{port}")
    app.run(host=host, port=port, debug=True)
```

#### **Variáveis de Ambiente**
```bash
# Configurações do Flask
FLASK_HOST=0.0.0.0
FLASK_PORT=8082
FLASK_ENV=development
FLASK_DEBUG=True

# Configurações do banco
MYSQL_HOST=localhost
MYSQL_USER=app_user
MYSQL_PASSWORD=app_password
MYSQL_DATABASE=acesso_funcionarios_db

# Configurações de segurança
SECRET_KEY=sua_chave_secreta_aqui
```

---

## 📊 Configurações de Performance

### ⚡ Otimizações Implementadas

#### **Cache de Encodings Faciais**
```python
# Cache para encodings faciais (otimização de performance)
facial_encodings_cache = {}
CACHE_EXPIRY = 300  # 5 minutos

def limpar_cache_expirado():
    """Limpa cache de encodings expirados"""
    current_time = time.time()
    expired_keys = [key for key, (encoding, timestamp) in facial_encodings_cache.items() 
                    if current_time - timestamp > CACHE_EXPIRY]
    
    for key in expired_keys:
        del facial_encodings_cache[key]
```

#### **Rate Limiting Inteligente**
```python
def verificar_rate_limiting_facial(client_ip):
    """Verifica se o cliente está dentro dos limites de processamento facial"""
    import time
    current_time = time.time()
    
    if client_ip not in facial_processing_cache:
        facial_processing_cache[client_ip] = {
            'requests': [],
            'last_request': 0,
            'cooldown_until': 0
        }
    
    client_data = facial_processing_cache[client_ip]
    
    # Verificar se está em cooldown
    if current_time < client_data['cooldown_until']:
        return False, f"Cooldown ativo. Aguarde {int(client_data['cooldown_until'] - current_time)} segundos"
    
    # ... resto da lógica de rate limiting
```

---

## 🔒 Configurações de Segurança Avançadas

### 🛡️ Proteções Adicionais

#### **Validação de Entrada**
```python
def validar_numero_registro(numero_registro):
    """Valida formato do número de registro"""
    if not numero_registro or not isinstance(numero_registro, str):
        return False, "Número de registro inválido"
    
    numero_registro = numero_registro.strip()
    
    # Verificar comprimento
    if len(numero_registro) < 3 or len(numero_registro) > 20:
        return False, "Número de registro deve ter entre 3 e 20 caracteres"
    
    # Verificar se contém apenas caracteres válidos
    if not numero_registro.replace('-', '').replace('_', '').isalnum():
        return False, "Número de registro deve conter apenas letras, números, hífen e underscore"
    
    return True, numero_registro
```

#### **Sanitização de Dados**
```python
def sanitizar_texto(texto):
    """Remove caracteres perigosos do texto"""
    if not texto:
        return ""
    
    # Remover caracteres de controle
    texto = ''.join(char for char in texto if ord(char) >= 32)
    
    # Escapar caracteres especiais HTML
    import html
    texto = html.escape(texto)
    
    # Limitar comprimento
    if len(texto) > 1000:
        texto = texto[:1000]
    
    return texto.strip()
```

---

## 📱 Configurações de Interface

### 🎨 Configurações de UI

#### **Cores do Sistema**
```css
:root {
    /* Cores principais */
    --primary-color: #007bff;
    --secondary-color: #6c757d;
    --success-color: #28a745;
    --danger-color: #dc3545;
    --warning-color: #ffc107;
    --info-color: #17a2b8;
    
    /* Cores de fundo */
    --bg-primary: #ffffff;
    --bg-secondary: #f8f9fa;
    --bg-dark: #343a40;
    
    /* Cores de texto */
    --text-primary: #212529;
    --text-secondary: #6c757d;
    --text-light: #ffffff;
    
    /* Cores de status */
    --status-presente: #28a745;
    --status-ausente: #dc3545;
    --status-atraso: #ffc107;
    --status-saida: #6c757d;
}
```

#### **Configurações de Responsividade**
```css
/* Breakpoints responsivos */
@media (max-width: 576px) {
    /* Mobile */
    .container { padding: 0 15px; }
    .btn { width: 100%; margin-bottom: 10px; }
}

@media (min-width: 577px) and (max-width: 768px) {
    /* Tablet */
    .container { padding: 0 30px; }
}

@media (min-width: 769px) {
    /* Desktop */
    .container { padding: 0 50px; }
}
```

---

## 🔧 Configurações de Backup

### 💾 Sistema de Backup

#### **Script de Backup Automático**
```bash
#!/bin/bash
# backup_automatico.sh

# Configurações
BACKUP_DIR="/backups/sistema_acesso"
MYSQL_CONTAINER="acesso_mysql"
MYSQL_DB="acesso_funcionarios_db"
MYSQL_USER="root"
MYSQL_PASSWORD="root_password"
RETENTION_DAYS=30

# Criar diretório de backup se não existir
mkdir -p $BACKUP_DIR

# Data atual
DATE=$(date +%Y%m%d_%H%M%S)

# Backup do banco de dados
echo "Iniciando backup do banco de dados..."
docker exec $MYSQL_CONTAINER mysqldump -u $MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DB > $BACKUP_DIR/backup_db_$DATE.sql

# Backup dos arquivos de configuração
echo "Iniciando backup dos arquivos..."
tar -czf $BACKUP_DIR/backup_files_$DATE.tar.gz \
    --exclude=venv \
    --exclude=logs/*.log \
    --exclude=backups \
    .

# Remover backups antigos
echo "Removendo backups antigos..."
find $BACKUP_DIR -name "*.sql" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup concluído: $DATE"
```

#### **Configuração de Cron**
```bash
# Adicionar ao crontab (crontab -e)
# Backup diário às 2h da manhã
0 2 * * * /caminho/para/backup_automatico.sh >> /var/log/backup.log 2>&1

# Backup semanal aos domingos às 3h
0 3 * * 0 /caminho/para/backup_completo.sh >> /var/log/backup_completo.log 2>&1
```

---

## 📊 Configurações de Monitoramento

### 📈 Métricas do Sistema

#### **Health Check Endpoint**
```python
@app.route('/api/health')
def health_check():
    """Endpoint para verificação de saúde do sistema"""
    try:
        # Verificar banco de dados
        conn = get_simple_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        db_status = cursor.fetchone() is not None
        cursor.close()
        conn.close()
        
        # Verificar câmera (se disponível)
        camera_status = False
        try:
            cap = cv2.VideoCapture(0)
            camera_status = cap.isOpened()
            cap.release()
        except:
            pass
        
        # Verificar uso de recursos
        import psutil
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_percent = psutil.virtual_memory().percent
        disk_percent = psutil.disk_usage('/').percent
        
        return jsonify({
            'status': 'healthy' if db_status else 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'database': 'connected' if db_status else 'disconnected',
            'camera': 'available' if camera_status else 'unavailable',
            'resources': {
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'disk_percent': disk_percent
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500
```

---

## 🎯 Configurações de Produção

### 🚀 Otimizações para Produção

#### **Configurações de Produção**
```python
# Configurações para produção
if os.getenv('FLASK_ENV') == 'production':
    # Desabilitar debug
    app.debug = False
    
    # Configurações de sessão mais seguras
    app.config.update(
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Strict',
        PERMANENT_SESSION_LIFETIME=timedelta(hours=1)
    )
    
    # Configurações de logging
    import logging
    from logging.handlers import RotatingFileHandler
    
    if not app.debug:
        file_handler = RotatingFileHandler('logs/sistema_acesso.log', 
                                         maxBytes=10240000, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Sistema de Acesso iniciado em modo produção')
```

#### **Configurações de WSGI**
```python
# wsgi.py para produção
from sistema_acesso_funcionarios import app

if __name__ == "__main__":
    app.run()
```

---

**📋 Nota**: Esta documentação técnica deve ser mantida atualizada conforme o sistema evolui. Todas as configurações são testadas e validadas antes de serem implementadas em produção. 