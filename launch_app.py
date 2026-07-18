#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║  launch_app.py — AgenteDSGE                                ║
║  Interface de lançamento com loading animado + botão       ║
║                                                            ║
║  Etapa 3 de 7: Startup visual do agente                    ║
║  Versão: 2.1 — Julho 2026 (+ Octave + Dynare)              ║
╚══════════════════════════════════════════════════════════════╝

Responsabilidades:
  1. Mostrar loading animado para cada fase de inicialização
  2. Barra de progresso para instalação de skills externas
  3. Botão elegante para abrir o chatbot em nova guia
"""

import os
import subprocess
import time
import threading
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

try:
    from google.colab import output
    from IPython.display import display, HTML
    IN_COLAB = True
except ImportError:
    IN_COLAB = False
    output = None
    display = None
    HTML = None


# ══════════════════════════════════════════════════════════════
# CONSTANTES
# ══════════════════════════════════════════════════════════════

TERMINAL_PORT = 8000
WRAPPER_PORT  = 8001
WRAPPER_DIR   = "/tmp/agentedsge-wrapper"

_opencode_bin = None
_env          = None


# ══════════════════════════════════════════════════════════════
# 1. LOADING ANIMADO — TELA DE INICIALIZAÇÃO
# ══════════════════════════════════════════════════════════════

def show_splash():
    """
    Exibe a tela de abertura da AgenteDSGE com identidade visual.
    Mostra o logo, a versão e uma mensagem de boas-vindas.
    """
    if not IN_COLAB or not display or not HTML:
        print("  ╔════════════════════════════════════════╗")
        print("  ║       🔷 AGENTEDSGE v2.1              ║")
        print("  ║   Modelagem DSGE · 17 Etapas          ║")
        print("  ║   Octave + Dynare · Zero Alucinação   ║")
        print("  ╚════════════════════════════════════════╝")
        return

    display(HTML("""
    <style>
      @keyframes fadeSlideIn {
        0%   { opacity: 0; transform: translateY(16px); }
        100% { opacity: 1; transform: translateY(0); }
      }
      @keyframes shimmer {
        0%   { background-position: -200% 0; }
        100% { background-position: 200% 0; }
      }
      @keyframes breathe {
        0%, 100% { opacity: 0.6; }
        50%      { opacity: 1; }
      }
      .dsge-splash {
        display: flex; flex-direction: column; align-items: center;
        padding: 40px 20px 20px 20px;
        animation: fadeSlideIn 0.8s ease-out;
        font-family: 'DM Mono', 'Courier New', monospace;
      }
      .dsge-splash-brand {
        display: flex; align-items: baseline; gap: 3px;
        margin-bottom: 6px;
      }
      .dsge-splash-brand .brand-agent {
        font-size: 28px; font-weight: 800;
        background: linear-gradient(135deg, #4a8cf7, #a78bfa, #56d8cc);
        background-size: 200% 200%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: shimmer 3s ease-in-out infinite;
        letter-spacing: -0.5px;
        font-family: 'Syne', sans-serif;
      }
      .dsge-splash-brand .brand-dsge {
        font-size: 28px; font-weight: 800;
        color: #e0e4f0;
        letter-spacing: -0.5px;
        font-family: 'Syne', sans-serif;
      }
      .dsge-splash-version {
        font-size: 11px; color: #4a8cf7;
        background: rgba(74,140,247,0.12);
        border: 1px solid rgba(74,140,247,0.2);
        padding: 2px 10px; border-radius: 4px;
        letter-spacing: 0.08em; margin-bottom: 8px;
      }
      .dsge-splash-sub {
        font-size: 13px; color: #7a84a0;
        letter-spacing: 0.05em; text-align: center;
        line-height: 1.5;
      }
      .dsge-splash-sub span {
        display: inline-block;
        animation: breathe 2.4s ease-in-out infinite;
      }
    </style>
    <div class="dsge-splash">
      <div class="dsge-splash-brand">
        <span class="brand-agent">Agente</span><span class="brand-dsge">DSGE</span>
      </div>
      <div class="dsge-splash-version">v2.1 · Protocolo 17 Etapas · Octave+Dynare</div>
      <div class="dsge-splash-sub">
        <span>Modelagem Macroeconômica · Zero Alucinação</span>
      </div>
    </div>
    """))


def show_loading_phase(phase_name, phase_num, total_phases, sub_message=""):
    """
    Exibe uma barra de carregamento para cada fase da inicialização.

    Args:
        phase_name: Nome da fase (ex: "Instalação de Dependências")
        phase_num: Número atual (1-indexed)
        total_phases: Total de fases
        sub_message: Mensagem secundária (opcional)
    """
    icons = {
        "dependências":    "📦",
        "skills":          "🔧",
        "modelos":         "📐",
        "calibração":      "📊",
        "lançamento":      "🚀",
        "default":         "⚙️",
    }
    icon = icons.get("default")
    for key, val in icons.items():
        if key in phase_name.lower():
            icon = val
            break

    bar_len = 28
    filled = phase_num - 1
    empty = total_phases - 1
    bar = "━" * filled + "╸" + "─" * max(0, empty - 1) if filled > 0 else "╸" + "─" * max(0, total_phases - 1)

    print(f"\n    {icon}  {bar}  {phase_num}/{total_phases}")
    print(f"       ── {phase_name}")
    if sub_message:
        print(f"       {sub_message}")


def show_phase_complete(phase_name):
    """Marca uma fase como concluída."""
    print(f"       ✅ {phase_name} — concluída")


def show_skills_progress(skills_list):
    """
    Exibe uma barra de progresso específica para instalação de skills externas.
    skills_list: lista de nomes das skills a instalar.
    """
    if not skills_list:
        return

    total = len(skills_list)
    print(f"\n    🔧  ─────────────────────────────────────")
    print(f"       Skills Externas ({total} para instalar)")
    print(f"       ─────────────────────────────────────")

    for i, skill_name in enumerate(skills_list, 1):
        # Mostra a skill com animação de progresso
        dots = "." * ((i % 4) + 1)
        pct = int((i / total) * 100)
        bar_len = 20
        filled = int((i / total) * bar_len)
        bar = "█" * filled + "░" * (bar_len - filled)

        print(f"       [{bar}] {pct}%  {skill_name}")
        time.sleep(0.15)  # Efeito visual de progresso

    print(f"       ─────────────────────────────────────")
    print(f"       ✅ {total} skills instaladas")


# ══════════════════════════════════════════════════════════════
# 2. INFRAESTRUTURA — TTYD + OPENCODE
# ══════════════════════════════════════════════════════════════

def resolve_opencode():
    """Localiza o binário do OpenCode no sistema."""
    global _opencode_bin, _env

    if "OPENCODE_BIN" in os.environ and os.path.isfile(os.environ["OPENCODE_BIN"]):
        _opencode_bin = os.environ["OPENCODE_BIN"]
    else:
        candidates = [
            os.path.expanduser("~/.local/bin/opencode"),
            os.path.expanduser("~/bin/opencode"),
            "/root/.local/bin/opencode",
            "/root/bin/opencode",
            "/usr/local/bin/opencode",
            "/usr/bin/opencode",
        ]
        found = next((p for p in candidates if os.path.isfile(p)), None)
        if found is None:
            result = subprocess.run(
                ["find", "/root", "/home", "/usr/local", "-name", "opencode", "-type", "f", "-maxdepth", "4"],
                capture_output=True, text=True
            )
            hits = [l.strip() for l in result.stdout.splitlines() if l.strip()]
            found = hits[0] if hits else "opencode"
        _opencode_bin = found

    extra_path = (
        os.path.dirname(_opencode_bin)
        if os.path.isfile(_opencode_bin)
        else os.path.expanduser("~/.local/bin")
    )

    _env = {
        **os.environ,
        "OPENCODE_EXPERIMENTAL_DISABLE_COPY_ON_SELECT": "1",
        "PATH": os.environ.get("PATH", "") + ":" + extra_path,
    }

    return _opencode_bin, _env


def install_ttyd():
    """Instala o ttyd (terminal web)."""
    subprocess.run(
        "apt-get update -qq && apt-get install -y -qq ttyd 2>&1",
        shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )


def kill_previous():
    """Mata processos anteriores do ttyd."""
    subprocess.run("pkill -9 -f ttyd 2>/dev/null || true", shell=True)
    subprocess.run(f"pkill -9 -f 'python3.*{WRAPPER_PORT}' 2>/dev/null || true", shell=True)
    time.sleep(0.5)


def start_ttyd():
    """Inicia o terminal web com OpenCode."""
    opencode_bin, env = resolve_opencode()
    subprocess.Popen(
        ["ttyd", "-p", str(TERMINAL_PORT), "bash", "-i", "-c",
         f"{opencode_bin}; exec bash"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
    )
    time.sleep(2)


# ══════════════════════════════════════════════════════════════
# 3. BOTÃO DE LANÇAMENTO — ABRIR O CHATBOT
# ══════════════════════════════════════════════════════════════

def show_launch_button(banner_url):
    """
    Exibe o botão principal para abrir o AgenteDSGE em nova guia.
    Design refinado com gradiente, glow pulsante e seta animada.
    """
    if not IN_COLAB or not display or not HTML:
        print(f"\n  🚀 Acesse a AgenteDSGE: {banner_url}")
        return

    display(HTML(f"""
    <style>
      @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@700;800&display=swap');

      @keyframes dsge-glow {{
        0%, 100% {{
          box-shadow:
            0 0 24px rgba(74,140,247,0.25),
            0 0 60px rgba(74,140,247,0.10),
            0 8px 32px rgba(0,0,0,0.35);
        }}
        50% {{
          box-shadow:
            0 0 40px rgba(74,140,247,0.45),
            0 0 80px rgba(167,139,250,0.15),
            0 12px 40px rgba(0,0,0,0.40);
        }}
      }}

      @keyframes dsge-float {{
        0%, 100% {{ transform: translateY(0); }}
        50%      {{ transform: translateY(-3px); }}
      }}

      @keyframes dsge-arrow {{
        0%   {{ transform: translateX(0) scale(1); }}
        50%  {{ transform: translateX(6px) scale(1.1); }}
        100% {{ transform: translateX(0) scale(1); }}
      }}

      @keyframes dsge-shine {{
        0%   {{ left: -150%; }}
        100% {{ left: 150%; }}
      }}

      @keyframes dsge-fadeIn {{
        0%   {{ opacity: 0; transform: translateY(24px) scale(0.96); }}
        100% {{ opacity: 1; transform: translateY(0) scale(1); }}
      }}

      .dsge-btn-container {{
        display: flex; justify-content: center; align-items: center;
        padding: 40px 20px 28px 20px;
        animation: dsge-fadeIn 0.9s cubic-bezier(0.16, 1, 0.3, 1);
      }}

      .dsge-btn {{
        position: relative;
        display: inline-flex; align-items: center; gap: 20px;
        padding: 22px 48px;
        background: linear-gradient(135deg,
          #1a2a4a 0%,
          #2a4a7a 35%,
          #4a8cf7 65%,
          #3a6aaa 100%
        );
        background-size: 200% 200%;
        border: none;
        border-radius: 16px;
        cursor: pointer;
        text-decoration: none;
        animation:
          dsge-glow   2.8s ease-in-out infinite,
          dsge-float  3.6s ease-in-out infinite,
          dsge-fadeIn 0.9s cubic-bezier(0.16, 1, 0.3, 1);
        overflow: hidden;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        font-family: 'Syne', sans-serif;
      }}

      .dsge-btn::before {{
        content: '';
        position: absolute;
        top: 0; left: -150%;
        width: 60%; height: 100%;
        background: linear-gradient(
          90deg,
          transparent,
          rgba(255,255,255,0.12),
          transparent
        );
        transform: skewX(-25deg);
        animation: dsge-shine 4.8s ease-in-out infinite;
      }}

      .dsge-btn::after {{
        content: '';
        position: absolute;
        inset: 1px;
        border-radius: 15px;
        background: linear-gradient(135deg,
          rgba(255,255,255,0.06) 0%,
          transparent 50%,
          rgba(255,255,255,0.03) 100%
        );
        pointer-events: none;
      }}

      .dsge-btn:hover {{
        transform: translateY(-5px) scale(1.02);
        filter: brightness(1.12) saturate(1.2);
        animation-duration: 1.4s, 2s, 0.5s;
      }}

      .dsge-btn:active {{
        transform: translateY(-1px) scale(0.98);
        filter: brightness(0.95);
      }}

      .dsge-btn-icon {{
        font-size: 32px;
        line-height: 1;
        position: relative;
        z-index: 1;
      }}

      .dsge-btn-text {{
        display: flex; flex-direction: column; align-items: flex-start;
        gap: 3px; position: relative; z-index: 1;
      }}

      .dsge-btn-main {{
        font-size: 22px; font-weight: 800;
        color: #ffffff;
        letter-spacing: 0.04em;
        line-height: 1.2;
      }}

      .dsge-btn-sub {{
        font-family: 'DM Mono', 'Courier New', monospace;
        font-size: 11px; font-weight: 500;
        color: rgba(255,255,255,0.6);
        letter-spacing: 0.08em;
      }}

      .dsge-btn-arrow {{
        font-size: 30px;
        color: rgba(255,255,255,0.8);
        position: relative; z-index: 1;
        animation: dsge-arrow 2s ease-in-out infinite;
        transition: transform 0.3s ease;
      }}

      .dsge-btn:hover .dsge-btn-arrow {{
        animation-duration: 0.8s;
      }}

      .dsge-btn-badge {{
        position: absolute;
        top: -10px; right: -8px;
        background: linear-gradient(135deg, #a78bfa, #56d8cc);
        color: #080a0f;
        font-family: 'DM Mono', monospace;
        font-size: 9px; font-weight: 700;
        letter-spacing: 0.05em;
        padding: 3px 10px;
        border-radius: 20px;
        box-shadow: 0 2px 12px rgba(167,139,250,0.4);
        z-index: 2;
      }}

      .dsge-btn-hint {{
        text-align: center;
        font-family: 'DM Mono', monospace;
        font-size: 11px;
        color: #4a4e5a;
        margin-top: 10px;
        letter-spacing: 0.04em;
        animation: dsge-fadeIn 1.2s ease-out;
      }}
    </style>

    <div class="dsge-btn-container">
      <a href="{banner_url}" target="_blank" class="dsge-btn">
        <span class="dsge-btn-icon">📈</span>
        <span class="dsge-btn-text">
          <span class="dsge-btn-main">ABRIR AGENTEDSGE</span>
          <span class="dsge-btn-sub">Modelagem DSGE · Chatbot Interativo</span>
        </span>
        <span class="dsge-btn-arrow">→</span>
        <span class="dsge-btn-badge">17 etapas</span>
      </a>
    </div>
    <div class="dsge-btn-hint">↳ Será aberta em uma nova guia do navegador</div>
    """))


def show_ready_message():
    """Exibe a mensagem de que o agente está pronto."""
    if not IN_COLAB or not display or not HTML:
        print("\n  ✅ AgenteDSGE pronta!\n")
        return

    display(HTML("""
    <style>
      @keyframes dsge-ready-glow {
        0%, 100% { box-shadow: 0 0 16px rgba(74,140,247,0.2); }
        50%      { box-shadow: 0 0 32px rgba(74,140,247,0.4); }
      }
      .dsge-ready {
        display: flex; flex-direction: column; align-items: center;
        padding: 16px;
      }
      .dsge-ready-badge {
        display: inline-flex; align-items: center; gap: 12px;
        padding: 14px 28px;
        background: rgba(74,140,247,0.08);
        border: 1px solid rgba(74,140,247,0.2);
        border-radius: 10px;
        animation: dsge-ready-glow 2.4s ease-in-out infinite;
        font-family: 'DM Mono', monospace;
      }
      .dsge-ready-icon { font-size: 22px; }
      .dsge-ready-text {
        font-size: 16px; font-weight: 600;
        color: #4a8cf7; letter-spacing: 0.04em;
      }
    </style>
    <div class="dsge-ready">
      <div class="dsge-ready-badge">
        <span class="dsge-ready-icon">✅</span>
        <span class="dsge-ready-text">AgenteDSGE pronta para operar</span>
      </div>
    </div>
    """))


# ══════════════════════════════════════════════════════════════
# 4. SERVIDOR WRAPPER (ESSENCIAL)
# ══════════════════════════════════════════════════════════════

_drive_url   = "https://drive.google.com/drive/my-drive"
_folder_path = "/content"

def set_drive_info(folder_path, drive_url):
    global _drive_url, _folder_path
    _drive_url   = drive_url
    _folder_path = folder_path


def create_wrapper_html(terminal_url, drive_url):
    """Cria a página HTML wrapper que emoldura o terminal."""
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AgenteDSGE — Modelagem Macroeconômica</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@700;800&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    :root {{
      --ink:         #e0e4f0;
      --ink-muted:   #7a84a0;
      --surface:     #080a0f;
      --rail:        #0d1018;
      --line:        rgba(74,140,247,.10);
      --blue:        #4a8cf7;
      --blue-dim:    rgba(74,140,247,.12);
      --blue-glow:   rgba(74,140,247,.25);
      --purple:      #a78bfa;
      --amber:       #e8b84b;
      --red:         #e07070;
      --radius:      5px;
    }}
    html, body {{ height: 100%; background: var(--surface); color: var(--ink); font-family: "DM Mono", monospace; overflow: hidden; }}

    /* ── TOP BAR ── */
    #topbar {{
      position: fixed; inset: 0 0 auto 0; height: 48px;
      background: var(--rail); border-bottom: 1px solid var(--line);
      display: flex; align-items: center; padding: 0 16px; gap: 12px; z-index: 9999;
    }}
    .logo {{ display: flex; align-items: baseline; gap: 2px; }}
    .logo-agent {{ font-family:"Syne",sans-serif; font-weight:800; font-size:16px; color:var(--ink); letter-spacing:-.4px; }}
    .logo-dsge  {{ font-family:"Syne",sans-serif; font-weight:800; font-size:16px; color:var(--blue); letter-spacing:-.4px; }}
    .logo-tag {{ margin-left:8px; font-size:10px; color:var(--ink-muted); letter-spacing:.07em; padding:1px 6px; border:1px solid var(--line); border-radius:3px; }}
    .status {{ display:flex; align-items:center; gap:6px; font-size:11px; color:var(--ink-muted); }}
    .status-dot {{ width:6px; height:6px; border-radius:50%; background:var(--blue); animation: pulse 2.4s ease infinite; }}
    @keyframes pulse {{ 0%,100% {{ box-shadow:0 0 0 0 rgba(74,140,247,.5); }} 50% {{ box-shadow:0 0 0 5px rgba(74,140,247,0); }} }}
    .sep {{ flex: 1; }}
    .tb-btn {{
      display: inline-flex; align-items: center; gap: 6px;
      padding: 0 12px; height: 28px;
      font-family: "DM Mono", monospace; font-size: 10.5px; font-weight: 500;
      letter-spacing: .04em; border-radius: var(--radius); cursor: pointer;
      border: 1px solid; transition: background .15s, transform .1s;
      text-decoration: none; white-space: nowrap;
    }}
    .tb-btn:active {{ transform: scale(.96); }}
    .btn-drive  {{ color:var(--blue); background:var(--blue-dim); border-color:rgba(74,140,247,.25); }}
    .btn-drive:hover  {{ background:var(--blue-glow); border-color:rgba(74,140,247,.5); }}

    /* ── TERMINAL IFRAME ── */
    #terminal-frame {{
      position: absolute; inset: 48px 0 0 0;
      width: 100%; height: calc(100% - 48px);
      border: none;
    }}
  </style>
</head>
<body>
  <div id="topbar">
    <div class="logo">
      <span class="logo-agent">Agente</span><span class="logo-dsge">DSGE</span>
      <span class="logo-tag">v2.1</span>
    </div>
    <div class="status">
      <span class="status-dot"></span>
      agente pronto
    </div>
    <div class="sep"></div>
    <a href="{drive_url}" target="_blank" class="tb-btn btn-drive">
      📁 Drive
    </a>
  </div>
  <iframe id="terminal-frame" src="{terminal_url}"
    allow="clipboard-read; clipboard-write"
    tabindex="0" autofocus>
  </iframe>
</body>
</html>"""

    os.makedirs(WRAPPER_DIR, exist_ok=True)
    with open(os.path.join(WRAPPER_DIR, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(html)


def start_wrapper_server():
    """Inicia o servidor HTTP que serve o wrapper HTML."""
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_GET(self):
            p = urlparse(self.path).path
            if p in ("/", "/index.html"):
                fpath = os.path.join(WRAPPER_DIR, "index.html")
                with open(fpath, "rb") as f:
                    body = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            self.send_error(404)

    threading.Thread(
        target=lambda: HTTPServer(("0.0.0.0", WRAPPER_PORT), Handler).serve_forever(),
        daemon=True,
    ).start()


# ══════════════════════════════════════════════════════════════
# 5. ORQUESTRADOR DE LANÇAMENTO
# ══════════════════════════════════════════════════════════════

def launch(total_phases=5):
    """
    Orquestra o lançamento completo da AgenteDSGE com loading animado.

    Args:
        total_phases: Número total de fases (para a barra de progresso)
    """
    global _drive_url

    resolve_opencode()

    # ── SPLASH ──
    show_splash()
    time.sleep(0.8)

    # ── FASE 1: Instalação ttyd ──
    show_loading_phase("Instalação do Terminal Web (ttyd)", 1, total_phases)
    install_ttyd()
    kill_previous()
    show_phase_complete("Terminal Web instalado")
    time.sleep(0.3)

    # ── FASE 2: Inicialização do OpenCode ──
    show_loading_phase("Inicialização do OpenCode", 2, total_phases)
    start_ttyd()
    show_phase_complete("OpenCode iniciado no terminal")
    time.sleep(0.3)

    # ── FASE 3: Resolução de URLs ──
    show_loading_phase("Resolução de URLs do ambiente", 3, total_phases,
                       "configurando proxies do Colab...")

    if IN_COLAB and output:
        terminal_url = output.eval_js(f"google.colab.kernel.proxyPort({TERMINAL_PORT})")
        banner_url   = output.eval_js(f"google.colab.kernel.proxyPort({WRAPPER_PORT})")
    else:
        terminal_url = f"http://localhost:{TERMINAL_PORT}"
        banner_url   = f"http://localhost:{WRAPPER_PORT}"

    show_phase_complete("URLs resolvidas")
    time.sleep(0.3)

    # ── FASE 4: Interface wrapper ──
    show_loading_phase("Montagem da interface wrapper", 4, total_phases,
                       "gerando página HTML...")
    create_wrapper_html(terminal_url, _drive_url)
    start_wrapper_server()
    show_phase_complete("Interface wrapper no ar")
    time.sleep(0.3)

    # ── FASE 5: Pronto ──
    show_loading_phase("AgenteDSGE pronta para uso", 5, total_phases,
                       "✓ Todas as fases concluídas")

    time.sleep(0.5)
    show_ready_message()
    show_launch_button(banner_url)

    return banner_url


# ══════════════════════════════════════════════════════════════
# EXECUÇÃO DIRETA
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    launch()
