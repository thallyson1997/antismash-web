# antiSMASH Web Interface

Uma aplicação web em Flask para executar análises de **antiSMASH** (antibiotic & Secondary Metabolite Analysis SHell) de forma fácil e intuitiva, com acompanhamento de progresso em tempo real.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/flask-2.0+-green.svg)
![Docker](https://img.shields.io/badge/docker-required-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## 🔬 Sobre o antiSMASH

O [antiSMASH](https://antismash.secondarymetabolites.org/) é uma ferramenta líder para identificação, anotação e análise de clusters de genes de metabolitos secundários em genomas bacterianos e fúngicos. Esta aplicação web fornece uma interface amigável para executar análises antiSMASH localmente.

## ✨ Funcionalidades

- 📁 **Upload de arquivos FASTA/GenBank** - Suporte para múltiplos formatos
- 🐳 **Integração com Docker** - Execução isolada e segura do antiSMASH
- 📊 **Progresso em tempo real** - Acompanhe o andamento da análise com barra de progresso
- 🧬 **Visualização de proteínas** - Tabela interativa com dados das proteínas identificadas
- 💾 **Download de resultados** - Acesso completo aos arquivos de saída do antiSMASH
- 🌐 **Interface em português** - Interface totalmente localizada

## 🚀 Demonstração

### Fluxo da aplicação:
1. **Upload** → Envie seu arquivo FASTA/GBK
2. **Progresso** → Acompanhe a análise em tempo real
3. **Resultados** → Visualize as proteínas identificadas

### Interface de progresso:
```
Progresso da Análise antiSMASH
Run: run_20241018_143022
[████████████████████████████████████████] 85%
🔄 antiSMASH: Generating cluster overview...
```

## 🛠️ Instalação

### Pré-requisitos

1. **Python 3.8+**
2. **Docker Desktop** executando
3. **Imagem antiSMASH**:
   ```bash
   docker pull antismash/standalone:latest
   ```

### Configuração

1. **Clone o repositório**:
   ```bash
   git clone https://github.com/thallyson1997/antismash-web.git
   cd antismash-web
   ```

2. **Crie um ambiente virtual**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # ou
   source .venv/bin/activate  # Linux/Mac
   ```

3. **Instale as dependências**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Execute a aplicação**:
   ```bash
   python app.py
   ```

5. **Acesse**: http://localhost:5000

## 📋 Formatos de arquivo suportados

| Extensão | Descrição |
|----------|-----------|
| `.fasta`, `.fa`, `.fna` | Arquivos FASTA |
| `.gb`, `.gbk` | Arquivos GenBank |
| `.txt`, `.ffn`, `.fas` | Outros formatos de sequência |

## 🏗️ Arquitetura

```
antismash-web/
├── app.py              # Aplicação Flask principal
├── requirements.txt    # Dependências Python
├── templates/          # Templates HTML
│   ├── index.html      # Página de upload
│   ├── progress.html   # Página de progresso
│   └── results.html    # Página de resultados
├── static/
│   └── style.css       # Estilos CSS
├── uploads/            # Arquivos enviados (auto-criado)
└── runs/               # Resultados das análises (auto-criado)
```

### Fluxo de dados:
```
Upload → Docker antiSMASH → Parse GenBank → Visualização Web
```

## 🔧 Configuração avançada

### Variáveis de ambiente

| Variável | Descrição | Padrão |
|----------|-----------|---------|
| `FLASK_SECRET` | Chave secreta do Flask | `troque_esta_chave_em_producao` |

### Personalização do Docker

Para usar uma versão específica do antiSMASH, edite a variável `DOCKER_IMAGE` em `app.py`:

```python
DOCKER_IMAGE = "antismash/standalone:6.1.1"  # Versão específica
```

## 📊 Sistema de progresso

A aplicação monitora o progresso da análise antiSMASH através de:

- **Palavras-chave do log**: Detecta etapas específicas da análise
- **Atualizações em tempo real**: JavaScript faz polling da API de progresso
- **Estados de execução**: Setup → Running → Parsing → Completed/Error
- **Percentual estimado**: Baseado nas etapas identificadas

## 🧬 Dados extraídos

Para cada proteína identificada, a aplicação extrai:

- **Record ID**: Identificador da sequência
- **Gene/Locus**: Nome do gene ou locus tag
- **Product**: Descrição do produto proteico  
- **AA Length**: Comprimento em aminoácidos
- **Sequence**: Sequência de aminoácidos (primeiros 120 aa)
- **Source**: Arquivo GenBank de origem

## 🔍 API Endpoints

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/` | GET | Página inicial de upload |
| `/upload` | POST | Processa upload e inicia análise |
| `/progress/<run_id>/<run_name>` | GET | Página de progresso |
| `/api/progress/<run_id>` | GET | API JSON de progresso |
| `/results/<run_name>` | GET | Página de resultados |
| `/download_run/<run_name>/<filename>` | GET | Download de arquivos |

## 🛡️ Segurança

- ✅ Validação de tipos de arquivo
- ✅ Nomes de arquivo seguros (`secure_filename`)
- ✅ Isolamento via Docker
- ✅ Prefixos únicos para evitar conflitos
- ⚠️ **Nota**: Não há sistema de autenticação implementado

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Roadmap

- [ ] Sistema de autenticação
- [ ] Histórico de análises
- [ ] Análise de múltiplos arquivos
- [ ] Visualização gráfica dos clusters
- [ ] API REST completa
- [ ] Containerização da aplicação web

## 🐛 Solução de problemas

### Docker não encontrado
```bash
# Verifique se o Docker está executando
docker --version
docker ps
```

### Erro de permissão nos volumes
```bash
# No Windows, certifique-se que o drive está compartilhado
# Docker Desktop → Settings → Resources → File Sharing
```

### Análise trava no progresso
- Verifique os logs do Docker
- Confirme que a imagem antiSMASH está atualizada
- Verifique o formato do arquivo de entrada

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🙏 Agradecimentos

- [antiSMASH team](https://antismash.secondarymetabolites.org/) pela ferramenta incrível
- [Flask](https://flask.palletsprojects.com/) pelo framework web
- [BioPython](https://biopython.org/) pela manipulação de dados biológicos

## 📧 Contato

Thallyson Silva - [@thallyson1997](https://github.com/thallyson1997)

Link do projeto: [https://github.com/thallyson1997/antismash-web](https://github.com/thallyson1997/antismash-web)

---

⭐ **Se este projeto foi útil para você, considere dar uma estrela!**