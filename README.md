
# Sistema de Gestão - Escola Sol Maior 🎵

Um sistema completo de gestão para escolas de música, desenvolvido com Flask e PostgreSQL, oferecendo funcionalidades abrangentes para administração, professores e alunos.

## 📋 Sobre o Sistema

O Sistema Escola Sol Maior é uma plataforma digital que facilita a gestão completa de uma escola de música, incluindo:

- **Gestão de Alunos e Professores**: Cadastro completo com informações pessoais e contatos de emergência
- **Cursos e Matrículas**: Gerenciamento de cursos, horários e matrículas de alunos
- **Sistema Financeiro**: Controle de pagamentos, mensalidades e relatórios financeiros
- **Materiais Didáticos**: Upload e distribuição de materiais por curso
- **Agendamento**: Sistema de horários para aulas e uso de salas
- **Comunicação**: Notificações automáticas por email para pagamentos e lembretes

## 🚀 Primeiros Passos

### Requisitos do Sistema
- Python 3.11+
- PostgreSQL
- Conta de email para notificações (Gmail recomendado)

### Configuração Inicial

1. **Clone ou baixe o projeto** para sua máquina

2. **Configure as variáveis de ambiente** criando um arquivo `.env`:
```env
# Configurações do Banco de Dados
DATABASE_URL=postgresql://usuario:senha@localhost/escola_sol_maior

# Configurações de Email
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=seu_email@gmail.com
MAIL_PASSWORD=sua_senha_de_app

# Chave Secreta (gere uma chave aleatória)
SECRET_KEY=sua_chave_secreta_muito_aleatoria

# Configurações de Pagamento (opcional)
PAYMENT_API_KEY=sua_chave_do_gateway
PAYMENT_API_URL=https://api.gateway.com
PAYMENT_WEBHOOK_URL=https://seu_site.com
```

3. **Instale as dependências**:
```bash
pip install -r requirements.txt
```

4. **Configure o banco de dados**:
```bash
# Crie o banco no PostgreSQL
createdb escola_sol_maior

# Execute as migrações (se houver)
python main.py
```

5. **Execute o sistema**:
```bash
python main.py
```

O sistema estará disponível em `http://localhost:5000`

## 👥 Tipos de Usuário

### 🔧 Administrador
- Acesso completo ao sistema
- Gerenciamento de usuários, cursos e finanças
- Relatórios e dashboard completo
- Configurações do sistema

### 👨‍🏫 Professor
- Visualização de horários e alunos
- Acesso aos materiais dos cursos que leciona
- Comunicação com alunos

### 🎓 Aluno
- Visualização de horários e pagamentos
- Acesso aos materiais do curso
- Realização de pagamentos online

## 📚 Funcionalidades Principais

### Gestão de Alunos
- Cadastro completo com dados pessoais
- Contatos de emergência
- Histórico de matrículas e pagamentos
- Sistema de comunicação

### Gestão de Cursos
- Criação e edição de cursos
- Definição de horários e salas
- Upload de materiais didáticos
- Controle de vagas

### Sistema Financeiro
- Geração automática de mensalidades
- Controle de status de pagamentos
- Relatórios financeiros
- Integração com gateway de pagamento
- Lembretes automáticos de vencimento

### Agendamento
- Visualização de calendário
- Controle de ocupação de salas
- Horários de professores e alunos

## ⚙️ Configurações Avançadas

### Email
Configure seu provedor de email nas variáveis de ambiente. Para Gmail:
1. Ative a verificação em 2 etapas
2. Gere uma senha de app específica
3. Use essa senha na variável `MAIL_PASSWORD`

### Gateway de Pagamento
O sistema suporta integração com gateways de pagamento:
- Configure as chaves de API nas variáveis de ambiente
- Ajuste os webhooks para confirmação automática de pagamentos

### Backup do Banco
Recomendamos backups regulares:
```bash
pg_dump escola_sol_maior > backup_$(date +%Y%m%d).sql
```

## 🔒 Segurança

- Senhas criptografadas com Werkzeug
- Proteção CSRF em todos os formulários
- Validação de uploads de arquivos
- Sessions seguras
- Logs de auditoria

## 📱 Responsividade

O sistema é totalmente responsivo e funciona em:
- Computadores desktop
- Tablets
- Smartphones

## 🆘 Suporte e Problemas

### Problemas Comuns

**Erro de conexão com banco:**
- Verifique se o PostgreSQL está rodando
- Confirme as credenciais no `.env`

**Emails não enviados:**
- Verifique as configurações SMTP
- Confirme se a senha de app está correta

**Erro 404 em arquivos:**
- Verifique se a pasta `uploads/` existe
- Confirme as permissões da pasta

### Logs do Sistema
Os logs ficam na pasta `logs/` e incluem:
- `audit_YYYYMMDD.log`: Logs de auditoria
- Logs do Flask no console

## 🔄 Atualizações

Para atualizar o sistema:
1. Faça backup do banco de dados
2. Baixe a nova versão
3. Execute as migrações se necessário
4. Reinicie o sistema

## 📞 Contato

Para suporte técnico ou dúvidas sobre o sistema, entre em contato com a equipe de desenvolvimento.

---

**Desenvolvido com ❤️ para facilitar a gestão de escolas de música**
