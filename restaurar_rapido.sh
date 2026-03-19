#!/bin/bash
# Script portátil para restaurar backup em máquina nova
# Este script pode ser executado diretamente do backup extraído

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}📥 Restauração Rápida em Máquina Nova${NC}"
echo "=========================================="
echo ""

# Detectar onde estamos
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR=""

# Tentar encontrar o backup
if [ -d "backups/completo" ]; then
    BACKUP_DIR="backups/completo"
elif [ -d "../backups/completo" ]; then
    BACKUP_DIR="../backups/completo"
elif [ -d "$SCRIPT_DIR/backups/completo" ]; then
    BACKUP_DIR="$SCRIPT_DIR/backups/completo"
fi

if [ -z "$BACKUP_DIR" ] || [ ! -d "$BACKUP_DIR" ]; then
    echo -e "${RED}❌ Erro: Diretório de backup não encontrado!${NC}"
    echo ""
    echo -e "${YELLOW}💡 Instruções:${NC}"
    echo "  1. Extraia o backup: tar -xzf sistema_funcionarios_backup_*.tar.gz"
    echo "  2. Execute este script de dentro da pasta extraída"
    echo "  3. Ou copie este script para a pasta do backup"
    echo ""
    echo -e "${BLUE}Estrutura esperada:${NC}"
    echo "  backups/completo/sistema_funcionarios_backup_YYYYMMDD_HHMMSS/"
    echo "    ├── volumes/"
    echo "    ├── arquivos/"
    echo "    └── INFO_BACKUP.txt"
    exit 1
fi

# Listar backups disponíveis
echo -e "${BLUE}📦 Backups encontrados:${NC}"
BACKUPS=($(ls -1d "$BACKUP_DIR"/sistema_funcionarios_backup_* 2>/dev/null))
if [ ${#BACKUPS[@]} -eq 0 ]; then
    echo -e "${RED}❌ Nenhum backup encontrado em $BACKUP_DIR${NC}"
    exit 1
fi

for i in "${!BACKUPS[@]}"; do
    backup_name=$(basename "${BACKUPS[$i]}")
    echo "  $((i+1))) $backup_name"
done

echo ""
read -p "Escolha o backup [1-${#BACKUPS[@]}]: " ESCOLHA

if ! [[ "$ESCOLHA" =~ ^[0-9]+$ ]] || [ "$ESCOLHA" -lt 1 ] || [ "$ESCOLHA" -gt ${#BACKUPS[@]} ]; then
    echo -e "${RED}❌ Escolha inválida!${NC}"
    exit 1
fi

BACKUP_NAME=$(basename "${BACKUPS[$((ESCOLHA-1))]}")
BACKUP_PATH="${BACKUPS[$((ESCOLHA-1))]}"

echo ""
echo -e "${BLUE}📋 Backup selecionado: $BACKUP_NAME${NC}"
echo ""

# Mostrar informações do backup
if [ -f "$BACKUP_PATH/INFO_BACKUP.txt" ]; then
    echo -e "${YELLOW}📄 Informações do backup:${NC}"
    head -20 "$BACKUP_PATH/INFO_BACKUP.txt"
    echo ""
fi

# Confirmar
echo -e "${RED}⚠️  Esta operação irá:${NC}"
echo "  1. Criar/restaurar volumes Docker"
echo "  2. Copiar arquivos de configuração"
echo "  3. Iniciar o sistema"
echo ""
read -p "Deseja continuar? (sim/não): " CONFIRM

if [[ ! "$CONFIRM" =~ ^[Ss][Ii][Mm]$ ]] && [[ ! "$CONFIRM" =~ ^[Ss]$ ]]; then
    echo -e "${YELLOW}Operação cancelada.${NC}"
    exit 0
fi

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker não encontrado!${NC}"
    echo "Instale Docker primeiro: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! docker compose version &> /dev/null && ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose não encontrado!${NC}"
    echo "Instale Docker Compose primeiro"
    exit 1
fi

# Criar diretório do sistema se não existir
SISTEMA_DIR="$(pwd)"
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${YELLOW}📁 Preparando diretório do sistema...${NC}"
    mkdir -p sistema-funcionarios-restaurado
    SISTEMA_DIR="$(pwd)/sistema-funcionarios-restaurado"
    mkdir -p "$SISTEMA_DIR"
fi

# Restaurar volumes
echo -e "${YELLOW}📦 Restaurando volumes Docker...${NC}"

declare -A VOLUME_MAP=(
    ["mysql_data"]="sistema-funcionarios_mysql_acesso_data"
    ["caddy_data"]="sistema-funcionarios_caddy_acesso_data"
    ["caddy_config"]="sistema-funcionarios_caddy_acesso_config"
)

for volume_file in "$BACKUP_PATH/volumes"/*.tar.gz; do
    if [ ! -f "$volume_file" ]; then
        continue
    fi
    
    filename=$(basename "$volume_file")
    volume_key=""
    
    if [[ "$filename" =~ ^mysql_data ]]; then
        volume_key="mysql_acesso_data"
    elif [[ "$filename" =~ ^caddy_data ]]; then
        volume_key="caddy_acesso_data"
    elif [[ "$filename" =~ ^caddy_config ]]; then
        volume_key="caddy_acesso_config"
    fi
    
    if [ -z "$volume_key" ] || [ -z "${VOLUME_MAP[$volume_key]}" ]; then
        echo -e "  ${YELLOW}⚠️  Volume desconhecido: $filename (pulando)${NC}"
        continue
    fi
    
    volume_name="${VOLUME_MAP[$volume_key]}"
    echo -e "  📦 Restaurando: $volume_name"
    
    # Remover volume antigo
    docker volume rm "$volume_name" 2>/dev/null || true
    
    # Criar novo volume
    docker volume create "$volume_name" 2>/dev/null || true
    
    # Restaurar dados
    docker run --rm \
        -v "$volume_name":/dest \
        -v "$(realpath "$volume_file")":/backup.tar.gz:ro \
        alpine sh -c "cd /dest && tar -xzf /backup.tar.gz && chown -R 999:999 /dest 2>/dev/null || chown -R 1000:1000 /dest 2>/dev/null || true" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo -e "    ${GREEN}✅ $volume_name restaurado${NC}"
    else
        echo -e "    ${RED}❌ Erro ao restaurar $volume_name${NC}"
    fi
done

echo ""

# Copiar arquivos de configuração
echo -e "${YELLOW}📁 Copiando arquivos de configuração...${NC}"

if [ -d "$BACKUP_PATH/arquivos" ]; then
    # Copiar arquivos essenciais
    for file in docker-compose.yml Dockerfile Caddyfile init.sql requirements.txt app.py; do
        if [ -f "$BACKUP_PATH/arquivos/$file" ]; then
            cp "$BACKUP_PATH/arquivos/$file" "$SISTEMA_DIR/" 2>/dev/null
            echo -e "  ${GREEN}✅ $file${NC}"
        fi
    done
    
    # Copiar diretórios
    if [ -d "$BACKUP_PATH/arquivos/templates" ]; then
        cp -r "$BACKUP_PATH/arquivos/templates" "$SISTEMA_DIR/" 2>/dev/null
        echo -e "  ${GREEN}✅ templates/${NC}"
    fi
    
    # Copiar scripts SQL
    for sql_file in "$BACKUP_PATH/arquivos"/*.sql; do
        if [ -f "$sql_file" ]; then
            cp "$sql_file" "$SISTEMA_DIR/" 2>/dev/null
            echo -e "  ${GREEN}✅ $(basename "$sql_file")${NC}"
        fi
    done
else
    echo -e "${YELLOW}⚠️  Diretório arquivos/ não encontrado${NC}"
fi

echo ""

# Ir para diretório do sistema
cd "$SISTEMA_DIR"

# Iniciar sistema
echo -e "${GREEN}🚀 Iniciando sistema...${NC}"
docker compose up -d

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Restauração concluída!${NC}"
    echo ""
    echo -e "${BLUE}💡 Próximos passos:${NC}"
    echo "  1. Aguarde alguns segundos para os containers iniciarem"
    echo "  2. Verifique os logs: cd $SISTEMA_DIR && docker compose logs"
    echo "  3. Acesse o sistema: https://localhost:8444"
    echo "  4. Verifique se os dados foram restaurados corretamente"
    echo ""
    echo -e "${YELLOW}📁 Sistema restaurado em: $SISTEMA_DIR${NC}"
else
    echo -e "${RED}❌ Erro ao iniciar sistema!${NC}"
    echo -e "${YELLOW}💡 Verifique os logs: docker compose logs${NC}"
    exit 1
fi
