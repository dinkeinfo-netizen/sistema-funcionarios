-- Usar o banco de dados correto
USE acesso_funcionarios_db;

-- Adicionar coluna role na tabela admin_users (ignora erro se já existir)
SET @col_exists = 0;
SELECT COUNT(*) INTO @col_exists 
FROM information_schema.COLUMNS 
WHERE TABLE_SCHEMA = 'acesso_funcionarios_db' 
  AND TABLE_NAME = 'admin_users' 
  AND COLUMN_NAME = 'role';

SET @sql = IF(@col_exists = 0,
    'ALTER TABLE admin_users ADD COLUMN role VARCHAR(20) DEFAULT ''admin'' COMMENT ''admin, portaria'' AFTER email',
    'SELECT ''Coluna role já existe'' AS mensagem');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Atualizar admin existente para ter role 'admin'
UPDATE admin_users SET role = 'admin' WHERE role IS NULL OR role = '';

-- Criar usuário portaria (senha inicial: portaria123)
INSERT INTO admin_users (username, password_hash, nome_completo, email, role, ativo) VALUES 
('portaria', '582556a2bd24449b32abfabc541d8264968ccea03a278fc9c10d538c0b0d1c00a32b8e051dc02d7fc2bba0507adae54322c399030d794b42b48459e93ed95d9d', 'Usuário Portaria', 'portaria@empresa.com', 'portaria', TRUE)
ON DUPLICATE KEY UPDATE 
    role = 'portaria',
    ativo = TRUE;
