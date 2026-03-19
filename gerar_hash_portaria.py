#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para gerar hash da senha do usuário portaria
"""

import hashlib
import secrets

def hash_password(password):
    """Cria hash seguro da senha usando PBKDF2"""
    salt = secrets.token_hex(32)
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return salt + pwdhash.hex()

if __name__ == '__main__':
    senha = 'portaria123'
    senha_hash = hash_password(senha)
    
    print('\n' + '='*80)
    print('HASH GERADO PARA SENHA: portaria123')
    print('='*80)
    print(f'\nHash: {senha_hash}\n')
    print('='*80)
    print('\nUse este hash no script SQL para criar o usuário portaria.')
    print('='*80 + '\n')
    
    # Também gerar o SQL completo
    print('\nSQL PRONTO PARA EXECUTAR:')
    print('-'*80)
    print(f"""
-- Adicionar coluna role na tabela admin_users
ALTER TABLE admin_users 
ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'admin' 
COMMENT 'admin, portaria' AFTER email;

-- Atualizar admin existente para ter role 'admin'
UPDATE admin_users SET role = 'admin' WHERE role IS NULL OR role = '';

-- Criar usuário portaria (senha inicial: portaria123)
INSERT INTO admin_users (username, password_hash, nome_completo, email, role, ativo) VALUES 
('portaria', '{senha_hash}', 'Usuário Portaria', 'portaria@empresa.com', 'portaria', TRUE)
ON DUPLICATE KEY UPDATE 
    role = 'portaria',
    ativo = TRUE;
""")
    print('-'*80 + '\n')
