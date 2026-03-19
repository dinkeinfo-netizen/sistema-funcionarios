#!/bin/bash

# Script para ativar o sistema de usuários e permissões
# Sistema de Controle de Acesso de Funcionários

echo "=========================================="
echo "Ativando Sistema de Usuários e Permissões"
echo "=========================================="
echo ""

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Verificar se está no diretório correto
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}Erro: docker-compose.yml não encontrado!${NC}"
    echo "Execute este script no diretório raiz do projeto."
    exit 1
fi

# Verificar se o arquivo SQL existe
if [ ! -f "criar_usuario_portaria.sql" ]; then
    echo -e "${RED}Erro: criar_usuario_portaria.sql não encontrado!${NC}"
    exit 1
fi

echo -e "${YELLOW}Passo 1: Executando SQL no banco de dados...${NC}"

# Tentar executar o SQL no container MySQL
if docker exec -i acesso_mysql mysql -u app_user -papp_password acesso_funcionarios_db < criar_usuario_portaria.sql 2>/dev/null; then
    echo -e "${GREEN}✓ SQL executado com sucesso!${NC}"
else
    echo -e "${YELLOW}Aviso: Não foi possível executar via docker exec.${NC}"
    echo "Tentando método alternativo..."
    
    # Método alternativo: copiar para o container e executar
    docker cp criar_usuario_portaria.sql acesso_mysql:/tmp/criar_usuario_portaria.sql
    if docker exec acesso_mysql mysql -u app_user -papp_password acesso_funcionarios_db -e "source /tmp/criar_usuario_portaria.sql" 2>/dev/null; then
        echo -e "${GREEN}✓ SQL executado com sucesso (método alternativo)!${NC}"
        docker exec acesso_mysql rm /tmp/criar_usuario_portaria.sql
    else
        echo -e "${RED}Erro ao executar SQL!${NC}"
        echo ""
        echo "Execute manualmente:"
        echo "  docker exec -i acesso_mysql mysql -u app_user -papp_password acesso_funcionarios_db < criar_usuario_portaria.sql"
        echo ""
        echo "Ou conecte-se ao MySQL e execute o conteúdo do arquivo criar_usuario_portaria.sql"
        exit 1
    fi
fi

echo ""
echo -e "${YELLOW}Passo 2: Reiniciando container Flask...${NC}"

# Reiniciar o container Flask
if docker restart acesso_flask 2>/dev/null; then
    echo -e "${GREEN}✓ Container Flask reiniciado!${NC}"
    sleep 2
    echo -e "${YELLOW}Aguardando inicialização...${NC}"
else
    echo -e "${RED}Erro ao reiniciar container!${NC}"
    echo "Execute manualmente:"
    echo "  docker restart acesso_flask"
    exit 1
fi

echo ""
echo -e "${GREEN}=========================================="
echo "Sistema ativado com sucesso!"
echo "==========================================${NC}"
echo ""
echo "Credenciais de acesso:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "👤 ADMINISTRADOR:"
echo "   Usuário: admin"
echo "   Senha: admin123 (ou a senha configurada)"
echo "   Acesso: Completo ao sistema"
echo ""
echo "👤 PORTARIA:"
echo "   Usuário: portaria"
echo "   Senha: portaria123"
echo "   Acesso: Apenas relatório online"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANTE:${NC}"
echo "   Altere a senha do usuário portaria após o primeiro login!"
echo ""
echo "   Para alterar:"
echo "   1. Faça login como admin"
echo "   2. Acesse 'Gerenciar Usuários' no menu"
echo "   3. Clique no ícone de chave ao lado do usuário portaria"
echo "   4. Digite a nova senha"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
