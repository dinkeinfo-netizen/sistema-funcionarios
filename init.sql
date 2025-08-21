-- ========================================
-- SISTEMA DE CONTROLE DE ACESSO DE FUNCIONÁRIOS
-- Banco de Dados de Inicialização
-- Versão: 1.0
-- ========================================

-- Criação do banco de dados
CREATE DATABASE IF NOT EXISTS acesso_funcionarios_db 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE acesso_funcionarios_db;

-- ========================================
-- TABELAS PRINCIPAIS
-- ========================================

-- Tabela de funcionários
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
) ENGINE=InnoDB;

-- Tabela de acessos de funcionários
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
) ENGINE=InnoDB;

-- Tabela de horários de trabalho
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
) ENGINE=InnoDB;

-- Tabela de feriados e dias especiais
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
) ENGINE=InnoDB;

-- Tabela de justificativas
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
) ENGINE=InnoDB;

-- Tabela de configurações
CREATE TABLE IF NOT EXISTS configuracoes_acesso (
    chave VARCHAR(50) PRIMARY KEY,
    valor TEXT,
    descricao VARCHAR(255) NULL,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Tabela de logs
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
) ENGINE=InnoDB;

-- Tabela de administradores
CREATE TABLE IF NOT EXISTS admin_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    nome_completo VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    ativo BOOLEAN DEFAULT TRUE,
    ultimo_login TIMESTAMP NULL,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tentativas_login INT DEFAULT 0,
    bloqueado_ate TIMESTAMP NULL,
    
    -- Índices
    INDEX idx_username (username),
    INDEX idx_ativo (ativo),
    INDEX idx_ultimo_login (ultimo_login)
) ENGINE=InnoDB;

-- ========================================
-- DADOS INICIAIS
-- ========================================

-- Inserir administrador padrão (senha: admin123)
INSERT INTO admin_users (username, password_hash, nome_completo, email) VALUES 
('admin', '483a6b228dc77d100ca71fa11c3cf2b7651b0da154cf157da545f9b5a6942c960b2e0b415afe24abf17b5e2e4565f943dae1ee5fc1f6bdf3030410dde5700f5e', 'Administrador Sistema', 'admin@empresa.com')
ON DUPLICATE KEY UPDATE nome_completo = VALUES(nome_completo);

-- Inserir funcionários de exemplo
INSERT INTO funcionarios (numero_registro, nome, cpf, departamento, cargo, empresa, data_admissao) VALUES 
('001', 'João Silva', '123.456.789-00', 'TI', 'Desenvolvedor', 'Empresa A', '2023-01-15'),
('002', 'Maria Santos', '987.654.321-00', 'RH', 'Analista', 'Empresa A', '2023-02-20'),
('003', 'Pedro Oliveira', '456.789.123-00', 'Financeiro', 'Contador', 'Empresa A', '2023-03-10')
ON DUPLICATE KEY UPDATE nome = VALUES(nome);

-- Inserir configurações padrão
INSERT INTO configuracoes_acesso (chave, valor, descricao) VALUES
('sistema_nome', 'Sistema de Controle de Acesso de Funcionários', 'Nome do sistema'),
('sistema_versao', '1.0.0', 'Versão do sistema'),
('horario_entrada_padrao', '08:00', 'Horário padrão de entrada'),
('horario_saida_padrao', '18:00', 'Horário padrão de saída'),
('tolerancia_padrao', '15', 'Tolerância padrão em minutos'),
('permitir_finais_semana', 'false', 'Permitir acesso em finais de semana'),
('max_tentativas_login', '5', 'Máximo de tentativas de login'),
('tempo_bloqueio_login', '30', 'Tempo de bloqueio em minutos')
ON DUPLICATE KEY UPDATE valor = VALUES(valor);

-- Inserir feriados nacionais de exemplo (2024)
INSERT INTO feriados_dias_especiais (data_feriado, descricao, tipo) VALUES
('2024-01-01', 'Confraternização Universal', 'feriado'),
('2024-04-21', 'Tiradentes', 'feriado'),
('2024-05-01', 'Dia do Trabalho', 'feriado'),
('2024-09-07', 'Independência do Brasil', 'feriado'),
('2024-10-12', 'Nossa Senhora Aparecida', 'feriado'),
('2024-11-02', 'Finados', 'feriado'),
('2024-11-15', 'Proclamação da República', 'feriado'),
('2024-12-25', 'Natal', 'feriado')
ON DUPLICATE KEY UPDATE descricao = VALUES(descricao);

