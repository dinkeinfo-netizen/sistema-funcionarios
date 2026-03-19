# ⚙️ Configuração Técnica - Sistema de Controle de Acesso

## 🔧 Configurações Principais

### 📊 Performance
```python
# Rate limiting facial
PROCESSAMENTO_FACIAL_LIMITS = {
    'max_requests_per_minute': 120,
    'max_processing_time': 5,
    'cooldown_period': 30
}

# Cache e otimização
OPTIMIZATION_CONFIG = {
    'max_image_size': (640, 480),
    'use_cache': True,
    'cache_ttl': 300,
    'min_confidence': 0.65,
    'max_processing_time': 3
}
```

### 🔐 Segurança
```python
# Sessões seguras
app.config.update(
    SESSION_COOKIE_SECURE=False,  # True para produção
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(hours=2)
)

# Hash de senhas PBKDF2
def hash_password(password):
    salt = secrets.token_hex(32)
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), 
                                  salt.encode('utf-8'), 100000)
    return salt + pwdhash.hex()
```

### 🌍 Timezone
```python
# Configurar timezone Brasil
os.environ['TZ'] = 'America/Sao_Paulo'

def get_data_atual():
    tz_brasil = pytz.timezone('America/Sao_Paulo')
    agora = datetime.now(tz_brasil)
    return agora.date()
```

## 🗄️ Banco de Dados

### 🔌 Conexão MySQL
```python
def get_simple_connection():
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
```

### 🏗️ Tabelas Principais
```sql
-- Funcionários
CREATE TABLE funcionarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    numero_registro VARCHAR(20) UNIQUE NOT NULL,
    nome VARCHAR(100) NOT NULL,
    departamento VARCHAR(50) NOT NULL,
    cargo VARCHAR(50) NOT NULL,
    empresa VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'ativo',
    ativo BOOLEAN DEFAULT TRUE,
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Acessos
CREATE TABLE acessos_funcionarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    numero_registro VARCHAR(20) NOT NULL,
    tipo_acesso VARCHAR(20) NOT NULL,
    data_acesso DATE NOT NULL,
    hora_acesso TIME NOT NULL,
    metodo_acesso VARCHAR(20) DEFAULT 'manual',
    FOREIGN KEY (numero_registro) REFERENCES funcionarios(numero_registro)
);

-- Facial
CREATE TABLE funcionarios_facial (
    id INT AUTO_INCREMENT PRIMARY KEY,
    numero_registro VARCHAR(20) NOT NULL,
    encoding_facial LONGTEXT NOT NULL,
    confianca_minima DECIMAL(3,2) DEFAULT 0.60,
    FOREIGN KEY (numero_registro) REFERENCES funcionarios(numero_registro)
);
```

## 📷 Reconhecimento Facial

### 🎯 Processamento de Imagem
```python
def normalizar_iluminacao(imagem_rgb):
    # Converter RGB para LAB
    lab = cv2.cvtColor(imagem_rgb, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    
    # Aplicar CLAHE no canal L
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_normalizado = clahe.apply(l)
    
    # Reunir canais e converter de volta
    lab_normalizado = cv2.merge([l_normalizado, a, b])
    return cv2.cvtColor(lab_normalizado, cv2.COLOR_LAB2RGB)

def calcular_qualidade_imagem(imagem_rgb):
    gray = cv2.cvtColor(imagem_rgb, cv2.COLOR_RGB2GRAY)
    
    # Contraste, nitidez, brilho, entropia
    contraste = np.std(gray) / 255.0
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    nitidez = np.var(laplacian) / 10000.0
    brilho_medio = np.mean(gray) / 255.0
    score_brilho = 1.0 - abs(brilho_medio - 0.5) * 2
    
    # Score final
    score_final = (contraste * 0.25 + min(nitidez, 1.0) * 0.25 + 
                   score_brilho * 0.25 + score_entropia * 0.25)
    return min(score_final, 1.0)
```

### 🔍 Detecção Otimizada
```python
# Detecção de faces
face_locations = face_recognition.face_locations(
    imagem_final, 
    model="hog",                    # Modelo rápido
    number_of_times_to_upsample=1   # Upsample mínimo
)

# Encoding facial
face_encodings = face_recognition.face_encodings(
    imagem_final, 
    face_locations, 
    num_jitters=1,  # Para performance
    model="small"   # Modelo rápido
)
```

## 🐳 Docker

### 📦 Docker Compose
```yaml
version: '3.8'
services:
  acesso_mysql:
    image: mysql:8.0
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

  flask_acesso:
    build: .
    environment:
      MYSQL_HOST: acesso_mysql
      MYSQL_USER: app_user
      MYSQL_PASSWORD: app_password
      MYSQL_DATABASE: acesso_funcionarios_db
      SECRET_KEY: acesso_secret_key_2024
    ports:
      - "5009:8081"
    depends_on:
      acesso_mysql:
        condition: service_healthy

  caddy_acesso:
    image: caddy:2-alpine
    ports:
      - "8081:80"
      - "8444:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - ./certs:/etc/caddy/certs
    depends_on:
      - flask_acesso
```

### 🐋 Dockerfile
```dockerfile
FROM python:3.12-slim

# Dependências do sistema
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 \
    libxrender-dev libgomp1 libgtk-3-0 \
    libavcodec-dev libavformat-dev libswscale-dev \
    libv4l-dev libxvidcore-dev libx264-dev \
    libjpeg-dev libpng-dev libtiff-dev \
    libatlas-base-dev gfortran wget curl

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8081
CMD ["python", "sistema_acesso_funcionarios.py"]
```

## 🔌 APIs

### 📡 Endpoints Principais
```python
# Acesso
POST /registrar_acesso_funcionario
POST /registrar_acesso_facial
POST /api/detectar_face

# Dashboard
GET /api/dashboard-data
GET /api/relatorios/diario
GET /api/relatorios/funcionario

# Gestão
GET /api/funcionarios
POST /api/funcionarios
PUT /api/funcionarios/{id}
DELETE /api/funcionarios/{id}
```

### 📊 Exemplo de API
```python
@app.route('/api/dashboard-data')
@login_required
def dashboard_data():
    try:
        conn = get_simple_connection()
        cursor = conn.cursor()
        
        # Estatísticas básicas
        cursor.execute("SELECT COUNT(*) FROM funcionarios WHERE ativo = TRUE")
        total_funcionarios = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM acessos_funcionarios 
            WHERE DATE(data_acesso) = CURDATE()
        """)
        acessos_hoje = cursor.fetchone()[0]
        
        # ... mais estatísticas
        
        return jsonify({
            'success': True,
            'stats': {
                'total_funcionarios': total_funcionarios,
                'acessos_hoje': acessos_hoje
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
```

## ⏰ Horários

### 🕐 Configuração de Horários
```python
# Horários padrão
HORARIOS_PADRAO = {
    'entrada': '08:00',
    'saida': '18:00',
    'almoco_inicio': '12:00',
    'almoco_fim': '13:00',
    'tolerancia_entrada': 15,
    'tolerancia_saida': 15
}

# Tipos de acesso
TIPOS_ACESSO = {
    'entrada': 'Entrada',
    'saida': 'Saída',
    'almoco_entrada': 'Entrada Almoço',
    'almoco_saida': 'Saída Almoço'
}

def verificar_horario_trabalho(numero_registro, tipo_acesso):
    agora = datetime.now()
    hora_atual = agora.time()
    
    # Determinar configuração aplicável
    horario_config = determinar_horario_aplicavel(
        numero_registro, hora_atual.strftime('%H:%M'), agora.weekday()
    )
    
    # ... lógica de verificação de horário
```

## 📝 Logs

### 📋 Sistema de Logs
```python
def log_acesso(tipo_evento, descricao, dados_extras=None):
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

## 🔒 Segurança

### 🛡️ Validações
```python
def validar_numero_registro(numero_registro):
    if not numero_registro or not isinstance(numero_registro, str):
        return False, "Número de registro inválido"
    
    numero_registro = numero_registro.strip()
    
    if len(numero_registro) < 3 or len(numero_registro) > 20:
        return False, "Número de registro deve ter entre 3 e 20 caracteres"
    
    if not numero_registro.replace('-', '').replace('_', '').isalnum():
        return False, "Número de registro deve conter apenas letras, números, hífen e underscore"
    
    return True, numero_registro

def sanitizar_texto(texto):
    if not texto:
        return ""
    
    # Remover caracteres de controle
    texto = ''.join(char for char in texto if ord(char) >= 32)
    
    # Escapar HTML
    import html
    texto = html.escape(texto)
    
    # Limitar comprimento
    if len(texto) > 1000:
        texto = texto[:1000]
    
    return texto.strip()
```

## 🚀 Produção

### ⚙️ Configurações de Produção
```python
# Configurações para produção
if os.getenv('FLASK_ENV') == 'production':
    app.debug = False
    
    # Sessões mais seguras
    app.config.update(
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Strict',
        PERMANENT_SESSION_LIFETIME=timedelta(hours=1)
    )
    
    # Logging
    import logging
    from logging.handlers import RotatingFileHandler
    
    file_handler = RotatingFileHandler('logs/sistema_acesso.log', 
                                     maxBytes=10240000, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
```

## 📊 Monitoramento

### 📈 Health Check
```python
@app.route('/api/health')
def health_check():
    try:
        # Verificar banco
        conn = get_simple_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        db_status = cursor.fetchone() is not None
        cursor.close()
        conn.close()
        
        # Verificar câmera
        camera_status = False
        try:
            cap = cv2.VideoCapture(0)
            camera_status = cap.isOpened()
            cap.release()
        except:
            pass
        
        # Recursos do sistema
        import psutil
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_percent = psutil.virtual_memory().percent
        
        return jsonify({
            'status': 'healthy' if db_status else 'unhealthy',
            'database': 'connected' if db_status else 'disconnected',
            'camera': 'available' if camera_status else 'unavailable',
            'resources': {
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500
```

## 🔧 Variáveis de Ambiente

### 🌍 Configurações
```bash
# Flask
FLASK_HOST=0.0.0.0
FLASK_PORT=8082
FLASK_ENV=development
FLASK_DEBUG=True

# Banco de dados
MYSQL_HOST=localhost
MYSQL_USER=app_user
MYSQL_PASSWORD=app_password
MYSQL_DATABASE=acesso_funcionarios_db

# Segurança
SECRET_KEY=sua_chave_secreta_aqui

# Timezone
TZ=America/Sao_Paulo
```

---

**📋 Nota**: Esta configuração técnica deve ser mantida atualizada conforme o sistema evolui. Todas as configurações são testadas antes da implementação em produção.










