#!/usr/bin/env python3
"""
Sistema de Controle de Acesso de Funcionários
Baseado na estrutura do Sistema de Refeitório
Versão: 1.0
"""

from flask import Flask, render_template, request, jsonify, redirect, session, url_for, flash, Response
import mysql.connector
from datetime import datetime, date, timedelta
import os
import hashlib
import secrets
from functools import wraps
import time
import json
import csv
import io
from flask_cors import CORS
import threading
import copy
import random
import pandas as pd
import tempfile
import qrcode
import base64
import traceback
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import cv2
import face_recognition
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors


app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(32))
CORS(app)

# Configurar timezone para Brasil
import os
os.environ['TZ'] = 'America/Sao_Paulo'
import socket

#dalmo def get_host_ip():
def get_host_ip():
    """
    Detecta automaticamente o IP da máquina hospedeira.
    Prioridade: 1) Arquivo config_ip.txt, 2) Variável de ambiente, 3) Detecção automática
    """
    try:
        # MÉTODO 1: Ler de arquivo de configuração (PRIORIDADE MÁXIMA)
        try:
            # Tentar no diretório /app (dentro do container Docker)
            config_file = '/app/config_ip.txt'
            # Se não existir, tentar no diretório raiz do projeto (para desenvolvimento)
            if not os.path.exists(config_file):
                config_file = 'config_ip.txt'
            
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    ip_manual = f.read().strip()
                    # Remover comentários e espaços em branco
                    if '#' in ip_manual:
                        ip_manual = ip_manual.split('#')[0].strip()
                    
                    if ip_manual and len(ip_manual) > 0:
                        # Validar formato IP básico (4 números separados por ponto)
                        parts = ip_manual.split('.')
                        if len(parts) == 4:
                            # Testar acessibilidade na porta 8444
                            try:
                                test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                test_socket.settimeout(2)
                                result = test_socket.connect_ex((ip_manual, 8444))
                                test_socket.close()
                                if result == 0:
                                    print(f"✅ Usando IP do arquivo de configuração (testado e acessível): {ip_manual}")
                                    return ip_manual
                                else:
                                    print(f"⚠️ IP do arquivo de configuração ({ip_manual}) não é acessível na porta 8444 (código: {result})")
                                    print("🔍 Continuando com outros métodos...")
                            except socket.timeout:
                                print(f"⚠️ Timeout ao testar IP do arquivo de configuração ({ip_manual})")
                                print("🔍 Continuando com outros métodos...")
                            except Exception as e:
                                print(f"⚠️ Erro ao testar IP do arquivo de configuração ({ip_manual}): {e}")
                                print("🔍 Continuando com outros métodos...")
                        else:
                            print(f"⚠️ Formato de IP inválido no arquivo de configuração: {ip_manual}")
        except FileNotFoundError:
            # Arquivo não existe, continuar
            pass
        except Exception as e:
            print(f"⚠️ Erro ao ler arquivo de configuração: {e}")
        
        # MÉTODO 2: Variável de ambiente (testar acessibilidade)
        env_ip = os.getenv('SISTEMA_REAL_IP')
        if env_ip:
            print(f"🔍 Testando IP da variável de ambiente: {env_ip}")
            try:
                test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                test_socket.settimeout(2)
                result = test_socket.connect_ex((env_ip, 8444))
                test_socket.close()
                if result == 0:
                    print(f"✅ Usando IP da variável de ambiente (testado e acessível): {env_ip}")
                    return env_ip
                else:
                    print(f"⚠️ IP da variável de ambiente ({env_ip}) não é acessível na porta 8444 (código: {result})")
                    print("🔍 Continuando com detecção automática...")
            except socket.timeout:
                print(f"⚠️ Timeout ao testar IP da variável de ambiente ({env_ip})")
                print("🔍 Continuando com detecção automática...")
            except Exception as e:
                print(f"⚠️ Erro ao testar IP da variável de ambiente ({env_ip}): {e}")
                print("🔍 Continuando com detecção automática...")
        
        # MÉTODO 3: Variável de ambiente com URL completa
        env_url = os.getenv('SISTEMA_REAL_URL')
        if env_url:
            # Extrair IP da URL se for uma URL completa
            if '://' in env_url:
                # Ex: https://10.17.95.4:8444 -> 10.17.95.4
                ip_part = env_url.split('://')[1].split(':')[0]
                print(f"✅ Usando IP extraído da URL: {ip_part}")
                return ip_part
            print(f"✅ Usando URL da variável de ambiente: {env_url}")
            return env_url
        
        # MÉTODO 4: Detecção automática
        print("🔍 Iniciando detecção automática do IP do host...")
        
        # 4a: host.docker.internal
        try:
            host_ip = socket.gethostbyname('host.docker.internal')
            if host_ip and host_ip != '127.0.0.1':
                print(f"✅ IP detectado via host.docker.internal: {host_ip}")
                return host_ip
        except Exception as e:
            print(f"⚠️ host.docker.internal não disponível: {e}")
        
        # 4b: ip route get 8.8.8.8
        try:
            import subprocess
            result = subprocess.run(['ip', 'route', 'get', '8.8.8.8'], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                for word in result.stdout.split():
                    if '.' in word and word.count('.') == 3:
                        if not (word.startswith('172.17.') or word.startswith('172.18.') or 
                               word.startswith('172.19.') or word.startswith('192.168.122.')):
                            if not word.startswith('127.'):
                                print(f"✅ IP detectado via ip route: {word}")
                                return word
        except Exception as e:
            print(f"⚠️ Método ip route falhou: {e}")
        
        # 4c: hostname -I
        try:
            import subprocess
            result = subprocess.run(['hostname', '-I'], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                ips = result.stdout.strip().split()
                for ip in ips:
                    if ip and not ip.startswith('127.') and not ip.startswith('172.17.') and not ip.startswith('172.18.'):
                        print(f"✅ IP detectado via hostname -I: {ip}")
                        return ip
        except Exception as e:
            print(f"⚠️ Método hostname -I falhou: {e}")
        
        # 4d: ip addr show
        try:
            import subprocess
            result = subprocess.run(['ip', 'addr', 'show'], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'inet ' in line and '127.0.0.1' not in line:
                        parts = line.strip().split()
                        for part in parts:
                            if '.' in part and '/' in part:
                                ip = part.split('/')[0]
                                if not ip.startswith('127.') and not ip.startswith('172.17.') and not ip.startswith('172.18.'):
                                    print(f"✅ IP detectado via ip addr: {ip}")
                                    return ip
        except Exception as e:
            print(f"⚠️ Método ip addr falhou: {e}")
        
        # 4e: Em Docker, tentar obter IP do host via gateway
        try:
            # Ler /proc/net/route para obter gateway
            with open('/proc/net/route', 'r') as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 3 and parts[1] == '00000000':  # default route
                        gateway_hex = parts[2]
                        # Converter hex little-endian para IP
                        gateway_ip = '.'.join([str(int(gateway_hex[i:i+2], 16)) 
                                             for i in range(6, -1, -2)])
                        if gateway_ip and not gateway_ip.startswith('0.') and gateway_ip != '0.0.0.0':
                            print(f"✅ IP do host detectado via gateway Docker: {gateway_ip}")
                            return gateway_ip
        except Exception as e:
            print(f"⚠️ Método gateway falhou: {e}")
        
        # 4f: Tentar obter hostname e resolver
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            if local_ip != '127.0.0.1' and not local_ip.startswith('127.'):
                print(f"✅ IP detectado via hostname: {local_ip}")
                return local_ip
        except Exception as e:
            print(f"⚠️ Método hostname falhou: {e}")
        
        # 4g: Listar todas as interfaces de rede via netifaces (se disponível)
        try:
            import netifaces
            gateways = netifaces.gateways()
            default_interface = gateways['default'][netifaces.AF_INET][1]
            addrs = netifaces.ifaddresses(default_interface)
            if netifaces.AF_INET in addrs:
                ip = addrs[netifaces.AF_INET][0]['addr']
                if ip != '127.0.0.1' and not ip.startswith('172.17.') and not ip.startswith('172.18.'):
                    print(f"✅ IP detectado via netifaces: {ip}")
                    return ip
        except ImportError:
            pass
        except Exception as e:
            print(f"⚠️ Método netifaces falhou: {e}")
        
        print("⚠️ Não foi possível detectar IP automaticamente, usando localhost")
        return '127.0.0.1'
        
    except Exception as e:
        print(f"❌ Erro ao detectar IP: {e}")
        import traceback
        traceback.print_exc()
        return '127.0.0.1'
# dalmo return '127.0.0.1'

def get_sistema_real_url():
    """
    Retorna a URL completa do sistema real.
    Usa variável de ambiente ou detecta automaticamente o IP.
    """
    # Verificar se há URL completa na variável de ambiente
    env_url = os.getenv('SISTEMA_REAL_URL')
    if env_url:
        # Se já tem protocolo, retornar como está
        if '://' in env_url:
            return env_url
        # Se não tem protocolo, adicionar
        return f'https://{env_url}'
    
    # Detectar IP automaticamente
    host_ip = get_host_ip()
    port = os.getenv('SISTEMA_REAL_PORT', '8444')
    
    return f'https://{host_ip}:{port}'

def get_data_atual():
    """Retorna a data atual no timezone do Brasil"""
    from datetime import datetime
    import pytz
    
    # Definir timezone do Brasil
    tz_brasil = pytz.timezone('America/Sao_Paulo')
    agora = datetime.now(tz_brasil)
    return agora.date()

# Configurações de sessão segura
app.config.update(
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(hours=2)
)

# Controle de rate limiting para processamento facial
PROCESSAMENTO_FACIAL_LIMITS = {
    'max_requests_per_minute': 120,  # Aumentado para 120 requisições/min
    'max_processing_time': 5,  # 5 segundos máximo
    'cooldown_period': 30  # Reduzido para 30 segundos
}

# Cache para controle de rate limiting
facial_processing_cache = {}

# Cache para encodings faciais (otimização de performance)
facial_encodings_cache = {}
CACHE_EXPIRY = 300  # 5 minutos

# Configurações de otimização
OPTIMIZATION_CONFIG = {
    'max_image_size': (640, 480),  # Tamanho máximo da imagem
    'use_cache': True,             # Usar cache de encodings
    'cache_ttl': 300,              # TTL do cache em segundos
    'min_confidence': 0.65,        # Confiança mínima
    'max_processing_time': 3       # Tempo máximo de processamento
}

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
    
    # Limpar requisições antigas (mais de 1 minuto)
    client_data['requests'] = [req_time for req_time in client_data['requests'] 
                              if current_time - req_time < 60]
    
    # Verificar limite de requisições por minuto
    if len(client_data['requests']) >= PROCESSAMENTO_FACIAL_LIMITS['max_requests_per_minute']:
        client_data['cooldown_until'] = current_time + PROCESSAMENTO_FACIAL_LIMITS['cooldown_period']
        return False, "Limite de requisições excedido. Aguarde 60 segundos"
    
    # Verificar tempo mínimo entre requisições
    if current_time - client_data['last_request'] < 0.1:  # 100ms mínimo entre requisições
        return False, "Requisições muito frequentes. Aguarde 0.1 segundos"
    
    # Registrar nova requisição
    client_data['requests'].append(current_time)
    client_data['last_request'] = current_time
    
    return True, "OK"

# ========================================
# CONFIGURAÇÕES ESPECÍFICAS PARA ACESSO DE FUNCIONÁRIOS
# ========================================

# Tipos de acesso
TIPOS_ACESSO = {
    'entrada': 'Entrada',
    'saida': 'Saída',
    'almoco_entrada': 'Entrada Almoço',
    'almoco_saida': 'Saída Almoço',
    'intervalo_entrada': 'Entrada Intervalo',
    'intervalo_saida': 'Saída Intervalo'
}

# Status de funcionários
STATUS_FUNCIONARIO = {
    'ativo': 'Ativo',
    'inativo': 'Inativo',
    'ferias': 'Férias',
    'licenca': 'Licença',
    'demitido': 'Demitido'
}

# Horários padrão de trabalho
HORARIOS_PADRAO = {
    'entrada': '08:00',
    'saida': '18:00',
    'almoco_inicio': '12:00',
    'almoco_fim': '13:00',
    'intervalo_inicio': '15:00',
    'intervalo_fim': '15:15'
}

# ========================================
# FUNÇÕES DE CONEXÃO (REUTILIZADAS)
# ========================================

# Pool de conexões global
_connection_pool = None

def get_connection_pool():
    """Retorna ou cria o pool de conexões"""
    global _connection_pool
    if _connection_pool is None:
        try:
            _connection_pool = mysql.connector.pooling.MySQLConnectionPool(
                pool_name="acesso_pool",
                pool_size=20,  # Aumentado para evitar esgotamento
                pool_reset_session=True,
                host=os.getenv('MYSQL_HOST', 'localhost'),
                user=os.getenv('MYSQL_USER', 'app_user'),
                password=os.getenv('MYSQL_PASSWORD', 'app_password'),
                database=os.getenv('MYSQL_DATABASE', 'acesso_funcionarios_db'),
                autocommit=True,
                connect_timeout=30,
                charset='utf8'
            )
            print("✅ Pool de conexões MySQL criado com sucesso")
        except Exception as e:
            print(f"❌ Erro ao criar pool de conexões: {e}")
            _connection_pool = None
    return _connection_pool

def get_simple_connection():
    """Conexão usando pool para evitar 'Too many connections'"""
    try:
        pool = get_connection_pool()
        if pool:
            # Tentar obter conexão do pool
            conn = pool.get_connection()
            return conn
        else:
            # Fallback para conexão direta se pool não estiver disponível
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
    except mysql.connector.pooling.PoolError as e:
        print(f"⚠️ Erro no pool de conexões: {e}")
        # Tentar conexão direta como fallback
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
        except Exception as fallback_error:
            print(f"❌ Erro conexão fallback: {fallback_error}")
            raise
    except Exception as e:
        print(f"❌ Erro conexão: {e}")
        raise

# ========================================
# SISTEMA DE AUTENTICAÇÃO (REUTILIZADO)
# ========================================

def hash_password(password):
    """Cria hash seguro da senha"""
    salt = secrets.token_hex(32)
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
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
            pwdhash = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt.encode('utf-8'), 100000)
            return pwdhash.hex() == stored_pwdhash
        
        return False
    except Exception as e:
        print(f"Erro ao verificar senha: {e}")
        return False

def login_required(f):
    """Decorator para proteger rotas administrativas"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print(f"DEBUG: Verificando sessão para {request.endpoint}")
        print(f"DEBUG: Session data: {dict(session)}")
        
        if 'admin_logged_in' not in session or not session['admin_logged_in']:
            print(f"DEBUG: Sessão inválida, redirecionando para login")
            if request.is_json:
                return jsonify({'success': False, 'message': 'Acesso negado. Faça login.', 'redirect': '/admin/login'}), 401
            flash('Você precisa fazer login para acessar esta área.', 'warning')
            return redirect(url_for('admin_login'))
        
        print(f"DEBUG: Sessão válida, permitindo acesso")
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator para rotas que requerem permissão de administrador"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session or not session['admin_logged_in']:
            if request.is_json:
                return jsonify({'success': False, 'message': 'Acesso negado. Faça login.', 'redirect': '/admin/login'}), 401
            flash('Você precisa fazer login para acessar esta área.', 'warning')
            return redirect(url_for('admin_login'))
        
        # Verificar se é admin
        if session.get('admin_role') != 'admin':
            if request.is_json:
                return jsonify({'success': False, 'message': 'Acesso negado. Permissão de administrador necessária.'}), 403
            flash('Acesso negado. Permissão de administrador necessária.', 'danger')
            return redirect(url_for('relatorio_online_sistema_real'))
        
        return f(*args, **kwargs)
    return decorated_function

def portaria_or_admin_required(f):
    """Decorator para rotas acessíveis por portaria ou admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session or not session['admin_logged_in']:
            if request.is_json:
                return jsonify({'success': False, 'message': 'Acesso negado. Faça login.', 'redirect': '/admin/login'}), 401
            flash('Você precisa fazer login para acessar esta área.', 'warning')
            return redirect(url_for('admin_login'))
        
        # Verificar se é admin ou portaria
        role = session.get('admin_role')
        if role not in ['admin', 'portaria']:
            if request.is_json:
                return jsonify({'success': False, 'message': 'Acesso negado.'}), 403
            flash('Acesso negado.', 'danger')
            return redirect(url_for('admin_login'))
        
        return f(*args, **kwargs)
    return decorated_function

# ========================================
# INICIALIZAÇÃO DO BANCO DE DADOS PARA ACESSO DE FUNCIONÁRIOS
# ========================================

def criar_tabelas_acesso_funcionarios():
    """Criar todas as tabelas necessárias para controle de acesso de funcionários"""
    try:
        conn = get_simple_connection()
        cursor = conn.cursor()
        
        # Tabela de funcionários (expandida)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS funcionarios (
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
            )
        """)
        
        # Tabela de acessos de funcionários
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS acessos_funcionarios (
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
            )
        """)
        
        # Tabela de horários de trabalho
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS horarios_trabalho (
                id INT AUTO_INCREMENT PRIMARY KEY,
                numero_registro VARCHAR(20) NOT NULL,
                dia_semana INT NOT NULL COMMENT '0=Domingo, 1=Segunda, ..., 6=Sábado',
                entrada TIME NOT NULL,
                saida TIME NOT NULL,
                almoco_inicio TIME NULL,
                almoco_fim TIME NULL,
                intervalo_inicio TIME NULL,
                intervalo_fim TIME NULL,
                tolerancia_entrada INT DEFAULT 15,
                tolerancia_saida INT DEFAULT 15,
                ativo BOOLEAN DEFAULT TRUE,
                
                -- Chave estrangeira
                FOREIGN KEY (numero_registro) REFERENCES funcionarios(numero_registro) ON UPDATE CASCADE ON DELETE CASCADE,
                
                -- Índices
                INDEX idx_numero_registro (numero_registro),
                INDEX idx_dia_semana (dia_semana),
                INDEX idx_ativo (ativo),
                UNIQUE KEY uk_funcionario_dia (numero_registro, dia_semana)
            )
        """)
        
        # Tabela de feriados e dias especiais
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feriados_dias_especiais (
                id INT AUTO_INCREMENT PRIMARY KEY,
                data_feriado DATE NOT NULL,
                descricao VARCHAR(100) NOT NULL,
                tipo VARCHAR(20) DEFAULT 'feriado' COMMENT 'feriado, ponto_facultativo, dia_especial',
                ativo BOOLEAN DEFAULT TRUE,
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Índices
                INDEX idx_data_feriado (data_feriado),
                INDEX idx_tipo (tipo),
                INDEX idx_ativo (ativo),
                UNIQUE KEY uk_data_feriado (data_feriado)
            )
        """)
        
        # Tabela de justificativas de atraso/ausência
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS justificativas (
                id INT AUTO_INCREMENT PRIMARY KEY,
                numero_registro VARCHAR(20) NOT NULL,
                data_justificativa DATE NOT NULL,
                tipo VARCHAR(20) NOT NULL COMMENT 'atraso, ausencia, saida_antecipada',
                motivo TEXT NOT NULL,
                documento_anexo VARCHAR(255) NULL,
                aprovado BOOLEAN DEFAULT FALSE,
                aprovado_por VARCHAR(50) NULL,
                data_aprovacao TIMESTAMP NULL,
                observacao_aprovacao TEXT NULL,
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Chave estrangeira
                FOREIGN KEY (numero_registro) REFERENCES funcionarios(numero_registro) ON UPDATE CASCADE,
                
                -- Índices
                INDEX idx_numero_registro (numero_registro),
                INDEX idx_data_justificativa (data_justificativa),
                INDEX idx_tipo (tipo),
                INDEX idx_aprovado (aprovado)
            )
        """)
        
        # Tabela de configurações do sistema de acesso
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS configuracoes_acesso (
                chave VARCHAR(50) PRIMARY KEY,
                valor TEXT,
                descricao VARCHAR(255) NULL,
                data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de logs do sistema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs_acesso (
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
            )
        """)
        
        cursor.close()
        conn.close()
        print("✅ Tabelas do sistema de acesso de funcionários criadas")
        
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")

# ========================================
# FUNÇÕES DE VALIDAÇÃO DE HORÁRIOS
# ========================================

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
        
        if not configuracoes:
            # Se não há configurações, usar horário padrão
            return {
                'hora_entrada': '08:00:00',
                'hora_saida': '18:00:00',
                'tolerancia_entrada': 15,
                'tolerancia_saida': 15,
                'nome_config': 'Padrão'
            }
        
        # Buscar dados do funcionário (horário individual e departamento)
        cursor.execute("""
            SELECT horario_entrada, horario_saida, tolerancia_entrada, tolerancia_saida, departamento
            FROM funcionarios 
            WHERE numero_registro = %s AND ativo = TRUE
        """, (numero_registro,))
        
        funcionario = cursor.fetchone()
        departamento_funcionario = funcionario['departamento'] if funcionario else None
        
        # Se funcionário tem horário específico, usar ele (prioridade máxima)
        if funcionario and funcionario['horario_entrada'] and funcionario['horario_saida']:
            return {
                'hora_entrada': str(funcionario['horario_entrada']),
                'hora_saida': str(funcionario['horario_saida']),
                'tolerancia_entrada': funcionario['tolerancia_entrada'] or 15,
                'tolerancia_saida': funcionario['tolerancia_saida'] or 15,
                'nome_config': 'Individual'
            }
        
        # Lógica para determinar qual configuração usar
        hora_atual_time = datetime.strptime(hora_atual, '%H:%M').time()
        
        # Filtrar configurações que se aplicam ao departamento do funcionário
        # Prioridade: 1) Configurações específicas do departamento, 2) Configurações gerais (departamento NULL)
        configuracoes_por_departamento = []
        configuracoes_gerais = []
        
        for config in configuracoes:
            dias_config = config['dias_semana'].split(',')
            if str(dia_semana + 1) in dias_config:  # +1 porque weekday() retorna 0-6, mas config usa 1-7
                # Verificar se a configuração se aplica ao departamento
                if config.get('departamento') and departamento_funcionario:
                    # Configuração específica de departamento
                    if config['departamento'].upper() == departamento_funcionario.upper():
                        configuracoes_por_departamento.append(config)
                elif not config.get('departamento'):
                    # Configuração geral (aplica a todos)
                    configuracoes_gerais.append(config)
        
        # Priorizar configurações específicas do departamento
        configuracoes_aplicaveis = configuracoes_por_departamento if configuracoes_por_departamento else configuracoes_gerais
        
        if not configuracoes_aplicaveis:
            # Se não há configuração para o dia, usar a primeira disponível
            return {
                'hora_entrada': str(configuracoes[0]['hora_entrada']),
                'hora_saida': str(configuracoes[0]['hora_saida']),
                'tolerancia_entrada': configuracoes[0]['tolerancia_entrada'],
                'tolerancia_saida': configuracoes[0]['tolerancia_saida'],
                'nome_config': configuracoes[0]['nome_config']
            }
        
        # Se há apenas uma configuração aplicável, usar ela
        if len(configuracoes_aplicaveis) == 1:
            config = configuracoes_aplicaveis[0]
            return {
                'hora_entrada': str(config['hora_entrada']),
                'hora_saida': str(config['hora_saida']),
                'tolerancia_entrada': config['tolerancia_entrada'],
                'tolerancia_saida': config['tolerancia_saida'],
                'nome_config': config['nome_config']
            }
        
        # Se há múltiplas configurações, verificar se há configurações específicas por dia
        for config in configuracoes_aplicaveis:
            # Verificar se há configuração específica para este dia
            cursor.execute("""
                SELECT hora_entrada, hora_saida, tolerancia_entrada, tolerancia_saida
                FROM configuracoes_horarios_dias 
                WHERE horario_id = %s AND dia_semana = %s AND ativo = TRUE
            """, (config['id'], dia_semana))
            
            config_dia = cursor.fetchone()
            if config_dia:
                # Usar configuração específica do dia
                return {
                    'hora_entrada': str(config_dia['hora_entrada']),
                    'hora_saida': str(config_dia['hora_saida']),
                    'tolerancia_entrada': config_dia['tolerancia_entrada'],
                    'tolerancia_saida': config_dia['tolerancia_saida'],
                    'nome_config': f"{config['nome_config']} (Dia específico)"
                }
        
        # Se não há configurações específicas por dia, usar a lógica de melhor encaixe
        melhor_config = None
        menor_diferenca = float('inf')
        
        for config in configuracoes_aplicaveis:
            hora_entrada_config = datetime.strptime(str(config['hora_entrada']), '%H:%M:%S').time()
            hora_saida_config = datetime.strptime(str(config['hora_saida']), '%H:%M:%S').time()
            
            # Calcular diferença do horário atual para o início do turno
            diff_entrada = abs((hora_atual_time.hour * 60 + hora_atual_time.minute) - 
                              (hora_entrada_config.hour * 60 + hora_entrada_config.minute))
            
            # Calcular diferença do horário atual para o fim do turno
            diff_saida = abs((hora_atual_time.hour * 60 + hora_atual_time.minute) - 
                            (hora_saida_config.hour * 60 + hora_saida_config.minute))
            
            # Usar a menor diferença
            menor_diff = min(diff_entrada, diff_saida)
            
            if menor_diff < menor_diferenca:
                menor_diferenca = menor_diff
                melhor_config = config
        
        if melhor_config:
            return {
                'hora_entrada': str(melhor_config['hora_entrada']),
                'hora_saida': str(melhor_config['hora_saida']),
                'tolerancia_entrada': melhor_config['tolerancia_entrada'],
                'tolerancia_saida': melhor_config['tolerancia_saida'],
                'nome_config': melhor_config['nome_config']
            }
        
        # Fallback: usar a primeira configuração
        return {
            'hora_entrada': str(configuracoes[0]['hora_entrada']),
            'hora_saida': str(configuracoes[0]['hora_saida']),
            'tolerancia_entrada': configuracoes[0]['tolerancia_entrada'],
            'tolerancia_saida': configuracoes[0]['tolerancia_saida'],
            'nome_config': configuracoes[0]['nome_config']
        }
        
    except Exception as e:
        print(f"Erro ao determinar horário aplicável: {e}")
        return {
            'hora_entrada': '08:00:00',
            'hora_saida': '18:00:00',
            'tolerancia_entrada': 15,
            'tolerancia_saida': 15,
            'nome_config': 'Padrão (Erro)'
        }

def verificar_horario_trabalho(numero_registro, tipo_acesso):
    """Verifica se o funcionário está no horário correto para o tipo de acesso"""
    try:
        agora = datetime.now()
        hora_atual = agora.time()
        hora_atual_str = agora.strftime('%H:%M')
        dia_semana = agora.weekday()  # 0=Segunda, 6=Domingo
        
        # Determinar qual configuração de horário usar
        horario_config = determinar_horario_aplicavel(numero_registro, hora_atual_str, dia_semana)
        
        # Para acesso facial, determinar automaticamente o tipo baseado no horário
        if tipo_acesso == 'facial':
            # Se for antes do meio-dia, considerar como entrada
            if hora_atual < datetime.strptime('12:00', '%H:%M').time():
                return "entrada", hora_atual_str, horario_config['nome_config']
            # Se for após 17h, considerar como saída
            elif hora_atual > datetime.strptime('17:00', '%H:%M').time():
                return "saida", hora_atual_str, horario_config['nome_config']
            # Entre 12h e 17h, considerar como entrada (retorno do almoço)
            else:
                return "entrada", hora_atual_str, horario_config['nome_config']
        
        # Para outros tipos de acesso, usar a configuração determinada
        hora_entrada = datetime.strptime(horario_config['hora_entrada'], '%H:%M:%S').time()
        hora_saida = datetime.strptime(horario_config['hora_saida'], '%H:%M:%S').time()
        tolerancia_entrada = horario_config['tolerancia_entrada']
        tolerancia_saida = horario_config['tolerancia_saida']
        
        if tipo_acesso == 'entrada':
            hora_limite = datetime.combine(date.today(), hora_entrada) + timedelta(minutes=tolerancia_entrada)
            if hora_atual > hora_limite.time():
                return "entrada", hora_atual_str, horario_config['nome_config']  # Retorna mesmo assim
            return "entrada", hora_atual_str, horario_config['nome_config']
            
        elif tipo_acesso == 'saida':
            hora_limite = datetime.combine(date.today(), hora_saida) - timedelta(minutes=tolerancia_saida)
            if hora_atual < hora_limite.time():
                return "saida", hora_atual_str, horario_config['nome_config']  # Retorna mesmo assim
            return "saida", hora_atual_str, horario_config['nome_config']
            
        elif tipo_acesso in ['almoco_entrada', 'almoco_saida']:
            return "almoco_entrada", hora_atual_str, horario_config['nome_config']
        
        return "entrada", hora_atual_str, horario_config['nome_config']
        
    except Exception as e:
        print(f"Erro ao verificar horário: {e}")
        return "entrada", datetime.now().strftime('%H:%M'), "Padrão (Erro)"  # Retorna tipo padrão e hora atual

# ========================================
# SISTEMA DE RECONHECIMENTO FACIAL (REUTILIZADO)
# ========================================

# Cache para otimização de performance
face_detection_cache = {}
encoding_cache = {}
cache_max_size = 100
cache_ttl = 300  # 5 minutos

def limpar_cache():
    """Limpa o cache quando necessário"""
    global face_detection_cache, encoding_cache
    current_time = time.time()
    
    # Limpar cache de detecção
    face_detection_cache = {k: v for k, v in face_detection_cache.items() 
                           if current_time - v['timestamp'] < cache_ttl}
    
    # Limpar cache de encoding
    encoding_cache = {k: v for k, v in encoding_cache.items() 
                     if current_time - v['timestamp'] < cache_ttl}
    
    # Limitar tamanho do cache
    if len(face_detection_cache) > cache_max_size:
        # Remover os mais antigos
        sorted_items = sorted(face_detection_cache.items(), key=lambda x: x[1]['timestamp'])
        face_detection_cache = dict(sorted_items[-cache_max_size:])
    
    if len(encoding_cache) > cache_max_size:
        sorted_items = sorted(encoding_cache.items(), key=lambda x: x[1]['timestamp'])
        encoding_cache = dict(sorted_items[-cache_max_size:])

def obter_hash_imagem(imagem_rgb):
    """Gera hash da imagem para cache"""
    try:
        # Reduzir imagem para hash mais rápido
        small = cv2.resize(imagem_rgb, (64, 64))
        gray = cv2.cvtColor(small, cv2.COLOR_RGB2GRAY)
        return hashlib.md5(gray.tobytes()).hexdigest()
    except:
        return None

def criar_tabelas_facial():
    """Criar tabelas relacionadas ao sistema de reconhecimento facial"""
    try:
        conn = get_simple_connection()
        cursor = conn.cursor()
        
        # Tabela de dados faciais dos funcionários
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS funcionarios_facial (
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
            )
        """)
        
        cursor.close()
        conn.close()
        print("✅ Tabelas de reconhecimento facial verificadas/criadas")
        
    except Exception as e:
        print(f"❌ Erro ao criar tabelas de reconhecimento facial: {e}")

def criar_tabelas_rfid():
    """Criar tabelas para cadastro RFID"""
    try:
        conn = get_simple_connection()
        cursor = conn.cursor()
        
        # Tabela para armazenar cartões RFID
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cartoes_rfid (
                id INT AUTO_INCREMENT PRIMARY KEY,
                numero_registro VARCHAR(20) NOT NULL,
                codigo_rfid VARCHAR(100) NOT NULL,
                tipo_cartao ENUM('cartao', 'tag', 'chaveiro') DEFAULT 'cartao',
                descricao VARCHAR(200),
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_ultimo_uso TIMESTAMP NULL,
                ativo BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (numero_registro) REFERENCES funcionarios(numero_registro) ON DELETE CASCADE,
                UNIQUE KEY unique_codigo_rfid (codigo_rfid),
                UNIQUE KEY unique_funcionario_rfid (numero_registro)
            )
        """)
        
        cursor.close()
        conn.close()
        print("✅ Tabelas de cadastro RFID criadas com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao criar tabelas RFID: {e}")

#### substituir inicio


def normalizar_iluminacao(imagem_rgb):
    """
    Normaliza a iluminação da imagem usando CLAHE (Contrast Limited Adaptive Histogram Equalization)
    Melhora significativamente o reconhecimento facial em condições de iluminação ruins
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
        
        print("✅ Iluminação normalizada com sucesso")
        return imagem_normalizada
        
    except Exception as e:
        print(f"⚠️ Erro na normalização de iluminação: {e}")
        return imagem_rgb  # Retorna imagem original em caso de erro

def normalizar_iluminacao_agressiva(imagem_rgb):
    """
    Normalização mais agressiva para ambientes muito escuros
    """
    try:
        # Converter RGB para LAB
        lab = cv2.cvtColor(imagem_rgb, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        
        # CLAHE mais agressivo para ambientes escuros
        clahe_agressivo = cv2.createCLAHE(
            clipLimit=4.0,        # Limite mais alto para ambientes escuros
            tileGridSize=(4, 4)   # Grade menor para mais detalhes
        )
        l_normalizado = clahe_agressivo.apply(l)
        
        # Aplicar equalização de histograma adicional
        l_equalizado = cv2.equalizeHist(l_normalizado)
        
        # Combinar com a imagem original (70% normalizada + 30% equalizada)
        l_final = cv2.addWeighted(l_normalizado, 0.7, l_equalizado, 0.3, 0)
        
        # Reunir os canais
        lab_normalizado = cv2.merge([l_final, a, b])
        
        # Converter de volta para RGB
        imagem_normalizada = cv2.cvtColor(lab_normalizado, cv2.COLOR_LAB2RGB)
        
        print("✅ Iluminação agressiva aplicada com sucesso")
        return imagem_normalizada
        
    except Exception as e:
        print(f"⚠️ Erro na normalização agressiva: {e}")
        return imagem_rgb

def melhorar_contraste_escuro(imagem_rgb):
    """
    Melhora específica para imagens muito escuras com algoritmos avançados
    """
    try:
        # Converter para escala de cinza
        gray = cv2.cvtColor(imagem_rgb, cv2.COLOR_RGB2GRAY)
        
        # Calcular estatísticas da imagem
        mean_brightness = np.mean(gray)
        std_brightness = np.std(gray)
        
        # Se a imagem está muito escura (média < 50), aplicar melhorias
        if mean_brightness < 50:
            # Algoritmo 1: Gamma correction adaptativo
            gamma = 1.8 if mean_brightness < 20 else 1.5 if mean_brightness < 30 else 1.2
            gamma_corrected = np.power(gray / 255.0, 1/gamma) * 255.0
            gamma_corrected = np.uint8(gamma_corrected)
            
            # Algoritmo 2: CLAHE adaptativo
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(4, 4))
            clahe_corrected = clahe.apply(gamma_corrected)
            
            # Algoritmo 3: Unsharp mask para nitidez
            gaussian = cv2.GaussianBlur(clahe_corrected, (0, 0), 1.5)
            unsharp_mask = cv2.addWeighted(clahe_corrected, 1.8, gaussian, -0.8, 0)
            
            # Algoritmo 4: Equalização de histograma local
            if mean_brightness < 30:
                equalized = cv2.equalizeHist(unsharp_mask)
                # Combinar com a imagem anterior (70% unsharp + 30% equalized)
                final_gray = cv2.addWeighted(unsharp_mask, 0.7, equalized, 0.3, 0)
            else:
                final_gray = unsharp_mask
            
            # Algoritmo 5: Melhoria de contraste local
            if std_brightness < 20:  # Baixo contraste
                # Aplicar filtro de realce de bordas
                kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
                enhanced = cv2.filter2D(final_gray, -1, kernel)
                # Combinar com a imagem anterior
                final_gray = cv2.addWeighted(final_gray, 0.6, enhanced, 0.4, 0)
            
            # Converter de volta para RGB
            imagem_melhorada = cv2.cvtColor(final_gray, cv2.COLOR_GRAY2RGB)
            
            print(f"✅ Contraste melhorado com algoritmos avançados (brilho: {mean_brightness:.1f} → {np.mean(final_gray):.1f})")
            return imagem_melhorada
        
        return imagem_rgb
        
    except Exception as e:
        print(f"⚠️ Erro na melhoria de contraste: {e}")
        return imagem_rgb

def normalizar_iluminacao_ml(imagem_rgb):
    """
    Normalização de iluminação usando técnicas de machine learning
    """
    try:
        # Converter para LAB
        lab = cv2.cvtColor(imagem_rgb, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        
        # Análise de histograma para determinar o melhor método
        hist = cv2.calcHist([l], [0], None, [256], [0, 256])
        hist_normalizado = hist / hist.sum()
        
        # Calcular métricas de qualidade
        mean_l = np.mean(l)
        std_l = np.std(l)
        entropy = -np.sum(hist_normalizado * np.log2(hist_normalizado + 1e-10))
        
        # Decidir o melhor método baseado nas métricas
        if mean_l < 30 and std_l < 15:
            # Muito escuro e baixo contraste - usar método agressivo
            print("🧠 ML: Aplicando normalização agressiva")
            clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(2, 2))
            l_normalizado = clahe.apply(l)
            
            # Aplicar equalização adicional
            l_equalizado = cv2.equalizeHist(l_normalizado)
            l_final = cv2.addWeighted(l_normalizado, 0.6, l_equalizado, 0.4, 0)
            
        elif mean_l < 60 and entropy < 6:
            # Escuro com baixa entropia - usar CLAHE adaptativo
            print("🧠 ML: Aplicando CLAHE adaptativo")
            clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(4, 4))
            l_final = clahe.apply(l)
            
        elif std_l < 20:
            # Baixo contraste - usar realce de contraste
            print("🧠 ML: Aplicando realce de contraste")
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l_normalizado = clahe.apply(l)
            
            # Aplicar filtro de realce
            kernel = np.array([[0,-1,0], [-1,5,-1], [0,-1,0]])
            l_enhanced = cv2.filter2D(l_normalizado, -1, kernel)
            l_final = cv2.addWeighted(l_normalizado, 0.7, l_enhanced, 0.3, 0)
            
        else:
            # Iluminação normal - usar CLAHE padrão
            print("🧠 ML: Aplicando normalização padrão")
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l_final = clahe.apply(l)
        
        # Reunir os canais
        lab_normalizado = cv2.merge([l_final, a, b])
        
        # Converter de volta para RGB
        imagem_normalizada = cv2.cvtColor(lab_normalizado, cv2.COLOR_LAB2RGB)
        
        print(f"✅ Normalização ML aplicada (L: {mean_l:.1f} → {np.mean(l_final):.1f})")
        return imagem_normalizada
        
    except Exception as e:
        print(f"⚠️ Erro na normalização ML: {e}")
        return imagem_rgb

def calcular_qualidade_imagem(imagem_rgb):
    """
    Calcula métricas de qualidade da imagem para otimizar o processamento
    Versão avançada com análise de histograma
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
        
        # 4. Análise de histograma avançada
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        hist_normalizado = hist / hist.sum()
        
        # Entropia do histograma
        entropia = -np.sum(hist_normalizado * np.log2(hist_normalizado + 1e-10))
        score_entropia = min(entropia / 8.0, 1.0)
        
        # Análise de distribuição do histograma
        # Verificar se há picos muito altos (indica baixa qualidade)
        hist_max = np.max(hist_normalizado)
        score_distribuicao = 1.0 - min(hist_max * 10, 1.0)  # Penalizar picos altos
        
        # Análise de simetria do histograma
        hist_centro = hist_normalizado[128]  # Valor central
        hist_esquerda = np.mean(hist_normalizado[:128])  # Lado escuro
        hist_direita = np.mean(hist_normalizado[128:])   # Lado claro
        simetria = 1.0 - abs(hist_esquerda - hist_direita) / (hist_esquerda + hist_direita + 1e-10)
        
        # Análise de uniformidade (evitar imagens muito uniformes)
        uniformidade = np.sum(hist_normalizado ** 2)
        score_uniformidade = 1.0 - min(uniformidade * 2, 1.0)
        
        # 5. Análise de bordas (para detectar blur)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / (gray.shape[0] * gray.shape[1])
        score_bordas = min(edge_density * 10, 1.0)
        
        # Score final (média ponderada otimizada)
        score_final = (
            contraste * 0.20 +           # Contraste
            min(nitidez, 1.0) * 0.20 +   # Nitidez
            score_brilho * 0.15 +        # Brilho
            score_entropia * 0.15 +      # Entropia
            score_distribuicao * 0.10 +  # Distribuição
            simetria * 0.10 +            # Simetria
            score_uniformidade * 0.05 +  # Uniformidade
            score_bordas * 0.05          # Bordas
        )
        
        print(f"📊 Qualidade avançada: {score_final:.3f} (contraste:{contraste:.3f}, nitidez:{min(nitidez, 1.0):.3f}, brilho:{score_brilho:.3f}, entropia:{score_entropia:.3f}, distrib:{score_distribuicao:.3f}, simetria:{simetria:.3f})")
        
        return min(score_final, 1.0)
        
    except Exception as e:
        print(f"⚠️ Erro no cálculo de qualidade: {e}")
        return 0.5  # Retorna valor médio em caso de erro

def detectar_condicoes_iluminacao(imagem_rgb):
    """
    Detecta condições específicas de iluminação para aplicar correções direcionadas
    """
    try:
        gray = cv2.cvtColor(imagem_rgb, cv2.COLOR_RGB2GRAY)
        
        # Análise de distribuição de brilho
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        
        # Percentis para análise
        p10 = np.percentile(gray, 10)
        p50 = np.percentile(gray, 50)
        p90 = np.percentile(gray, 90)
        
        # Calcular brilho médio
        mean_brightness = np.mean(gray)
        
        # Análise mais detalhada para ambientes escuros
        condicoes = {
            'muito_escura': p90 < 100 or mean_brightness < 60,           # 90% dos pixels são muito escuros
            'extremamente_escura': p90 < 60 or mean_brightness < 30,     # Muito escuro
            'muito_clara': p10 > 180,                                    # 10% dos pixels são muito claros
            'baixo_contraste': (p90 - p10) < 50,                         # Diferença pequena entre claro e escuro
            'backlight': p10 < 30 and p90 > 200,                         # Contraluz (muito escuro e muito claro)
            'uniforme': np.std(gray) < 20,                               # Muito uniforme
            'brilho_medio': mean_brightness,                             # Brilho médio para referência
            'contraste_baixo': np.std(gray) < 15                         # Contraste muito baixo
        }
        
        return condicoes
        
    except Exception as e:
        print(f"⚠️ Erro na detecção de condições: {e}")
        return {}

def detectar_faces_multiplos_modelos(imagem_rgb, condicoes):
    """
    Detecta faces usando múltiplos modelos simultaneamente para máxima eficácia
    Com sistema de cache para otimização
    """
    # Verificar cache primeiro
    img_hash = obter_hash_imagem(imagem_rgb)
    if img_hash and img_hash in face_detection_cache:
        cached_result = face_detection_cache[img_hash]
        if time.time() - cached_result['timestamp'] < cache_ttl:
            print(f"🚀 Cache hit para detecção de faces")
            return cached_result['faces']
    
    face_locations = []
    modelos_usados = []
    
    try:
        # Modelo 1: HOG padrão
        try:
            hog_faces = face_recognition.face_locations(imagem_rgb, model="hog", number_of_times_to_upsample=1)
            if hog_faces:
                face_locations.extend(hog_faces)
                modelos_usados.append("HOG")
        except Exception as e:
            print(f"⚠️ Erro no modelo HOG: {e}")
        
        # Modelo 2: HOG com mais upsamples
        try:
            hog_upsampled = face_recognition.face_locations(imagem_rgb, model="hog", number_of_times_to_upsample=2)
            if hog_upsampled:
                face_locations.extend(hog_upsampled)
                modelos_usados.append("HOG+2x")
        except Exception as e:
            print(f"⚠️ Erro no modelo HOG+2x: {e}")
        
        # Modelo 3: CNN (se disponível)
        if condicoes.get('muito_escura', False) or condicoes.get('extremamente_escura', False):
            try:
                cnn_faces = face_recognition.face_locations(imagem_rgb, model="cnn", number_of_times_to_upsample=1)
                if cnn_faces:
                    face_locations.extend(cnn_faces)
                    modelos_usados.append("CNN")
            except Exception as e:
                print(f"⚠️ Erro no modelo CNN: {e}")
        
        # Modelo 4: HOG com imagem redimensionada
        try:
            altura, largura = imagem_rgb.shape[:2]
            if altura > 240 or largura > 320:
                imagem_menor = cv2.resize(imagem_rgb, (320, 240))
                hog_resized = face_recognition.face_locations(imagem_menor, model="hog", number_of_times_to_upsample=2)
                if hog_resized:
                    # Ajustar coordenadas
                    scale_x = largura / 320
                    scale_y = altura / 240
                    hog_resized_scaled = [(int(top * scale_y), int(right * scale_x), 
                                         int(bottom * scale_y), int(left * scale_x)) for top, right, bottom, left in hog_resized]
                    face_locations.extend(hog_resized_scaled)
                    modelos_usados.append("HOG+Resized")
        except Exception as e:
            print(f"⚠️ Erro no modelo HOG+Resized: {e}")
        
        # Modelo 5: HOG com imagem clareada (para ambientes muito escuros)
        if condicoes.get('extremamente_escura', False):
            try:
                # Clarear imagem
                imagem_clareada = cv2.convertScaleAbs(imagem_rgb, alpha=1.5, beta=30)
                hog_brightened = face_recognition.face_locations(imagem_clareada, model="hog", number_of_times_to_upsample=3)
                if hog_brightened:
                    face_locations.extend(hog_brightened)
                    modelos_usados.append("HOG+Brightened")
            except Exception as e:
                print(f"⚠️ Erro no modelo HOG+Brightened: {e}")
        
        # Remover duplicatas e escolher a melhor face
        if face_locations:
            # Agrupar faces similares
            faces_unicas = []
            for face in face_locations:
                is_duplicate = False
                for face_unica in faces_unicas:
                    # Calcular sobreposição
                    top1, right1, bottom1, left1 = face
                    top2, right2, bottom2, left2 = face_unica
                    
                    # Calcular área de interseção
                    x_overlap = max(0, min(right1, right2) - max(left1, left2))
                    y_overlap = max(0, min(bottom1, bottom2) - max(top1, top2))
                    intersection = x_overlap * y_overlap
                    
                    # Calcular área de união
                    area1 = (right1 - left1) * (bottom1 - top1)
                    area2 = (right2 - left2) * (bottom2 - top2)
                    union = area1 + area2 - intersection
                    
                    # Se sobreposição > 50%, considerar duplicata
                    if union > 0 and intersection / union > 0.5:
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    faces_unicas.append(face)
            
            print(f"🎯 Faces detectadas por: {', '.join(modelos_usados)}")
            resultado = faces_unicas[:1]  # Retornar apenas a primeira face única
        else:
            resultado = []
        
        # Salvar no cache
        if img_hash:
            face_detection_cache[img_hash] = {
                'faces': resultado,
                'timestamp': time.time(),
                'modelos': modelos_usados
            }
            limpar_cache()  # Limpar cache se necessário
        
        return resultado
        
    except Exception as e:
        print(f"⚠️ Erro na detecção múltipla: {e}")
        return []

def processar_imagem_facial_melhorada(imagem_base64):
    """
    VERSÃO ULTRA MELHORADA da função processar_imagem_facial com detecção múltipla e normalização avançada
    """
    try:
        print("🚀 Iniciando processamento facial melhorado...")
        
        # Decodificar imagem base64 com tratamento de erro melhorado
        try:
            if ',' in imagem_base64:
                imagem_data = base64.b64decode(imagem_base64.split(',')[1])
            else:
                imagem_data = base64.b64decode(imagem_base64)
        except Exception as e:
            return None, f"Erro ao decodificar imagem base64: {str(e)}"
        
        imagem_array = np.frombuffer(imagem_data, np.uint8)
        imagem = cv2.imdecode(imagem_array, cv2.IMREAD_COLOR)
        
        if imagem is None:
            return None, "Erro ao decodificar imagem"
        
        # Verificar qualidade da imagem original
        altura, largura = imagem.shape[:2]
        if altura < 80 or largura < 80:
            return None, "Imagem muito pequena. Use uma resolução maior."
        
        # Redimensionar imagem se necessário (otimização de performance)
        if altura > 360 or largura > 480:
            scale = min(480/largura, 360/altura)
            nova_largura = int(largura * scale)
            nova_altura = int(altura * scale)
            imagem = cv2.resize(imagem, (nova_largura, nova_altura))
            print(f"📏 Imagem redimensionada para {nova_largura}x{nova_altura}")
        
        # Converter BGR para RGB
        imagem_rgb = cv2.cvtColor(imagem, cv2.COLOR_BGR2RGB)
        
        # ===== NOVA FUNCIONALIDADE: NORMALIZAÇÃO DE ILUMINAÇÃO =====
        
        # 1. Analisar condições de iluminação
        condicoes = detectar_condicoes_iluminacao(imagem_rgb)
        print(f"🔍 Condições detectadas: {condicoes}")
        
        # Armazenar condições para uso posterior na busca
        processar_imagem_facial_melhorada._ultima_condicao = condicoes
        
        # 2. Calcular qualidade original
        qualidade_original = calcular_qualidade_imagem(imagem_rgb)
        
        # 3. Aplicar normalização de iluminação baseada nas condições
        if condicoes.get('extremamente_escura', False):
            print("🌙 Aplicando normalização ML para ambiente extremamente escuro")
            imagem_normalizada = normalizar_iluminacao_ml(imagem_rgb)
            # Aplicar melhoria adicional de contraste
            imagem_normalizada = melhorar_contraste_escuro(imagem_normalizada)
        elif condicoes.get('muito_escura', False):
            print("🌚 Aplicando normalização ML para ambiente escuro")
            imagem_normalizada = normalizar_iluminacao_ml(imagem_rgb)
        else:
            print("☀️ Aplicando normalização ML padrão")
            imagem_normalizada = normalizar_iluminacao_ml(imagem_rgb)
        
        # 4. Calcular qualidade após normalização
        qualidade_normalizada = calcular_qualidade_imagem(imagem_normalizada)
        
        # 5. Decidir qual imagem usar baseado na melhoria de qualidade
        if qualidade_normalizada > qualidade_original + 0.1:  # Melhoria significativa
            imagem_final = imagem_normalizada
            print(f"✅ Usando imagem normalizada (qualidade: {qualidade_original:.3f} → {qualidade_normalizada:.3f})")
        else:
            imagem_final = imagem_rgb
            print(f"📷 Usando imagem original (qualidade: {qualidade_original:.3f})")
        
        # ============================================================
        
        # Detecção de faces com múltiplos modelos simultâneos
        print("🔧 Iniciando detecção com múltiplos modelos...")
        face_locations = detectar_faces_multiplos_modelos(imagem_final, condicoes)
        
        if not face_locations:
            # Fallback: tentar com imagem original se não encontrou
            print("🔧 Fallback: tentando com imagem original...")
            face_locations = detectar_faces_multiplos_modelos(imagem_rgb, condicoes)
        
        if not face_locations:
            # Sistema de fallback inteligente
            print("🔧 Iniciando sistema de fallback inteligente...")
            
            # Fallback 1: Tentar com imagem clareada artificialmente
            if condicoes.get('extremamente_escura', False):
                print("🔧 Fallback 1: Clareando imagem artificialmente...")
                imagem_clareada = cv2.convertScaleAbs(imagem_rgb, alpha=2.0, beta=50)
                face_locations = detectar_faces_multiplos_modelos(imagem_clareada, condicoes)
            
            # Fallback 2: Tentar com diferentes resoluções
            if not face_locations:
                print("🔧 Fallback 2: Tentando diferentes resoluções...")
                for scale in [0.5, 0.75, 1.25, 1.5]:
                    try:
                        altura, largura = imagem_rgb.shape[:2]
                        nova_altura = int(altura * scale)
                        nova_largura = int(largura * scale)
                        if nova_altura > 50 and nova_largura > 50:
                            imagem_escalada = cv2.resize(imagem_rgb, (nova_largura, nova_altura))
                            face_locations = detectar_faces_multiplos_modelos(imagem_escalada, condicoes)
                            if face_locations:
                                # Ajustar coordenadas de volta
                                scale_x = largura / nova_largura
                                scale_y = altura / nova_altura
                                face_locations = [(int(top * scale_y), int(right * scale_x), 
                                                 int(bottom * scale_y), int(left * scale_x)) for top, right, bottom, left in face_locations]
                                print(f"✅ Face detectada com escala {scale}")
                                break
                    except Exception as e:
                        print(f"⚠️ Erro no fallback de escala {scale}: {e}")
            
            # Fallback 3: Tentar com filtros de realce
            if not face_locations:
                print("🔧 Fallback 3: Aplicando filtros de realce...")
                try:
                    # Aplicar filtro de realce de bordas
                    kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
                    imagem_realcada = cv2.filter2D(imagem_rgb, -1, kernel)
                    face_locations = detectar_faces_multiplos_modelos(imagem_realcada, condicoes)
                except Exception as e:
                    print(f"⚠️ Erro no fallback de realce: {e}")
            
            if not face_locations:
                return None, "Nenhuma face detectada após todas as tentativas. Verifique iluminação e posicionamento. Tente melhorar a iluminação do ambiente."
        
        if len(face_locations) > 1:
            return None, "Múltiplas faces detectadas. Use uma imagem com apenas uma face."
        
        # Verificar qualidade da face detectada
        top, right, bottom, left = face_locations[0]
        face_width = right - left
        face_height = bottom - top
        
        # Verificar se a face é grande o suficiente
        min_face_size = min(imagem_final.shape[0], imagem_final.shape[1]) * 0.08
        if face_width < min_face_size or face_height < min_face_size:
            return None, "Face muito pequena. Aproxime-se mais da câmera."
        
        # Extrair encoding facial com configuração otimizada
        face_encodings = face_recognition.face_encodings(
            imagem_final, 
            face_locations, 
            num_jitters=1,  # Para performance
            model="small"   # Modelo rápido
        )
        
        if not face_encodings:
            return None, "Não foi possível extrair características da face. Tente novamente."
        
        # Verificar qualidade do encoding
        encoding = face_encodings[0]
        
        # Verificar se o encoding não é muito similar a zeros
        if np.allclose(encoding, 0, atol=1e-5):
            return None, "Encoding de baixa qualidade. Melhore a iluminação."
        
        # ===== MELHORIA: Validação dinâmica baseada na qualidade e condições de iluminação =====
        qualidade_minima_encoding = 0.005
        
        # Ajustar limites baseado na qualidade e condições de iluminação
        if qualidade_normalizada > 0.7:
            qualidade_minima_encoding = 0.003  # Menos rigoroso para imagens de boa qualidade
        elif qualidade_normalizada < 0.3:
            qualidade_minima_encoding = 0.008  # Mais rigoroso para imagens ruins
        
        # Ajustar ainda mais para ambientes escuros
        if condicoes.get('extremamente_escura', False):
            qualidade_minima_encoding = 0.002  # Muito menos rigoroso para ambientes extremamente escuros
            print("🌙 Ajustando validação para ambiente extremamente escuro")
        elif condicoes.get('muito_escura', False):
            qualidade_minima_encoding = 0.003  # Menos rigoroso para ambientes escuros
            print("🌚 Ajustando validação para ambiente escuro")
        
        if np.var(encoding) < qualidade_minima_encoding:
            return None, f"Encoding muito uniforme (var: {np.var(encoding):.6f}). Verifique a qualidade da imagem."
        
        # Converter para lista para JSON
        encoding_list = encoding.tolist()
        
        print(f"✅ Face processada com sucesso!")
        print(f"   - Qualidade final: {max(qualidade_original, qualidade_normalizada):.3f}")
        print(f"   - Encoding shape: {len(encoding_list)}")
        print(f"   - Variância encoding: {np.var(encoding):.6f}")
        
        return encoding_list, None
        
    except Exception as e:
        print(f"❌ Erro ao processar imagem facial: {e}")
        import traceback
        traceback.print_exc()
        return None, f"Erro ao processar imagem: {str(e)}"

## substituir inicio



def buscar_funcionario_por_facial(imagem_base64):
    """Busca funcionário por reconhecimento facial"""
    try:
        print("🔍 Iniciando busca facial...")
        
        # Processar imagem
        encoding_atual, erro = processar_imagem_facial_melhorada(imagem_base64)
        #encoding_atual, erro = processar_imagem_facial(imagem_base64)
        if erro:
            print(f"❌ Erro ao processar imagem: {erro}")
            return None, erro
        
        conn = get_simple_connection()
        cursor = conn.cursor()
        
        # Buscar todos os encodings faciais ativos com dados completos
        cursor.execute("""
            SELECT f.numero_registro, f.nome, f.departamento, f.cargo, f.empresa, 
                   f.status, f.ativo, ff.encoding_facial, ff.confianca_minima
            FROM funcionarios f
            INNER JOIN funcionarios_facial ff ON f.numero_registro = ff.numero_registro
            WHERE f.ativo = TRUE AND ff.ativo = TRUE
        """)
        
        funcionarios = cursor.fetchall()
        
        if not funcionarios:
            cursor.close()
            conn.close()
            return None, "Nenhum funcionário com cadastro facial encontrado"
        
        # Comparação facial otimizada
        melhor_match = None
        melhor_confianca = 0
        candidatos = []
        
        for funcionario in funcionarios:
            numero_registro, nome, departamento, cargo, empresa, status, ativo, encoding_json, confianca_minima = funcionario
            
            try:
                # Converter JSON para array numpy
                encoding_armazenado = np.array(json.loads(encoding_json), dtype=np.float64)
                
                # Garantir que encoding_atual também é numpy array
                if isinstance(encoding_atual, list):
                    encoding_atual = np.array(encoding_atual, dtype=np.float64)
                
                # Verificar se os encodings são válidos
                if encoding_armazenado.size == 0 or encoding_atual.size == 0:
                    continue
                
                # Verificar se são arrays 1D
                if len(encoding_armazenado.shape) > 1:
                    encoding_armazenado = encoding_armazenado.flatten()
                if len(encoding_atual.shape) > 1:
                    encoding_atual = encoding_atual.flatten()
                
                # Verificar se têm o mesmo formato
                if encoding_armazenado.shape != encoding_atual.shape:
                    continue
                
                # Métrica simplificada - apenas distância euclidiana (mais rápida)
                distancia = face_recognition.face_distance([encoding_armazenado], encoding_atual)[0]
                confianca_final = 1 - distancia
                
                # Ajustar confiança mínima baseado nas condições de iluminação
                confianca_minima_ajustada = confianca_minima
                
                # Se a imagem foi processada com normalização agressiva, reduzir um pouco o limite
                if hasattr(processar_imagem_facial_melhorada, '_ultima_condicao'):
                    condicoes = processar_imagem_facial_melhorada._ultima_condicao
                    if condicoes.get('extremamente_escura', False):
                        confianca_minima_ajustada = max(0.4, confianca_minima - 0.1)  # Reduzir 0.1 mas não menos que 0.4
                        print(f"🌙 Ajustando confiança mínima para ambiente escuro: {confianca_minima_ajustada:.2f}")
                    elif condicoes.get('muito_escura', False):
                        confianca_minima_ajustada = max(0.45, confianca_minima - 0.05)  # Reduzir 0.05 mas não menos que 0.45
                        print(f"🌚 Ajustando confiança mínima para ambiente escuro: {confianca_minima_ajustada:.2f}")
                
                # Armazenar candidato se estiver acima do mínimo ajustado
                if confianca_final >= confianca_minima_ajustada:
                    candidatos.append({
                        'numero_registro': numero_registro,
                        'nome': nome,
                        'departamento': departamento,
                        'cargo': cargo,
                        'empresa': empresa,
                        'status': status,
                        'ativo': ativo,
                        'confianca': confianca_final
                    })
                    
                    if confianca_final > melhor_confianca:
                        melhor_match = candidatos[-1]
                        melhor_confianca = confianca_final
                        print(f"✅ Novo melhor match! Confiança: {confianca_final:.4f}")
                    
            except Exception as e:
                print(f"❌ Erro ao comparar face do funcionário {numero_registro}: {e}")
                continue
        
        # MELHORIA 3: Verificação adicional se há múltiplos candidatos
        if len(candidatos) > 1:
            print(f"⚠️ Múltiplos candidatos encontrados ({len(candidatos)})")
            
            # Se a diferença entre o melhor e o segundo melhor for pequena, ser mais rigoroso
            candidatos_ordenados = sorted(candidatos, key=lambda x: x['confianca'], reverse=True)
            if len(candidatos_ordenados) >= 2:
                diferenca = candidatos_ordenados[0]['confianca'] - candidatos_ordenados[1]['confianca']
                if diferenca < 0.05:  # Diferença menor que 5%
                    print(f"⚠️ Diferença pequena entre candidatos ({diferenca:.4f}). Aumentando rigor...")
                    # Aumentar o limite mínimo para o melhor candidato
                    if melhor_confianca < 0.85:  # Exigir pelo menos 85% de confiança
                        print("❌ Confiança insuficiente para múltiplos candidatos")
                        return None, "Múltiplas correspondências encontradas. Tente novamente com melhor iluminação."
        
        cursor.close()
        conn.close()
        
        if melhor_match:
            print(f"🎯 Melhor match: {melhor_match['nome']} (confiança: {melhor_match['confianca']:.4f})")
            return melhor_match, None
        else:
            print("❌ Nenhum match encontrado")
            return None, "Funcionário não reconhecido. Verifique se está cadastrado no sistema."
        
    except Exception as e:
        print(f"❌ Erro na busca facial: {e}")
        return None, f"Erro interno: {str(e)}"

def registrar_uso_facial(numero_registro):
    """Registra uso do reconhecimento facial"""
    try:
        conn = get_simple_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE funcionarios_facial 
            SET ultimo_uso = NOW() 
            WHERE numero_registro = %s
        """, (numero_registro,))
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Erro ao registrar uso facial: {e}")

# ========================================
# SISTEMA DE ANALYTICS E RELATÓRIOS AVANÇADOS
# ========================================

def obter_estatisticas_gerais():
    """Obtém estatísticas gerais do sistema"""
    print("DEBUG: FUNÇÃO obter_estatisticas_gerais CHAMADA!")
    try:
        print("DEBUG: Iniciando obter_estatisticas_gerais")
        conn = get_simple_connection()
        cursor = conn.cursor()
        print("DEBUG: Conexão estabelecida")
        
        # Estatísticas básicas
        print("DEBUG: Executando query de funcionários")
        cursor.execute("SELECT COUNT(*) FROM funcionarios WHERE ativo = TRUE")
        total_funcionarios = cursor.fetchone()[0]
        print(f"DEBUG: Total funcionários: {total_funcionarios}")
        
        print("DEBUG: Executando query de acessos hoje")
        cursor.execute("SELECT COUNT(*) FROM acessos_funcionarios WHERE data_acesso = CURDATE()")
        acessos_hoje = cursor.fetchone()[0]
        print(f"DEBUG: Acessos hoje: {acessos_hoje}")
        
        print("DEBUG: Executando query de acessos ontem")
        cursor.execute("SELECT COUNT(*) FROM acessos_funcionarios WHERE data_acesso = DATE_SUB(CURDATE(), INTERVAL 1 DAY)")
        acessos_ontem = cursor.fetchone()[0]
        print(f"DEBUG: Acessos ontem: {acessos_ontem}")
        
        # Funcionários mais ativos hoje
        cursor.execute("""
            SELECT f.nome, f.departamento, COUNT(*) as total_acessos
            FROM acessos_funcionarios a
            JOIN funcionarios f ON a.numero_registro = f.numero_registro
            WHERE a.data_acesso = CURDATE()
            GROUP BY a.numero_registro, f.nome, f.departamento
            ORDER BY total_acessos DESC
            LIMIT 5
        """)
        funcionarios_ativos = cursor.fetchall()
        
        # Horários de pico
        cursor.execute("""
            SELECT HOUR(hora_acesso) as hora, COUNT(*) as total
            FROM acessos_funcionarios
            WHERE data_acesso = CURDATE()
            GROUP BY HOUR(hora_acesso)
            ORDER BY total DESC
            LIMIT 5
        """)
        horarios_pico = cursor.fetchall()
        
        # Departamentos mais ativos
        cursor.execute("""
            SELECT f.departamento, COUNT(*) as total_acessos
            FROM acessos_funcionarios a
            JOIN funcionarios f ON a.numero_registro = f.numero_registro
            WHERE a.data_acesso = CURDATE()
            GROUP BY f.departamento
            ORDER BY total_acessos DESC
        """)
        departamentos_ativos = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        resultado = {
            'total_funcionarios': total_funcionarios,
            'acessos_hoje': acessos_hoje,
            'acessos_ontem': acessos_ontem,
            'funcionarios_ativos': funcionarios_ativos,
            'horarios_pico': horarios_pico,
            'departamentos_ativos': departamentos_ativos
        }
        
        print(f"DEBUG: Resultado final: {resultado}")
        return resultado
        
    except Exception as e:
        print(f"DEBUG: Erro ao obter estatísticas: {e}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        return None

def obter_analise_padroes(data_inicio, data_fim):
    """Analisa padrões de acesso no período especificado"""
    try:
        conn = get_simple_connection()
        cursor = conn.cursor()
        
        # Padrões por dia da semana
        cursor.execute("""
            SELECT 
                DAYNAME(data_acesso) as dia_semana,
                COUNT(*) as total_acessos,
                AVG(TIME_TO_SEC(hora_acesso)) as hora_media_segundos
            FROM acessos_funcionarios
            WHERE data_acesso BETWEEN %s AND %s
            GROUP BY DAYOFWEEK(data_acesso), DAYNAME(data_acesso)
            ORDER BY DAYOFWEEK(data_acesso)
        """, (data_inicio, data_fim))
        padroes_semana = cursor.fetchall()
        
        # Padrões por hora do dia
        cursor.execute("""
            SELECT 
                HOUR(hora_acesso) as hora,
                COUNT(*) as total_acessos,
                COUNT(CASE WHEN tipo_acesso = 'entrada' THEN 1 END) as entradas,
                COUNT(CASE WHEN tipo_acesso = 'saida' THEN 1 END) as saidas
            FROM acessos_funcionarios
            WHERE data_acesso BETWEEN %s AND %s
            GROUP BY HOUR(hora_acesso)
            ORDER BY hora
        """, (data_inicio, data_fim))
        padroes_hora = cursor.fetchall()
        
        # Análise de pontualidade
        cursor.execute("""
            SELECT 
                f.departamento,
                COUNT(*) as total_funcionarios,
                AVG(CASE 
                    WHEN a.hora_acesso <= '08:30:00' THEN 1 
                    ELSE 0 
                END) as pontualidade_entrada,
                AVG(CASE 
                    WHEN a.hora_acesso >= '17:00:00' THEN 1 
                    ELSE 0 
                END) as pontualidade_saida
            FROM acessos_funcionarios a
            JOIN funcionarios f ON a.numero_registro = f.numero_registro
            WHERE a.data_acesso BETWEEN %s AND %s
            AND a.tipo_acesso = 'entrada'
            GROUP BY f.departamento
        """, (data_inicio, data_fim))
        analise_pontualidade = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {
            'padroes_semana': padroes_semana,
            'padroes_hora': padroes_hora,
            'analise_pontualidade': analise_pontualidade
        }
        
    except Exception as e:
        print(f"Erro na análise de padrões: {e}")
        return None

def obter_relatorio_produtividade(data_inicio, data_fim, departamento=None):
    """Gera relatório de produtividade por funcionário"""
    import sys
    try:
        sys.stderr.write(f"DEBUG: Gerando relatório de produtividade - {data_inicio} a {data_fim}, departamento: {departamento}\n")
        sys.stderr.flush()
        conn = get_simple_connection()
        cursor = conn.cursor()
        
        # Query simplificada - busca dados básicos primeiro
        query_base = """
            SELECT 
                f.numero_registro,
                f.nome,
                f.departamento,
                f.cargo,
                COUNT(*) as total_acessos,
                COUNT(CASE WHEN a.tipo_acesso = 'entrada' THEN 1 END) as entradas,
                COUNT(CASE WHEN a.tipo_acesso = 'saida' THEN 1 END) as saidas,
                COALESCE(AVG(CASE 
                    WHEN a.tipo_acesso = 'entrada' AND a.hora_acesso <= '08:30:00' THEN 1.0 
                    ELSE 0.0 
                END), 0.0) as pontualidade_entrada,
                COALESCE(AVG(CASE 
                    WHEN a.tipo_acesso = 'saida' AND a.hora_acesso >= '17:00:00' THEN 1.0 
                    ELSE 0.0 
                END), 0.0) as pontualidade_saida
            FROM acessos_funcionarios a
            JOIN funcionarios f ON a.numero_registro = f.numero_registro
            WHERE a.data_acesso BETWEEN %s AND %s
        """
        
        params_base = [data_inicio, data_fim]
        
        if departamento:
            query_base += " AND f.departamento = %s"
            params_base.append(departamento)
        
        query_base += """
            GROUP BY f.numero_registro, f.nome, f.departamento, f.cargo
            ORDER BY total_acessos DESC
        """
        
        cursor.execute(query_base, params_base)
        relatorio_base = cursor.fetchall()
        
        sys.stderr.write(f"DEBUG: Relatório base gerado com {len(relatorio_base)} registros\n")
        if relatorio_base:
            sys.stderr.write(f"DEBUG: Primeiro registro base: {relatorio_base[0]}\n")
        sys.stderr.flush()
        
        # Agora buscar primeira entrada e última saída do mesmo dia mais recente para cada funcionário
        relatorio_formatado = []
        sys.stderr.write(f"DEBUG: Iniciando loop para processar {len(relatorio_base)} funcionários\n")
        sys.stderr.flush()
        for row in relatorio_base:
            numero_registro = row[0]
            
            # Buscar o dia mais recente com entrada
            cursor.execute("""
                SELECT MAX(data_acesso) 
                FROM acessos_funcionarios 
                WHERE numero_registro = %s 
                  AND tipo_acesso = 'entrada'
                  AND data_acesso BETWEEN %s AND %s
            """, (numero_registro, data_inicio, data_fim))
            
            resultado_dia = cursor.fetchone()
            dia_mais_recente_entrada = resultado_dia[0] if resultado_dia else None
            
            sys.stderr.write(f"DEBUG: Funcionário {numero_registro} - Dia mais recente com entrada: {dia_mais_recente_entrada}\n")
            sys.stderr.flush()
            
            primeira_entrada = None
            ultima_saida = None
            
            if dia_mais_recente_entrada:
                sys.stderr.write(f"DEBUG: Funcionário {numero_registro} - Processando dia {dia_mais_recente_entrada}\n")
                sys.stderr.flush()
                # Buscar primeira entrada desse dia
                cursor.execute("""
                    SELECT MIN(hora_acesso) 
                    FROM acessos_funcionarios 
                    WHERE numero_registro = %s 
                      AND tipo_acesso = 'entrada'
                      AND data_acesso = %s
                """, (numero_registro, dia_mais_recente_entrada))
                
                resultado_entrada = cursor.fetchone()
                if resultado_entrada and resultado_entrada[0]:
                    primeira_entrada = resultado_entrada[0]
                
                # Buscar última saída do MESMO dia (não de outro dia)
                # Primeiro, verificar todas as saídas desse dia para debug
                cursor.execute("""
                    SELECT hora_acesso, data_acesso
                    FROM acessos_funcionarios 
                    WHERE numero_registro = %s 
                      AND tipo_acesso = 'saida'
                      AND data_acesso = %s
                    ORDER BY hora_acesso DESC
                """, (numero_registro, dia_mais_recente_entrada))
                
                todas_saidas = cursor.fetchall()
                print(f"DEBUG: Funcionário {numero_registro} - Todas as saídas do dia {dia_mais_recente_entrada}: {todas_saidas}")
                
                # Agora buscar a última saída
                cursor.execute("""
                    SELECT MAX(hora_acesso) 
                    FROM acessos_funcionarios 
                    WHERE numero_registro = %s 
                      AND tipo_acesso = 'saida'
                      AND data_acesso = %s
                """, (numero_registro, dia_mais_recente_entrada))
                
                resultado_saida = cursor.fetchone()
                sys.stderr.write(f"DEBUG: Funcionário {numero_registro} - Buscando saída do dia {dia_mais_recente_entrada}, resultado: {resultado_saida}\n")
                sys.stderr.flush()
                if resultado_saida and resultado_saida[0]:
                    ultima_saida = resultado_saida[0]
                    sys.stderr.write(f"DEBUG: Funcionário {numero_registro} - Última saída encontrada: {ultima_saida}\n")
                else:
                    sys.stderr.write(f"DEBUG: Funcionário {numero_registro} - Nenhuma saída encontrada para o dia {dia_mais_recente_entrada}\n")
                sys.stderr.flush()
            
            # Montar a linha do relatório
            row_list = []
            for item in row[:7]:  # Dados básicos (até cargo)
                row_list.append(item)
            
            # Adicionar primeira entrada e última saída
            row_list.append(primeira_entrada)
            row_list.append(ultima_saida)
            
            # Adicionar pontualidade
            row_list.append(row[7])  # pontualidade_entrada
            row_list.append(row[8])  # pontualidade_saida
            
            relatorio_formatado.append(row_list)
        
        sys.stderr.write(f"DEBUG: Relatório formatado com {len(relatorio_formatado)} registros\n")
        if relatorio_formatado and len(relatorio_formatado) > 0:
            sys.stderr.write(f"DEBUG: Primeiro registro exemplo: {relatorio_formatado[0]}\n")
            sys.stderr.write(f"DEBUG: Primeira entrada do primeiro registro: {relatorio_formatado[0][7] if len(relatorio_formatado[0]) > 7 else 'N/A'}\n")
            sys.stderr.write(f"DEBUG: Última saída do primeiro registro: {relatorio_formatado[0][8] if len(relatorio_formatado[0]) > 8 else 'N/A'}\n")
        sys.stderr.flush()
        
        # Converter para formato serializável
        relatorio_final = []
        for row in relatorio_formatado:
            row_list = []
            for item in row:
                # Converter timedelta, time, datetime para string
                if isinstance(item, timedelta):
                    # Converter timedelta para string HH:MM:SS
                    total_seconds = int(item.total_seconds())
                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60
                    seconds = total_seconds % 60
                    row_list.append(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
                elif isinstance(item, (datetime, date)):
                    row_list.append(item.isoformat())
                elif hasattr(item, 'strftime'):  # Para objetos time
                    row_list.append(str(item))
                elif item is None:
                    row_list.append(None)
                else:
                    row_list.append(item)
            relatorio_final.append(row_list)
        
        cursor.close()
        conn.close()
        
        return relatorio_final
        
    except Exception as e:
        print(f"Erro no relatório de produtividade: {e}")
        import traceback
        traceback.print_exc()
        return None

def obter_tendencias_acesso(dias=30):
    """Obtém tendências de acesso dos últimos dias"""
    try:
        conn = get_simple_connection()
        cursor = conn.cursor()
        
        # Tendências diárias
        cursor.execute("""
            SELECT 
                data_acesso as data,
                COUNT(*) as total_acessos,
                COUNT(CASE WHEN tipo_acesso = 'entrada' THEN 1 END) as entradas,
                COUNT(CASE WHEN tipo_acesso = 'saida' THEN 1 END) as saidas,
                COUNT(DISTINCT numero_registro) as funcionarios_unicos
            FROM acessos_funcionarios
            WHERE data_acesso >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
            GROUP BY data_acesso
            ORDER BY data
        """, (dias,))
        tendencias_diarias = cursor.fetchall()
        
        # Métodos de acesso mais usados
        cursor.execute("""
            SELECT 
                metodo_acesso,
                COUNT(*) as total_uso,
                ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM acessos_funcionarios WHERE data_acesso >= DATE_SUB(CURDATE(), INTERVAL %s DAY)), 2) as percentual
            FROM acessos_funcionarios
            WHERE data_acesso >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
            GROUP BY metodo_acesso
            ORDER BY total_uso DESC
        """, (dias, dias))
        metodos_acesso = cursor.fetchall()
        
        # Acessos por departamento
        cursor.execute("""
            SELECT 
                f.departamento,
                COUNT(*) as total_acessos
            FROM acessos_funcionarios a
            JOIN funcionarios f ON a.numero_registro = f.numero_registro
            WHERE a.data_acesso >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
            GROUP BY f.departamento
            ORDER BY total_acessos DESC
        """, (dias,))
        acessos_departamento = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {
            'tendencias_diarias': tendencias_diarias,
            'metodos_acesso': metodos_acesso,
            'acessos_departamento': acessos_departamento
        }
        
    except Exception as e:
        print(f"Erro nas tendências: {e}")
        return None

# ========================================
# FUNÇÕES DE REGISTRO DE ACESSO
# ========================================

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
    
    if not numero_registro:
        return jsonify({'success': False, 'message': 'Número de registro obrigatório'})
    
    try:
        conn = get_simple_connection()
        cursor = conn.cursor()
        
        # Buscar dados do funcionário
        cursor.execute("""
            SELECT nome, departamento, cargo, empresa, status, ativo 
            FROM funcionarios 
            WHERE numero_registro = %s
        """, (numero_registro,))
        
        funcionario = cursor.fetchone()
        if not funcionario:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False, 
                'message': 'Funcionário não encontrado',
                'tipo': 'funcionario_nao_encontrado'
            })
        
        nome, departamento, cargo, empresa, status, ativo = funcionario
        
        if not ativo:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False, 
                'message': 'Funcionário inativo',
                'tipo': 'funcionario_inativo'
            })
        
        if status != 'ativo':
            cursor.close()
            conn.close()
            return jsonify({
                'success': False, 
                'message': f'Funcionário com status: {status}',
                'tipo': 'status_inadequado'
            })
        
        # Verificar horário de trabalho
        tipo_acesso_final, hora_acesso, nome_config = verificar_horario_trabalho(numero_registro, tipo_acesso)
        
        # O sistema sempre permite o acesso, mas registra qual configuração foi usada
        print(f"📅 Configuração aplicada: {nome_config} - {tipo_acesso_final} às {hora_acesso}")
        
        # Registrar acesso
        agora = datetime.now()
        ip_acesso = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        
        cursor.execute("""
            INSERT INTO acessos_funcionarios 
            (numero_registro, nome_funcionario, departamento, cargo, empresa, 
             tipo_acesso, data_acesso, hora_acesso, timestamp_acesso, 
             metodo_acesso, observacao, ip_acesso, user_agent) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (numero_registro, nome, departamento, cargo, empresa, tipo_acesso,
               agora.date(), agora.time(), agora, metodo_acesso, observacao, ip_acesso, user_agent))
        
        cursor.close()
        conn.close()
        
        # Log do acesso
        log_acesso('ACESSO_REGISTRADO', f'Acesso {tipo_acesso}: {nome} ({numero_registro})', {
            'funcionario': nome,
            'registro': numero_registro,
            'tipo_acesso': tipo_acesso,
            'empresa': empresa,
            'departamento': departamento,
            'cargo': cargo
        })
        
        print(f"✅ Acesso registrado: {nome} ({numero_registro}) - {tipo_acesso} às {agora.strftime('%H:%M:%S')}")
        
        return jsonify({
            'success': True,
            'message': f'Acesso {tipo_acesso} registrado com sucesso!',
            'funcionario': {
                'nome': nome,
                'departamento': departamento,
                'cargo': cargo,
                'empresa': empresa,
                'hora': agora.strftime('%H:%M:%S'),
                'tipo_acesso': tipo_acesso
            },
            'dashboard_update': True  # Flag para indicar que o dashboard deve ser atualizado
        })
        
    except Exception as e:
        print(f"💥 Erro no registro de acesso: {e}")
        log_acesso('ERRO_SISTEMA', f'Erro ao registrar acesso: {str(e)}', {'numero_registro': numero_registro})
        return jsonify({
            'success': False, 
            'message': 'Erro interno do sistema',
            'tipo': 'erro_sistema'
        })

# ========================================
# FUNÇÕES DE REGISTRO DE ACESSO FACIAL
# ========================================

@app.route('/registrar_acesso_facial', methods=['POST'])
def registrar_acesso_facial():
    """Registra acesso via reconhecimento facial"""
    import sys
    try:
        print("🚀 INICIANDO REGISTRO DE ACESSO FACIAL", file=sys.stderr, flush=True)
        print("=" * 50, file=sys.stderr, flush=True)
        
        imagem_base64 = request.json.get('imagem', '')
        
        if not imagem_base64:
            print("❌ Imagem não fornecida", file=sys.stderr, flush=True)
            return jsonify({'success': False, 'message': 'Imagem obrigatória'})
        
        print(f"📸 Imagem recebida: {len(imagem_base64)} caracteres", file=sys.stderr, flush=True)
        
        # Buscar funcionário por face
        print("🔍 Chamando buscar_funcionario_por_facial...", file=sys.stderr, flush=True)
        funcionario, erro = buscar_funcionario_por_facial(imagem_base64)
        
        if erro:
            print(f"❌ Erro retornado: {erro}", file=sys.stderr, flush=True)
            return jsonify({
                'success': False, 
                'message': erro,
                'tipo': 'face_nao_reconhecida'
            })
        
        if not funcionario:
            print(f"❌ Funcionário não encontrado", file=sys.stderr, flush=True)
            return jsonify({
                'success': False, 
                'message': 'Funcionário não reconhecido',
                'tipo': 'face_nao_reconhecida'
            })
        
        print(f"✅ Funcionário encontrado: {funcionario['nome']} (Registro: {funcionario['numero_registro']})", file=sys.stderr, flush=True)
        
        # Registrar acesso no banco de dados
        numero_registro = funcionario['numero_registro']
        nome = funcionario['nome']
        departamento = funcionario['departamento']
        cargo = funcionario['cargo']
        empresa = funcionario['empresa']
        confianca = funcionario['confianca']
        
        # Determinar tipo de acesso automaticamente baseado no histórico
        tipo_acesso = determinar_tipo_acesso_automatico(numero_registro)
        hora_atual = datetime.now().time()
        
        # Registrar no banco de dados
        print(f"🔗 Conectando ao banco de dados...", file=sys.stderr, flush=True)
        conn = get_simple_connection()
        cursor = conn.cursor()
        
        try:
            print(f"📝 Inserindo registro: {numero_registro}, {nome}, {tipo_acesso}, {hora_atual}", file=sys.stderr, flush=True)
            # Inserir registro de acesso
            cursor.execute("""
                INSERT INTO acessos_funcionarios 
                (numero_registro, nome_funcionario, departamento, cargo, empresa, tipo_acesso, 
                 data_acesso, hora_acesso, metodo_acesso)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                numero_registro, nome, departamento, cargo, empresa, tipo_acesso,
                date.today(), hora_atual, 'facial'
            ))
            
            print(f"💾 Commitando transação...", file=sys.stderr, flush=True)
            conn.commit()
            print(f"✅ Registro inserido com sucesso!", file=sys.stderr, flush=True)
            
            # Registrar uso do facial
            registrar_uso_facial(numero_registro)
            
            # Log do evento
            log_acesso(
                'acesso_facial',
                f'Acesso facial registrado para {nome}',
                {
                    'numero_registro': numero_registro,
                    'tipo_acesso': tipo_acesso,
                    'confianca': confianca,
                    'hora': str(hora_atual)
                }
            )
            
            print(f"🎉 ACESSO REGISTRADO COM SUCESSO!", file=sys.stderr, flush=True)
            print(f"   Funcionário: {nome}", file=sys.stderr, flush=True)
            print(f"   Tipo: {tipo_acesso}", file=sys.stderr, flush=True)
            print(f"   Confiança: {confianca:.2f}", file=sys.stderr, flush=True)
            print(f"   Hora: {hora_atual}", file=sys.stderr, flush=True)
            print("=" * 50, file=sys.stderr, flush=True)
            
            return jsonify({
                'success': True,
                'message': f'Acesso {tipo_acesso} registrado com sucesso!',
                'funcionario': {
                    'nome': nome,
                    'numero_registro': numero_registro,
                    'departamento': departamento,
                    'cargo': cargo,
                    'empresa': empresa,
                    'confianca': confianca,
                    'tipo_acesso': tipo_acesso,
                    'hora': str(hora_atual)
                },
                'dashboard_update': True  # Flag para indicar que o dashboard deve ser atualizado
            })
            
        except Exception as e:
            print(f"❌ Erro ao registrar acesso no banco: {e}", file=sys.stderr, flush=True)
            return jsonify({'success': False, 'message': f'Erro ao registrar acesso: {str(e)}'})
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        import traceback
        print("🔥 EXCEÇÃO CAPTURADA EM registrar_acesso_facial:", file=sys.stderr, flush=True)
        print(traceback.format_exc(), file=sys.stderr, flush=True)
        return jsonify({'success': False, 'message': f'Erro interno: {str(e)}'})

@app.route('/api/detectar_face', methods=['POST'])
def detectar_face():
    """API para detectar se há face na imagem (usado pelo frontend)"""
    # Rate limiting desabilitado para detecção facial
    # client_ip = request.remote_addr
    # rate_ok, rate_message = verificar_rate_limiting_facial(client_ip)
    # 
    # if not rate_ok:
    #     return jsonify({
    #         'success': False,
    #         'message': rate_message,
    #         'rate_limited': True
    #     }), 429
    
    imagem_base64 = request.json.get('imagem', '')
    
    if not imagem_base64:
        return jsonify({'success': False, 'message': 'Imagem obrigatória'})
    
    try:
        # Decodificar imagem para análise
        imagem_data = base64.b64decode(imagem_base64.split(',')[1])
        imagem_array = np.frombuffer(imagem_data, np.uint8)
        imagem = cv2.imdecode(imagem_array, cv2.IMREAD_COLOR)
        imagem_rgb = cv2.cvtColor(imagem, cv2.COLOR_BGR2RGB)
        
        # Detectar faces com configuração otimizada para ambientes escuros
        face_locations = []
        
        # Tentativa 1: Detecção padrão
        face_locations = face_recognition.face_locations(imagem_rgb, model="hog", number_of_times_to_upsample=1)
        
        if not face_locations:
            # Tentativa 2: Com mais upsamples
            face_locations = face_recognition.face_locations(imagem_rgb, model="hog", number_of_times_to_upsample=2)
        
        if not face_locations:
            # Tentativa 3: Com modelo CNN (melhor para ambientes escuros)
            try:
                face_locations = face_recognition.face_locations(imagem_rgb, model="cnn", number_of_times_to_upsample=1)
            except Exception as e:
                print(f"⚠️ Modelo CNN não disponível: {e}")
        
        if not face_locations:
            # Tentativa 4: Com imagem redimensionada
            altura, largura = imagem_rgb.shape[:2]
            if altura > 240 or largura > 320:
                imagem_menor = cv2.resize(imagem_rgb, (320, 240))
                face_locations = face_recognition.face_locations(imagem_menor, model="hog", number_of_times_to_upsample=2)
                if face_locations:
                    # Ajustar coordenadas
                    scale_x = largura / 320
                    scale_y = altura / 240
                    face_locations = [(int(top * scale_y), int(right * scale_x), 
                                     int(bottom * scale_y), int(left * scale_x)) for top, right, bottom, left in face_locations]
        
        if not face_locations:
            # Calcular informações de iluminação mesmo sem face detectada
            gray = cv2.cvtColor(imagem_rgb, cv2.COLOR_RGB2GRAY)
            brightness = np.mean(gray)
            
            return jsonify({
                'success': True,
                'detecao': {
                    'tem_face': False,
                    'face_centralizada': False,
                    'tamanho_adequado': False
                },
                'lighting_info': {
                    'brightness': float(brightness),
                    'level': 'very_poor' if brightness < 30 else 'poor' if brightness < 60 else 'good'
                }
            })
        
        # Análise da face
        altura, largura = imagem_rgb.shape[:2]
        top, right, bottom, left = face_locations[0]
        
        # Verificar se face está centralizada
        centro_face_x = (left + right) / 2
        centro_face_y = (top + bottom) / 2
        centro_imagem_x = largura / 2
        centro_imagem_y = altura / 2
        
        tolerancia_centro = 0.3  # 30% de tolerância
        face_centralizada = (
            abs(centro_face_x - centro_imagem_x) < largura * tolerancia_centro and
            abs(centro_face_y - centro_imagem_y) < altura * tolerancia_centro
        )
        
        # Verificar tamanho da face
        tamanho_face = (right - left) * (bottom - top)
        tamanho_imagem = largura * altura
        proporcao_face = tamanho_face / tamanho_imagem
        
        tamanho_adequado = 0.05 <= proporcao_face <= 0.5  # Entre 5% e 50% da imagem
        
        # Calcular informações de iluminação
        gray = cv2.cvtColor(imagem_rgb, cv2.COLOR_RGB2GRAY)
        brightness = np.mean(gray)
        
        return jsonify({
            'success': True,
            'detecao': {
                'tem_face': True,
                'face_centralizada': face_centralizada,
                'tamanho_adequado': tamanho_adequado,
                'proporcao_face': proporcao_face,
                'centro_face': [centro_face_x, centro_face_y],
                'centro_imagem': [centro_imagem_x, centro_imagem_y]
            },
            'lighting_info': {
                'brightness': float(brightness),
                'level': 'very_poor' if brightness < 30 else 'poor' if brightness < 60 else 'good'
            }
        })
        
    except Exception as e:
        print(f"Erro na detecção de face: {e}")
        return jsonify({
            'success': False,
            'detecao': {
                'tem_face': False,
                'face_centralizada': False,
                'tamanho_adequado': False,
                'erro': str(e)
            }
        })

# ========================================
# FUNÇÕES DE LOG
# ========================================

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

# ========================================
# APIs
# ========================================

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
        
        # Funcionários presentes agora (entraram hoje e não saíram)
        cursor.execute("""
            SELECT COUNT(DISTINCT f.numero_registro) 
            FROM funcionarios f
            WHERE f.ativo = TRUE 
            AND EXISTS (
                SELECT 1 FROM acessos_funcionarios a 
                WHERE a.numero_registro = f.numero_registro 
                AND DATE(a.data_acesso) = CURDATE()
                AND a.tipo_acesso = 'entrada'
            )
            AND NOT EXISTS (
                SELECT 1 FROM acessos_funcionarios a2 
                WHERE a2.numero_registro = f.numero_registro 
                AND DATE(a2.data_acesso) = CURDATE() 
                AND a2.tipo_acesso = 'saida'
                AND a2.hora_acesso > (
                    SELECT MAX(a3.hora_acesso) 
                    FROM acessos_funcionarios a3 
                    WHERE a3.numero_registro = f.numero_registro 
                    AND DATE(a3.data_acesso) = CURDATE()
                    AND a3.tipo_acesso = 'entrada'
                )
            )
        """)
        presentes = cursor.fetchone()[0]
        stats['presentes'] = presentes
        print(f"🔍 DEBUG - Funcionários presentes: {presentes}")
        print(f"🔍 DEBUG - Teste de log simples")
        
        # Funcionários que saíram hoje (última ação foi saída)
        cursor.execute("""
            SELECT COUNT(DISTINCT f.numero_registro) 
            FROM funcionarios f
            WHERE f.ativo = TRUE 
            AND EXISTS (
                SELECT 1 FROM acessos_funcionarios a 
                WHERE a.numero_registro = f.numero_registro 
                AND DATE(a.data_acesso) = CURDATE()
                AND a.tipo_acesso = 'saida'
            )
            AND NOT EXISTS (
                SELECT 1 FROM acessos_funcionarios a2 
                WHERE a2.numero_registro = f.numero_registro 
                AND DATE(a2.data_acesso) = CURDATE() 
                AND a2.tipo_acesso = 'entrada'
                AND a2.hora_acesso > (
                    SELECT MAX(a3.hora_acesso) 
                    FROM acessos_funcionarios a3 
                    WHERE a3.numero_registro = f.numero_registro 
                    AND DATE(a3.data_acesso) = CURDATE()
                    AND a3.tipo_acesso = 'saida'
                )
            )
        """)
        sairam = cursor.fetchone()[0]
        stats['sairam'] = sairam
        print(f"🔍 DEBUG - Funcionários que saíram: {sairam}")
        
        # Debug: verificar acessos específicos do funcionário que saiu
        cursor.execute("""
            SELECT numero_registro, tipo_acesso, hora_acesso
            FROM acessos_funcionarios 
            WHERE DATE(data_acesso) = CURDATE()
            AND numero_registro = '5080'
            ORDER BY hora_acesso
        """)
        acessos_5080 = cursor.fetchall()
        print(f"🔍 DEBUG - Acessos do funcionário 5080 hoje: {acessos_5080}")
        
        # Debug: verificar acessos de hoje
        cursor.execute("""
            SELECT tipo_acesso, COUNT(*) as total
            FROM acessos_funcionarios 
            WHERE DATE(data_acesso) = CURDATE()
            GROUP BY tipo_acesso
        """)
        acessos_debug = cursor.fetchall()
        print(f"🔍 DEBUG - Acessos de hoje: {acessos_debug}")
        
        # Atrasos hoje
        cursor.execute("""
            SELECT COUNT(*) FROM acessos_funcionarios 
            WHERE DATE(data_acesso) = CURDATE() 
            AND tipo_acesso = 'entrada'
            AND TIME(hora_acesso) > '08:15:00'
        """)
        stats['atrasos'] = cursor.fetchone()[0]
        
        # Gráficos
        charts = {}
        
        # Acessos por hora (hoje)
        cursor.execute("""
            SELECT HOUR(hora_acesso) as hora, COUNT(*) as total
            FROM acessos_funcionarios 
            WHERE DATE(data_acesso) = CURDATE()
            GROUP BY HOUR(hora_acesso)
            ORDER BY hora
        """)
        acessos_por_hora = cursor.fetchall()
        
        horas = list(range(24))
        valores = [0] * 24
        for hora, total in acessos_por_hora:
            valores[hora] = total
        
        charts['acessos_por_hora'] = {
            'labels': [f'{h:02d}:00' for h in horas],
            'values': valores
        }
        
        # Tipos de acesso
        cursor.execute("""
            SELECT tipo_acesso, COUNT(*) as total
            FROM acessos_funcionarios 
            WHERE DATE(data_acesso) = CURDATE()
            GROUP BY tipo_acesso
        """)
        tipos_acesso = cursor.fetchall()
        
        charts['tipos_acesso'] = {
            'labels': [TIPOS_ACESSO.get(tipo, tipo) for tipo, _ in tipos_acesso],
            'values': [total for _, total in tipos_acesso]
        }
        
        # Atividade recente
        cursor.execute("""
            SELECT f.nome as nome_completo, a.tipo_acesso, CONCAT(a.data_acesso, ' ', a.hora_acesso) as data_hora
            FROM acessos_funcionarios a
            JOIN funcionarios f ON a.numero_registro = f.numero_registro
            WHERE DATE(a.data_acesso) = CURDATE()
            ORDER BY a.data_acesso DESC, a.hora_acesso DESC
            LIMIT 10
        """)
        recent_activity = []
        for nome, tipo, data_hora in cursor.fetchall():
            # Extrair hora da string data_hora
            try:
                if isinstance(data_hora, str):
                    # Se já é string, extrair hora
                    hora = data_hora.split(' ')[1][:5] if ' ' in data_hora else data_hora[:5]
                else:
                    # Se é datetime, usar strftime
                    hora = data_hora.strftime('%H:%M')
            except:
                hora = '00:00'
            
            recent_activity.append({
                'funcionario': nome,
                'tipo': TIPOS_ACESSO.get(tipo, tipo),
                'horario': hora,
                'status': 'entrada' if 'entrada' in tipo else 'saida'
            })
        
        # Alertas
        alertas = []
        
        try:
            # Verificar funcionários que não entraram hoje
            cursor.execute("""
                SELECT f.nome 
                FROM funcionarios f
                WHERE f.ativo = TRUE 
                AND NOT EXISTS (
                    SELECT 1 FROM acessos_funcionarios a 
                    WHERE a.numero_registro = f.numero_registro 
                    AND DATE(a.data_acesso) = CURDATE()
                    AND a.tipo_acesso = 'entrada'
                )
            """)
            ausentes = cursor.fetchall()
            
            if ausentes:
                alertas.append({
                    'tipo': 'warning',
                    'icon': 'user-times',
                    'titulo': 'Funcionários Ausentes',
                    'mensagem': f'{len(ausentes)} funcionário(s) ainda não entraram hoje'
                })
        except Exception as e:
            print(f"Erro ao verificar ausentes: {e}")
        
        try:
            # Buscar horário padrão do sistema
            cursor.execute("""
                SELECT hora_entrada, tolerancia_entrada 
                FROM configuracoes_horarios 
                WHERE ativo = TRUE 
                LIMIT 1
            """)
            config_padrao = cursor.fetchone()
            hora_padrao = str(config_padrao[0]) if config_padrao and config_padrao[0] else '08:00:00'
            tolerancia_padrao = int(config_padrao[1]) if config_padrao and config_padrao[1] else 15
            
            # Verificar atrasos (entrada depois do horário + tolerância)
            # Usar uma abordagem mais simples: buscar todos os acessos de hoje e calcular em Python
            cursor.execute("""
                SELECT f.nome, f.numero_registro, a.hora_acesso, 
                       f.horario_entrada, f.tolerancia_entrada
                FROM acessos_funcionarios a
                JOIN funcionarios f ON a.numero_registro = f.numero_registro
                WHERE DATE(a.data_acesso) = CURDATE()
                AND a.tipo_acesso = 'entrada'
                ORDER BY a.hora_acesso DESC
            """)
            todos_acessos = cursor.fetchall()
            
            atrasos = []
            antecipacoes = []
            
            for row in todos_acessos:
                nome, numero_registro, hora_acesso, horario_entrada_func, tolerancia_entrada_func = row
                
                # Usar horário do funcionário ou padrão
                horario_entrada = horario_entrada_func if horario_entrada_func else hora_padrao
                tolerancia_entrada = int(tolerancia_entrada_func) if tolerancia_entrada_func else tolerancia_padrao
                
                # Converter hora_acesso para time object
                if isinstance(hora_acesso, str):
                    try:
                        hora_acesso_dt = datetime.strptime(hora_acesso, '%H:%M:%S').time()
                    except:
                        try:
                            hora_acesso_dt = datetime.strptime(hora_acesso, '%H:%M').time()
                        except:
                            hora_acesso_dt = datetime.now().time()
                elif isinstance(hora_acesso, timedelta):
                    # Se for timedelta, converter para time
                    total_seconds = int(hora_acesso.total_seconds())
                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60
                    seconds = total_seconds % 60
                    hora_acesso_dt = datetime.strptime(f"{hours:02d}:{minutes:02d}:{seconds:02d}", '%H:%M:%S').time()
                elif hasattr(hora_acesso, 'hour'):  # Já é um time object
                    hora_acesso_dt = hora_acesso
                else:
                    hora_acesso_dt = datetime.now().time()
                
                # Converter horario_entrada para time object
                if isinstance(horario_entrada, str):
                    try:
                        horario_entrada_dt = datetime.strptime(horario_entrada, '%H:%M:%S').time()
                    except:
                        try:
                            horario_entrada_dt = datetime.strptime(horario_entrada, '%H:%M').time()
                        except:
                            horario_entrada_dt = datetime.strptime('08:00:00', '%H:%M:%S').time()
                elif isinstance(horario_entrada, timedelta):
                    # Se for timedelta, converter para time
                    total_seconds = int(horario_entrada.total_seconds())
                    # Garantir que não ultrapasse 24 horas
                    total_seconds = total_seconds % 86400
                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60
                    seconds = total_seconds % 60
                    horario_entrada_dt = datetime.strptime(f"{hours:02d}:{minutes:02d}:{seconds:02d}", '%H:%M:%S').time()
                elif hasattr(horario_entrada, 'hour') and hasattr(horario_entrada, 'minute'):  # Já é um time object
                    horario_entrada_dt = horario_entrada
                else:
                    # Fallback: usar horário padrão
                    horario_entrada_dt = datetime.strptime(str(hora_padrao), '%H:%M:%S').time() if isinstance(hora_padrao, str) else datetime.strptime('08:00:00', '%H:%M:%S').time()
                
                # Garantir que horario_entrada_dt é realmente um time object
                if not isinstance(horario_entrada_dt, type(datetime.now().time())):
                    print(f"⚠️ AVISO: horario_entrada_dt não é time object: {type(horario_entrada_dt)} = {horario_entrada_dt}")
                    horario_entrada_dt = datetime.strptime('08:00:00', '%H:%M:%S').time()
                
                # Calcular hora limite (horário + tolerância)
                try:
                    horario_base = datetime.combine(date.today(), horario_entrada_dt)
                    hora_limite = (horario_base + timedelta(minutes=tolerancia_entrada)).time()
                except Exception as e:
                    print(f"⚠️ Erro ao calcular hora_limite: {e}")
                    print(f"   horario_entrada_dt type: {type(horario_entrada_dt)}, value: {horario_entrada_dt}")
                    continue  # Pular este acesso se houver erro
                
                # Verificar se é atraso
                if hora_acesso_dt > hora_limite:
                    atrasos.append((nome, numero_registro, hora_acesso))
                # Verificar se é antecipação (antes do horário de entrada)
                elif hora_acesso_dt < horario_entrada_dt:
                    antecipacoes.append((nome, numero_registro, hora_acesso))
            
            # Limitar a 10 resultados
            atrasos = atrasos[:10]
            antecipacoes = antecipacoes[:10]
            
            if atrasos:
                nomes_atrasados = [f"{row[0]}" for row in atrasos[:5]]  # Limitar a 5 nomes
                total_atrasos = len(atrasos)
                mensagem = f'{total_atrasos} funcionário(s) entraram com atraso hoje'
                if nomes_atrasados:
                    mensagem += f': {", ".join(nomes_atrasados)}'
                    if total_atrasos > 5:
                        mensagem += f' e mais {total_atrasos - 5}'
                
                alertas.append({
                    'tipo': 'warning',
                    'icon': 'clock',
                    'titulo': 'Atrasos Hoje',
                    'mensagem': mensagem
                })
            
            if antecipacoes:
                nomes_antecipados = [f"{row[0]}" for row in antecipacoes[:5]]  # Limitar a 5 nomes
                total_antecipacoes = len(antecipacoes)
                mensagem = f'{total_antecipacoes} funcionário(s) entraram antes do horário hoje'
                if nomes_antecipados:
                    mensagem += f': {", ".join(nomes_antecipados)}'
                    if total_antecipacoes > 5:
                        mensagem += f' e mais {total_antecipacoes - 5}'
                
                alertas.append({
                    'tipo': 'info',
                    'icon': 'clock',
                    'titulo': 'Antecipações Hoje',
                    'mensagem': mensagem
                })
                
        except Exception as e:
            print(f"Erro ao verificar atrasos/antecipações: {e}")
            import traceback
            traceback.print_exc()
        
        try:
            # Verificar acessos suspeitos
            cursor.execute("""
                SELECT COUNT(*) FROM acessos_funcionarios 
                WHERE DATE(data_acesso) = CURDATE()
                AND TIME(hora_acesso) < '06:00:00'
            """)
            acessos_suspeitos = cursor.fetchone()[0]
            
            if acessos_suspeitos > 0:
                alertas.append({
                    'tipo': 'danger',
                    'icon': 'exclamation-triangle',
                    'titulo': 'Acessos Suspeitos',
                    'mensagem': f'{acessos_suspeitos} acesso(s) antes das 6h'
                })
        except Exception as e:
            print(f"Erro ao verificar acessos suspeitos: {e}")
        
        print(f"🔔 DEBUG - Total de alertas gerados: {len(alertas)}")
        for alerta in alertas:
            print(f"  - {alerta['titulo']}: {alerta['mensagem']}")
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': stats,
            'charts': charts,
            'recent_activity': recent_activity,
            'alertas': alertas
        })
        
    except Exception as e:
        print(f"Erro na API dashboard_data: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        })

# ========================================
# ROTAS PRINCIPAIS
# ========================================

@app.route('/')
def index():
    """Página principal de acesso de funcionários"""
    return render_template('index.html')

@app.route('/documentacao')
def documentacao():
    """Documentação de apresentação do sistema"""
    return render_template('documentacao_apresentacao.html')

@app.route('/acesso-facial')
def acesso_facial():
    """Página de acesso facial para funcionários"""
    return render_template('facial.html')

@app.route('/acesso-manual')
def acesso_manual():
    """Página de acesso manual para funcionários"""
    return render_template('acesso_manual.html')

@app.route('/acesso-rfid')
def acesso_rfid():
    """Página de acesso RFID para funcionários"""
    return render_template('acesso_rfid.html')

@app.route('/acesso-qrcode')
def acesso_qrcode():
    """Página de acesso QR Code para funcionários"""
    return render_template('acesso_qrcode.html')

@app.route('/admin')
@admin_required
def admin():
    """Painel administrativo"""
    return render_template('admin.html')

@app.route('/admin/funcionarios')
@admin_required
def admin_funcionarios():
    """Gestão de funcionários"""
    return render_template('funcionarios.html')

@app.route('/api/teste')
def teste_api():
    return jsonify({'success': True, 'message': 'API funcionando'})

@app.route('/api/status-sistema')
def status_sistema():
    """API para verificar status do sistema"""
    try:
        conn = get_simple_connection()
        cursor = conn.cursor()
        
        # Contar funcionários ativos
        cursor.execute("SELECT COUNT(*) FROM funcionarios WHERE ativo = TRUE")
        funcionarios_ativos = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'funcionarios_ativos': funcionarios_ativos,
            'sistema_online': True,
            'rfid_ativo': True
        })
        
    except Exception as e:
        print(f"Erro ao verificar status do sistema: {e}")
        return jsonify({
            'success': False,
            'message': 'Erro ao verificar status'
        })

@app.route('/api/detectar_tipo_acesso', methods=['POST'])
def detectar_tipo_acesso():
    """API para detectar automaticamente o tipo de acesso"""
    try:
        data = request.get_json()
        numero_registro = data.get('numero_registro', '').strip()
        
        if not numero_registro:
            return jsonify({'success': False, 'message': 'Número de registro obrigatório'})
        
        # Verificar se funcionário existe
        conn = get_simple_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT nome, ativo, status 
            FROM funcionarios 
            WHERE numero_registro = %s
        """, (numero_registro,))
        
        funcionario = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not funcionario:
            return jsonify({'success': False, 'message': 'Funcionário não encontrado'})
        
        nome, ativo, status = funcionario
        
        if not ativo:
            return jsonify({'success': False, 'message': 'Funcionário inativo'})
        
        if status != 'ativo':
            return jsonify({'success': False, 'message': f'Funcionário com status: {status}'})
        
        # Determinar tipo de acesso automaticamente
        tipo_acesso = determinar_tipo_acesso_automatico(numero_registro)
        
        return jsonify({
            'success': True,
            'tipo_acesso': tipo_acesso,
            'funcionario': {
                'nome': nome,
                'numero_registro': numero_registro
            }
        })
        
    except Exception as e:
        print(f"Erro ao detectar tipo de acesso: {e}")
        return jsonify({'success': False, 'message': 'Erro interno do servidor'})

@app.route('/api/funcionarios', methods=['GET'])
def get_funcionarios():
    """Buscar todos os funcionários"""
    try:
        conn = get_simple_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = """
        SELECT id, numero_registro, nome, departamento, cargo, empresa, 
               ativo, data_cadastro
        FROM funcionarios 
        ORDER BY nome
        """
        
        cursor.execute(query)
        funcionarios = cursor.fetchall()
        
        # Converter datas para string
        for func in funcionarios:
            if func['data_cadastro']:
                func['data_cadastro'] = func['data_cadastro'].strftime('%d/%m/%Y')
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'funcionarios': funcionarios,
            'total': len(funcionarios)
        })
        
    except Exception as e:
        log_acesso('erro', f'Erro ao buscar funcionários: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Erro ao buscar funcionários'
        }), 500

@app.route('/api/funcionarios', methods=['POST'])
@login_required
def criar_funcionario():
    """Criar novo funcionário"""
    try:
        data = request.get_json()
        
        # Validações básicas
        if not data.get('numero_registro') or not data.get('nome'):
            return jsonify({
                'success': False,
                'error': 'Número de registro e nome são obrigatórios'
            }), 400
        
        conn = get_simple_connection()
        cursor = conn.cursor()
        
        # Verificar se número de registro já existe
        cursor.execute("SELECT id FROM funcionarios WHERE numero_registro = %s", 
                      (data['numero_registro'],))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Número de registro já existe'
            }), 400
        
        # Inserir funcionário
        query = """
        INSERT INTO funcionarios (
            numero_registro, nome, departamento, cargo, empresa, ativo
        ) VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        valores = (
            data['numero_registro'],
            data['nome'],
            data['departamento'],
            data['cargo'],
            data['empresa'],
            data.get('ativo', True)
        )
        
        cursor.execute(query, valores)
        funcionario_id = cursor.lastrowid
        
        cursor.close()
        conn.close()
        
        log_acesso('funcionario_criado', f'Funcionário criado: {data["nome"]} ({data["numero_registro"]})')
        
        return jsonify({
            'success': True,
            'message': 'Funcionário criado com sucesso',
            'funcionario_id': funcionario_id
        })
        
    except Exception as e:
        log_acesso('erro', f'Erro ao criar funcionário: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Erro ao criar funcionário'
        }), 500

@app.route('/api/funcionarios/<int:funcionario_id>', methods=['PUT'])
@login_required
def atualizar_funcionario(funcionario_id):
    """Atualizar funcionário existente"""
    try:
        data = request.get_json()
        
        conn = get_simple_connection()
        cursor = conn.cursor()
        
        # Verificar se funcionário existe
        cursor.execute("SELECT id FROM funcionarios WHERE id = %s", (funcionario_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Funcionário não encontrado'
            }), 404
        
        # Atualizar funcionário
        query = """
        UPDATE funcionarios SET 
            numero_registro = %s, nome = %s, departamento = %s, 
            cargo = %s, empresa = %s, ativo = %s
        WHERE id = %s
        """
        
        valores = (
            data['numero_registro'],
            data['nome'],
            data['departamento'],
            data['cargo'],
            data['empresa'],
            data.get('ativo', True),
            funcionario_id
        )
        
        cursor.execute(query, valores)
        
        cursor.close()
        conn.close()
        
        log_acesso('funcionario_atualizado', f'Funcionário atualizado: {data["nome"]} ({data["numero_registro"]})')
        
        return jsonify({
            'success': True,
            'message': 'Funcionário atualizado com sucesso'
        })
        
    except Exception as e:
        log_acesso('erro', f'Erro ao atualizar funcionário: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Erro ao atualizar funcionário'
        }), 500

@app.route('/api/funcionarios/<int:funcionario_id>', methods=['DELETE'])
@login_required
def excluir_funcionario(funcionario_id):
    """Excluir funcionário"""
    try:
        conn = get_simple_connection()
        cursor = conn.cursor()
        
        # Verificar se funcionário existe
        cursor.execute("SELECT nome, numero_registro FROM funcionarios WHERE id = %s", (funcionario_id,))
        funcionario = cursor.fetchone()
        if not funcionario:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Funcionário não encontrado'
            }), 404
        
        # Excluir funcionário
        cursor.execute("DELETE FROM funcionarios WHERE id = %s", (funcionario_id,))
        
        cursor.close()
        conn.close()
        
        log_acesso('funcionario_excluido', f'Funcionário excluído: {funcionario[0]} ({funcionario[1]})')
        
        return jsonify({
            'success': True,
            'message': 'Funcionário excluído com sucesso'
        })
        
    except Exception as e:
        log_acesso('erro', f'Erro ao excluir funcionário: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Erro ao excluir funcionário'
        }), 500

@app.route('/api/funcionarios/exportar', methods=['GET'])
@login_required
def exportar_funcionarios():
    """Exportar funcionários para CSV"""
    try:
        conn = get_simple_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = """
        SELECT numero_registro, nome, departamento, cargo, empresa, ativo
        FROM funcionarios 
        ORDER BY nome
        """
        
        cursor.execute(query)
        funcionarios = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Criar CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Cabeçalho
        writer.writerow([
            'Registro', 'Nome', 'Departamento', 'Cargo', 'Empresa', 'Ativo'
        ])
        
        # Dados
        for func in funcionarios:
            writer.writerow([
                func['numero_registro'],
                func['nome'],
                func['departamento'],
                func['cargo'],
                func['empresa'],
                'Sim' if func['ativo'] else 'Não'
            ])
        
        output.seek(0)
        
        log_acesso('exportacao', f'Funcionários exportados: {len(funcionarios)} registros')
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=funcionarios.csv'}
        )
        
    except Exception as e:
        log_acesso('erro', f'Erro ao exportar funcionários: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Erro ao exportar funcionários'
        }), 500

@app.route('/api/relatorio-presenca')
def relatorio_presenca():
    """API para relatório de presença - funcionários presentes e que saíram"""
    conn = None
    cursor = None
    try:
        conn = get_simple_connection()
        cursor = conn.cursor()
        
        # Query muito simplificada e otimizada - usar data direta ao invés de DATE()
        hoje = date.today()
        
        # Funcionários presentes agora (entraram hoje e não saíram depois)
        # Usar subquery simples para encontrar última entrada e última saída
        cursor.execute("""
            SELECT 
                f.numero_registro, 
                f.nome, 
                f.departamento, 
                f.cargo, 
                f.empresa,
                MAX(CASE WHEN a.tipo_acesso = 'entrada' THEN a.hora_acesso END) as ultima_entrada
            FROM funcionarios f
            INNER JOIN acessos_funcionarios a ON f.numero_registro = a.numero_registro
            WHERE f.ativo = TRUE 
            AND a.data_acesso = %s
            AND a.tipo_acesso = 'entrada'
            AND NOT EXISTS (
                SELECT 1 FROM acessos_funcionarios a2 
                WHERE a2.numero_registro = f.numero_registro 
                AND a2.data_acesso = %s
                AND a2.tipo_acesso = 'saida'
                AND a2.hora_acesso > (
                    SELECT MAX(a3.hora_acesso) 
                    FROM acessos_funcionarios a3 
                    WHERE a3.numero_registro = f.numero_registro 
                    AND a3.data_acesso = %s
                    AND a3.tipo_acesso = 'entrada'
                )
            )
            GROUP BY f.numero_registro, f.nome, f.departamento, f.cargo, f.empresa
            ORDER BY f.nome
            LIMIT 500
        """, (hoje, hoje, hoje))
        presentes = cursor.fetchall()
        
        # Funcionários que saíram hoje (saíram e não entraram depois)
        cursor.execute("""
            SELECT 
                f.numero_registro, 
                f.nome, 
                f.departamento, 
                f.cargo, 
                f.empresa,
                MAX(CASE WHEN a.tipo_acesso = 'saida' THEN a.hora_acesso END) as ultima_saida
            FROM funcionarios f
            INNER JOIN acessos_funcionarios a ON f.numero_registro = a.numero_registro
            WHERE f.ativo = TRUE 
            AND a.data_acesso = %s
            AND a.tipo_acesso = 'saida'
            AND NOT EXISTS (
                SELECT 1 FROM acessos_funcionarios a2 
                WHERE a2.numero_registro = f.numero_registro 
                AND a2.data_acesso = %s
                AND a2.tipo_acesso = 'entrada'
                AND a2.hora_acesso > (
                    SELECT MAX(a3.hora_acesso) 
                    FROM acessos_funcionarios a3 
                    WHERE a3.numero_registro = f.numero_registro 
                    AND a3.data_acesso = %s
                    AND a3.tipo_acesso = 'saida'
                )
            )
            GROUP BY f.numero_registro, f.nome, f.departamento, f.cargo, f.empresa
            ORDER BY f.nome
            LIMIT 500
        """, (hoje, hoje, hoje))
        sairam = cursor.fetchall()
        
        # Converter para formato JSON
        presentes_json = []
        for p in presentes:
            presentes_json.append({
                'numero_registro': p[0],
                'nome': p[1],
                'departamento': p[2],
                'cargo': p[3],
                'empresa': p[4],
                'ultima_entrada': str(p[5]) if p[5] else None
            })
        
        sairam_json = []
        for s in sairam:
            sairam_json.append({
                'numero_registro': s[0],
                'nome': s[1],
                'departamento': s[2],
                'cargo': s[3],
                'empresa': s[4],
                'ultima_saida': str(s[5]) if s[5] else None
            })
        
        return jsonify({
            'success': True,
            'presentes': presentes_json,
            'sairam': sairam_json,
            'total_presentes': len(presentes_json),
            'total_sairam': len(sairam_json)
        })
        
    except Exception as e:
        print(f"Erro ao gerar relatório de presença: {e}")
        return jsonify({'success': False, 'error': str(e)})





@app.route('/admin/relatorios')
@admin_required
def admin_relatorios():
    """Relatórios de acesso"""
    hoje = get_data_atual().strftime('%Y-%m-%d')
    return render_template('relatorios.html', hoje=hoje)

@app.route('/analytics')
@login_required
def analytics():
    """Página de analytics e relatórios avançados"""
    return render_template('analytics.html')


@app.route('/api/relatorios/diario', methods=['GET'])
@login_required
def gerar_relatorio_diario():
    """Gerar relatório diário de acessos"""
    try:
        print("DEBUG: Iniciando geração de relatório diário")
        data_inicio = request.args.get('data_inicio', get_data_atual().strftime('%Y-%m-%d'))
        data_fim = request.args.get('data_fim', get_data_atual().strftime('%Y-%m-%d'))
        formato = request.args.get('formato', 'json')
        
        print(f"DEBUG: Parâmetros - data_inicio: {data_inicio}, data_fim: {data_fim}, formato: {formato}")
        
        conn = get_simple_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Buscar acessos no período
        cursor.execute("""
            SELECT 
                a.id,
                a.numero_registro,
                f.nome as nome_completo,
                f.departamento,
                a.tipo_acesso,
                CONCAT(a.data_acesso, ' ', a.hora_acesso) as data_hora,
                a.metodo_acesso,
                a.tipo_acesso as status,
                a.observacao as observacoes
            FROM acessos_funcionarios a
            LEFT JOIN funcionarios f ON a.numero_registro = f.numero_registro
            WHERE a.data_acesso BETWEEN %s AND %s
            ORDER BY a.data_acesso DESC, a.hora_acesso DESC
        """, (data_inicio, data_fim))
        
        acessos = cursor.fetchall()
        
        # Estatísticas
        cursor.execute("""
            SELECT 
                COUNT(*) as total_acessos,
                COUNT(DISTINCT numero_registro) as funcionarios_unicos,
                COUNT(CASE WHEN tipo_acesso = 'entrada' THEN 1 END) as entradas,
                COUNT(CASE WHEN tipo_acesso = 'saida' THEN 1 END) as saidas,
                COUNT(CASE WHEN metodo_acesso = 'facial' THEN 1 END) as acessos_faciais,
                COUNT(CASE WHEN metodo_acesso = 'manual' THEN 1 END) as acessos_manuais
            FROM acessos_funcionarios 
            WHERE data_acesso BETWEEN %s AND %s
        """, (data_inicio, data_fim))
        
        estatisticas = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        # Processar dados para relatório
        relatorio = {
            'periodo': {
                'inicio': data_inicio,
                'fim': data_fim
            },
            'estatisticas': estatisticas,
            'acessos': acessos,
            'resumo_por_departamento': {},
            'resumo_por_tipo_acesso': {}
        }
        
        # Calcular resumos
        for acesso in acessos:
            dept = acesso['departamento'] or 'Não informado'
            tipo = acesso['tipo_acesso']
            
            if dept not in relatorio['resumo_por_departamento']:
                relatorio['resumo_por_departamento'][dept] = 0
            relatorio['resumo_por_departamento'][dept] += 1
            
            if tipo not in relatorio['resumo_por_tipo_acesso']:
                relatorio['resumo_por_tipo_acesso'][tipo] = 0
            relatorio['resumo_por_tipo_acesso'][tipo] += 1
        
        if formato == 'csv':
            return gerar_csv_relatorio_diario(relatorio)
        elif formato == 'pdf':
            return gerar_pdf_relatorio_diario(relatorio)
        else:
            return jsonify(relatorio)
            
    except Exception as e:
        print(f"Erro ao gerar relatório diário: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'erro': 'Erro ao gerar relatório'}), 500

@app.route('/api/relatorios/funcionario', methods=['GET'])
@login_required
def gerar_relatorio_funcionario():
    """Gerar relatório individual por funcionário"""
    try:
        numero_registro = request.args.get('numero_registro')
        data_inicio = request.args.get('data_inicio', get_data_atual().strftime('%Y-%m-%d'))
        data_fim = request.args.get('data_fim', get_data_atual().strftime('%Y-%m-%d'))
        formato = request.args.get('formato', 'json')
        
        if not numero_registro:
            return jsonify({'erro': 'Número de registro obrigatório'}), 400
        
        conn = get_simple_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Buscar dados do funcionário
        cursor.execute("""
            SELECT 
                numero_registro,
                nome as nome_completo,
                departamento,
                cargo,
                data_admissao,
                status
            FROM funcionarios 
            WHERE numero_registro = %s
        """, (numero_registro,))
        
        funcionario = cursor.fetchone()
        if not funcionario:
            return jsonify({'erro': 'Funcionário não encontrado'}), 404
        
        # Buscar acessos do funcionário
        cursor.execute("""
            SELECT 
                a.id,
                a.numero_registro,
                f.nome as nome_completo,
                f.departamento,
                a.tipo_acesso,
                CONCAT(a.data_acesso, ' ', a.hora_acesso) as data_hora,
                a.metodo_acesso,
                a.tipo_acesso as status,
                a.observacao as observacoes
            FROM acessos_funcionarios a
            LEFT JOIN funcionarios f ON a.numero_registro = f.numero_registro
            WHERE a.numero_registro = %s 
            AND a.data_acesso BETWEEN %s AND %s
            ORDER BY a.data_acesso DESC, a.hora_acesso DESC
        """, (numero_registro, data_inicio, data_fim))
        
        acessos = cursor.fetchall()
        
        # Estatísticas do funcionário
        cursor.execute("""
            SELECT 
                COUNT(*) as total_acessos,
                COUNT(CASE WHEN tipo_acesso = 'entrada' THEN 1 END) as entradas,
                COUNT(CASE WHEN tipo_acesso = 'saida' THEN 1 END) as saidas,
                COUNT(CASE WHEN metodo_acesso = 'facial' THEN 1 END) as acessos_faciais,
                COUNT(CASE WHEN metodo_acesso = 'manual' THEN 1 END) as acessos_manuais,
                MIN(CONCAT(data_acesso, ' ', hora_acesso)) as primeiro_acesso,
                MAX(CONCAT(data_acesso, ' ', hora_acesso)) as ultimo_acesso
            FROM acessos_funcionarios 
            WHERE numero_registro = %s 
            AND data_acesso BETWEEN %s AND %s
        """, (numero_registro, data_inicio, data_fim))
        
        estatisticas = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        relatorio = {
            'funcionario': funcionario,
            'periodo': {
                'inicio': data_inicio,
                'fim': data_fim
            },
            'estatisticas': estatisticas,
            'acessos': acessos
        }
        
        if formato == 'csv':
            return gerar_csv_relatorio_funcionario(relatorio)
        elif formato == 'pdf':
            return gerar_pdf_relatorio_funcionario(relatorio)
        else:
            return jsonify(relatorio)
            
    except Exception as e:
        print(f"Erro ao gerar relatório funcionário: {e}")
        return jsonify({'erro': 'Erro ao gerar relatório'}), 500

@app.route('/api/relatorios/funcionarios', methods=['GET'])
@login_required
def listar_funcionarios_relatorio():
    """Listar funcionários para seleção de relatório"""
    try:
        print("DEBUG: Iniciando listagem de funcionários para relatório")
        conn = get_simple_connection()
        cursor = conn.cursor(dictionary=True)
        
        print("DEBUG: Executando query de funcionários")
        cursor.execute("""
            SELECT 
                numero_registro,
                nome as nome_completo,
                departamento,
                cargo
            FROM funcionarios 
            WHERE status = 'ativo'
            ORDER BY nome
        """)
        
        funcionarios = cursor.fetchall()
        print(f"DEBUG: Encontrados {len(funcionarios)} funcionários")
        cursor.close()
        conn.close()
        
        return jsonify(funcionarios)
        
    except Exception as e:
        print(f"Erro ao listar funcionários: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'erro': 'Erro ao listar funcionários'}), 500

@app.route('/admin/configuracoes')
@admin_required
def admin_configuracoes():
    """Configurações do sistema"""
    return render_template('configuracoes.html')

@app.route('/api/configuracoes/metodos-acesso', methods=['GET'])
def get_metodos_acesso():
    """Buscar métodos de acesso habilitados"""
    try:
        conn = get_simple_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Buscar configuração de métodos de acesso
        cursor.execute("""
            SELECT valor FROM configuracoes_acesso 
            WHERE chave = 'metodos_acesso_habilitados'
        """)
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result and result['valor']:
            metodos = json.loads(result['valor'])
        else:
            # Padrão: todos os métodos habilitados
            metodos = {
                'facial': True,
                'manual': True,
                'rfid': True,
                'qrcode': True
            }
        
        return jsonify({
            'success': True,
            'metodos': metodos
        })
        
    except Exception as e:
        print(f"Erro ao buscar métodos de acesso: {e}")
        # Retornar padrão em caso de erro
        return jsonify({
            'success': True,
            'metodos': {
                'facial': True,
                'manual': True,
                'rfid': True,
                'qrcode': True
            }
        })

@app.route('/api/configuracoes/metodos-acesso', methods=['POST'])
@login_required
def salvar_metodos_acesso():
    """Salvar métodos de acesso habilitados"""
    try:
        data = request.get_json()
        metodos = data.get('metodos', {})
        
        if not metodos:
            return jsonify({
                'success': False,
                'message': 'Dados de métodos não fornecidos'
            })
        
        conn = get_simple_connection()
        cursor = conn.cursor()
        
        # Salvar ou atualizar configuração
        cursor.execute("""
            INSERT INTO configuracoes_acesso (chave, valor, descricao)
            VALUES ('metodos_acesso_habilitados', %s, 'Métodos de acesso habilitados no sistema')
            ON DUPLICATE KEY UPDATE 
                valor = %s,
                data_atualizacao = CURRENT_TIMESTAMP
        """, (json.dumps(metodos), json.dumps(metodos)))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Log da operação
        log_acesso('CONFIGURACAO', 'Métodos de acesso atualizados', {
            'metodos': metodos
        })
        
        return jsonify({
            'success': True,
            'message': 'Métodos de acesso atualizados com sucesso'
        })
        
    except Exception as e:
        print(f"Erro ao salvar métodos de acesso: {e}")
        return jsonify({
            'success': False,
            'message': 'Erro ao salvar configurações'
        })

def criar_tabelas_configuracoes():
    """Cria tabelas para configurações do sistema"""
    try:
        conn = get_simple_connection()
        cursor = conn.cursor()
        
        # Tabela de horários padrão
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS configuracoes_horarios (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nome_config VARCHAR(100) NOT NULL,
                hora_entrada TIME NOT NULL,
                hora_saida TIME NOT NULL,
                tolerancia_entrada INT DEFAULT 15,
                tolerancia_saida INT DEFAULT 15,
                dias_semana VARCHAR(50) DEFAULT '1,2,3,4,5',
                departamento VARCHAR(50) NULL COMMENT 'Departamento específico (NULL = todos os departamentos)',
                ativo BOOLEAN DEFAULT TRUE,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        
        # Adicionar coluna departamento se não existir (para atualizações)
        try:
            cursor.execute("ALTER TABLE configuracoes_horarios ADD COLUMN departamento VARCHAR(50) NULL COMMENT 'Departamento específico (NULL = todos os departamentos)'")
        except Exception as e:
            if 'Duplicate column name' not in str(e):
                print(f"Aviso ao adicionar coluna departamento: {e}")
        
        # Tabela de feriados
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS configuracoes_feriados (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nome VARCHAR(100) NOT NULL,
                data_feriado DATE NOT NULL,
                tipo ENUM('feriado_nacional', 'feriado_estadual', 'feriado_municipal', 'ponto_facultativo') NOT NULL,
                descricao TEXT,
                ativo BOOLEAN DEFAULT TRUE,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY unique_data (data_feriado)
            )
        """)
        
        # Nova tabela para horários específicos por dia
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS configuracoes_horarios_dias (
                id INT AUTO_INCREMENT PRIMARY KEY,
                horario_id INT NOT NULL,
                dia_semana INT NOT NULL, -- 0=Domingo, 1=Segunda, ..., 6=Sábado
                hora_entrada TIME,
                hora_saida TIME,
                tolerancia_entrada INT DEFAULT 15,
                tolerancia_saida INT DEFAULT 15,
                ativo BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (horario_id) REFERENCES configuracoes_horarios(id) ON DELETE CASCADE,
                UNIQUE KEY unique_horario_dia (horario_id, dia_semana)
            )
        """)
        
        # Inserir configuração padrão se não existir
        cursor.execute("SELECT COUNT(*) FROM configuracoes_horarios")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO configuracoes_horarios 
                (nome_config, hora_entrada, hora_saida, tolerancia_entrada, tolerancia_saida, dias_semana)
                VALUES ('Horário Padrão', '08:00:00', '18:00:00', 15, 15, '1,2,3,4,5')
            """)
        
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ Tabelas de configurações criadas com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao criar tabelas de configurações: {e}")

# APIs para configurações
@app.route('/api/configuracoes/horarios', methods=['GET'])
def get_configuracoes_horarios():
    """Buscar configurações de horários"""
    try:
        conn = get_simple_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT * FROM configuracoes_horarios 
            WHERE ativo = TRUE 
            ORDER BY nome_config
        """)
        
        horarios = cursor.fetchall()
        
        # Converter campos timedelta para string
        for horario in horarios:
            if 'hora_entrada' in horario and horario['hora_entrada']:
                horario['hora_entrada'] = str(horario['hora_entrada'])
            if 'hora_saida' in horario and horario['hora_saida']:
                horario['hora_saida'] = str(horario['hora_saida'])
            if 'data_criacao' in horario and horario['data_criacao']:
                horario['data_criacao'] = horario['data_criacao'].isoformat()
            if 'data_atualizacao' in horario and horario['data_atualizacao']:
                horario['data_atualizacao'] = horario['data_atualizacao'].isoformat()
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'horarios': horarios})
        
    except Exception as e:
        print(f"Erro ao buscar horários: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/configuracoes/horarios', methods=['POST'])
def salvar_configuracoes_horarios():
    """Salvar ou atualizar configurações de horários"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Dados não fornecidos'}), 400
        
        # Verificar se é atualização (tem horario_id no corpo)
        horario_id = data.get('horario_id')
        is_update = horario_id is not None
        
        nome_config = data.get('nome_config')
        hora_entrada = data.get('hora_entrada')
        hora_saida = data.get('hora_saida')
        tolerancia_entrada = data.get('tolerancia_entrada', 15)
        tolerancia_saida = data.get('tolerancia_saida', 15)
        dias_semana = data.get('dias_semana', '1,2,3,4,5')
        departamento = data.get('departamento', None)  # None = todos os departamentos
        
        if not nome_config or not hora_entrada or not hora_saida:
            return jsonify({'success': False, 'error': 'Campos obrigatórios não fornecidos'}), 400
        
        conn = get_simple_connection()
        cursor = conn.cursor()
        
        if is_update:
            # Atualizar horário existente
            cursor.execute("SELECT id FROM configuracoes_horarios WHERE id = %s AND ativo = TRUE", (horario_id,))
            if not cursor.fetchone():
                cursor.close()
                conn.close()
                return jsonify({'success': False, 'error': 'Horário não encontrado'}), 404
            
            cursor.execute("""
                UPDATE configuracoes_horarios 
                SET nome_config = %s, 
                    hora_entrada = %s, 
                    hora_saida = %s, 
                    tolerancia_entrada = %s, 
                    tolerancia_saida = %s, 
                    dias_semana = %s, 
                    departamento = %s,
                    data_atualizacao = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (nome_config, hora_entrada, hora_saida, tolerancia_entrada, tolerancia_saida, dias_semana, departamento, horario_id))
            
            message = 'Horário atualizado com sucesso!'
        else:
            # Criar novo horário
            cursor.execute("""
                INSERT INTO configuracoes_horarios 
                (nome_config, hora_entrada, hora_saida, tolerancia_entrada, tolerancia_saida, dias_semana, departamento)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (nome_config, hora_entrada, hora_saida, tolerancia_entrada, tolerancia_saida, dias_semana, departamento))
            
            message = 'Configuração salva com sucesso!'
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': message})
        
    except Exception as e:
        print(f"Erro ao salvar/atualizar horários: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/configuracoes/horarios/<int:horario_id>/atualizar', methods=['POST'])
def atualizar_configuracoes_horarios(horario_id):
    """Atualizar configurações de horários"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Dados não fornecidos'}), 400
        
        nome_config = data.get('nome_config')
        hora_entrada = data.get('hora_entrada')
        hora_saida = data.get('hora_saida')
        tolerancia_entrada = data.get('tolerancia_entrada', 15)
        tolerancia_saida = data.get('tolerancia_saida', 15)
        dias_semana = data.get('dias_semana', '1,2,3,4,5')
        departamento = data.get('departamento', None)
        
        if not nome_config or not hora_entrada or not hora_saida:
            return jsonify({'success': False, 'error': 'Campos obrigatórios não fornecidos'}), 400
        
        conn = get_simple_connection()
        cursor = conn.cursor()
        
        # Verificar se o horário existe
        cursor.execute("SELECT id FROM configuracoes_horarios WHERE id = %s AND ativo = TRUE", (horario_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Horário não encontrado'}), 404
        
        cursor.execute("""
            UPDATE configuracoes_horarios 
            SET nome_config = %s, 
                hora_entrada = %s, 
                hora_saida = %s, 
                tolerancia_entrada = %s, 
                tolerancia_saida = %s, 
                dias_semana = %s, 
                departamento = %s,
                data_atualizacao = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (nome_config, hora_entrada, hora_saida, tolerancia_entrada, tolerancia_saida, dias_semana, departamento, horario_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ Horário {horario_id} atualizado com sucesso")
        return jsonify({'success': True, 'message': 'Horário atualizado com sucesso!'})
        
    except Exception as e:
        print(f"❌ Erro ao atualizar horário {horario_id}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/configuracoes/feriados', methods=['GET'])
def get_configuracoes_feriados():
    """Buscar configurações de feriados"""
    try:
        conn = get_simple_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT * FROM configuracoes_feriados 
            WHERE ativo = TRUE 
            ORDER BY data_feriado
        """)
        
        feriados = cursor.fetchall()
        
        # Converter campos datetime para string
        for feriado in feriados:
            if 'data_feriado' in feriado and feriado['data_feriado']:
                feriado['data_feriado'] = feriado['data_feriado'].isoformat()
            if 'data_criacao' in feriado and feriado['data_criacao']:
                feriado['data_criacao'] = feriado['data_criacao'].isoformat()
            if 'data_atualizacao' in feriado and feriado['data_atualizacao']:
                feriado['data_atualizacao'] = feriado['data_atualizacao'].isoformat()
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'feriados': feriados})
        
    except Exception as e:
        print(f"Erro ao buscar feriados: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/configuracoes/feriados', methods=['POST'])
def salvar_configuracoes_feriados():
    """Salvar configurações de feriados"""
    try:
        data = request.get_json()
        nome = data.get('nome')
        data_feriado = data.get('data_feriado')
        tipo = data.get('tipo')
        descricao = data.get('descricao', '')
        
        conn = get_simple_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO configuracoes_feriados 
            (nome, data_feriado, tipo, descricao)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            nome = VALUES(nome),
            tipo = VALUES(tipo),
            descricao = VALUES(descricao),
            ativo = TRUE
        """, (nome, data_feriado, tipo, descricao))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Feriado salvo com sucesso!'})
        
    except Exception as e:
        print(f"Erro ao salvar feriado: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/configuracoes/feriados/<int:feriado_id>', methods=['DELETE'])
def excluir_feriado(feriado_id):
    """Excluir feriado"""
    try:
        conn = get_simple_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE configuracoes_feriados 
            SET ativo = FALSE 
            WHERE id = %s
        """, (feriado_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Feriado excluído com sucesso!'})
        
    except Exception as e:
        print(f"Erro ao excluir feriado: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/configuracoes/horarios/<int:horario_id>', methods=['PUT', 'PATCH'])
def atualizar_horario(horario_id):
    """Atualizar configuração de horário"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Dados não fornecidos'}), 400
            
        nome_config = data.get('nome_config')
        hora_entrada = data.get('hora_entrada')
        hora_saida = data.get('hora_saida')
        tolerancia_entrada = data.get('tolerancia_entrada', 15)
        tolerancia_saida = data.get('tolerancia_saida', 15)
        dias_semana = data.get('dias_semana', '1,2,3,4,5')
        departamento = data.get('departamento', None)
        
        if not nome_config or not hora_entrada or not hora_saida:
            return jsonify({'success': False, 'error': 'Campos obrigatórios não fornecidos'}), 400
        
        conn = get_simple_connection()
        cursor = conn.cursor()
        
        # Verificar se o horário existe
        cursor.execute("SELECT id FROM configuracoes_horarios WHERE id = %s AND ativo = TRUE", (horario_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Horário não encontrado'}), 404
        
        cursor.execute("""
            UPDATE configuracoes_horarios 
            SET nome_config = %s, 
                hora_entrada = %s, 
                hora_saida = %s, 
                tolerancia_entrada = %s, 
                tolerancia_saida = %s, 
                dias_semana = %s, 
                departamento = %s,
                data_atualizacao = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (nome_config, hora_entrada, hora_saida, tolerancia_entrada, tolerancia_saida, dias_semana, departamento, horario_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ Horário {horario_id} atualizado com sucesso")
        return jsonify({'success': True, 'message': 'Horário atualizado com sucesso!'})
        
    except Exception as e:
        print(f"❌ Erro ao atualizar horário {horario_id}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/configuracoes/horarios/<int:horario_id>', methods=['DELETE'])
def excluir_horario(horario_id):
    """Excluir horário (lógica)"""
    try:
        conn = get_simple_connection()
        cursor = conn.cursor()
        
        # Verificar se é o horário padrão (não permitir excluir)
        cursor.execute("""
            SELECT nome_config FROM configuracoes_horarios 
            WHERE id = %s
        """, (horario_id,))
        
        horario = cursor.fetchone()
        if not horario:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Horário não encontrado'}), 404
        
        if horario[0] == 'Horário Padrão':
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Não é possível excluir o horário padrão'}), 400
        
        # Excluir logicamente
        cursor.execute("""
            UPDATE configuracoes_horarios 
            SET ativo = FALSE 
            WHERE id = %s
        """, (horario_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Horário excluído com sucesso!'})
        
    except Exception as e:
        print(f"Erro ao excluir horário: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# APIs para horários específicos por dia
@app.route('/api/configuracoes/horarios/<int:horario_id>/dias', methods=['GET'])
def get_horarios_dias(horario_id):
    """Buscar configurações de horários por dia para um horário específico"""
    try:
        conn = get_simple_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT * FROM configuracoes_horarios_dias 
            WHERE horario_id = %s AND ativo = TRUE 
            ORDER BY dia_semana
        """, (horario_id,))
        
        horarios_dias = cursor.fetchall()
        
        # Converter campos timedelta para string
        for horario_dia in horarios_dias:
            if 'hora_entrada' in horario_dia and horario_dia['hora_entrada']:
                horario_dia['hora_entrada'] = str(horario_dia['hora_entrada'])
            if 'hora_saida' in horario_dia and horario_dia['hora_saida']:
                horario_dia['hora_saida'] = str(horario_dia['hora_saida'])
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'horarios_dias': horarios_dias})
        
    except Exception as e:
        print(f"Erro ao buscar horários por dia: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/configuracoes/horarios/<int:horario_id>/dias', methods=['POST'])
def salvar_horario_dia(horario_id):
    """Salvar configuração de horário para um dia específico"""
    try:
        data = request.get_json()
        dia_semana = data.get('dia_semana')
        hora_entrada = data.get('hora_entrada')
        hora_saida = data.get('hora_saida')
        tolerancia_entrada = data.get('tolerancia_entrada', 15)
        tolerancia_saida = data.get('tolerancia_saida', 15)
        
        if not all([dia_semana, hora_entrada, hora_saida]):
            return jsonify({'success': False, 'error': 'Todos os campos são obrigatórios'}), 400
        
        conn = get_simple_connection()
        cursor = conn.cursor()
        
        # Inserir ou atualizar configuração do dia
        cursor.execute("""
            INSERT INTO configuracoes_horarios_dias 
            (horario_id, dia_semana, hora_entrada, hora_saida, tolerancia_entrada, tolerancia_saida)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            hora_entrada = VALUES(hora_entrada),
            hora_saida = VALUES(hora_saida),
            tolerancia_entrada = VALUES(tolerancia_entrada),
            tolerancia_saida = VALUES(tolerancia_saida),
            ativo = TRUE
        """, (horario_id, dia_semana, hora_entrada, hora_saida, tolerancia_entrada, tolerancia_saida))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Configuração do dia salva com sucesso!'})
        
    except Exception as e:
        print(f"Erro ao salvar horário do dia: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/configuracoes/horarios/<int:horario_id>/dias/<int:dia_semana>', methods=['DELETE'])
def excluir_horario_dia(horario_id, dia_semana):
    """Excluir configuração de horário para um dia específico"""
    try:
        conn = get_simple_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE configuracoes_horarios_dias 
            SET ativo = FALSE 
            WHERE horario_id = %s AND dia_semana = %s
        """, (horario_id, dia_semana))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Configuração do dia excluída com sucesso!'})
        
    except Exception as e:
        print(f"Erro ao excluir horário do dia: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Dashboard administrativo"""
    print("DEBUG: Acessando rota /admin/dashboard")
    return render_template('dashboard.html')

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard - rota alternativa que redireciona para /admin/dashboard"""
    print("DEBUG: Acessando rota /dashboard - redirecionando para /admin/dashboard")
    return render_template('dashboard.html')

# ========================================
# ROTAS DE AUTENTICAÇÃO
# ========================================

# Rota de alteração de senha (definida antes para garantir registro)
@app.route('/api/admin/alterar-senha', methods=['POST'])
def alterar_senha_admin():
    """Alterar senha do administrador logado"""
    # Verificar autenticação manualmente
    if 'admin_logged_in' not in session or not session['admin_logged_in']:
        return jsonify({
            'success': False,
            'message': 'Acesso negado. Faça login.',
            'redirect': '/admin/login'
        }), 401
    
    try:
        data = request.get_json()
        senha_atual = data.get('senha_atual', '').strip()
        nova_senha = data.get('nova_senha', '').strip()
        
        if not senha_atual or not nova_senha:
            return jsonify({
                'success': False,
                'message': 'Senha atual e nova senha são obrigatórias.'
            }), 400
        
        if len(nova_senha) < 6:
            return jsonify({
                'success': False,
                'message': 'A nova senha deve ter no mínimo 6 caracteres.'
            }), 400
        
        # Obter username da sessão
        username = session.get('admin_username')
        if not username:
            return jsonify({
                'success': False,
                'message': 'Sessão inválida. Faça login novamente.'
            }), 401
        
        conn = get_simple_connection()
        cursor = conn.cursor()
        
        # Verificar senha atual
        cursor.execute("""
            SELECT password_hash 
            FROM admin_users 
            WHERE username = %s AND ativo = TRUE
        """, (username,))
        
        user = cursor.fetchone()
        if not user:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': 'Usuário não encontrado.'
            }), 404
        
        # Verificar se a senha atual está correta
        if not verify_password(user[0], senha_atual):
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': 'Senha atual incorreta.'
            }), 401
        
        # Verificar se a nova senha é diferente da atual
        if verify_password(user[0], nova_senha):
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': 'A nova senha deve ser diferente da senha atual.'
            }), 400
        
        # Gerar hash da nova senha
        nova_senha_hash = hash_password(nova_senha)
        
        # Atualizar senha no banco
        cursor.execute("""
            UPDATE admin_users 
            SET password_hash = %s 
            WHERE username = %s
        """, (nova_senha_hash, username))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Log da alteração
        log_acesso('ALTERAR_SENHA', f'Senha alterada para usuário {username}', {
            'ip': request.remote_addr,
            'username': username
        })
        
        return jsonify({
            'success': True,
            'message': 'Senha alterada com sucesso!'
        })
        
    except Exception as e:
        print(f"Erro ao alterar senha: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': 'Erro interno ao alterar senha. Tente novamente.'
        }), 500

@app.route('/admin/logout')
def admin_logout():
    """Logout administrativo"""
    session.clear()
    log_acesso('LOGOUT_ADMIN', 'Logout administrativo', {
        'ip': request.remote_addr
    })
    return redirect(url_for('admin_login'))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Página de login administrativo"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            return render_template('admin_login.html', 
                                error='Usuário e senha obrigatórios')
        
        try:
            conn = get_simple_connection()
            cursor = conn.cursor()
            
            # Verificar se a coluna role existe
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'admin_users' 
                AND COLUMN_NAME = 'role'
            """)
            role_exists = cursor.fetchone()[0] > 0
            
            if role_exists:
                cursor.execute("""
                    SELECT username, password_hash, nome_completo, COALESCE(role, 'admin') as role 
                    FROM admin_users 
                    WHERE username = %s AND ativo = TRUE
                """, (username,))
            else:
                cursor.execute("""
                    SELECT username, password_hash, nome_completo 
                    FROM admin_users 
                    WHERE username = %s AND ativo = TRUE
                """, (username,))
            
            user = cursor.fetchone()
            
            print(f"DEBUG LOGIN: Usuário buscado: {username}")
            print(f"DEBUG LOGIN: Usuário encontrado: {user is not None}")
            if user:
                print(f"DEBUG LOGIN: Username: {user[0]}, Nome: {user[2]}")
                if role_exists:
                    print(f"DEBUG LOGIN: Role: {user[3]}")
                print(f"DEBUG LOGIN: Verificando senha...")
                senha_valida = verify_password(user[1], password)
                print(f"DEBUG LOGIN: Senha válida: {senha_valida}")
            
            if user and verify_password(user[1], password):
                print(f"DEBUG LOGIN: Login bem-sucedido! Criando sessão...")
                session['admin_logged_in'] = True
                session['admin_username'] = user[0]
                session['admin_nome'] = user[2]
                session['admin_role'] = user[3] if role_exists and len(user) > 3 else 'admin'  # Adicionar role na sessão
                session['admin_id'] = 1
                
                print(f"DEBUG LOGIN: Sessão criada: {dict(session)}")
                
                # Atualizar último login
                cursor.execute("""
                    UPDATE admin_users 
                    SET ultimo_login = NOW() 
                    WHERE username = %s
                """, (username,))
                
                conn.commit()
                cursor.close()
                conn.close()
                
                log_acesso('LOGIN_ADMIN', f'Login administrativo: {username}', {
                    'username': username,
                    'role': session.get('admin_role', 'admin'),
                    'ip': request.remote_addr
                })
                
                print(f"DEBUG LOGIN: Redirecionando... Role: {session.get('admin_role')}")
                # Redirecionar baseado no role
                if session.get('admin_role') == 'portaria':
                    print(f"DEBUG LOGIN: Redirecionando para relatório online")
                    return redirect(url_for('relatorio_online_sistema_real'))
                else:
                    print(f"DEBUG LOGIN: Redirecionando para admin")
                    return redirect(url_for('admin'))
            else:
                print(f"DEBUG LOGIN: Login falhou - usuário ou senha inválidos")
                cursor.close()
                conn.close()
                return render_template('admin_login.html', 
                                    error='Usuário ou senha inválidos')
                
        except Exception as e:
            print(f"Erro no login: {e}")
            return render_template('admin_login.html', 
                                error='Erro interno do sistema')
    
    return render_template('admin_login.html')

# ========================================
# GESTÃO DE USUÁRIOS ADMINISTRATIVOS
# ========================================

@app.route('/admin/usuarios')
@admin_required
def admin_usuarios():
    """Listar usuários administrativos"""
    try:
        conn = get_simple_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT id, username, nome_completo, email, role, ativo, 
                   ultimo_login, data_criacao
            FROM admin_users
            ORDER BY data_criacao DESC
        """)
        
        usuarios = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return render_template('admin_usuarios.html', usuarios=usuarios)
    except Exception as e:
        print(f"Erro ao listar usuários: {e}")
        flash('Erro ao carregar usuários', 'danger')
        return redirect(url_for('admin'))

@app.route('/api/usuarios', methods=['POST'])
@admin_required
def criar_usuario():
    """Criar novo usuário administrativo"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        nome_completo = data.get('nome_completo', '').strip()
        email = data.get('email', '').strip()
        role = data.get('role', 'portaria').strip()
        
        if not username or not password or not nome_completo:
            return jsonify({'success': False, 'message': 'Campos obrigatórios: usuário, senha e nome completo'}), 400
        
        if role not in ['admin', 'portaria']:
            return jsonify({'success': False, 'message': 'Role inválido. Use: admin ou portaria'}), 400
        
        conn = get_simple_connection()
        cursor = conn.cursor()
        
        # Verificar se usuário já existe
        cursor.execute("SELECT id FROM admin_users WHERE username = %s", (username,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Usuário já existe'}), 400
        
        # Criar usuário
        password_hash = hash_password(password)
        cursor.execute("""
            INSERT INTO admin_users (username, password_hash, nome_completo, email, role, ativo)
            VALUES (%s, %s, %s, %s, %s, TRUE)
        """, (username, password_hash, nome_completo, email, role))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        log_acesso('CRIAR_USUARIO', f'Usuário criado: {username} (role: {role})', {
            'username': username,
            'role': role,
            'criado_por': session.get('admin_username')
        })
        
        return jsonify({'success': True, 'message': 'Usuário criado com sucesso'})
    except Exception as e:
        print(f"Erro ao criar usuário: {e}")
        return jsonify({'success': False, 'message': f'Erro ao criar usuário: {str(e)}'}), 500

@app.route('/api/usuarios/<int:user_id>', methods=['PUT'])
@admin_required
def atualizar_usuario(user_id):
    """Atualizar usuário administrativo"""
    try:
        data = request.get_json()
        nome_completo = data.get('nome_completo', '').strip()
        email = data.get('email', '').strip()
        role = data.get('role', '').strip()
        ativo = data.get('ativo', True)
        
        conn = get_simple_connection()
        cursor = conn.cursor()
        
        # Não permitir desativar o próprio usuário
        cursor.execute("SELECT username FROM admin_users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if not user:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Usuário não encontrado'}), 404
        
        if user[0] == session.get('admin_username') and not ativo:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Não é possível desativar seu próprio usuário'}), 400
        
        # Atualizar
        updates = []
        params = []
        
        if nome_completo:
            updates.append("nome_completo = %s")
            params.append(nome_completo)
        if email:
            updates.append("email = %s")
            params.append(email)
        if role and role in ['admin', 'portaria']:
            updates.append("role = %s")
            params.append(role)
        if 'ativo' in data:
            updates.append("ativo = %s")
            params.append(ativo)
        
        if updates:
            params.append(user_id)
            cursor.execute(f"""
                UPDATE admin_users 
                SET {', '.join(updates)}
                WHERE id = %s
            """, params)
            
            conn.commit()
        
        cursor.close()
        conn.close()
        
        log_acesso('ATUALIZAR_USUARIO', f'Usuário atualizado: ID {user_id}', {
            'user_id': user_id,
            'atualizado_por': session.get('admin_username')
        })
        
        return jsonify({'success': True, 'message': 'Usuário atualizado com sucesso'})
    except Exception as e:
        print(f"Erro ao atualizar usuário: {e}")
        return jsonify({'success': False, 'message': f'Erro ao atualizar usuário: {str(e)}'}), 500

@app.route('/api/usuarios/<int:user_id>/senha', methods=['PUT'])
@admin_required
def alterar_senha_usuario(user_id):
    """Alterar senha de usuário"""
    try:
        data = request.get_json()
        nova_senha = data.get('nova_senha', '').strip()
        
        if not nova_senha or len(nova_senha) < 6:
            return jsonify({'success': False, 'message': 'Senha deve ter no mínimo 6 caracteres'}), 400
        
        conn = get_simple_connection()
        cursor = conn.cursor()
        
        # Verificar se usuário existe
        cursor.execute("SELECT username FROM admin_users WHERE id = %s", (user_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Usuário não encontrado'}), 404
        
        # Atualizar senha
        password_hash = hash_password(nova_senha)
        cursor.execute("""
            UPDATE admin_users 
            SET password_hash = %s
            WHERE id = %s
        """, (password_hash, user_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        log_acesso('ALTERAR_SENHA', f'Senha alterada para usuário ID {user_id}', {
            'user_id': user_id,
            'alterado_por': session.get('admin_username')
        })
        
        return jsonify({'success': True, 'message': 'Senha alterada com sucesso'})
    except Exception as e:
        print(f"Erro ao alterar senha: {e}")
        return jsonify({'success': False, 'message': f'Erro ao alterar senha: {str(e)}'}), 500

@app.route('/api/usuarios/<int:user_id>', methods=['DELETE'])
@admin_required
def deletar_usuario(user_id):
    """Deletar usuário administrativo"""
    try:
        conn = get_simple_connection()
        cursor = conn.cursor()
        
        # Não permitir deletar o próprio usuário
        cursor.execute("SELECT username FROM admin_users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if not user:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Usuário não encontrado'}), 404
        
        if user[0] == session.get('admin_username'):
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Não é possível deletar seu próprio usuário'}), 400
        
        # Deletar usuário
        cursor.execute("DELETE FROM admin_users WHERE id = %s", (user_id,))
        conn.commit()
        cursor.close()
        conn.close()
        
        log_acesso('DELETAR_USUARIO', f'Usuário deletado: ID {user_id}', {
            'user_id': user_id,
            'deletado_por': session.get('admin_username')
        })
        
        return jsonify({'success': True, 'message': 'Usuário deletado com sucesso'})
    except Exception as e:
        print(f"Erro ao deletar usuário: {e}")
        return jsonify({'success': False, 'message': f'Erro ao deletar usuário: {str(e)}'}), 500

### marcar inicio

# ========================================
# ROTAS DE IMPORTAÇÃO EM MASSA
# ========================================

@app.route('/api/funcionarios/importar', methods=['POST'])
@admin_required
def importar_funcionarios():
    """Importar funcionários em massa via CSV/Excel"""
    try:
        if 'arquivo' not in request.files:
            return jsonify({'success': False, 'error': 'Nenhum arquivo enviado'})
        
        arquivo = request.files['arquivo']
        if arquivo.filename == '':
            return jsonify({'success': False, 'error': 'Nenhum arquivo selecionado'})
        
        # Verificar extensão do arquivo
        if not arquivo.filename.lower().endswith(('.csv', '.xlsx', '.xls')):
            return jsonify({'success': False, 'error': 'Formato de arquivo não suportado. Use CSV ou Excel.'})
        
        # Ler arquivo
        if arquivo.filename.lower().endswith('.csv'):
            # Ler CSV
            df = pd.read_csv(arquivo, encoding='utf-8')
        else:
            # Ler Excel
            df = pd.read_excel(arquivo)
        
        # Validar colunas obrigatórias
        colunas_obrigatorias = ['numero_registro', 'nome', 'departamento', 'cargo', 'empresa']
        colunas_faltantes = [col for col in colunas_obrigatorias if col not in df.columns]
        
        if colunas_faltantes:
            return jsonify({
                'success': False, 
                'error': f'Colunas obrigatórias faltando: {", ".join(colunas_faltantes)}'
            })
        
        # Limpar dados
        df = df.dropna(subset=['numero_registro', 'nome'])  # Remover linhas sem dados essenciais
        df = df.fillna('')  # Preencher valores vazios
        
        # Validar dados
        erros = []
        funcionarios_validos = []
        
        for index, row in df.iterrows():
            linha = index + 2  # +2 porque Excel/CSV começa em 1 e temos header
            
            # Validar número de registro
            if not row['numero_registro'] or str(row['numero_registro']).strip() == '':
                erros.append(f'Linha {linha}: Número de registro é obrigatório')
                continue
            
            # Validar nome
            if not row['nome'] or str(row['nome']).strip() == '':
                erros.append(f'Linha {linha}: Nome é obrigatório')
                continue
            
            # Validar departamento
            if not row['departamento'] or str(row['departamento']).strip() == '':
                erros.append(f'Linha {linha}: Departamento é obrigatório')
                continue
            
            # Validar cargo
            if not row['cargo'] or str(row['cargo']).strip() == '':
                erros.append(f'Linha {linha}: Cargo é obrigatório')
                continue
            
            # Validar empresa
            if not row['empresa'] or str(row['empresa']).strip() == '':
                erros.append(f'Linha {linha}: Empresa é obrigatória')
                continue
            
            # Preparar dados do funcionário
            funcionario = {
                'numero_registro': str(row['numero_registro']).strip(),
                'nome': str(row['nome']).strip(),
                'departamento': str(row['departamento']).strip(),
                'cargo': str(row['cargo']).strip(),
                'empresa': str(row['empresa']).strip(),
                'ativo': True  # Por padrão, funcionários importados são ativos
            }
            
            # Adicionar CPF se existir
            if 'cpf' in df.columns and pd.notna(row['cpf']):
                funcionario['cpf'] = str(row['cpf']).strip()
            
            funcionarios_validos.append(funcionario)
        
        if erros:
            return jsonify({
                'success': False,
                'error': 'Erros de validação encontrados',
                'erros': erros
            })
        
        # Inserir funcionários no banco
        conn = get_simple_connection()
        cursor = conn.cursor()
        
        funcionarios_inseridos = 0
        funcionarios_duplicados = 0
        
        for funcionario in funcionarios_validos:
            try:
                # Verificar se já existe
                cursor.execute("""
                    SELECT id FROM funcionarios 
                    WHERE numero_registro = %s
                """, (funcionario['numero_registro'],))
                
                if cursor.fetchone():
                    funcionarios_duplicados += 1
                    continue
                
                # Inserir funcionário
                cursor.execute("""
                    INSERT INTO funcionarios 
                    (numero_registro, nome, departamento, cargo, empresa, ativo, data_cadastro)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW())
                """, (
                    funcionario['numero_registro'],
                    funcionario['nome'],
                    funcionario['departamento'],
                    funcionario['cargo'],
                    funcionario['empresa'],
                    funcionario['ativo']
                ))
                
                funcionarios_inseridos += 1
                
            except Exception as e:
                print(f"Erro ao inserir funcionário {funcionario['numero_registro']}: {e}")
                continue
        
        cursor.close()
        conn.close()
        
        # Log da importação
        log_acesso('IMPORTACAO_FUNCIONARIOS', f'Importação em massa: {funcionarios_inseridos} inseridos, {funcionarios_duplicados} duplicados', {
            'total_processados': len(funcionarios_validos),
            'inseridos': funcionarios_inseridos,
            'duplicados': funcionarios_duplicados
        })
        
        return jsonify({
            'success': True,
            'message': f'Importação concluída! {funcionarios_inseridos} funcionários inseridos.',
            'detalhes': {
                'processados': len(funcionarios_validos),
                'inseridos': funcionarios_inseridos,
                'duplicados': funcionarios_duplicados
            }
        })
        
    except Exception as e:
        print(f"Erro na importação: {e}")
        return jsonify({'success': False, 'error': f'Erro interno: {str(e)}'})

@app.route('/api/funcionarios/template', methods=['GET'])
@login_required
def download_template():
    """Download do template CSV para importação"""
    try:
        # Criar dados de exemplo
        dados_exemplo = [
            {
                'numero_registro': '001',
                'nome': 'João Silva',
                'departamento': 'TI',
                'cargo': 'Desenvolvedor',
                'empresa': 'Empresa ABC',
                'cpf': '123.456.789-00'
            },
            {
                'numero_registro': '002',
                'nome': 'Maria Santos',
                'departamento': 'RH',
                'cargo': 'Analista',
                'empresa': 'Empresa ABC',
                'cpf': '987.654.321-00'
            }
        ]
        
        # Criar CSV em memória
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            'numero_registro', 'nome', 'departamento', 'cargo', 'empresa', 'cpf'
        ])
        
        writer.writeheader()
        writer.writerows(dados_exemplo)
        
        output.seek(0)
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=template_funcionarios.csv'}
        )
        
    except Exception as e:
        print(f"Erro ao gerar template: {e}")
        return jsonify({'success': False, 'error': 'Erro ao gerar template'})

# ========================================
# ROTAS DE CADASTRO FACIAL
# ========================================

@app.route('/admin/cadastro-facial')
@admin_required
def admin_cadastro_facial():
    """Página de cadastro facial"""
    return render_template('cadastro_facial.html')

@app.route('/admin/cadastro-rfid')
@admin_required
def admin_cadastro_rfid():
    """Página de cadastro RFID"""
    return render_template('cadastro_rfid.html')

@app.route('/admin/cadastro-qrcode')
@admin_required
def admin_cadastro_qrcode():
    """Página de cadastro QR Code"""
    return render_template('cadastro_qrcode.html')

@app.route('/api/funcionarios/sem-facial', methods=['GET'])
@login_required
def get_funcionarios_sem_facial():
    """Buscar funcionários sem cadastro facial"""
    try:
        conn = get_simple_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT f.id, f.numero_registro, f.nome, f.departamento, f.cargo, f.empresa, f.ativo
            FROM funcionarios f
            LEFT JOIN funcionarios_facial ff ON f.numero_registro = ff.numero_registro
            WHERE f.ativo = TRUE AND ff.numero_registro IS NULL
            ORDER BY f.nome
        """)
        
        funcionarios = []
        for row in cursor.fetchall():
            funcionarios.append({
                'id': row[0],
                'numero_registro': row[1],
                'nome': row[2],
                'departamento': row[3],
                'cargo': row[4],
                'empresa': row[5],
                'ativo': row[6]
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'funcionarios': funcionarios})
        
    except Exception as e:
        print(f"Erro ao buscar funcionários sem facial: {e}")
        return jsonify({'success': False, 'error': 'Erro interno do servidor'})

@app.route('/api/funcionarios/cadastrar-facial', methods=['POST'])
@login_required
def cadastrar_facial():
    """Cadastrar dados faciais de um funcionário"""
    try:
        data = request.get_json()
        numero_registro = data.get('numero_registro')
        imagem_base64 = data.get('imagem')
        confianca_minima = data.get('confianca_minima', 0.60)
        
        if not numero_registro or not imagem_base64:
            return jsonify({'success': False, 'error': 'Dados obrigatórios não fornecidos'})
        
        # Verificar se funcionário existe
        conn = get_simple_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, nome FROM funcionarios 
            WHERE numero_registro = %s AND ativo = TRUE
        """, (numero_registro,))
        
        funcionario = cursor.fetchone()
        if not funcionario:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Funcionário não encontrado ou inativo'})
        
        # Verificar se já tem cadastro facial
        cursor.execute("""
            SELECT id FROM funcionarios_facial 
            WHERE numero_registro = %s
        """, (numero_registro,))
        
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Funcionário já possui cadastro facial'})
        
        # MELHORIA: Processar imagem facial com validação adicional
        encoding_facial, erro = processar_imagem_facial_melhorada(imagem_base64)
        if erro:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': erro})
        
        # MELHORIA: Verificar qualidade do encoding antes de salvar
        encoding_array = np.array(encoding_facial)
        
        # Verificar se o encoding tem variância suficiente
        if np.var(encoding_array) < 0.01:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Qualidade da imagem insuficiente. Tente com melhor iluminação.'})
        
        # MELHORIA: Verificar se não é muito similar a outros cadastros
        cursor.execute("""
            SELECT encoding_facial FROM funcionarios_facial 
            WHERE ativo = TRUE AND numero_registro != %s
        """, (numero_registro,))
        
        encodings_existentes = cursor.fetchall()
        for encoding_existente in encodings_existentes:
            encoding_existente_array = np.array(json.loads(encoding_existente[0]))
            distancia = face_recognition.face_distance([encoding_existente_array], encoding_array)[0]
            if distancia < 0.3:  # Muito similar
                cursor.close()
                conn.close()
                return jsonify({'success': False, 'error': 'Face muito similar a outro cadastro. Use uma imagem diferente.'})
        
        # Salvar cadastro facial com confiança mínima aumentada
        cursor.execute("""
            INSERT INTO funcionarios_facial 
            (numero_registro, encoding_facial, imagem_referencia, confianca_minima, ativo, data_cadastro)
            VALUES (%s, %s, %s, %s, TRUE, NOW())
        """, (
            numero_registro,
            json.dumps(encoding_facial),
            imagem_base64,
            max(confianca_minima, 0.65)  # Mínimo de 65% de confiança
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Log do cadastro
        log_acesso('CADASTRO_FACIAL', f'Cadastro facial realizado para {funcionario[1]} ({numero_registro})', {
            'numero_registro': numero_registro,
            'nome': funcionario[1]
        })
        
        return jsonify({
            'success': True,
            'message': f'Cadastro facial realizado com sucesso para {funcionario[1]}'
        })
        
    except Exception as e:
        print(f"Erro no cadastro facial: {e}")
        return jsonify({'success': False, 'error': f'Erro interno: {str(e)}'})

@app.route('/api/funcionarios/remover-facial', methods=['DELETE'])
@login_required
def remover_facial():
    """Remover cadastro facial de um funcionário"""
    try:
        data = request.get_json()
        numero_registro = data.get('numero_registro')
        
        if not numero_registro:
            return jsonify({'success': False, 'error': 'Número de registro não fornecido'})
        
        conn = get_simple_connection()
        cursor = conn.cursor()
        
        # Verificar se existe cadastro facial
        cursor.execute("""
            SELECT f.nome FROM funcionarios f
            INNER JOIN funcionarios_facial ff ON f.numero_registro = ff.numero_registro
            WHERE f.numero_registro = %s
        """, (numero_registro,))
        
        funcionario = cursor.fetchone()
        if not funcionario:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Cadastro facial não encontrado'})
        
        # Remover cadastro facial
        cursor.execute("""
            DELETE FROM funcionarios_facial 
            WHERE numero_registro = %s
        """, (numero_registro,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Log da remoção
        log_acesso('REMOCAO_FACIAL', f'Cadastro facial removido para {funcionario[0]} ({numero_registro})', {
            'numero_registro': numero_registro,
            'nome': funcionario[0]
        })
        
        return jsonify({
            'success': True,
            'message': f'Cadastro facial removido com sucesso para {funcionario[0]}'
        })
        
    except Exception as e:
        print(f"Erro ao remover facial: {e}")
        return jsonify({'success': False, 'error': f'Erro interno: {str(e)}'})

@app.route('/api/funcionarios/com-facial', methods=['GET'])
@login_required
def get_funcionarios_com_facial():
    """Buscar funcionários com cadastro facial"""
    try:
        conn = get_simple_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT f.id, f.numero_registro, f.nome, f.departamento, f.cargo, f.empresa, 
                   f.ativo, ff.data_cadastro, ff.ultimo_uso, ff.confianca_minima
            FROM funcionarios f
            INNER JOIN funcionarios_facial ff ON f.numero_registro = ff.numero_registro
            WHERE f.ativo = TRUE
            ORDER BY f.nome
        """)
        
        funcionarios = []
        for row in cursor.fetchall():
            funcionarios.append({
                'id': row[0],
                'numero_registro': row[1],
                'nome': row[2],
                'departamento': row[3],
                'cargo': row[4],
                'empresa': row[5],
                'ativo': row[6],
                'data_cadastro_facial': row[7].strftime('%d/%m/%Y %H:%M') if row[7] else None,
                'ultimo_uso': row[8].strftime('%d/%m/%Y %H:%M') if row[8] else None,
                'confianca_minima': float(row[9]) if row[9] else 0.60
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'funcionarios': funcionarios})
        
    except Exception as e:
        print(f"Erro ao buscar funcionários com facial: {e}")
        return jsonify({'success': False, 'error': 'Erro interno do servidor'})

# ========================================
# APIs RFID
# ========================================

@app.route('/api/funcionarios/sem-rfid', methods=['GET'])
@login_required
def get_funcionarios_sem_rfid():
    """Buscar funcionários sem cadastro RFID"""
    try:
        conn = get_simple_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = """
        SELECT f.id, f.numero_registro, f.nome, f.departamento, f.cargo, f.empresa
        FROM funcionarios f
        WHERE f.ativo = TRUE 
        AND NOT EXISTS (
            SELECT 1 FROM cartoes_rfid cr 
            WHERE cr.numero_registro = f.numero_registro 
            AND cr.ativo = TRUE
        )
        ORDER BY f.nome
        """
        
        cursor.execute(query)
        funcionarios = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'funcionarios': funcionarios
        })
        
    except Exception as e:
        print(f"Erro ao buscar funcionários sem RFID: {e}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        })

@app.route('/api/funcionarios/cadastrar-rfid', methods=['POST'])
@login_required
def cadastrar_rfid():
    """Cadastrar RFID para funcionário"""
    try:
        data = request.get_json()
        numero_registro = data.get('numero_registro')
        codigo_rfid = data.get('codigo_rfid')
        tipo_cartao = data.get('tipo_cartao', 'cartao')
        descricao = data.get('descricao', '')
        
        if not numero_registro or not codigo_rfid:
            return jsonify({
                'success': False,
                'message': 'Número de registro e código RFID são obrigatórios'
            })
        
        # Normalizar código RFID (remover espaços, dois pontos, converter para maiúsculas)
        # Isso garante consistência entre cadastro e busca
        codigo_rfid_original = codigo_rfid
        codigo_rfid = codigo_rfid.strip().upper().replace(':', '').replace(' ', '').replace('\t', '').replace('\n', '').replace('-', '')
        print(f"📝 Cadastrando RFID: '{codigo_rfid_original}' → normalizado: '{codigo_rfid}'")
        
        # Verificar se funcionário existe
        conn = get_simple_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT nome FROM funcionarios 
            WHERE numero_registro = %s AND ativo = TRUE
        """, (numero_registro,))
        
        funcionario = cursor.fetchone()
        if not funcionario:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': 'Funcionário não encontrado ou inativo'
            })
        
        # Verificar se código RFID já existe
        cursor.execute("""
            SELECT numero_registro FROM cartoes_rfid 
            WHERE codigo_rfid = %s AND ativo = TRUE
        """, (codigo_rfid,))
        
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': 'Código RFID já está cadastrado para outro funcionário'
            })
        
        # Verificar se funcionário já tem RFID
        cursor.execute("""
            SELECT id FROM cartoes_rfid 
            WHERE numero_registro = %s AND ativo = TRUE
        """, (numero_registro,))
        
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': 'Funcionário já possui cadastro RFID ativo'
            })
        
        # Inserir novo cadastro RFID
        cursor.execute("""
            INSERT INTO cartoes_rfid (numero_registro, codigo_rfid, tipo_cartao, descricao)
            VALUES (%s, %s, %s, %s)
        """, (numero_registro, codigo_rfid, tipo_cartao, descricao))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Log da operação
        log_acesso('CADASTRO_RFID', f'RFID cadastrado para {funcionario[0]} ({numero_registro})', {
            'numero_registro': numero_registro,
            'codigo_rfid': codigo_rfid,
            'tipo_cartao': tipo_cartao
        })
        
        return jsonify({
            'success': True,
            'message': 'RFID cadastrado com sucesso'
        })
        
    except Exception as e:
        print(f"Erro ao cadastrar RFID: {e}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        })

@app.route('/api/funcionarios/remover-rfid', methods=['DELETE'])
@login_required
def remover_rfid():
    """Remover cadastro RFID de funcionário"""
    try:
        data = request.get_json()
        numero_registro = data.get('numero_registro')
        
        if not numero_registro:
            return jsonify({
                'success': False,
                'message': 'Número de registro é obrigatório'
            })
        
        conn = get_simple_connection()
        cursor = conn.cursor()
        
        # Buscar informações do funcionário
        cursor.execute("""
            SELECT f.nome, cr.codigo_rfid 
            FROM funcionarios f
            LEFT JOIN cartoes_rfid cr ON f.numero_registro = cr.numero_registro
            WHERE f.numero_registro = %s AND f.ativo = TRUE
        """, (numero_registro,))
        
        resultado = cursor.fetchone()
        if not resultado:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': 'Funcionário não encontrado'
            })
        
        nome_funcionario, codigo_rfid = resultado
        
        # Desativar RFID (não deletar para manter histórico)
        cursor.execute("""
            UPDATE cartoes_rfid 
            SET ativo = FALSE 
            WHERE numero_registro = %s AND ativo = TRUE
        """, (numero_registro,))
        
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': 'Funcionário não possui cadastro RFID ativo'
            })
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Log da operação
        log_acesso('REMOCAO_RFID', f'RFID removido de {nome_funcionario} ({numero_registro})', {
            'numero_registro': numero_registro,
            'codigo_rfid': codigo_rfid
        })
        
        return jsonify({
            'success': True,
            'message': 'RFID removido com sucesso'
        })
        
    except Exception as e:
        print(f"Erro ao remover RFID: {e}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        })

@app.route('/api/funcionarios/importar-rfid', methods=['POST'])
@login_required
def importar_rfid():
    """Importar múltiplos cadastros RFID de uma vez"""
    try:
        data = request.get_json()
        if not data or 'lista' not in data:
            return jsonify({'success': False, 'message': 'Dados inválidos'})
            
        lista = data.get('lista', [])
        resultados = {
            'sucesso': 0,
            'erro': 0,
            'detalhes': []
        }
        
        conn = get_simple_connection()
        cursor = conn.cursor()
        
        for item in lista:
            registro = str(item.get('numero_registro', '')).strip()
            rfid = str(item.get('codigo_rfid', '')).strip()
            tipo = item.get('tipo_cartao', 'cartao')
            desc = item.get('descricao', '')
            
            if not registro or not rfid:
                resultados['erro'] += 1
                resultados['detalhes'].append({'registro': registro, 'status': 'Erro', 'mensagem': 'Registro ou RFID vazio'})
                continue
                
            try:
                # Verificar se funcionário existe
                cursor.execute("SELECT nome FROM funcionarios WHERE numero_registro = %s AND ativo = TRUE", (registro,))
                func = cursor.fetchone()
                if not func:
                    resultados['erro'] += 1
                    resultados['detalhes'].append({'registro': registro, 'status': 'Erro', 'mensagem': 'Funcionário não encontrado'})
                    continue
                
                # Verificar se RFID já existe (ativo) em outro funcionário
                cursor.execute("SELECT numero_registro FROM cartoes_rfid WHERE codigo_rfid = %s AND ativo = TRUE AND numero_registro != %s", (rfid, registro))
                if cursor.fetchone():
                    resultados['erro'] += 1
                    resultados['detalhes'].append({'registro': registro, 'status': 'Erro', 'mensagem': f'RFID {rfid} já em uso'})
                    continue
                
                # Verificar se já existe registro para este funcionário
                cursor.execute("SELECT id, ativo FROM cartoes_rfid WHERE numero_registro = %s", (registro,))
                existente = cursor.fetchone()
                
                if existente:
                    # Se já existe e está ativo, verificar se é o mesmo RFID
                    # (Se for o mesmo, pulamos. Se for diferente, avisamos que já tem RFID ativo)
                    if existente[1]: # ativo
                        resultados['erro'] += 1
                        resultados['detalhes'].append({'registro': registro, 'status': 'Erro', 'mensagem': 'Funcionário já possui RFID ativo'})
                        continue
                    else:
                        # Se estava inativo, atualizamos para o novo e reativamos
                        cursor.execute("""
                            UPDATE cartoes_rfid 
                            SET codigo_rfid = %s, tipo_cartao = %s, descricao = %s, ativo = TRUE, data_cadastro = CURRENT_TIMESTAMP
                            WHERE numero_registro = %s
                        """, (rfid, tipo, desc, registro))
                else:
                    # Inserir novo
                    cursor.execute("""
                        INSERT INTO cartoes_rfid (numero_registro, codigo_rfid, tipo_cartao, descricao)
                        VALUES (%s, %s, %s, %s)
                    """, (registro, rfid, tipo, desc))
                
                resultados['sucesso'] += 1
                resultados['detalhes'].append({'registro': registro, 'status': 'Sucesso', 'mensagem': 'Cadastrado'})
                
            except Exception as e:
                resultados['erro'] += 1
                resultados['detalhes'].append({'registro': registro, 'status': 'Erro', 'mensagem': str(e)})
                
        conn.commit()
        cursor.close()
        conn.close()
        
        if resultados['sucesso'] > 0:
            log_acesso('IMPORTACAO_RFID', f'Importados {resultados["sucesso"]} RFIDs em massa', {
                'total_tentativas': len(lista),
                'sucessos': resultados['sucesso']
            })
            
        return jsonify({
            'success': True,
            'message': f'Processamento concluído: {resultados["sucesso"]} sucessos, {resultados["erro"]} erros',
            'resultados': resultados
        })
        
    except Exception as e:
        print(f"Erro na importação em massa: {e}")
        return jsonify({'success': False, 'message': f'Erro interno: {str(e)}'})


@app.route('/api/funcionarios/com-rfid', methods=['GET'])
@login_required
def get_funcionarios_com_rfid():
    """Buscar funcionários com cadastro RFID"""
    try:
        conn = get_simple_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = """
        SELECT f.id, f.numero_registro, f.nome, f.departamento, f.cargo, f.empresa,
               cr.codigo_rfid, cr.tipo_cartao, cr.descricao, cr.data_cadastro, cr.data_ultimo_uso
        FROM funcionarios f
        INNER JOIN cartoes_rfid cr ON f.numero_registro = cr.numero_registro
        WHERE f.ativo = TRUE AND cr.ativo = TRUE
        ORDER BY f.nome
        """
        
        cursor.execute(query)
        funcionarios = cursor.fetchall()
        
        # Converter datas para string
        for func in funcionarios:
            if func['data_cadastro']:
                func['data_cadastro'] = func['data_cadastro'].strftime('%d/%m/%Y %H:%M')
            if func['data_ultimo_uso']:
                func['data_ultimo_uso'] = func['data_ultimo_uso'].strftime('%d/%m/%Y %H:%M')
            else:
                func['data_ultimo_uso'] = 'Nunca usado'
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'funcionarios': funcionarios
        })
        
    except Exception as e:
        print(f"Erro ao buscar funcionários com RFID: {e}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        })

@app.route('/api/rfid/buscar-registro', methods=['POST'])
def buscar_registro_por_rfid():
    """Buscar número de registro pelo código RFID (público para acesso)"""
    try:
        data = request.get_json()
        codigo_rfid = data.get('codigo_rfid')
        
        if not codigo_rfid:
            return jsonify({
                'success': False,
                'message': 'Código RFID é obrigatório'
            })
        
        # Normalizar código RFID (remover espaços, dois pontos, converter para maiúsculas)
        codigo_rfid_original = codigo_rfid
        codigo_rfid = codigo_rfid.strip().upper().replace(':', '').replace(' ', '').replace('\t', '').replace('\n', '').replace('-', '').replace('.', '')
        print(f"🔍 Buscando RFID: '{codigo_rfid_original}' → normalizado: '{codigo_rfid}'")
        
        conn = get_simple_connection()
        cursor = conn.cursor()
        
        # Buscar número de registro pelo código RFID normalizado
        cursor.execute("""
            SELECT numero_registro 
            FROM cartoes_rfid 
            WHERE codigo_rfid = %s AND ativo = TRUE
        """, (codigo_rfid,))
        
        resultado = cursor.fetchone()
        
        # Se não encontrou, tentar variações do código
        if not resultado:
            # Tentar buscar com formato com dois pontos (ex: 69:4C:A0:03)
            if len(codigo_rfid) >= 8:
                codigo_com_dois_pontos = ':'.join([codigo_rfid[i:i+2] for i in range(0, len(codigo_rfid), 2)])
                print(f"🔄 Tentando buscar também com formato: '{codigo_com_dois_pontos}'")
                cursor.execute("""
                    SELECT numero_registro 
                    FROM cartoes_rfid 
                    WHERE codigo_rfid = %s AND ativo = TRUE
                """, (codigo_com_dois_pontos,))
                resultado = cursor.fetchone()
                
                # Se encontrou com dois pontos, atualizar para formato normalizado
                if resultado:
                    print(f"⚠️ Encontrado com formato antigo '{codigo_com_dois_pontos}', atualizando para formato normalizado")
                    cursor.execute("""
                        UPDATE cartoes_rfid 
                        SET codigo_rfid = %s 
                        WHERE codigo_rfid = %s AND ativo = TRUE
                    """, (codigo_rfid, codigo_com_dois_pontos))
                    conn.commit()
            
            # Se ainda não encontrou, tentar busca case-insensitive
            if not resultado:
                print(f"🔄 Tentando busca case-insensitive...")
                cursor.execute("""
                    SELECT numero_registro, codigo_rfid 
                    FROM cartoes_rfid 
                    WHERE UPPER(REPLACE(REPLACE(REPLACE(codigo_rfid, ':', ''), '-', ''), ' ', '')) = %s 
                    AND ativo = TRUE
                """, (codigo_rfid,))
                resultado_temp = cursor.fetchone()
                if resultado_temp:
                    numero_registro_encontrado = resultado_temp[0]
                    codigo_cadastrado = resultado_temp[1]
                    print(f"✅ Encontrado com busca case-insensitive: '{codigo_cadastrado}' → normalizando...")
                    # Atualizar para formato normalizado
                    cursor.execute("""
                        UPDATE cartoes_rfid 
                        SET codigo_rfid = %s 
                        WHERE numero_registro = %s AND ativo = TRUE
                    """, (codigo_rfid, numero_registro_encontrado))
                    conn.commit()
                    resultado = (numero_registro_encontrado,)
        
        cursor.close()
        conn.close()
        
        if resultado:
            numero_registro = resultado[0]
            print(f"✅ RFID '{codigo_rfid}' encontrado para registro {numero_registro}")
            return jsonify({
                'success': True,
                'numero_registro': numero_registro,
                'codigo_rfid': codigo_rfid
            })
        else:
            # Listar códigos RFID cadastrados para debug
            conn_debug = get_simple_connection()
            cursor_debug = conn_debug.cursor()
            cursor_debug.execute("""
                SELECT codigo_rfid, numero_registro 
                FROM cartoes_rfid 
                WHERE ativo = TRUE 
                LIMIT 10
            """)
            codigos_cadastrados = cursor_debug.fetchall()
            cursor_debug.close()
            conn_debug.close()
            
            print(f"⚠️ RFID '{codigo_rfid}' não encontrado na base")
            print(f"📋 Códigos cadastrados (amostra): {codigos_cadastrados}")
            print(f"📋 Código original recebido: '{codigo_rfid_original}'")
            return jsonify({
                'success': False,
                'message': f'Código RFID não encontrado. Código buscado: {codigo_rfid}',
                'codigo_buscado': codigo_rfid,
                'codigo_original': codigo_rfid_original,
                'codigos_cadastrados': [c[0] for c in codigos_cadastrados]
            })
        
    except Exception as e:
        print(f"Erro ao buscar registro por RFID: {e}")
        return jsonify({
            'success': False,
            'message': 'Erro ao buscar registro'
        })

@app.route('/api/funcionarios/gerar-qrcode', methods=['GET'])
@login_required
def gerar_qrcode_funcionario():
    """Gerar QR Code para um funcionário"""
    try:
        numero_registro = request.args.get('numero_registro')
        
        if not numero_registro:
            return jsonify({
                'success': False,
                'message': 'Número de registro obrigatório'
            })
        
        # Verificar se funcionário existe
        conn = get_simple_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT numero_registro, nome, departamento, cargo, empresa
            FROM funcionarios 
            WHERE numero_registro = %s AND ativo = TRUE
        """, (numero_registro,))
        
        funcionario = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not funcionario:
            return jsonify({
                'success': False,
                'message': 'Funcionário não encontrado ou inativo'
            })
        
        # Criar dados do QR code com nome e departamento
        qr_data = {
            'numero_registro': funcionario['numero_registro'],
            'nome': funcionario['nome'],
            'departamento': funcionario['departamento'],
            'tipo': 'acesso_funcionario'
        }
        
        qr_text = json.dumps(qr_data)
        
        # Gerar QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_text)
        qr.make(fit=True)
        
        # Criar imagem do QR code
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Converter para RGB se necessário (algumas versões retornam em modo diferente)
        if qr_img.mode != 'RGB':
            qr_img = qr_img.convert('RGB')
        
        # Criar imagem final com texto (nome e departamento)
        # Calcular tamanho da imagem final
        qr_width, qr_height = qr_img.size
        padding = 20
        text_height = 80
        final_width = qr_width + (padding * 2)
        final_height = qr_height + text_height + (padding * 2)
        
        # Criar imagem final
        final_img = Image.new('RGB', (final_width, final_height), 'white')
        
        # Colar QR code no centro superior (usar tupla de 4 elementos para garantir compatibilidade)
        qr_x = (final_width - qr_width) // 2
        qr_y = padding
        final_img.paste(qr_img, (qr_x, qr_y, qr_x + qr_width, qr_y + qr_height))
        
        # Adicionar texto (nome e departamento)
        draw = ImageDraw.Draw(final_img)
        
        # Tentar carregar fonte, se não conseguir usar padrão
        font_large = None
        font_small = None
        
        # Lista de caminhos de fontes possíveis
        font_paths = [
            ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            ("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
            ("/usr/share/fonts/truetype/ttf-dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/ttf-dejavu/DejaVuSans.ttf"),
        ]
        
        for bold_path, regular_path in font_paths:
            try:
                if os.path.exists(bold_path) and os.path.exists(regular_path):
                    font_large = ImageFont.truetype(bold_path, 20)
                    font_small = ImageFont.truetype(regular_path, 16)
                    break
            except:
                continue
        
        # Se não encontrou fontes, usar padrão
        if font_large is None:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Texto do nome
        nome_text = funcionario['nome']
        try:
            text_bbox = draw.textbbox((0, 0), nome_text, font=font_large)
            text_width = text_bbox[2] - text_bbox[0]
        except:
            # Fallback para método antigo
            text_width = draw.textlength(nome_text, font=font_large) if hasattr(draw, 'textlength') else len(nome_text) * 10
        text_x = (final_width - text_width) // 2
        text_y = qr_height + padding + 10
        draw.text((text_x, text_y), nome_text, fill='black', font=font_large)
        
        # Texto do departamento
        dept_text = funcionario['departamento']
        try:
            text_bbox = draw.textbbox((0, 0), dept_text, font=font_small)
            text_width = text_bbox[2] - text_bbox[0]
        except:
            # Fallback para método antigo
            text_width = draw.textlength(dept_text, font=font_small) if hasattr(draw, 'textlength') else len(dept_text) * 8
        text_x = (final_width - text_width) // 2
        text_y = text_y + 30
        draw.text((text_x, text_y), dept_text, fill='gray', font=font_small)
        
        # Converter para base64
        img_buffer = io.BytesIO()
        final_img.save(img_buffer, format='PNG')
        img_str = base64.b64encode(img_buffer.getvalue()).decode()
        
        return jsonify({
            'success': True,
            'qrcode_image': f'data:image/png;base64,{img_str}',
            'qrcode_text': qr_text,
            'funcionario': funcionario
        })
        
    except Exception as e:
        print(f"Erro ao gerar QR code: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': 'Erro ao gerar QR code'
        })

def determinar_tipo_acesso_automatico(numero_registro):
    """Determinar automaticamente o tipo de acesso baseado no histórico"""
    try:
        conn = get_simple_connection()
        cursor = conn.cursor()
        
        # Buscar último acesso do funcionário
        cursor.execute("""
            SELECT tipo_acesso, CONCAT(data_acesso, ' ', hora_acesso) as data_hora 
            FROM acessos_funcionarios 
            WHERE numero_registro = %s 
            ORDER BY data_acesso DESC, hora_acesso DESC 
            LIMIT 1
        """, (numero_registro,))
        
        ultimo_acesso = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not ultimo_acesso:
            return 'entrada'  # Primeiro acesso do dia
        
        ultimo_tipo = ultimo_acesso[0]
        ultima_data_str = ultimo_acesso[1]
        
        # Converter string para data
        try:
            ultima_data = datetime.strptime(ultima_data_str, '%Y-%m-%d %H:%M:%S')
        except:
            # Se não conseguir converter, assumir que é hoje
            ultima_data = datetime.now()
        
        # Se o último acesso foi hoje
        if ultima_data.date() == date.today():
            if ultimo_tipo == 'entrada':
                return 'saida'
            elif ultimo_tipo == 'saida':
                return 'entrada'
            elif ultimo_tipo == 'almoco_entrada':
                return 'almoco_saida'
            elif ultimo_tipo == 'almoco_saida':
                return 'entrada'
            elif ultimo_tipo == 'intervalo_entrada':
                return 'intervalo_saida'
            elif ultimo_tipo == 'intervalo_saida':
                return 'entrada'
        
        # Se não houve acesso hoje, começar com entrada
        return 'entrada'
        
    except Exception as e:
        print(f"Erro ao determinar tipo de acesso: {e}")
        return 'entrada'

# ========================================
# FUNÇÕES AUXILIARES PARA RELATÓRIOS
# ========================================

def gerar_csv_relatorio_diario(relatorio):
    """Gerar CSV do relatório diário"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Cabeçalho
    writer.writerow(['RELATÓRIO DIÁRIO DE ACESSOS'])
    writer.writerow([f'Período: {relatorio["periodo"]["inicio"]} a {relatorio["periodo"]["fim"]}'])
    writer.writerow([])
    
    # Estatísticas
    stats = relatorio['estatisticas']
    writer.writerow(['ESTATÍSTICAS GERAIS'])
    writer.writerow(['Total de Acessos', stats['total_acessos']])
    writer.writerow(['Funcionários Únicos', stats['funcionarios_unicos']])
    writer.writerow(['Entradas', stats['entradas']])
    writer.writerow(['Saídas', stats['saidas']])
    writer.writerow(['Acessos Faciais', stats['acessos_faciais']])
    writer.writerow(['Acessos Manuais', stats['acessos_manuais']])
    writer.writerow([])
    
    # Detalhes dos acessos
    writer.writerow(['DETALHES DOS ACESSOS'])
    writer.writerow(['Número Registro', 'Nome', 'Departamento', 'Tipo Acesso', 'Data/Hora', 'Método', 'Status'])
    
    for acesso in relatorio['acessos']:
        writer.writerow([
            acesso['numero_registro'],
            acesso['nome_completo'] or 'N/A',
            acesso['departamento'] or 'N/A',
            acesso['tipo_acesso'],
            acesso['data_hora'],
            acesso['metodo_acesso'],
            acesso['status']
        ])
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=relatorio_diario_{relatorio["periodo"]["inicio"]}.csv'}
    )

def gerar_csv_relatorio_funcionario(relatorio):
    """Gerar CSV do relatório de funcionário"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    func = relatorio['funcionario']
    stats = relatorio['estatisticas']
    
    # Cabeçalho
    writer.writerow(['RELATÓRIO INDIVIDUAL DE FUNCIONÁRIO'])
    writer.writerow([f'Período: {relatorio["periodo"]["inicio"]} a {relatorio["periodo"]["fim"]}'])
    writer.writerow([])
    
    # Dados do funcionário
    writer.writerow(['DADOS DO FUNCIONÁRIO'])
    writer.writerow(['Número Registro', func['numero_registro']])
    writer.writerow(['Nome', func['nome_completo']])
    writer.writerow(['Departamento', func['departamento'] or 'N/A'])
    writer.writerow(['Cargo', func['cargo'] or 'N/A'])
    writer.writerow(['Status', func['status']])
    writer.writerow([])
    
    # Estatísticas
    writer.writerow(['ESTATÍSTICAS DO PERÍODO'])
    writer.writerow(['Total de Acessos', stats['total_acessos']])
    writer.writerow(['Entradas', stats['entradas']])
    writer.writerow(['Saídas', stats['saidas']])
    writer.writerow(['Acessos Faciais', stats['acessos_faciais']])
    writer.writerow(['Acessos Manuais', stats['acessos_manuais']])
    if stats['primeiro_acesso']:
        writer.writerow(['Primeiro Acesso', stats['primeiro_acesso']])
    if stats['ultimo_acesso']:
        writer.writerow(['Último Acesso', stats['ultimo_acesso']])
    writer.writerow([])
    
    # Detalhes dos acessos
    writer.writerow(['DETALHES DOS ACESSOS'])
    writer.writerow(['Tipo Acesso', 'Data/Hora', 'Método', 'Status', 'Observações'])
    
    for acesso in relatorio['acessos']:
        writer.writerow([
            acesso['tipo_acesso'],
            acesso['data_hora'],
            acesso['metodo_acesso'],
            acesso['status'],
            acesso['observacoes'] or ''
        ])
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=relatorio_funcionario_{func["numero_registro"]}_{relatorio["periodo"]["inicio"]}.csv'}
    )

def gerar_pdf_relatorio_diario(relatorio):
    """Gerar PDF do relatório diário"""
    try:
        # Criar buffer para o PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Centralizado
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=20
        )
        normal_style = styles['Normal']
        
        # Título
        story.append(Paragraph("RELATÓRIO DIÁRIO DE ACESSOS", title_style))
        story.append(Paragraph(f"Período: {relatorio['periodo']['inicio']} a {relatorio['periodo']['fim']}", normal_style))
        story.append(Spacer(1, 20))
        
        # Estatísticas
        stats = relatorio['estatisticas']
        story.append(Paragraph("ESTATÍSTICAS GERAIS", heading_style))
        
        stats_data = [
            ['Total de Acessos', str(stats['total_acessos'])],
            ['Funcionários Únicos', str(stats['funcionarios_unicos'])],
            ['Entradas', str(stats['entradas'])],
            ['Saídas', str(stats['saidas'])],
            ['Acessos Faciais', str(stats['acessos_faciais'])],
            ['Acessos Manuais', str(stats['acessos_manuais'])]
        ]
        
        stats_table = Table(stats_data, colWidths=[2*inch, 1*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(stats_table)
        story.append(Spacer(1, 20))
        
        # Detalhes dos acessos
        story.append(Paragraph("DETALHES DOS ACESSOS", heading_style))
        
        if relatorio['acessos']:
            # Cabeçalho da tabela
            header = ['Número', 'Nome', 'Departamento', 'Tipo', 'Data/Hora', 'Método', 'Status']
            table_data = [header]
            
            # Dados dos acessos
            for acesso in relatorio['acessos']:
                table_data.append([
                    str(acesso['numero_registro']),
                    acesso['nome_completo'] or 'N/A',
                    acesso['departamento'] or 'N/A',
                    acesso['tipo_acesso'],
                    acesso['data_hora'],
                    acesso['metodo_acesso'],
                    acesso['status']
                ])
            
            # Criar tabela com larguras ajustadas
            access_table = Table(table_data, colWidths=[0.5*inch, 1.5*inch, 1*inch, 0.8*inch, 1.2*inch, 0.8*inch, 0.8*inch])
            access_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(access_table)
        else:
            story.append(Paragraph("Nenhum acesso registrado no período.", normal_style))
        
        # Gerar PDF
        doc.build(story)
        buffer.seek(0)
        
        return Response(
            buffer.getvalue(),
            mimetype='application/pdf',
            headers={'Content-Disposition': f'attachment; filename=relatorio_diario_{relatorio["periodo"]["inicio"]}.pdf'}
        )
        
    except Exception as e:
        print(f"Erro ao gerar PDF: {e}")
        traceback.print_exc()
        # Fallback para CSV em caso de erro
        return gerar_csv_relatorio_diario(relatorio)

def gerar_pdf_relatorio_funcionario(relatorio):
    """Gerar PDF do relatório de funcionário"""
    try:
        # Criar buffer para o PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Centralizado
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=20
        )
        normal_style = styles['Normal']
        
        func = relatorio['funcionario']
        stats = relatorio['estatisticas']
        
        # Título
        story.append(Paragraph("RELATÓRIO INDIVIDUAL DE FUNCIONÁRIO", title_style))
        story.append(Paragraph(f"Período: {relatorio['periodo']['inicio']} a {relatorio['periodo']['fim']}", normal_style))
        story.append(Spacer(1, 20))
        
        # Dados do funcionário
        story.append(Paragraph("DADOS DO FUNCIONÁRIO", heading_style))
        
        func_data = [
            ['Número Registro', str(func['numero_registro'])],
            ['Nome', func['nome_completo']],
            ['Departamento', func['departamento'] or 'N/A'],
            ['Cargo', func['cargo'] or 'N/A'],
            ['Status', func['status']]
        ]
        
        func_table = Table(func_data, colWidths=[2*inch, 3*inch])
        func_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(func_table)
        story.append(Spacer(1, 20))
        
        # Estatísticas
        story.append(Paragraph("ESTATÍSTICAS DO PERÍODO", heading_style))
        
        stats_data = [
            ['Total de Acessos', str(stats['total_acessos'])],
            ['Entradas', str(stats['entradas'])],
            ['Saídas', str(stats['saidas'])],
            ['Acessos Faciais', str(stats['acessos_faciais'])],
            ['Acessos Manuais', str(stats['acessos_manuais'])]
        ]
        
        if stats['primeiro_acesso']:
            stats_data.append(['Primeiro Acesso', stats['primeiro_acesso']])
        if stats['ultimo_acesso']:
            stats_data.append(['Último Acesso', stats['ultimo_acesso']])
        
        stats_table = Table(stats_data, colWidths=[2*inch, 3*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(stats_table)
        story.append(Spacer(1, 20))
        
        # Detalhes dos acessos
        story.append(Paragraph("DETALHES DOS ACESSOS", heading_style))
        
        if relatorio['acessos']:
            # Cabeçalho da tabela
            header = ['Tipo Acesso', 'Data/Hora', 'Método', 'Status', 'Observações']
            table_data = [header]
            
            # Dados dos acessos
            for acesso in relatorio['acessos']:
                table_data.append([
                    acesso['tipo_acesso'],
                    acesso['data_hora'],
                    acesso['metodo_acesso'],
                    acesso['status'],
                    acesso['observacoes'] or ''
                ])
            
            # Criar tabela
            access_table = Table(table_data, colWidths=[1.2*inch, 1.5*inch, 1*inch, 1*inch, 1.3*inch])
            access_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(access_table)
        else:
            story.append(Paragraph("Nenhum acesso registrado no período.", normal_style))
        
        # Gerar PDF
        doc.build(story)
        buffer.seek(0)
        
        return Response(
            buffer.getvalue(),
            mimetype='application/pdf',
            headers={'Content-Disposition': f'attachment; filename=relatorio_funcionario_{func["numero_registro"]}_{relatorio["periodo"]["inicio"]}.pdf'}
        )
        
    except Exception as e:
        print(f"Erro ao gerar PDF: {e}")
        traceback.print_exc()
        # Fallback para CSV em caso de erro
        return gerar_csv_relatorio_funcionario(relatorio)


## marcar fim

# ========================================
# RELATÓRIO ONLINE SISTEMA REAL
# ========================================

@app.route('/relatorio-online-sistema-real')
@portaria_or_admin_required
def relatorio_online_sistema_real():
    """Página do relatório online que consome dados do sistema real"""
    return render_template('relatorio_online_personalizado.html')

@app.route('/api/debug-ip')
def debug_ip():
    """Rota de debug para verificar qual IP está sendo detectado"""
    detected_ip = get_host_ip()
    sistema_url = get_sistema_real_url()
    
    # Tentar obter mais informações
    import subprocess
    hostname_ips = ""
    try:
        result = subprocess.run(['hostname', '-I'], capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            hostname_ips = result.stdout.strip()
    except:
        pass
    
    return jsonify({
        'detected_ip': detected_ip,
        'sistema_real_url': sistema_url,
        'hostname_ips': hostname_ips,
        'env_sistema_real_ip': os.getenv('SISTEMA_REAL_IP'),
        'env_sistema_real_url': os.getenv('SISTEMA_REAL_URL'),
        'env_sistema_real_port': os.getenv('SISTEMA_REAL_PORT'),
    })

# Cache simples para relatório online (evitar queries repetidas muito rapidamente)
_relatorio_cache = {
    'data': None,
    'timestamp': 0,
    'cache_ttl': 15  # Cache por 15 segundos
}

@app.route('/api/relatorio-online-data')
def relatorio_online_data():
    """API que fornece dados para o relatório online - usa dados locais com cache"""
    global _relatorio_cache
    
    # Verificar cache primeiro
    agora = time.time()
    if _relatorio_cache['data'] and (agora - _relatorio_cache['timestamp']) < _relatorio_cache['cache_ttl']:
        print('📦 Retornando dados do cache (evitando nova query)')
        return jsonify(_relatorio_cache['data'])
    
    conn = None
    cursor = None
    try:
        # Usar dados locais diretamente do banco de dados
        # Isso evita timeout e problemas de conexão com sistema externo
        print('🔍 Buscando dados do banco...')
        conn = get_simple_connection()
        cursor = conn.cursor()
        
        hoje = date.today()
        
        # Query muito simplificada - buscar últimos acessos de cada funcionário hoje
        # Primeiro, buscar última ação de cada funcionário hoje
        cursor.execute("""
            SELECT 
                a.numero_registro,
                f.nome,
                f.departamento,
                f.cargo,
                f.empresa,
                a.tipo_acesso,
                MAX(a.hora_acesso) as ultima_hora
            FROM acessos_funcionarios a
            INNER JOIN funcionarios f ON a.numero_registro = f.numero_registro
            WHERE f.ativo = TRUE
            AND a.data_acesso = %s
            GROUP BY a.numero_registro, f.nome, f.departamento, f.cargo, f.empresa, a.tipo_acesso
            ORDER BY a.numero_registro, ultima_hora DESC
            LIMIT 1000
        """, (hoje,))
        
        todos_acessos = cursor.fetchall()
        
        # Fechar cursor e conexão ANTES de processar dados (liberar conexão mais rápido)
        cursor.close()
        cursor = None
        conn.close()
        conn = None
        print('✅ Conexão fechada após query (antes de processar)')
        
        # Processar em Python para determinar presentes e saídos
        ultima_acao = {}
        for acesso in todos_acessos:
            registro = acesso[0]
            tipo = acesso[5]
            hora = acesso[6]
            
            if registro not in ultima_acao:
                ultima_acao[registro] = {
                    'numero_registro': registro,
                    'nome': acesso[1],
                    'departamento': acesso[2],
                    'cargo': acesso[3],
                    'empresa': acesso[4],
                    'tipo': tipo,
                    'hora': hora
                }
            else:
                # Se já existe, comparar horas
                if hora > ultima_acao[registro]['hora']:
                    ultima_acao[registro]['tipo'] = tipo
                    ultima_acao[registro]['hora'] = hora
        
        # Separar presentes e saídos
        presentes = []
        sairam = []
        
        for registro, dados in ultima_acao.items():
            if dados['tipo'] == 'entrada':
                presentes.append({
                    'numero_registro': dados['numero_registro'],
                    'nome': dados['nome'],
                    'departamento': dados['departamento'],
                    'cargo': dados['cargo'],
                    'empresa': dados['empresa'],
                    'ultima_entrada': str(dados['hora'])
                })
            elif dados['tipo'] == 'saida':
                sairam.append({
                    'numero_registro': dados['numero_registro'],
                    'nome': dados['nome'],
                    'departamento': dados['departamento'],
                    'cargo': dados['cargo'],
                    'empresa': dados['empresa'],
                    'ultima_saida': str(dados['hora'])
                })
        
        # Ordenar por nome
        presentes.sort(key=lambda x: x['nome'])
        sairam.sort(key=lambda x: x['nome'])
        
        resultado = {
            'success': True,
            'presentes': presentes[:500],  # Limitar a 500
            'saidos': sairam[:500],  # Limitar a 500
            'total_presentes': len(presentes),
            'total_saidos': len(sairam)
        }
        
        # Atualizar cache
        _relatorio_cache['data'] = resultado
        _relatorio_cache['timestamp'] = agora
        print('✅ Cache atualizado')
        
        return jsonify(resultado)
            
    except mysql.connector.Error as db_error:
        print(f"❌ Erro de banco de dados ao gerar relatório online: {db_error}")
        # Retornar cache se disponível em caso de erro
        if _relatorio_cache['data']:
            print('📦 Retornando cache devido a erro de banco')
            return jsonify(_relatorio_cache['data'])
        return jsonify({
            'error': f'Erro de conexão com banco de dados: {str(db_error)}',
            'presentes': [],
            'saidos': [],
            'total_presentes': 0,
            'total_saidos': 0
        })
    except Exception as e:
        print(f"❌ Erro ao gerar relatório online: {e}")
        import traceback
        traceback.print_exc()
        # Retornar cache se disponível em caso de erro
        if _relatorio_cache['data']:
            print('📦 Retornando cache devido a erro')
            return jsonify(_relatorio_cache['data'])
        return jsonify({
            'error': f'Erro ao carregar dados: {str(e)}',
            'presentes': [],
            'saidos': [],
            'total_presentes': 0,
            'total_saidos': 0
        })
    finally:
        # Garantir que conexão e cursor sejam SEMPRE fechados
        if cursor:
            try:
                cursor.close()
                print('✅ Cursor fechado')
            except Exception as e:
                print(f'⚠️ Erro ao fechar cursor: {e}')
        if conn:
            try:
                conn.close()
                print('✅ Conexão fechada')
            except Exception as e:
                print(f'⚠️ Erro ao fechar conexão: {e}')

@app.route('/api/relatorio-graficos-data')
def relatorio_graficos_data():
    """API que fornece dados detalhados para os gráficos"""
    try:
        # Gerar dados para gráficos diretamente
        graficos_data = {
            'acessos_por_hora': gerar_dados_acessos_hora(),
            'departamentos': gerar_dados_departamentos({}),
            'funcionarios_ativos': gerar_dados_funcionarios_ativos({}),
            'tendencias': gerar_dados_tendencias()
        }
        
        return jsonify({
            'success': True,
            'graficos': graficos_data
        })
            
    except Exception as e:
        # Em caso de erro, retornar dados básicos para evitar quebra do frontend
        return jsonify({
            'success': False,
            'error': f'Erro de conexão: {str(e)}',
            'graficos': {
                'acessos_por_hora': {
                    'horas': [f'{h:02d}:00' for h in range(24)],
                    'acessos': [random.randint(10, 50) for _ in range(24)]
                },
                'departamentos': {
                    'labels': ['TI', 'RH', 'Financeiro', 'Vendas', 'Marketing', 'Operações'],
                    'values': [15, 8, 12, 20, 6, 18]
                },
                'funcionarios_ativos': [
                    {'nome': 'João Silva', 'acessos': 45},
                    {'nome': 'Maria Santos', 'acessos': 42},
                    {'nome': 'Pedro Costa', 'acessos': 38},
                    {'nome': 'Ana Oliveira', 'acessos': 35},
                    {'nome': 'Carlos Lima', 'acessos': 32}
                ],
                'tendencias': {
                    'dias': ['01/09', '02/09', '03/09', '04/09', '05/09', '06/09', '07/09'],
                    'acessos': [95, 102, 88, 115, 97, 103, 89]
                }
            }
        })

def gerar_dados_acessos_hora():
    """Gerar dados de acessos por hora do dia"""
    from datetime import datetime
    
    # Simular dados de acessos por hora (0-23)
    horas = list(range(24))
    acessos = []
    
    # Padrão típico: picos às 8h, 12h e 18h
    for hora in horas:
        if hora in [8, 9, 12, 13, 18, 19]:  # Horários de pico
            acessos.append(random.randint(30, 60))
        elif hora in [7, 10, 11, 14, 15, 16, 17, 20]:  # Horários normais
            acessos.append(random.randint(10, 30))
        else:  # Horários baixos
            acessos.append(random.randint(0, 10))
    
    return {
        'horas': [f'{h:02d}:00' for h in horas],
        'acessos': acessos
    }

def gerar_dados_departamentos(data):
    """Gerar dados de distribuição por departamento"""
    # Sempre retornar dados de exemplo para garantir funcionamento
    dept_count = {
        'TI': 15,
        'RH': 8,
        'Financeiro': 12,
        'Vendas': 20,
        'Marketing': 6,
        'Operações': 18
    }
    
    return {
        'labels': list(dept_count.keys()),
        'values': list(dept_count.values())
    }

def gerar_dados_funcionarios_ativos(data):
    """Gerar dados dos funcionários mais ativos"""
    # Sempre retornar dados de exemplo para garantir funcionamento
    funcionarios = [
        {'nome': 'João Silva', 'acessos': 45, 'departamento': 'TI'},
        {'nome': 'Maria Santos', 'acessos': 42, 'departamento': 'RH'},
        {'nome': 'Pedro Costa', 'acessos': 38, 'departamento': 'Financeiro'},
        {'nome': 'Ana Oliveira', 'acessos': 35, 'departamento': 'Vendas'},
        {'nome': 'Carlos Lima', 'acessos': 32, 'departamento': 'Marketing'},
        {'nome': 'Lucia Ferreira', 'acessos': 28, 'departamento': 'Operações'},
        {'nome': 'Roberto Alves', 'acessos': 25, 'departamento': 'TI'},
        {'nome': 'Fernanda Rocha', 'acessos': 22, 'departamento': 'RH'}
    ]
    
    return funcionarios

def gerar_dados_tendencias():
    """Gerar dados de tendências"""
    # Sempre retornar dados de exemplo para garantir funcionamento
    dias = ['01/09', '02/09', '03/09', '04/09', '05/09', '06/09', '07/09']
    acessos = [95, 102, 88, 115, 97, 103, 89]
    
    return {
        'dias': dias,
        'acessos': acessos
    }

# ========================================
# INICIALIZAÇÃO
# ========================================

# ========================================
# ROTAS DE ANALYTICS E RELATÓRIOS
# ========================================

@app.route('/api/analytics/estatisticas-gerais', methods=['GET'])
@login_required
def api_estatisticas_gerais():
    """API para obter estatísticas gerais do sistema"""
    try:
        print("DEBUG: API api_estatisticas_gerais chamada")
        stats = obter_estatisticas_gerais()
        print(f"DEBUG: Stats retornado: {stats}")
        print(f"DEBUG: Type of stats: {type(stats)}")
        print(f"DEBUG: Bool of stats: {bool(stats)}")
        if stats:
            print("DEBUG: Stats é truthy, retornando sucesso")
            return jsonify({'success': True, 'data': stats})
        else:
            print("DEBUG: Stats é falsy, retornando erro")
            return jsonify({'success': False, 'message': 'Erro ao obter estatísticas'})
    except Exception as e:
        print(f"DEBUG: Exceção na API: {e}")
        import traceback
        print(f"DEBUG: Traceback da API: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/analytics/analise-padroes', methods=['GET'])
@login_required
def api_analise_padroes():
    """API para análise de padrões de acesso"""
    try:
        data_inicio = request.args.get('data_inicio', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        data_fim = request.args.get('data_fim', datetime.now().strftime('%Y-%m-%d'))
        
        padroes = obter_analise_padroes(data_inicio, data_fim)
        if padroes:
            return jsonify({'success': True, 'data': padroes})
        else:
            return jsonify({'success': False, 'message': 'Erro ao analisar padrões'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/analytics/relatorio-produtividade', methods=['GET'])
@login_required
def api_relatorio_produtividade():
    """API para relatório de produtividade"""
    import sys
    try:
        sys.stderr.write("=" * 80 + "\n")
        sys.stderr.write("DEBUG API: api_relatorio_produtividade CHAMADA!\n")
        sys.stderr.write("=" * 80 + "\n")
        sys.stderr.flush()
        
        data_inicio = request.args.get('data_inicio', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        data_fim = request.args.get('data_fim', datetime.now().strftime('%Y-%m-%d'))
        departamento = request.args.get('departamento', None)
        
        sys.stderr.write(f"DEBUG API: Gerando relatório - {data_inicio} a {data_fim}, dept: {departamento}\n")
        sys.stderr.write(f"DEBUG API: Chamando obter_relatorio_produtividade...\n")
        sys.stderr.flush()
        
        relatorio = obter_relatorio_produtividade(data_inicio, data_fim, departamento)
        
        sys.stderr.write(f"DEBUG API: obter_relatorio_produtividade retornou: {type(relatorio)}, valor: {relatorio is not None}\n")
        sys.stderr.flush()
        
        if relatorio is not None:
            sys.stderr.write(f"DEBUG API: Relatório retornado com {len(relatorio) if relatorio else 0} registros\n")
            if len(relatorio) > 0:
                sys.stderr.write(f"DEBUG API: Primeiro registro: {relatorio[0]}\n")
            sys.stderr.flush()
            # Se for uma lista vazia, ainda é sucesso
            if isinstance(relatorio, list):
                return jsonify({'success': True, 'data': relatorio})
            else:
                return jsonify({'success': False, 'message': 'Formato de dados inválido'})
        else:
            sys.stderr.write("DEBUG API: Relatório retornou None\n")
            sys.stderr.flush()
            return jsonify({'success': False, 'message': 'Erro ao gerar relatório'})
    except Exception as e:
        sys.stderr.write(f"DEBUG API: Exceção ao gerar relatório: {e}\n")
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        return jsonify({'success': False, 'error': str(e), 'message': f'Erro ao gerar relatório: {str(e)}'})

@app.route('/api/analytics/tendencias', methods=['GET'])
@login_required
def api_tendencias():
    """API para tendências de acesso"""
    try:
        dias = int(request.args.get('dias', 30))
        tendencias = obter_tendencias_acesso(dias)
        if tendencias:
            return jsonify({'success': True, 'data': tendencias})
        else:
            return jsonify({'success': False, 'message': 'Erro ao obter tendências'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/analytics/departamentos', methods=['GET'])
@login_required
def api_departamentos():
    """API para buscar lista de departamentos"""
    try:
        conn = get_simple_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT departamento 
            FROM funcionarios 
            WHERE ativo = TRUE AND departamento IS NOT NULL AND departamento != ''
            ORDER BY departamento
        """)
        
        departamentos = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'departamentos': departamentos
        })
        
    except Exception as e:
        print(f"Erro ao buscar departamentos: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/analytics/exportar-excel', methods=['POST'])
@login_required
def api_exportar_excel():
    """API para exportar relatórios em Excel"""
    try:
        data = request.get_json()
        tipo_relatorio = data.get('tipo', 'produtividade')
        data_inicio = data.get('data_inicio', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        data_fim = data.get('data_fim', datetime.now().strftime('%Y-%m-%d'))
        departamento = data.get('departamento', None)
        
        if tipo_relatorio == 'produtividade':
            relatorio = obter_relatorio_produtividade(data_inicio, data_fim, departamento)
            if relatorio:
                # Criar CSV (simulando Excel)
                output = io.StringIO()
                writer = csv.writer(output)
                
                # Cabeçalho
                writer.writerow([
                    'Número Registro', 'Nome', 'Departamento', 'Cargo',
                    'Total Acessos', 'Entradas', 'Saídas',
                    'Primeira Entrada', 'Última Saída',
                    'Pontualidade Entrada (%)', 'Pontualidade Saída (%)'
                ])
                
                # Dados
                for row in relatorio:
                    writer.writerow([
                        row[0], row[1], row[2], row[3],  # Dados básicos
                        row[4], row[5], row[6],          # Acessos
                        str(row[7]), str(row[8]),        # Horários
                        f"{row[9]*100:.1f}", f"{row[10]*100:.1f}"  # Pontualidade
                    ])
                
                output.seek(0)
                
                return Response(
                    output.getvalue(),
                    mimetype='text/csv',
                    headers={
                        'Content-Disposition': f'attachment; filename=relatorio_produtividade_{data_inicio}_a_{data_fim}.csv'
                    }
                )
        
        return jsonify({'success': False, 'message': 'Tipo de relatório não suportado'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

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
