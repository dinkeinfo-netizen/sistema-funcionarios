# Instruções - Sistema de Usuários e Permissões

## ✅ Alterações Implementadas

### 1. Sistema de Permissões (Roles)
- **Admin**: Acesso completo ao sistema
- **Portaria**: Acesso apenas ao relatório online para monitoramento

### 2. Arquivos Criados/Modificados

#### Arquivos Criados:
- `gerar_hash_portaria.py` - Script para gerar hash de senhas
- `criar_usuario_portaria.sql` - SQL para criar usuário portaria
- `templates/admin_usuarios.html` - Interface para gerenciar usuários
- `INSTRUCOES_USUARIO_PORTARIA.md` - Este arquivo

#### Arquivos Modificados:
- `sistema_acesso_funcionarios.py`:
  - Adicionados decorators: `@admin_required` e `@portaria_or_admin_required`
  - Modificada função `admin_login()` para incluir role na sessão
  - Adicionadas rotas de gerenciamento de usuários
  - Protegidas rotas administrativas com `@admin_required`
  - Rota `/relatorio-online-sistema-real` protegida com `@portaria_or_admin_required`
  
- `templates/components/sidebar.html`:
  - Adicionado link "Gerenciar Usuários" no menu

## 📋 Passos para Ativar o Sistema

### Passo 1: Executar SQL no Banco de Dados

Execute o arquivo SQL para adicionar a coluna `role` e criar o usuário portaria:

```bash
# Opção 1: Via Docker
docker exec -i acesso_mysql mysql -u app_user -papp_password sistema_acesso < criar_usuario_portaria.sql

# Opção 2: Conectar diretamente ao MySQL
mysql -u app_user -p sistema_acesso < criar_usuario_portaria.sql
```

Ou execute manualmente no MySQL:

```sql
-- Adicionar coluna role na tabela admin_users
ALTER TABLE admin_users 
ADD COLUMN role VARCHAR(20) DEFAULT 'admin' 
COMMENT 'admin, portaria' AFTER email;

-- Atualizar admin existente para ter role 'admin'
UPDATE admin_users SET role = 'admin' WHERE role IS NULL OR role = '';

-- Criar usuário portaria (senha inicial: portaria123)
INSERT INTO admin_users (username, password_hash, nome_completo, email, role, ativo) VALUES 
('portaria', '582556a2bd24449b32abfabc541d8264968ccea03a278fc9c10d538c0b0d1c00a32b8e051dc02d7fc2bba0507adae54322c399030d794b42b48459e93ed95d9d', 'Usuário Portaria', 'portaria@empresa.com', 'portaria', TRUE)
ON DUPLICATE KEY UPDATE 
    role = 'portaria',
    ativo = TRUE;
```

### Passo 2: Reiniciar o Sistema

```bash
# Se estiver usando Docker
docker-compose restart acesso_flask

# Ou recriar os containers
docker-compose down
docker-compose up -d
```

## 🔐 Credenciais de Acesso

### Usuário Admin (existente)
- **Usuário**: admin
- **Senha**: admin123 (ou a senha que você configurou)
- **Acesso**: Completo ao sistema

### Usuário Portaria (novo)
- **Usuário**: portaria
- **Senha**: portaria123
- **Acesso**: Apenas relatório online

⚠️ **IMPORTANTE**: Altere a senha do usuário portaria após o primeiro login!

## 🎯 Como Usar

### Para o Administrador:

1. **Fazer login** como admin
2. **Acessar "Gerenciar Usuários"** no menu lateral
3. **Criar novos usuários**:
   - Clique em "Novo Usuário"
   - Preencha os dados
   - Escolha o role (admin ou portaria)
4. **Gerenciar usuários existentes**:
   - **Editar**: Modificar nome, email, role e status
   - **Alterar Senha**: Clique no ícone de chave
   - **Deletar**: Remover usuário (não pode deletar seu próprio usuário)

### Para o Usuário Portaria:

1. **Fazer login** com usuário "portaria" e senha "portaria123"
2. **Será redirecionado automaticamente** para o relatório online
3. **Acesso limitado**: Apenas ao relatório online para monitoramento
4. **Não tem acesso** a:
   - Painel administrativo
   - Gestão de funcionários
   - Relatórios administrativos
   - Configurações
   - Cadastros (facial, RFID, QR Code)

## 🔒 Segurança

- Senhas são armazenadas com hash PBKDF2
- Cada usuário tem um salt único
- Não é possível deletar seu próprio usuário
- Não é possível desativar seu próprio usuário
- Todas as ações são registradas nos logs

## 📝 Notas

- O usuário portaria é redirecionado automaticamente para o relatório online após login
- O admin pode acessar todas as funcionalidades normalmente
- Você pode criar quantos usuários quiser com diferentes roles
- Para alterar a senha do usuário portaria, faça login como admin e use a função "Alterar Senha"

## 🐛 Troubleshooting

### Problema: Erro ao fazer login como portaria
**Solução**: Verifique se o SQL foi executado corretamente e se o usuário foi criado:
```sql
SELECT * FROM admin_users WHERE username = 'portaria';
```

### Problema: Portaria consegue acessar outras páginas
**Solução**: Verifique se as rotas estão protegidas com `@admin_required` ou `@portaria_or_admin_required`

### Problema: Não aparece o link "Gerenciar Usuários"
**Solução**: Limpe o cache do navegador e recarregue a página (Ctrl+F5)
