#!/bin/bash
# Script para configurar automaticamente o IP do sistema real no docker-compose.yml

echo "🔍 Detectando IP da máquina hospedeira..."

# Tentar detectar o IP da máquina
HOST_IP=$(hostname -I | awk '{print $1}')

# Se não conseguir, tentar outro método
if [ -z "$HOST_IP" ] || [ "$HOST_IP" == "127.0.0.1" ]; then
    HOST_IP=$(ip route get 8.8.8.8 | awk '{print $7; exit}')
fi

# Se ainda não conseguir, tentar via ip addr
if [ -z "$HOST_IP" ] || [ "$HOST_IP" == "127.0.0.1" ]; then
    HOST_IP=$(ip addr show | grep "inet " | grep -v "127.0.0.1" | awk '{print $2}' | cut -d/ -f1 | head -1)
fi

if [ -z "$HOST_IP" ] || [ "$HOST_IP" == "127.0.0.1" ]; then
    echo "❌ Não foi possível detectar o IP automaticamente."
    echo "Por favor, configure manualmente no docker-compose.yml:"
    echo "  SISTEMA_REAL_IP: SEU_IP_AQUI"
    exit 1
fi

echo "✅ IP detectado: $HOST_IP"

# Verificar se já está configurado
if grep -q "SISTEMA_REAL_IP:" docker-compose.yml; then
    # Atualizar IP existente
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/SISTEMA_REAL_IP:.*/SISTEMA_REAL_IP: $HOST_IP/" docker-compose.yml
    else
        # Linux
        sed -i "s/SISTEMA_REAL_IP:.*/SISTEMA_REAL_IP: $HOST_IP/" docker-compose.yml
    fi
    echo "✅ IP atualizado no docker-compose.yml"
else
    # Adicionar configuração
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "/TZ: America\/Sao_Paulo/a\\
      SISTEMA_REAL_IP: $HOST_IP
" docker-compose.yml
    else
        # Linux
        sed -i "/TZ: America\/Sao_Paulo/a\      SISTEMA_REAL_IP: $HOST_IP" docker-compose.yml
    fi
    echo "✅ IP adicionado ao docker-compose.yml"
fi

echo ""
echo "📝 Para aplicar as mudanças, execute:"
echo "   docker compose restart flask_acesso"
echo ""
echo "🔍 Para verificar qual IP está sendo usado:"
echo "   docker exec acesso_flask python3 -c \"from sistema_acesso_funcionarios import get_host_ip; print(get_host_ip())\""
