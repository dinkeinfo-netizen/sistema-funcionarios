# 🔧 Configuração Automática de IP do Sistema Real

## 📋 Visão Geral

O sistema agora detecta **automaticamente** o IP da máquina hospedeira quando instalado em um novo equipamento. Isso elimina a necessidade de configurar manualmente o IP em cada instalação.

## 🚀 Como Funciona

### Detecção Automática

O sistema usa a seguinte ordem de prioridade para determinar o IP:

1. **Variável de Ambiente `SISTEMA_REAL_URL`** (prioridade máxima)
   - URL completa: `https://10.17.95.4:8444`
   - O sistema extrai o IP automaticamente

2. **Variável de Ambiente `SISTEMA_REAL_IP`**
   - Apenas o IP: `10.17.95.4`
   - A porta padrão (8444) será usada

3. **Detecção Automática via Socket**
   - O sistema conecta a um servidor externo (8.8.8.8) para descobrir qual interface de rede usar
   - Retorna o IP da interface de rede padrão

4. **Resolução via Hostname**
   - Tenta resolver o hostname da máquina
   - Se não for localhost, usa esse IP

5. **Fallback: localhost**
   - Se nenhum método funcionar, usa `127.0.0.1`

## ⚙️ Configuração Manual (Opcional)

Se você quiser configurar manualmente o IP, adicione uma das variáveis de ambiente:

### Opção 1: Via docker-compose.yml

Edite o arquivo `docker-compose.yml` e adicione na seção `environment` do serviço `flask_acesso`:

```yaml
environment:
  # ... outras variáveis ...
  SISTEMA_REAL_IP: 10.17.95.4
  # Ou URL completa:
  # SISTEMA_REAL_URL: https://10.17.95.4:8444
  # Ou apenas a porta (IP será detectado):
  # SISTEMA_REAL_PORT: 8444
```

### Opção 2: Via arquivo .env

Crie um arquivo `.env` na raiz do projeto:

```bash
SISTEMA_REAL_IP=10.17.95.4
# Ou
SISTEMA_REAL_URL=https://10.17.95.4:8444
```

### Opção 3: Variáveis de Ambiente do Sistema

```bash
export SISTEMA_REAL_IP=10.17.95.4
# Ou
export SISTEMA_REAL_URL=https://10.17.95.4:8444
```

## 🔍 Verificação

Para verificar qual IP está sendo usado, verifique os logs do sistema:

```bash
docker logs acesso_flask | grep "Conectando ao sistema real"
```

Você verá uma mensagem como:
```
🔗 Conectando ao sistema real em: https://10.17.95.4:8444
```

## 🐛 Solução de Problemas

### Erro: "Connection timeout"

1. **Verifique se o IP está correto:**
   ```bash
   # No container
   docker exec -it acesso_flask python3 -c "from sistema_acesso_funcionarios import get_host_ip; print(get_host_ip())"
   ```

2. **Teste a conectividade:**
   ```bash
   # Do host
   curl -k https://SEU_IP:8444/api/relatorio-presenca
   ```

3. **Configure manualmente se necessário:**
   - Adicione `SISTEMA_REAL_IP` ou `SISTEMA_REAL_URL` no `docker-compose.yml`
   - Reinicie o container: `docker-compose restart flask_acesso`

### Erro: "IP não detectado"

Se a detecção automática não funcionar:

1. **Configure manualmente via variável de ambiente**
2. **Verifique se a máquina tem acesso à rede**
3. **Use o IP da interface de rede principal**

## 📝 Notas Importantes

- A detecção automática funciona melhor quando a máquina está conectada à rede
- Em ambientes Docker, o IP detectado será o IP do host, não do container
- Para ambientes com múltiplas interfaces de rede, configure manualmente o IP correto
- A porta padrão é `8444`, mas pode ser alterada via `SISTEMA_REAL_PORT`

## 🔄 Atualização

Se você já tinha o sistema instalado com IP fixo, o sistema continuará funcionando. A detecção automática só será usada se nenhuma variável de ambiente estiver configurada.
