# 🚀 Guia de Uso Rápido - Sistema de Controle de Acesso

## ⚡ Início Rápido

### 1. Acessar o Sistema
```
URL: https://10.17.94.107:8444
Login: admin
Senha: admin123
```

### 2. Páginas Principais
- **Dashboard**: `/admin` - Visão geral do sistema
- **Funcionários**: `/admin/funcionarios` - Gestão de funcionários
- **Relatórios**: `/admin/relatorios` - Relatórios e exportações
- **Configurações**: `/admin/configuracoes` - Horários e feriados

## 👥 Gestão de Funcionários

### Cadastrar Novo Funcionário
1. Acesse `/admin/funcionarios`
2. Clique em "Adicionar Funcionário"
3. Preencha os dados:
   - **Número de Registro**: ID único
   - **Nome**: Nome completo
   - **Departamento**: Departamento
   - **Cargo**: Função
   - **Empresa**: Empresa
4. Clique em "Salvar"

### Importar Funcionários em Massa
1. Baixe o template: `/admin/funcionarios` → "Download Template"
2. Preencha o arquivo CSV
3. Faça upload: "Importar Funcionários" → selecione arquivo
4. Confirme a importação

## 📊 Relatórios

### Relatório Online (Tempo Real)
- **URL**: `/relatorio-online-sistema-real`
- **Funcionalidades**:
  - ✅ Atualização automática a cada 30 segundos
  - ✅ Funcionários presentes e que saíram
  - ✅ Ordenação por colunas (clique nos cabeçalhos)
  - ✅ Layout responsivo

### Relatório Diário
1. Acesse `/admin/relatorios`
2. Selecione período (data início/fim)
3. Escolha formato: PDF, CSV ou JSON
4. Clique em "Gerar Relatório"

### Relatório por Funcionário
1. Acesse `/admin/relatorios`
2. Selecione funcionário no dropdown
3. Escolha período
4. Escolha formato
5. Clique em "Gerar Relatório"

## 🔐 Acessos de Funcionários

### Acesso Manual
- **URL**: `/acesso-manual`
- **Como usar**:
  1. Digite o número de registro
  2. Escolha tipo de acesso (Automático/Entrada/Saída)
  3. Clique em "Registrar Acesso"

### Acesso Facial
- **URL**: `/acesso-facial`
- **Como usar**:
  1. Posicione o rosto na câmera
  2. Aguarde o reconhecimento
  3. Acesso registrado automaticamente

### Acesso RFID
- **URL**: `/acesso-rfid`
- **Como usar**:
  1. Aproxime o cartão RFID
  2. Acesso registrado automaticamente

## ⚙️ Configurações

### Horários de Trabalho
1. Acesse `/admin/configuracoes`
2. Seção "Horários de Trabalho"
3. Configure:
   - **Horário de Entrada**: Ex: 08:00
   - **Horário de Saída**: Ex: 17:00
   - **Tolerância**: Ex: 15 minutos
   - **Dias da Semana**: Selecione os dias

### Feriados
1. Acesse `/admin/configuracoes`
2. Seção "Feriados"
3. Adicione:
   - **Data**: Data do feriado
   - **Descrição**: Nome do feriado
4. Clique em "Adicionar Feriado"

## 📱 Interface do Sistema

### Cores e Status
- 🟢 **Verde**: Funcionários presentes
- 🟡 **Amarelo**: Funcionários que saíram
- 🔴 **Vermelho**: Alertas/erros
- 🔵 **Azul**: Informações neutras

### Ícones Importantes
- 👥 **Funcionários**: Gestão de usuários
- 📊 **Relatórios**: Relatórios e exportações
- ⚙️ **Configurações**: Horários e feriados
- 🔐 **Acesso**: Páginas de entrada
- 📈 **Dashboard**: Visão geral

## 🔧 Comandos Úteis

### Verificar Status do Sistema
```bash
docker-compose ps
```

### Ver Logs
```bash
# Logs do Flask
docker-compose logs flask_acesso

# Logs do MySQL
docker-compose logs acesso_mysql

# Logs do Caddy
docker-compose logs caddy_acesso
```

### Reiniciar Sistema
```bash
docker-compose restart
```

### Backup do Banco
```bash
docker exec acesso_mysql mysqldump -u root -proot_password acesso_funcionarios_db > backup_$(date +%Y%m%d).sql
```

## 🚨 Problemas Comuns

### Sistema não carrega
1. Verifique se os containers estão rodando: `docker-compose ps`
2. Verifique os logs: `docker-compose logs`
3. Reinicie o sistema: `docker-compose restart`

### Erro de login
1. Verifique se está usando: admin / admin123
2. Limpe o cache do navegador
3. Tente em modo incógnito

### Relatório não gera
1. Verifique se selecionou o período
2. Verifique se há dados no período
3. Tente outro formato (PDF, CSV, JSON)

### Acesso facial não funciona
1. Verifique se a câmera está conectada
2. Verifique se o funcionário tem cadastro facial
3. Verifique a iluminação do ambiente

## 📞 Suporte

### Informações do Sistema
- **Versão**: 1.0.0
- **Última Atualização**: Agosto 2025
- **Status**: 100% Operacional

### URLs Importantes
- **Sistema Principal**: https://10.17.94.107:8444
- **Relatório Online**: https://10.17.94.107:8444/relatorio-online-sistema-real
- **Acesso Manual**: https://10.17.94.107:8444/acesso-manual
- **Acesso Facial**: https://10.17.94.107:8444/acesso-facial

---

## ✅ Checklist de Verificação

### Sistema Funcionando
- [ ] Containers rodando: `docker-compose ps`
- [ ] Login administrativo funcionando
- [ ] Relatório online acessível
- [ ] Acesso manual funcionando
- [ ] Acesso facial funcionando (se configurado)

### Funcionalidades Principais
- [ ] Cadastro de funcionários
- [ ] Importação em massa
- [ ] Relatórios gerando
- [ ] Configurações salvando
- [ ] Logs sendo gerados

### Segurança
- [ ] HTTPS funcionando
- [ ] Login obrigatório
- [ ] Logs de acesso
- [ ] Rate limiting ativo

**Status**: ✅ Sistema 100% Operacional 