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
    Fields: record_id, gene, product, protein_seq, aa_length, location, source_file
    """
    proteins = []
    for gbk in sorted(run_dir.rglob("*.gbk")):
        try:
            for rec in SeqIO.parse(str(gbk), "genbank"):
                for feat in rec.features:
                    if feat.type.lower() == "cds":
                        qualifiers = feat.qualifiers
                        prot_seq = qualifiers.get("translation", [""])[0]
                        gene = qualifiers.get("gene", qualifiers.get("locus_tag", [""]))[0]
                        product = qualifiers.get("product", [""])[0]
                        location = str(feat.location)
                        aa_len = len(prot_seq)
                        proteins.append({
                            "record_id": rec.id,
                            "gene": gene,
                            "product": product,
                            "protein_seq": prot_seq,
                            "aa_length": aa_len,
                            "location": location,
                            "source_file": gbk.name
                        })
        except Exception as e:
            app.logger.error(f"Error parsing {gbk}: {e}")
    return proteins

@app.route("/")
def index():
    return render_template("index.html")

def run_antismash_background(saved_path, run_name, run_id):
    """Executa antiSMASH em background thread"""
    try:
        run_dir = run_antismash_docker(saved_path, run_name, run_id)
        proteins = parse_gbk_for_proteins(run_dir)
        
        # Salvar resultados
        results_file = RUNS_FOLDER / run_name / "results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                'proteins': proteins,
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
    
    return render_template("results.html", proteins=data['proteins'], run_name=run_name)

@app.route("/download_run/<run_name>/<path:filename>")
def download_run_file(run_name, filename):
    target_dir = RUNS_FOLDER / run_name
    if not target_dir.exists():
        return "Run não encontrado", 404
    return send_from_directory(str(target_dir), filename, as_attachment=True)

if __name__ == "__main__":
    # Desenvolvimento: host 0.0.0.0 para testar de outros hosts se necessário
    app.run(host="0.0.0.0", port=5000, debug=True)