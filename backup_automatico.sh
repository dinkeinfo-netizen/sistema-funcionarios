#!/bin/bash
# Script para backup AUTOMÁTICO do sistema (Não-interativo)
# Ideal para ser usado no crontab

# Cores para output (uso em logs)
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo "=========================================="
echo "📦 Backup AUTOMÁTICO - $(date)"
echo "=========================================="

# Configurações
BASE_DIR="/sistema-funcionarios"
BACKUP_DIR="${BASE_DIR}/backups/completo"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="sistema_funcionarios_auto_${TIMESTAMP}"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

# Volumes
VOLUMES=(
    "sistema-funcionarios_mysql_acesso_data:mysql_acesso_data"
    "sistema-funcionarios_caddy_acesso_data:caddy_acesso_data"
    "sistema-funcionarios_caddy_acesso_config:caddy_acesso_config"
)

# Criar pastas
mkdir -p "$BACKUP_PATH/volumes"
mkdir -p "$BACKUP_PATH/arquivos"

echo "🛑 Parando sistema para backup consistente..."
cd "$BASE_DIR" || exit 1
docker compose stop

# Backup dos volumes
echo "📦 Copiando volumes Docker..."
for volume_info in "${VOLUMES[@]}"; do
    IFS=':' read -r vn vf <<< "$volume_info"
    if docker volume inspect "$vn" &>/dev/null; then
        echo "  - $vn"
        docker run --rm \
            -v "$vn":/source:ro \
            -v "$(pwd)/${BACKUP_PATH}/volumes":/backup \
            alpine tar czf "/backup/${vf}_${TIMESTAMP}.tar.gz" -C /source . 2>/dev/null
    else
        echo "⚠️  Volume $vn não encontrado."
    fi
done

# Backup de arquivos importantes
echo "📁 Copiando arquivos de configuração..."
FILES_TO_COPY=(
    "docker-compose.yml"
    "Dockerfile"
    "Caddyfile"
    "init.sql"
    "app.py"
    "sistema_acesso_funcionarios.py"
    "templates"
    "static"
    "*.sh"
    ".env"
)

for f in "${FILES_TO_COPY[@]}"; do
    if [ -e "$f" ]; then
        cp -r "$f" "${BACKUP_PATH}/arquivos/" 2>/dev/null
    fi
done

# Criar INFO
cat > "${BACKUP_PATH}/INFO.txt" <<EOF
Backup automático realizado em: $(date)
Path: ${BACKUP_PATH}
EOF

# Compactar final
echo "🗜️  Criando arquivo final..."
cd "$BACKUP_DIR" || exit 1
tar czf "${BACKUP_NAME}.tar.gz" "$BACKUP_NAME" 2>/dev/null

# Limpar pasta temporária
rm -rf "$BACKUP_NAME"

echo "🚀 Reiniciando sistema..."
cd "$BASE_DIR" || exit 1
docker compose start

if [ $? -eq 0 ]; then
    echo "✅ Backup concluído com sucesso: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
else
    echo "⚠️  Backup concluído, mas houve erro ao reiniciar o sistema!"
fi
echo "=========================================="
