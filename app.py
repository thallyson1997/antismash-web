#!/usr/bin/env python3
"""
Flask app: upload FASTA/GBK -> run antiSMASH via Docker -> parse .gbk -> show proteins.
Notas:
- Monta uploads folder em /input e runs folder em /output dentro do container.
- antiSMASH CLI na imagem antismash/standalone espera o arquivo como primeiro arg
  e um --output-dir (neste caso usamos /output/<run_name>).
- Requer Docker Desktop rodando e imagem antismash/standalone:latest disponível.
"""
import os
import uuid
import shutil
import subprocess
import threading
import time
import json
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, jsonify
from werkzeug.utils import secure_filename
from Bio import SeqIO

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "uploads"
RUNS_FOLDER = BASE_DIR / "runs"
ALLOWED_EXTENSIONS = {"fasta", "fa", "fna", "txt", "ffn", "fas", "gb", "gbk"}

DOCKER_IMAGE = "antismash/standalone:latest"

# Ensure folders exist
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
RUNS_FOLDER.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
app.secret_key = os.environ.get("FLASK_SECRET", "troque_esta_chave_em_producao")

# Sistema de tracking de progresso
progress_data = {}

def update_progress(run_id, step, message, percentage=None):
    """Atualiza o progresso de um run específico"""
    progress_data[run_id] = {
        'step': step,
        'message': message,
        'percentage': percentage,
        'timestamp': datetime.utcnow().isoformat()
    }

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def run_antismash_docker(saved_path: Path, run_name: str, run_id: str, genefinder: str = "prodigal"):
    """
    Run antiSMASH inside Docker with progress tracking.
    Mount uploads -> /input and runs -> /output.
    Command executed:
      docker run --rm -v "<uploads>:/input" -v "<runs>:/output" antismash/standalone:latest <input_filename> --genefinding-tool prodigal --output-dir /output/<run_name>
    Returns host_run_dir (Path)
    """
    update_progress(run_id, "setup", "Preparando ambiente Docker...", 5)
    
    input_parent = str(UPLOAD_FOLDER.resolve())
    runs_parent = str(RUNS_FOLDER.resolve())
    input_filename = saved_path.name

    host_run_dir = RUNS_FOLDER / run_name
    host_run_dir.mkdir(parents=True, exist_ok=True)

    docker_cmd = [
        "docker", "run", "--rm",
        "-v", f"{input_parent}:/input",
        "-v", f"{runs_parent}:/output",
        DOCKER_IMAGE,
        input_filename,
        "--genefinding-tool", genefinder,
        "--output-dir", f"/output/{run_name}"
    ]

    update_progress(run_id, "running", "Executando antiSMASH...", 10)
    
    # Palavras-chave para detectar progresso no log
    progress_keywords = {
        "Reading sequence": 15,
        "Downloading": 20,
        "Finding genes": 30,
        "Running gene": 40,
        "Detecting": 50,
        "Predicting": 60,
        "Creating": 70,
        "Generating": 80,
        "Writing": 90
    }
    
    # Run and stream output with progress tracking
    proc = subprocess.Popen(docker_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    for line in proc.stdout:
        line_clean = line.rstrip()
        app.logger.info(line_clean)
        
        # Detectar progresso baseado em palavras-chave
        for keyword, percentage in progress_keywords.items():
            if keyword.lower() in line_clean.lower():
                update_progress(run_id, "running", f"antiSMASH: {line_clean[:100]}...", percentage)
                break
    
    proc.wait()
    
    if proc.returncode != 0:
        update_progress(run_id, "error", f"antiSMASH falhou com código {proc.returncode}", None)
        raise RuntimeError(f"antiSMASH failed with exit code {proc.returncode}")
    
    update_progress(run_id, "parsing", "Processando resultados...", 95)
    return host_run_dir

def parse_gbk_for_proteins(run_dir: Path):
    """
    Parse all .gbk files under run_dir and return list of protein dicts.
    Prioritizes functional annotations from region files over main sequence file.
    Fields: record_id, gene, product, protein_seq, aa_length, location, source_file
    """
    proteins = []
    proteins_by_gene = {}  # Para agrupar por gene e priorizar anotações
    
    # Primeiro, processar arquivo principal para obter todas as proteínas
    main_files = [gbk for gbk in run_dir.rglob("*.gbk") if not gbk.name.startswith("NC_") or "region" not in gbk.name]
    region_files = [gbk for gbk in run_dir.rglob("*.gbk") if gbk.name.startswith("NC_") and "region" in gbk.name]
    
    app.logger.info(f"Found {len(main_files)} main files and {len(region_files)} region files")
    
    def extract_functional_annotation(qualifiers):
        """Extrai anotação funcional de vários campos possíveis"""
        # Prioridade: product > gene_functions > gene_kind
        product = qualifiers.get("product", [""])[0]
        if product.strip():
            return product.strip()
        
        # Extrair de gene_functions (comum no antiSMASH)
        gene_functions = qualifiers.get("gene_functions", [])
        if gene_functions:
            # Extrair a parte mais informativa
            for func in gene_functions:
                if "biosynthetic" in func.lower():
                    # Extrair o tipo de função
                    if ":" in func:
                        func_type = func.split(":")[-1].strip()
                        if func_type:
                            return func_type
                    elif ")" in func:
                        func_type = func.split(")")[-1].strip()
                        if func_type:
                            return func_type
        
        # Extrair de gene_kind
        gene_kind = qualifiers.get("gene_kind", [""])[0]
        if gene_kind.strip():
            return gene_kind.strip()
        
        # Extrair de sec_met_domain
        sec_met_domain = qualifiers.get("sec_met_domain", [])
        if sec_met_domain:
            for domain in sec_met_domain:
                if "(" in domain:
                    domain_name = domain.split("(")[0].strip()
                    if domain_name:
                        return f"domain: {domain_name}"
        
        return ""
    
    # Processar arquivos principais primeiro
    for gbk in sorted(main_files):
        try:
            for rec in SeqIO.parse(str(gbk), "genbank"):
                for feat in rec.features:
                    if feat.type.lower() == "cds":
                        qualifiers = feat.qualifiers
                        prot_seq = qualifiers.get("translation", [""])[0]
                        gene = qualifiers.get("gene", qualifiers.get("locus_tag", [""]))[0]
                        product = extract_functional_annotation(qualifiers)
                        location = str(feat.location)
                        aa_len = len(prot_seq)
                        
                        # Criar chave única baseada em gene e localização
                        key = f"{gene}_{location}"
                        
                        protein_data = {
                            "record_id": rec.id,
                            "gene": gene,
                            "product": product,
                            "protein_seq": prot_seq,
                            "aa_length": aa_len,
                            "location": location,
                            "source_file": gbk.name,
                            "is_from_region": False
                        }
                        proteins_by_gene[key] = protein_data
        except Exception as e:
            app.logger.error(f"Error parsing main file {gbk}: {e}")
    
    # Processar arquivos region para sobrescrever com anotações funcionais
    for gbk in sorted(region_files):
        try:
            for rec in SeqIO.parse(str(gbk), "genbank"):
                for feat in rec.features:
                    if feat.type.lower() == "cds":
                        qualifiers = feat.qualifiers
                        prot_seq = qualifiers.get("translation", [""])[0]
                        gene = qualifiers.get("gene", qualifiers.get("locus_tag", [""]))[0]
                        product = extract_functional_annotation(qualifiers)
                        location = str(feat.location)
                        aa_len = len(prot_seq)
                        
                        # Criar chave única baseada em gene e localização
                        key = f"{gene}_{location}"
                        
                        # Se já existe, atualizar com informações do region (prioritárias)
                        if key in proteins_by_gene:
                            # Priorizar anotação funcional do region se estiver preenchida
                            if product.strip():
                                proteins_by_gene[key]["product"] = product
                            proteins_by_gene[key]["source_file"] = f"{proteins_by_gene[key]['source_file']} + {gbk.name}"
                            proteins_by_gene[key]["is_from_region"] = True
                        else:
                            # Proteína nova encontrada apenas no region
                            protein_data = {
                                "record_id": rec.id,
                                "gene": gene,
                                "product": product,
                                "protein_seq": prot_seq,
                                "aa_length": aa_len,
                                "location": location,
                                "source_file": gbk.name,
                                "is_from_region": True
                            }
                            proteins_by_gene[key] = protein_data
        except Exception as e:
            app.logger.error(f"Error parsing region file {gbk}: {e}")
    
    # Converter dicionário de volta para lista, removendo campo auxiliar
    for protein_data in proteins_by_gene.values():
        protein_data.pop("is_from_region", None)  # Remove campo auxiliar
        proteins.append(protein_data)
    
    app.logger.info(f"Parsed {len(proteins)} total proteins")
    
    return proteins

def parse_clusters_from_regions(run_dir: Path):
    """
    Parse region files to extract cluster information.
    Returns list of cluster dictionaries with metadata and genes.
    """
    clusters = []
    region_files = [gbk for gbk in run_dir.rglob("*.gbk") if gbk.name.startswith("NC_") and "region" in gbk.name]
    
    app.logger.info(f"Parsing {len(region_files)} region files for clusters")
    
    for gbk in sorted(region_files):
        try:
            for rec in SeqIO.parse(str(gbk), "genbank"):
                cluster_info = {
                    "region_name": gbk.stem,  # NC_003888.3.region001
                    "region_number": gbk.stem.split(".")[-1],  # region001
                    "record_id": rec.id,
                    "sequence_length": len(rec.seq),
                    "products": [],
                    "cluster_type": "unknown",
                    "genes": [],
                    "location_start": None,
                    "location_end": None,
                    "source_file": gbk.name
                }
                
                # Extrair informações das features
                for feat in rec.features:
                    if feat.type.lower() == "region":
                        # Informações do cluster principal
                        qualifiers = feat.qualifiers
                        products = qualifiers.get("product", [])
                        if products:
                            cluster_info["products"] = products
                            cluster_info["cluster_type"] = " + ".join(products)
                        
                        # Localização do cluster
                        location = str(feat.location)
                        if "[" in location and ":" in location:
                            try:
                                loc_clean = location.replace("[", "").replace("]", "").replace("(+)", "").replace("(-)", "")
                                start, end = loc_clean.split(":")
                                cluster_info["location_start"] = int(start)
                                cluster_info["location_end"] = int(end)
                            except:
                                pass
                    
                    elif feat.type.lower() == "cds":
                        # Informações dos genes do cluster
                        qualifiers = feat.qualifiers
                        gene = qualifiers.get("gene", qualifiers.get("locus_tag", [""]))[0]
                        product = qualifiers.get("product", [""])[0]
                        gene_functions = qualifiers.get("gene_functions", [])
                        gene_kind = qualifiers.get("gene_kind", [""])[0]
                        sec_met_domain = qualifiers.get("sec_met_domain", [])
                        
                        # Extrair função mais específica
                        if not product and gene_functions:
                            for func in gene_functions:
                                if ":" in func:
                                    product = func.split(":")[-1].strip()
                                    break
                        
                        if not product and gene_kind:
                            product = gene_kind
                        
                        gene_info = {
                            "gene": gene,
                            "product": product,
                            "location": str(feat.location),
                            "gene_functions": gene_functions,
                            "sec_met_domain": sec_met_domain,
                            "gene_kind": gene_kind
                        }
                        cluster_info["genes"].append(gene_info)
                
                # Adicionar informações calculadas
                cluster_info["gene_count"] = len(cluster_info["genes"])
                cluster_info["size_kb"] = round(cluster_info["sequence_length"] / 1000, 2)
                
                # Classificar genes por importância
                biosynthetic_genes = [g for g in cluster_info["genes"] if g.get("gene_kind") == "biosynthetic"]
                regulatory_genes = [g for g in cluster_info["genes"] if "regulatory" in g.get("product", "").lower()]
                transport_genes = [g for g in cluster_info["genes"] if "transport" in g.get("product", "").lower()]
                
                cluster_info["biosynthetic_genes"] = len(biosynthetic_genes)
                cluster_info["regulatory_genes"] = len(regulatory_genes)
                cluster_info["transport_genes"] = len(transport_genes)
                
                clusters.append(cluster_info)
                break  # Só o primeiro record de cada arquivo
                
        except Exception as e:
            app.logger.error(f"Error parsing cluster file {gbk}: {e}")
    
    app.logger.info(f"Parsed {len(clusters)} clusters")
    return clusters

@app.route("/")
def index():
    return render_template("index.html")

def run_antismash_background(saved_path, run_name, run_id):
    """Executa antiSMASH em background thread"""
    try:
        run_dir = run_antismash_docker(saved_path, run_name, run_id)
        proteins = parse_gbk_for_proteins(run_dir)
        clusters = parse_clusters_from_regions(run_dir)
        
        # Salvar resultados
        results_file = RUNS_FOLDER / run_name / "results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                'proteins': proteins,
                'clusters': clusters,
                'run_name': run_name,
                'completed_at': datetime.utcnow().isoformat()
            }, f, ensure_ascii=False, indent=2)
        
        update_progress(run_id, "completed", "Análise concluída!", 100)
        
    except Exception as e:
        app.logger.exception("antiSMASH execution failed")
        update_progress(run_id, "error", f"Erro: {str(e)}", None)

@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        flash("Nenhum arquivo enviado.")
        return redirect(url_for("index"))
    file = request.files["file"]
    if file.filename == "":
        flash("Nome de arquivo vazio.")
        return redirect(url_for("index"))
    if not allowed_file(file.filename):
        flash("Tipo de arquivo não permitido. Envie FASTA/GBK.")
        return redirect(url_for("index"))

    filename = secure_filename(file.filename)
    unique_prefix = datetime.utcnow().strftime("%Y%m%d%H%M%S") + "_" + uuid.uuid4().hex[:6]
    saved_name = f"{unique_prefix}_{filename}"
    saved_path = UPLOAD_FOLDER / saved_name
    file.save(str(saved_path))

    run_name = "run_" + datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    run_id = uuid.uuid4().hex
    
    # Iniciar processamento em background
    update_progress(run_id, "starting", "Iniciando processamento...", 0)
    thread = threading.Thread(target=run_antismash_background, args=(saved_path, run_name, run_id))
    thread.daemon = True
    thread.start()
    
    # Redirecionar para página de progresso
    return redirect(url_for("progress", run_id=run_id, run_name=run_name))

@app.route("/progress/<run_id>/<run_name>")
def progress(run_id, run_name):
    """Página de progresso com atualizações em tempo real"""
    return render_template("progress.html", run_id=run_id, run_name=run_name)

@app.route("/api/progress/<run_id>")
def get_progress(run_id):
    """API para obter progresso atual"""
    if run_id in progress_data:
        return jsonify(progress_data[run_id])
    return jsonify({"step": "unknown", "message": "Run não encontrado", "percentage": None})

@app.route("/results/<run_name>")
def results(run_name):
    """Página de resultados (redirecionamento da página de progresso)"""
    results_file = RUNS_FOLDER / run_name / "results.json"
    if not results_file.exists():
        flash("Resultados não encontrados.")
        return redirect(url_for("index"))
    
    with open(results_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Se não tem clusters (arquivos antigos), parsear agora
    clusters = data.get('clusters', [])
    if not clusters:
        run_dir = RUNS_FOLDER / run_name
        if run_dir.exists():
            clusters = parse_clusters_from_regions(run_dir)
    
    return render_template("results.html", 
                         proteins=data['proteins'], 
                         clusters=clusters,
                         run_name=run_name)

@app.route("/download_run/<run_name>/<path:filename>")
def download_run_file(run_name, filename):
    target_dir = RUNS_FOLDER / run_name
    if not target_dir.exists():
        return "Run não encontrado", 404
    return send_from_directory(str(target_dir), filename, as_attachment=True)

if __name__ == "__main__":
    # Desenvolvimento: host 0.0.0.0 para testar de outros hosts se necessário
    app.run(host="0.0.0.0", port=5000, debug=True)