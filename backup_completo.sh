#!/bin/bash
# Script para fazer backup COMPLETO do sistema Docker
# Inclui: volumes, configurações, código e banco de dados

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}📦 Backup Completo do Sistema Docker${NC}"
echo "=========================================="
echo ""

# Configurações
BACKUP_DIR="./backups/completo"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="sistema_funcionarios_backup_${TIMESTAMP}"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

# Volumes do sistema (mysql_data contém TODOS os dados do banco)
VOLUMES=(
    "sistema-funcionarios_mysql_acesso_data:mysql_acesso_data"  # ⚠️ IMPORTANTE: Contém todos os dados do banco
    "sistema-funcionarios_caddy_acesso_data:caddy_acesso_data"
    "sistema-funcionarios_caddy_acesso_config:caddy_acesso_config"
)

# Criar diretório de backup
mkdir -p "$BACKUP_PATH"
mkdir -p "${BACKUP_PATH}/volumes"
mkdir -p "${BACKUP_PATH}/arquivos"

echo -e "${BLUE}📋 Itens que serão incluídos no backup:${NC}"
echo "  ✅ ${GREEN}Volumes Docker (mysql_data contém TODOS os dados do banco)${NC}"
echo "  ✅ Arquivos de configuração (docker-compose.yml, Caddyfile, etc)"
echo "  ✅ Código da aplicação (app.py, templates, etc)"
echo "  ✅ Scripts SQL (init.sql, migrações)"
echo "  ✅ Dump SQL do banco (backup adicional, se sistema estiver rodando)"
echo ""
echo -e "${GREEN}💾 IMPORTANTE: Os dados do banco estão no volume mysql_data${NC}"
echo -e "${GREEN}   Este volume será SEMPRE incluído no backup${NC}"
echo ""

# Verificar se containers estão rodando
CONTAINERS_RUNNING=false
if docker compose ps 2>/dev/null | grep -q "Up"; then
    CONTAINERS_RUNNING=true
fi

if [ "$CONTAINERS_RUNNING" = true ]; then
    echo -e "${YELLOW}⚠️  Containers estão rodando!${NC}"
    echo ""
    echo -e "${BLUE}💡 Recomendações:${NC}"
    echo "  • Para backup mais seguro e consistente: PARE o sistema primeiro"
    echo "  • Para backup rápido (com sistema ativo): Pode continuar, mas pode haver inconsistências"
    echo ""
    echo -e "${YELLOW}Escolha uma opção:${NC}"
    echo "  1) Parar sistema, fazer backup, e reiniciar (RECOMENDADO)"
    echo "  2) Fazer backup com sistema rodando (mais rápido, menos seguro)"
    echo "  3) Cancelar"
    echo ""
    read -p "Opção [1-3]: " OPCAO
    
    case $OPCAO in
        1)
            echo -e "${YELLOW}🛑 Parando containers...${NC}"
            docker compose stop
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}✅ Containers parados${NC}"
                echo ""
                STOPPED_BY_SCRIPT=true
            else
                echo -e "${RED}❌ Erro ao parar containers${NC}"
                exit 1
            fi
            ;;
        2)
            echo -e "${YELLOW}⚠️  Fazendo backup com sistema ativo...${NC}"
            echo -e "${YELLOW}   (Pode haver inconsistências nos dados)${NC}"
            echo ""
            
            # Fazer dump SQL adicional (mais seguro quando sistema está rodando)
            echo -e "${YELLOW}💾 Fazendo dump SQL do banco...${NC}"
            docker compose exec -T mysql mysqldump \
                -uroot \
                -proot_password \
                --single-transaction \
                --routines \
                --triggers \
                --events \
                --add-drop-database \
                --databases funcionarios_db > "${BACKUP_PATH}/arquivos/dump_sql_${TIMESTAMP}.sql" 2>/dev/null
            
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}✅ Dump SQL criado${NC}"
                # Comprimir dump
                gzip -f "${BACKUP_PATH}/arquivos/dump_sql_${TIMESTAMP}.sql"
            else
                echo -e "${YELLOW}⚠️  Não foi possível fazer dump SQL${NC}"
            fi
            echo ""
            STOPPED_BY_SCRIPT=false
            ;;
        3)
            echo -e "${YELLOW}Operação cancelada.${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Opção inválida!${NC}"
            exit 1
            ;;
    esac
else
    echo -e "${GREEN}✅ Containers não estão rodando. Backup será mais seguro e consistente.${NC}"
    echo ""
    STOPPED_BY_SCRIPT=false
    
    # Tentar fazer dump SQL mesmo com sistema parado (se MySQL estiver acessível)
    echo -e "${YELLOW}💾 Tentando fazer dump SQL do banco...${NC}"
    if docker compose exec -T mysql mysqldump \
        -uroot \
        -proot_password \
        --single-transaction \
        --routines \
        --triggers \
        --events \
        --add-drop-database \
        --databases refeitorio_db > "${BACKUP_PATH}/arquivos/dump_sql_${TIMESTAMP}.sql" 2>/dev/null; then
        echo -e "${GREEN}✅ Dump SQL criado${NC}"
        gzip -f "${BACKUP_PATH}/arquivos/dump_sql_${TIMESTAMP}.sql"
    else
        echo -e "${YELLOW}⚠️  Não foi possível fazer dump SQL (banco parado)${NC}"
        echo -e "${BLUE}💡 Os dados do banco estarão no volume mysql_data${NC}"
    fi
    echo ""
fi

# Backup dos volumes (SEMPRE inclui os dados do banco)
echo -e "${YELLOW}📦 Fazendo backup dos volumes Docker (incluindo dados do banco)...${NC}"
for volume_info in "${VOLUMES[@]}"; do
    IFS=':' read -r volume_name volume_file <<< "$volume_info"
    
    if docker volume inspect "$volume_name" &>/dev/null; then
        echo -e "  📦 Backup do volume: $volume_name"
        
        # Verificar se é o volume do MySQL (contém dados do banco)
        if [ "$volume_name" = "sistema-funcionarios_mysql_data" ]; then
            echo -e "    ${BLUE}💾 Este volume contém TODOS os dados do banco de dados${NC}"
        fi
        
        docker run --rm \
            -v "$volume_name":/source:ro \
            -v "$(pwd)/${BACKUP_PATH}/volumes":/backup \
            alpine tar czf "/backup/${volume_file}_${TIMESTAMP}.tar.gz" -C /source . 2>/dev/null
        
        if [ $? -eq 0 ]; then
            SIZE=$(du -h "${BACKUP_PATH}/volumes/${volume_file}_${TIMESTAMP}.tar.gz" 2>/dev/null | cut -f1)
            echo -e "    ${GREEN}✅ $volume_name → ${volume_file}_${TIMESTAMP}.tar.gz ($SIZE)${NC}"
            
            # Verificar se o arquivo tem conteúdo
            if [ "$volume_name" = "sistema-funcionarios_mysql_acesso_data" ]; then
                FILE_SIZE_BYTES=$(stat -f%z "${BACKUP_PATH}/volumes/${volume_file}_${TIMESTAMP}.tar.gz" 2>/dev/null || stat -c%s "${BACKUP_PATH}/volumes/${volume_file}_${TIMESTAMP}.tar.gz" 2>/dev/null || echo "0")
                if [ "$FILE_SIZE_BYTES" -lt 1000 ]; then
                    echo -e "    ${RED}⚠️  ATENÇÃO: Arquivo muito pequeno! Pode estar vazio.${NC}"
                else
                    echo -e "    ${GREEN}✅ Dados do banco incluídos no backup${NC}"
                fi
            fi
        else
            echo -e "    ${RED}❌ Erro ao fazer backup de $volume_name${NC}"
            if [ "$volume_name" = "sistema-funcionarios_mysql_acesso_data" ]; then
                echo -e "    ${RED}⚠️  ERRO CRÍTICO: Dados do banco NÃO foram incluídos!${NC}"
            fi
        fi
    else
        echo -e "    ${YELLOW}⚠️  Volume $volume_name não encontrado (pode não existir ainda)${NC}"
        if [ "$volume_name" = "sistema-funcionarios_mysql_acesso_data" ]; then
            echo -e "    ${RED}⚠️  ATENÇÃO: Volume do banco não encontrado! Dados não serão incluídos no backup!${NC}"
        fi
    fi
done

echo ""

# Backup dos arquivos importantes
echo -e "${YELLOW}📁 Fazendo backup dos arquivos de configuração...${NC}"

# Lista de arquivos e diretórios importantes
IMPORTANT_FILES=(
    "docker-compose.yml"
    "Dockerfile"
    "Caddyfile"
    "init.sql"
    "requirements.txt"
    "app.py"
    "templates/"
    "migracao_add_centro_custo.sql"
    "*.sh"
    "restaurar_completo_sistema.sh"
    "restaurar_rapido.sh"
    "RESTAURAR_MAQUINA_NOVA.md"
    "GUIA_BACKUP_RESTORE.md"
    "README_BACKUP.md"
)

# Copiar arquivos
for pattern in "${IMPORTANT_FILES[@]}"; do
    if [[ "$pattern" == *"/" ]]; then
        # É um diretório
        dir_name="${pattern%/}"
        if [ -d "$dir_name" ]; then
            cp -r "$dir_name" "${BACKUP_PATH}/arquivos/" 2>/dev/null
            echo -e "  ${GREEN}✅ $dir_name/${NC}"
        fi
    else
        # É um arquivo ou padrão
        for file in $pattern; do
            if [ -f "$file" ]; then
                cp "$file" "${BACKUP_PATH}/arquivos/" 2>/dev/null
                echo -e "  ${GREEN}✅ $file${NC}"
            fi
        done
    fi
done

# Criar arquivo de informações do backup
echo -e "${YELLOW}📝 Criando arquivo de informações...${NC}"
cat > "${BACKUP_PATH}/INFO_BACKUP.txt" <<EOF
========================================
BACKUP COMPLETO DO SISTEMA FUNCIONARIOS
========================================
Data/Hora: $(date)
Hostname: $(hostname)
Sistema: $(uname -a)

VOLUMES INCLUÍDOS (com dados do banco):
$(for volume_info in "${VOLUMES[@]}"; do 
    IFS=':' read -r vn vf <<< "$volume_info"
    if [ "$vn" = "sistema-funcionarios_mysql_acesso_data" ]; then
        echo "  - $vn → ${vf}_${TIMESTAMP}.tar.gz ⚠️ CONTÉM TODOS OS DADOS DO BANCO"
    else
        echo "  - $vn → ${vf}_${TIMESTAMP}.tar.gz"
    fi
done)

ARQUIVOS INCLUÍDOS:
  - Configurações Docker (docker-compose.yml, Dockerfile)
  - Configurações Caddy (Caddyfile)
  - Scripts SQL (init.sql, migrações)
  - Código da aplicação (app.py, templates/)
  - Scripts de backup/restauração (*.sh)
  - Dump SQL adicional (se disponível)

COMO RESTAURAR:
  1. Copie toda a pasta de backup para a nova máquina
  2. Execute: ./restaurar_completo_sistema.sh ${BACKUP_NAME}
  3. Ou siga as instruções em: GUIA_BACKUP_RESTORE.md

NOTAS:
  - Este backup contém TODOS os dados do sistema
  - Mantenha este backup em local seguro
  - Teste a restauração em ambiente de teste antes de usar em produção
EOF

echo -e "${GREEN}✅ Arquivo de informações criado${NC}"
echo ""

# Criar arquivo compactado final
echo -e "${YELLOW}🗜️  Compactando backup completo...${NC}"
cd "$BACKUP_DIR"
tar czf "${BACKUP_NAME}.tar.gz" "$BACKUP_NAME" 2>/dev/null

if [ $? -eq 0 ]; then
    FINAL_SIZE=$(du -h "${BACKUP_NAME}.tar.gz" | cut -f1)
    echo -e "${GREEN}✅ Backup compactado criado!${NC}"
    echo ""
    echo -e "${GREEN}📦 Backup completo salvo em:${NC}"
    echo "  ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
    echo "  Tamanho: $FINAL_SIZE"
    echo ""
    echo -e "${BLUE}💡 Para restaurar em outra máquina:${NC}"
    echo "  1. Copie o arquivo ${BACKUP_NAME}.tar.gz para a nova máquina"
    echo "  2. Extraia: tar -xzf ${BACKUP_NAME}.tar.gz"
    echo "  3. Execute: cd backups/completo/${BACKUP_NAME} && ./restaurar_rapido.sh"
    echo "     OU: ./restaurar_completo_sistema.sh ${BACKUP_NAME}"
    echo ""
    echo -e "${GREEN}📖 Veja também: RESTAURAR_MAQUINA_NOVA.md${NC}"
    echo ""
    echo -e "${YELLOW}⚠️  Mantenha este backup em local seguro!${NC}"
    
    # Limpar pasta não compactada (opcional - descomente se quiser)
    # rm -rf "$BACKUP_NAME"
else
    echo -e "${YELLOW}⚠️  Backup criado, mas não foi possível compactar${NC}"
    echo -e "${BLUE}💡 Backup está em: ${BACKUP_PATH}${NC}"
fi

# Reiniciar sistema se foi parado pelo script
if [ "${STOPPED_BY_SCRIPT}" = true ]; then
    echo ""
    echo -e "${YELLOW}🚀 Reiniciando sistema...${NC}"
    docker compose start
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Sistema reiniciado${NC}"
    else
        echo -e "${YELLOW}⚠️  Sistema não reiniciado automaticamente. Execute: docker compose start${NC}"
    fi
fi
