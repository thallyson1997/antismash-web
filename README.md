# antiSMASH Web Interface

Uma aplicação web moderna em Flask para executar análises de **antiSMASH** (antibiotic & Secondary Metabolite Analysis SHell) com interface intuitiva, acompanhamento de progresso em tempo real e visualização avançada de clusters de metabolitos secundários.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/flask-2.0+-green.svg)
![Docker](https://img.shields.io/badge/docker-required-blue.svg)
![BioPython](https://img.shields.io/badge/biopython-1.79+-green.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## 🔬 Sobre o antiSMASH

O [antiSMASH](https://antismash.secondarymetabolites.org/) é uma ferramenta mundialmente reconhecida para identificação, anotação e análise de clusters de genes de metabolitos secundários em genomas bacterianos e fúngicos. Esta aplicação web fornece uma interface amigável e moderna para executar análises antiSMASH localmente, com funcionalidades avançadas de visualização.

## ✨ Funcionalidades Principais

### 🚀 **Análise Avançada**
- 📁 **Upload de arquivos FASTA/GenBank** - Suporte para múltiplos formatos
- 🐳 **Integração com Docker** - Execução isolada e segura do antiSMASH
- 📊 **Progresso em tempo real** - Acompanhe o andamento com barra de progresso detalhada
- 🧬 **Anotações funcionais inteligentes** - Extração aprimorada de informações dos arquivos region

### 📋 **Interface com Abas**
- **Aba Proteínas** - Visualização completa de todas as proteínas identificadas
- **Aba Clusters** - Cards visuais dos clusters de metabolitos secundários
- 📈 **Estatísticas dinâmicas** - Resumos automáticos dos resultados
- 🎨 **Design responsivo** - Interface moderna e intuitiva

### 🏭 **Visualização de Clusters**
- 🧬 **Cards informativos** para cada cluster identificado
- 📍 **Localização genômica** precisa (posições em bp)
- � **Tipos de clusters** (PKS, NRPS, Terpenos, Lantipeptídeos, etc.)
- 📊 **Estatísticas detalhadas** (genes biossintéticos, regulatórios, transportadores)
- 🧾 **Lista de genes** de cada cluster com suas funções

### 💾 **Recursos Avançados**
- **Download completo** - Acesso a todos os arquivos de saída do antiSMASH
- **Compatibilidade total** - Funciona com runs novos e existentes
- 🌐 **Interface em português** - Totalmente localizada
- 🔄 **Parsing inteligente** - Processa arquivos principais e region automaticamente

## 🚀 Demonstração

### Fluxo da aplicação aprimorado:
1. **📤 Upload** → Envie seu arquivo FASTA/GBK
2. **⏳ Progresso** → Acompanhe a análise em tempo real com detalhes
3. **🧬 Resultados - Aba Proteínas** → Visualize todas as proteínas com anotações funcionais
4. **🏭 Resultados - Aba Clusters** → Explore clusters de metabolitos secundários

### Interface de progresso em tempo real:
```
Progresso da Análise antiSMASH
Run: run_20251019_143022
[████████████████████████████████████████] 85%
🔄 antiSMASH: Generating cluster overview...

Status: Processando resultados... (95%)
```

### Exemplo de resultados:
```
📊 Resumo - Aba Proteínas:
• 8,633 proteínas totais
• 880 com anotação funcional
• 7,753 hipotéticas

🏭 Resumo - Aba Clusters:
• 29 clusters identificados
• Tipos: PKS, NRPS, Terpenos, Lantipeptídeos
• 450+ genes nos clusters
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

### Fluxo de dados aprimorado:
```
Upload → Docker antiSMASH → Parse Inteligente → Abas Interativas
  ↓           ↓                    ↓                ↓
FASTA/GBK → Análise → Arquivos principais + → Proteínas + Clusters
                      arquivos region
```

### Arquivos processados:
- **Arquivo principal** (ex: `sequence.gbk`) → Todas as proteínas
- **Arquivos region** (ex: `NC_*.regionXXX.gbk`) → Clusters específicos  
- **Priorização inteligente** → Anotações funcionais dos regions

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

### 🔬 **Proteínas** (Aba 1):
Para cada proteína identificada, a aplicação extrai:

- **Record ID**: Identificador da sequência genômica
- **Gene/Locus**: Nome do gene ou locus tag  
- **Product**: Anotação funcional inteligente (gene_functions, product, sec_met_domain)
- **AA Length**: Comprimento em aminoácidos
- **Sequence**: Sequência completa de aminoácidos (preview de 120 aa)
- **Location**: Posição no genoma (início:fim, orientação)
- **Source**: Arquivo GenBank de origem

### 🏭 **Clusters de Metabolitos Secundários** (Aba 2):
Para cada cluster identificado, a aplicação extrai:

- **Region Name**: Identificador do cluster (ex: NC_003888.3.region001)
- **Cluster Type**: Tipo de metabolito (T1PKS, NRPS, terpene, lanthipeptide, etc.)
- **Location**: Posição precisa no genoma (início - fim em bp)
- **Size**: Tamanho do cluster em kilobases (kb)
- **Gene Count**: Número total de genes no cluster
- **Gene Classification**: 
  - Genes biossintéticos (enzimas principais)
  - Genes regulatórios (controle de expressão)  
  - Genes de transporte (exportação/importação)
- **Detailed Gene List**: Lista completa com função de cada gene

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

### ✅ **Implementado**
- [x] ✨ **Interface com abas** (Proteínas + Clusters)
- [x] 🧬 **Anotações funcionais aprimoradas** (gene_functions, sec_met_domain)
- [x] 🏭 **Visualização de clusters** com cards informativos
- [x] 📊 **Estatísticas dinâmicas** em tempo real
- [x] 🔄 **Parsing inteligente** de arquivos region
- [x] 📱 **Design responsivo** moderno

### 🚧 **Em desenvolvimento**
- [ ] 📈 **Visualização gráfica** dos clusters (mapa genômico)
- [ ] 🔍 **Filtros avançados** por tipo de cluster/função
- [ ] 📋 **Exportação de dados** (CSV, Excel)
- [ ] 🔗 **Links externos** (UniProt, NCBI, PDB)

### 🎯 **Próximas funcionalidades**
- [ ] 👤 **Sistema de autenticação** e usuários
- [ ] 📚 **Histórico de análises** persistente  
- [ ] 📦 **Análise de múltiplos arquivos** em lote
- [ ] 🌐 **API REST completa** para integração
- [ ] 🐳 **Containerização** da aplicação web
- [ ] ☁️ **Deploy em nuvem** (AWS, Azure, GCP)

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

## 🎓 **Casos de uso acadêmicos**

### 🔬 **Pesquisa em Microbiologia**
- Descoberta de novos antibióticos em *Streptomyces*
- Análise de diversidade de metabolitos secundários  
- Estudos de evolução de clusters biossintéticos

### 💊 **Biotecnologia Farmacêutica**
- Prospecção de compostos bioativos
- Engenharia de vias metabólicas
- Otimização de produção de antibióticos

### 📚 **Educação**
- Ensino de bioinformática aplicada
- Aulas práticas de genômica bacteriana
- Workshops de descoberta de fármacos

## 🏆 **Diferenciais técnicos**

- ⚡ **Performance otimizada** - Parsing paralelo de múltiplos arquivos
- 🧠 **Inteligência na extração** - Priorização automática de anotações funcionais
- 🎨 **UX moderna** - Interface intuitiva com abas e cards responsivos
- 🔄 **Compatibilidade total** - Funciona com runs antigos e novos
- 🌐 **Totalmente em português** - Primeira interface web antiSMASH em PT-BR

## 🙏 Agradecimentos

- [antiSMASH team](https://antismash.secondarymetabolites.org/) pela ferramenta científica excepcional
- [Flask](https://flask.palletsprojects.com/) pelo framework web elegante e poderoso
- [BioPython](https://biopython.org/) pela biblioteca robusta de bioinformática
- Comunidade científica brasileira pelo feedback e sugestões

## 📧 Contato

**Thallyson Silva** - [@thallyson1997](https://github.com/thallyson1997)  
🔬 Desenvolvedor & Pesquisador em Bioinformática

**Link do projeto**: [https://github.com/thallyson1997/antismash-web](https://github.com/thallyson1997/antismash-web)

---

⭐ **Se este projeto foi útil para sua pesquisa, considere dar uma estrela e citar em suas publicações!** ⭐