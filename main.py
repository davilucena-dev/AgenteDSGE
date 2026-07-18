#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║  main.py — AgenteDSGE                                      ║
║  Orquestrador principal de inicialização                   ║
║                                                            ║
║  Etapa 4 de 7: Ponto de entrada do sistema                 ║
║  Versão: 2.1 — Julho 2026 (+ Octave + Dynare)              ║
╚══════════════════════════════════════════════════════════════╝

Fluxo de Execução:
  1. Verificar se está no Google Colab
  2. Montar Google Drive + autenticar
  3. Instalar dependências (OpenCode, Python libs, tema, agente)
  4. Instalar skills (locais + externas)
  5. Lançar interface web (ttyd + wrapper + botão)

Uso (no Colab):
  from main import run
  run()
"""

import sys
import os
import time


# ══════════════════════════════════════════════════════════════
# CONFIGURAÇÕES
# ══════════════════════════════════════════════════════════════

REPO_URL = "https://github.com/gustavo-bbraga/AgenteDSGE.git"
DRIVE_FOLDER = "AgenteDSGE"
MOUNT_PATH = "/content/drive"
FOLDER_PATH = os.path.join(MOUNT_PATH, "My Drive", DRIVE_FOLDER)

# ── Mensagens temáticas exibidas durante cada etapa ──
JOKES = [
    "📈 Resolvendo estado estacionário...",
    "📐 Derivando condições de primeira ordem...",
    "🔧 Verificando Blanchard-Kahn...",
    "📊 Calibrando parâmetros da literatura...",
    "⚙️  Preparando estimação Bayesiana...",
    "📉 Linearizando em torno do steady-state...",
    "🎯 Verificando convergência MCMC...",
    "📋 Compilando relatório final...",
]

_joke_index = 0

def next_joke():
    global _joke_index
    joke = JOKES[_joke_index % len(JOKES)]
    _joke_index += 1
    return joke


# ══════════════════════════════════════════════════════════════
# UTILITÁRIOS
# ══════════════════════════════════════════════════════════════

def log(msg):
    print(f"  {msg}")

def log_ok(msg):
    print(f"  ✅ {msg}")

def log_warn(msg):
    print(f"  ⚠️  {msg}")

def log_fail(msg):
    print(f"  ❌ {msg}")

def section(title):
    """Desenha uma seção visual no terminal."""
    print(f"\n  ┌{'─'*50}┐")
    print(f"  │ {title}")
    print(f"  └{'─'*50}┘")

# ══════════════════════════════════════════════════════════════
# 1. VERIFICAÇÃO DE AMBIENTE
# ══════════════════════════════════════════════════════════════

def ensure_in_colab():
    """Verifica se está executando dentro do Google Colab."""
    try:
        import google.colab
        return True
    except ImportError:
        return False


# ══════════════════════════════════════════════════════════════
# 2. AUTENTICAÇÃO GOOGLE DRIVE
# ══════════════════════════════════════════════════════════════

def setup_auth():
    """
    Monta o Google Drive, autentica o usuário e retorna
    (folder_path, drive_url) para uso posterior.
    """
    section("🔐 Autenticação — Google Drive")

    FALLBACK_URL = "https://drive.google.com/drive/my-drive"
    url_direta = FALLBACK_URL

    try:
        from google.colab import drive, auth
        from googleapiclient.discovery import build
    except ImportError:
        log_warn("Não está no Colab. Pulando autenticação.")
        return "/tmp/agentedsge_work", FALLBACK_URL

    # 2.1 Montar Drive
    if not os.path.exists(os.path.join(MOUNT_PATH, "My Drive")):
        log("📂 Montando Google Drive...")
        try:
            drive.mount(MOUNT_PATH, force_remount=False)
            log_ok("Drive montado!")
        except Exception as e:
            log_fail(f"Erro ao montar: {e}")
            os.makedirs("/tmp/agentedsge_work", exist_ok=True)
            return "/tmp/agentedsge_work", FALLBACK_URL
    else:
        log_ok("Google Drive já está montado!")

    # 2.2 Autenticar para API do Drive
    log("🔑 Autenticando usuário para API do Drive...")
    try:
        auth.authenticate_user()
        log_ok("Autenticação concluída!")
    except Exception as e:
        log_warn(f"Aviso na autenticação: {e}")

    # 2.3 Criar pasta do projeto
    os.makedirs(FOLDER_PATH, exist_ok=True)
    os.chdir(FOLDER_PATH)
    log_ok(f"Pasta de trabalho: {FOLDER_PATH}")

    # 2.4 Obter URL direta da pasta
    try:
        service = build("drive", "v3")
        query = (
            f"name = '{DRIVE_FOLDER}' "
            "and mimeType = 'application/vnd.google-apps.folder' "
            "and trashed = false"
        )
        resultado = service.files().list(q=query, fields="files(id)").execute()
        arquivos = resultado.get("files", [])
        if arquivos:
            folder_id = arquivos[0]["id"]
            url_direta = f"https://drive.google.com/drive/folders/{folder_id}"
    except Exception:
        pass

    return FOLDER_PATH, url_direta


# ══════════════════════════════════════════════════════════════
# 3. TELA DE CARREGAMENTO
# ══════════════════════════════════════════════════════════════

def show_loading():
    """Exibe uma animação de carregamento inicial no Colab."""
    if not ensure_in_colab():
        log("⏳ Inicializando AgenteDSGE...")
        return

    from IPython.display import display, HTML
    display(HTML("""
    <style>
      @keyframes dsge-spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
      }
      @keyframes dsge-pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
      }
      @keyframes dsge-fadeIn {
        0% { opacity: 0; transform: translateY(10px); }
        100% { opacity: 1; transform: translateY(0); }
      }
      .dsge-loading {
        display: flex; flex-direction: column; align-items: center;
        justify-content: center; padding: 50px 20px;
        animation: dsge-fadeIn 0.6s ease-out;
      }
      .dsge-spinner {
        width: 48px; height: 48px;
        border: 3px solid rgba(74,140,247,0.12);
        border-top-color: #4a8cf7;
        border-radius: 50%;
        animation: dsge-spin 1s linear infinite;
        margin-bottom: 20px;
      }
      .dsge-loading-text {
        color: #4a8cf7; font-family: 'DM Mono', monospace;
        font-size: 14px; letter-spacing: 0.08em;
        animation: dsge-pulse 1.5s ease-in-out infinite;
      }
      .dsge-loading-sub {
        color: #7a84a0; font-family: 'DM Mono', monospace;
        font-size: 11px; margin-top: 8px;
        letter-spacing: 0.05em;
      }
    </style>
    <div class="dsge-loading">
      <div class="dsge-spinner"></div>
      <div class="dsge-loading-text">INICIALIZANDO AGENTEDSGE</div>
      <div class="dsge-loading-sub">Modelagem Macroeconômica · Protocolo 17 Etapas</div>
    </div>
    """))


# ══════════════════════════════════════════════════════════════
# 4. ORQUESTRADOR PRINCIPAL
# ══════════════════════════════════════════════════════════════

def run():
    """
    Ponto de entrada principal da AgenteDSGE.

    Fluxo completo:
      1. Loading screen
      2. Autenticação Google Drive
      3. Instalação de dependências (OpenCode + libs Python)
      4. Instalação de skills (locais + externas)
      5. Lançamento da interface web
    """
    start_time = time.time()

    # ── 4.0 Identidade ──
    print(f"")
    print(f"  ╔══════════════════════════════════════════════════╗")
    print(f"  ║     🔷 AGENTEDSGE  v2.1                        ║")
    print(f"  ║     Modelagem DSGE · Protocolo de 17 Etapas    ║")
    print(f"  ║     Octave + Dynare · Zero Alucinação          ║")
    print(f"  ╚══════════════════════════════════════════════════╝")
    print(f"")

    # ── 4.1 Loading ──
    show_loading()

    # ── 4.2 Autenticação ──
    print(f"\n  {next_joke()}")
    folder_path, drive_url = setup_auth()

    # ── 4.3 Dependências ──
    print(f"\n  {next_joke()}")
    from setup_dependencies import run_all as run_deps
    run_deps(drive_base_path=folder_path)

    # ── 4.4 Skills ──
    print(f"\n  {next_joke()}")
    from setup_skills import install_skills
    install_skills()

    # ── 4.5 Lançamento ──
    print(f"\n  {next_joke()}")
    from launch_app import launch, set_drive_info
    set_drive_info(folder_path, drive_url)

    print(f"\n  {next_joke()}")
    launch(total_phases=6)

    # ── 4.6 Tempo total ──
    elapsed = time.time() - start_time
    mins = int(elapsed // 60)
    secs = int(elapsed % 60)

    print(f"\n  ╔══════════════════════════════════════════════════╗")
    print(f"  ║   ✅ AGENTEDSGE INICIALIZADA                     ║")
    print(f"  ║   ⏱️  {mins}min {secs:02d}s                        ║")
    print(f"  ║   📁 {folder_path}              ║")
    print(f"  ╚══════════════════════════════════════════════════╝")
    print(f"")


# ══════════════════════════════════════════════════════════════
# EXECUÇÃO DIRETA
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    run()
