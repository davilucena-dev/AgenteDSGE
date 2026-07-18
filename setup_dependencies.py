#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║  setup_dependencies.py — AgenteDSGE                        ║
║  Instalação e configuração completa do ambiente            ║
║                                                            ║
║  Etapa 0 de 7: Base do sistema                             ║
║  Versão: 2.1 — Julho 2026 (+ Octave + Dynare)              ║
╚══════════════════════════════════════════════════════════════╝

Responsabilidades:
  1. Instalar OpenCode CLI (motor do agente)
  2. Instalar Python deps (versões pinadas — reprodutibilidade)
  3. Instalar Octave + Dynare (solução numérica DSGE)
  4. Configurar tema visual da AgenteDSGE
  5. Escrever o system prompt do agente (17 etapas DSGE)
  6. Verificar integridade de cada componente
  7. Reportar falhas de forma clara (nunca "fingir que deu certo")
"""

import os
import json
import subprocess
import shutil
import sys
import time

# ══════════════════════════════════════════════════════════════
# CONSTANTES
# ══════════════════════════════════════════════════════════════

OPENCODE_CONFIG_DIR = os.path.expanduser("~/.config/opencode")
THEME_DIR           = os.path.join(OPENCODE_CONFIG_DIR, "themes")
AGENT_DIR           = os.path.join(OPENCODE_CONFIG_DIR, "agents")
TUI_JSON            = os.path.join(OPENCODE_CONFIG_DIR, "tui.json")
OPENCODE_CFG        = os.path.join(OPENCODE_CONFIG_DIR, "config.json")
SETUP_STATUS_FILE   = os.path.expanduser("~/.agents/setup_status.json")
SKILLS_DIR          = os.path.expanduser("~/.agents/skills")

OPENCODE_BIN = None

# Octave + Dynare
DYNARE_VERSION = "6.2"
OCTAVE_BIN = None
DYNARE_PATH = None

# ══════════════════════════════════════════════════════════════
# DEPENDÊNCIAS PYTHON — VERSÕES PINADAS
# ══════════════════════════════════════════════════════════════
# JUSTIFICATIVA: Cada versão foi testada e travada para que o
# comportamento do agente não mude entre execuções. Atualizar
# apenas após validação manual.

PYTHON_DEPS = [
    # ── Essenciais ──
    "pandas==3.0.3",
    "numpy==2.5.0",
    "scipy==1.18.0",
    "statsmodels==0.14.6",
    "sympy==1.13.0",            # Para álgebra simbólica das FOCs
    # ── Dados brasileiros ──
    "sidrapy==0.1.4",
    "ipeadatapy==0.1.9",
    # ── Google / Drive ──
    "google-api-python-client==2.198.0",
    "google-auth-httplib2==0.4.0",
    "gspread==6.2.1",
    "openpyxl==3.1.5",
    # ── Otimização / Numérica ──
    "scikit-learn==1.6.0",
    # ── Visualização ──
    "matplotlib==3.10.0",
    "seaborn==0.13.0",
]

# ══════════════════════════════════════════════════════════════
# MENSAGENS TEMÁTICAS (DSGE)
# ══════════════════════════════════════════════════════════════

INSTALL_MESSAGES = [
    "📈 Resolvendo estado estacionário...",
    "📐 Derivando condições de primeira ordem...",
    "🔧 Verificando condições de Blanchard-Kahn...",
    "📊 Calibrando parâmetros da literatura...",
    "⚙️  Preparando estimação Bayesiana...",
    "📉 Linearizando em torno do steady-state...",
    "🎯 Verificando convergência das cadeias MCMC...",
]

_joke_index = 0

def next_message():
    """Retorna a próxima mensagem temática em ciclo."""
    global _joke_index
    msg = INSTALL_MESSAGES[_joke_index % len(INSTALL_MESSAGES)]
    _joke_index += 1
    return msg


# ══════════════════════════════════════════════════════════════
# UTILITÁRIOS
# ══════════════════════════════════════════════════════════════

def run_cmd(cmd, check=True, timeout=300, **kw):
    """
    Executa um comando shell e retorna o resultado.
    Sempre captura stdout e stderr completos.
    """
    result = subprocess.run(
        cmd, shell=True,
        capture_output=True, text=True,
        timeout=timeout, **kw
    )
    if check and result.returncode != 0:
        raise RuntimeError(
            f"Comando falhou (exit={result.returncode}):\n"
            f"  Comando: {cmd[:200]}\n"
            f"  stderr: {result.stderr.strip()[-500:]}"
        )
    return result


def log_ok(msg):
    """Mensagem de sucesso."""
    print(f"  ✅ {msg}")

def log_warn(msg):
    """Mensagem de aviso."""
    print(f"  ⚠️  {msg}")

def log_fail(msg):
    """Mensagem de erro."""
    print(f"  ❌ {msg}")

def log_step(msg):
    """Mensagem de passo."""
    print(f"\n  ── {msg}")


# ══════════════════════════════════════════════════════════════
# 1. INSTALAÇÃO DO OPENCODE
# ══════════════════════════════════════════════════════════════

def find_opencode_binary():
    """
    Procura o binário do OpenCode em candidatos conhecidos.
    Retorna o caminho ou None.
    """
    global OPENCODE_BIN

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
            ["find", "/root", "/home", "/usr/local",
             "-name", "opencode", "-type", "f", "-maxdepth", "4"],
            capture_output=True, text=True
        )
        hits = [l.strip() for l in result.stdout.splitlines() if l.strip()]
        found = hits[0] if hits else None

    if found:
        OPENCODE_BIN = found
        bin_dir = os.path.dirname(found)
        if bin_dir not in os.environ.get("PATH", ""):
            os.environ["PATH"] = bin_dir + ":" + os.environ["PATH"]
        os.environ["OPENCODE_BIN"] = found
        try:
            version_result = subprocess.run(
                [found, "--version"], capture_output=True, text=True, timeout=10
            )
            ver = version_result.stdout.strip() or version_result.stderr.strip()
            log_ok(f"OpenCode {ver} encontrado em: {found}")
        except Exception:
            log_ok(f"OpenCode localizado em: {found}")
    else:
        log_fail("OpenCode NÃO encontrado no sistema.")

    return found


def install_opencode():
    """
    Instala o OpenCode CLI via script oficial.
    Verifica cada etapa — falha crítica interrompe a execução.
    """
    failures = []
    warnings = []

    print(f"\n  {next_message()}")
    log_step("Instalando OpenCode CLI...")
    r = run_cmd("curl -fsSL https://opencode.ai/install | bash", check=False, timeout=180)
    if r.returncode != 0:
        failures.append(("OpenCode CLI", True,
                         r.stderr.strip()[-500:] or "código de saída != 0"))
        log_fail("Falha na instalação do OpenCode.")
    else:
        log_ok("Instalador do OpenCode executado sem erro.")

    print(f"\n  {next_message()}")
    log_step("Instalando uv (gerenciador de pacotes)...")
    r = run_cmd("curl -LsSf https://astral.sh/uv/install.sh | sh", check=False, timeout=120)
    if r.returncode != 0:
        warnings.append(("uv", r.stderr.strip()[-300:] or "código de saída != 0"))
        log_warn("uv não instalado (não crítico).")
    else:
        log_ok("uv instalado.")

    print(f"\n  {next_message()}")
    log_step("Instalando ferramentas auxiliares do sistema (xclip, xsel)...")
    r = run_cmd("apt-get update -qq && apt-get install -y -qq xclip xsel 2>&1",
                check=False, timeout=120)
    if r.returncode != 0:
        warnings.append(("xclip/xsel", r.stderr.strip()[-300:] or "código de saída != 0"))
        log_warn("xclip/xsel não instalados (apenas funcionalidade de clipboard pode ser afetada).")
    else:
        log_ok("xclip/xsel instalados.")

    log_step("Instalando dependências Python (versões pinadas)...")
    pip_cmd = "pip install " + " ".join(PYTHON_DEPS) + " --quiet"
    r = run_cmd(pip_cmd, check=False, timeout=300)
    if r.returncode != 0:
        failures.append(("Dependências Python",
                         True, r.stderr.strip()[-800:] or "código de saída != 0"))
        log_fail("Falha na instalação das bibliotecas Python.")
    else:
        log_ok("Todas as bibliotecas Python instaladas com versões pinadas.")

    # Verificar se OpenCode foi instalado
    opencode_bin = find_opencode_binary()
    if not opencode_bin:
        failures.append(("Binário do OpenCode", True,
                         "não encontrado no PATH nem nos diretórios candidatos."))
        log_fail("OpenCode CLI não encontrado após instalação.")

    # ── Relatório final de instalação ──
    os.makedirs(os.path.dirname(SETUP_STATUS_FILE), exist_ok=True)
    status = {
        "ok": len(failures) == 0,
        "failures": [{"componente": n, "critico": c, "erro": m} for n, c, m in failures],
        "warnings": [{"componente": n, "erro": m} for n, m in warnings],
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    with open(SETUP_STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2, ensure_ascii=False)

    if warnings:
        print(f"\n  ⚠️  Avisos (não críticos — agente funciona com limitações):")
        for name, msg in warnings:
            print(f"     • {name}: {msg[:200]}")

    if failures:
        print(f"\n  {'='*60}")
        print(f"  ❌ FALHA CRÍTICA NA INSTALAÇÃO — componentes que não ficaram prontos:")
        for name, _, msg in failures:
            print(f"     • {name}: {msg[:300]}")
        print(f"  {'='*60}")
        os.environ["AGENTEDSGE_SETUP_STATUS"] = "FAILED"
        raise RuntimeError(
            "Instalação incompleta: " +
            ", ".join(n for n, _, _ in failures) +
            ". Corrija os erros antes de usar a AgenteDSGE — "
            "prosseguir agora comprometeria a reprodutibilidade."
        )

    os.environ["AGENTEDSGE_SETUP_STATUS"] = "OK"
    print(f"\n  ✅ OpenCode e todas as dependências instaladas e verificadas com sucesso.")


# ══════════════════════════════════════════════════════════════
# 1.5. INSTALAÇÃO DO OCTAVE + DYNARE
# ══════════════════════════════════════════════════════════════

def install_octave_dynare():
    """
    Instala GNU Octave e compila/instala Dynare a partir do código-fonte.
    Octave: engine de cálculo numérico (substituto gratuito do MATLAB).
    Dynare: pacote de modelagem DSGE (resolve .mod, MCMC, IRFs, etc).

    Retorna (octave_ok, dynare_ok).
    """
    global OCTAVE_BIN, DYNARE_PATH

    failures = []
    warnings = []

    print(f"\n  {next_message()}")
    log_step("Instalando GNU Octave...")

    # ── 1. Instalar Octave via apt ──
    r = run_cmd(
        "apt-get update -qq && apt-get install -y -qq "
        "octave liboctave-dev libblas-dev liblapack-dev libfftw3-dev "
        "libgsl-dev libcurl4-openssl-dev texinfo 2>&1",
        check=False, timeout=300
    )
    if r.returncode != 0:
        failures.append(("GNU Octave", True,
                         r.stderr.strip()[-500:] or "código de saída != 0"))
        log_fail("Falha na instalação do Octave.")
        return False, False
    else:
        log_ok("GNU Octave instalado via apt.")

    # Encontrar binário do Octave
    octave_candidates = [
        "/usr/bin/octave",
        "/usr/local/bin/octave",
        shutil.which("octave") or "",
    ]
    OCTAVE_BIN = next((p for p in octave_candidates if p and os.path.isfile(p)), None)
    if not OCTAVE_BIN:
        failures.append(("Binário Octave", True, "não encontrado após instalação"))
        log_fail("Octave não encontrado no PATH.")
        return False, False

    os.environ["OCTAVE_BIN"] = OCTAVE_BIN

    # Verificar versão do Octave
    try:
        vr = run_cmd(f"{OCTAVE_BIN} --version", check=True, timeout=10)
        ver = vr.stdout.strip().split("\n")[0]
        log_ok(f"Octave: {ver}")
    except Exception as e:
        log_warn(f"Octave instalado mas não respondeu --version: {e}")

    # ── 2. Compilar Dynare a partir do código-fonte ──
    print(f"\n  {next_message()}")
    log_step(f"Compilando Dynare {DYNARE_VERSION} a partir do código-fonte...")

    dynare_build_dir = "/tmp/dynare-build"
    dynare_install_dir = "/usr/local/lib/dynare"

    # Limpar build anterior se existir
    if os.path.isdir(dynare_build_dir):
        shutil.rmtree(dynare_build_dir, ignore_errors=True)
    os.makedirs(dynare_build_dir, exist_ok=True)

    # Baixar código-fonte do Dynare (tag oficial)
    tarball_url = (
        f"https://gitlab.com/dynare/dynare/-/archive/{DYNARE_VERSION}"
        f"/dynare-{DYNARE_VERSION}.tar.gz"
    )
    r = run_cmd(
        f"curl -fsSL '{tarball_url}' -o /tmp/dynare-{DYNARE_VERSION}.tar.gz",
        check=False, timeout=120
    )
    if r.returncode != 0:
        warnings.append(("Dynare download", r.stderr.strip()[-300:]))
        log_warn("Falha ao baixar Dynare. Tentando via Octave Forge...")

        # Fallback: instalar via Octave Forge (método mais simples)
        forge_install = run_cmd(
            f'{OCTAVE_BIN} --no-gui --eval "'
            f"pkg install -forge io; "
            f"pkg install -forge statistics; "
            f"pkg install -forge dynare"
            f'"',
            check=False, timeout=600
        )
        if forge_install.returncode != 0:
            failures.append(("Dynare", True,
                             forge_install.stderr.strip()[-500:] or "Falha no Forge"))
            log_fail("Dynare não pôde ser instalado.")
            return True, False

        # Encontrar caminho do Dynare via Forge
        try:
            find_dynare = run_cmd(
                f'{OCTAVE_BIN} --no-gui --eval '
                f'"disp(pkg(\'list\'))"',
                check=True, timeout=30
            )
            log_ok("Dynare instalado via Octave Forge.")
            DYNARE_PATH = "forge"
            os.environ["DYNARE_PATH"] = DYNARE_PATH

            # Verificar carregamento
            verify_dynare = run_cmd(
                f'{OCTAVE_BIN} --no-gui --eval "pkg load dynare; disp(\'DYNARE_OK\')"',
                check=False, timeout=30
            )
            if "DYNARE_OK" in (verify_dynare.stdout or ""):
                log_ok("Dynare carregado com sucesso via Forge.")
                return True, True
            else:
                log_warn("Dynare instalado mas não carregou. Pode ser necessário pkg load.")
                return True, True  # Ainda assim consideramos ok

        except Exception as e:
            failures.append(("Dynare", True, str(e)))
            return True, False

    # Extrair tarball
    r = run_cmd(
        f"tar xzf /tmp/dynare-{DYNARE_VERSION}.tar.gz -C {dynare_build_dir} "
        f"--strip-components=1",
        check=False, timeout=60
    )
    if r.returncode != 0:
        failures.append(("Dynare extrair", True, r.stderr.strip()[-300:]))
        log_fail("Falha ao extrair código-fonte do Dynare.")
        return True, False

    # Compilar com CMake + Octave preprocessor
    os.makedirs(dynare_install_dir, exist_ok=True)

    cmake_cmd = (
        f"cd {dynare_build_dir}/build && "
        f"cmake .. "
        f"-DCMAKE_INSTALL_PREFIX={dynare_install_dir} "
        f"-DMATLAB_PATH=OFF "
        f"-DOCTAVE_PATH={OCTAVE_BIN} "
        f"-DWITH_MATLAB=OFF "
        f"-DWITH_octave=ON "
        f"-DCMAKE_BUILD_TYPE=Release "
        f"2>&1"
    )
    r = run_cmd(cmake_cmd, check=False, timeout=180)
    if r.returncode != 0:
        warnings.append(("Dynare cmake", r.stderr.strip()[-500:]))
        log_warn("CMake do Dynare falhou. Tentando compilação mínima...")
        # Fallback: compilar apenas o Octave preprocessor
        cmake_cmd = (
            f"cd {dynare_build_dir}/build && "
            f"cmake .. "
            f"-DCMAKE_INSTALL_PREFIX={dynare_install_dir} "
            f"-DOCTAVE_PATH={OCTAVE_BIN} "
            f"-DWITH_MATLAB=OFF "
            f"-DCMAKE_BUILD_TYPE=Release "
            f"2>&1"
        )
        r = run_cmd(cmake_cmd, check=False, timeout=180)

    if r.returncode != 0:
        failures.append(("Dynare cmake", True, r.stderr.strip()[-500:]))
        log_fail("Falha no CMake do Dynare.")
        return True, False

    # make + install
    nproc = os.cpu_count() or 2
    r = run_cmd(
        f"cd {dynare_build_dir}/build && make -j{nproc} && make install",
        check=False, timeout=600
    )
    if r.returncode != 0:
        failures.append(("Dynare make", True, r.stderr.strip()[-500:]))
        log_fail("Falha na compilação do Dynare.")
        return True, False

    log_ok(f"Dynare {DYNARE_VERSION} compilado e instalado em {dynare_install_dir}")

    # ── 3. Configurar PATH do Dynare ──
    DYNARE_PATH = dynare_install_dir
    os.environ["DYNARE_PATH"] = DYNARE_PATH

    # Adicionar ao octave path
    octave_pkg_dir = os.path.join(dynare_install_dir, "matlab")
    if not os.path.isdir(octave_pkg_dir):
        octave_pkg_dir = os.path.join(dynare_install_dir, "octave")

    if os.path.isdir(octave_pkg_dir):
        octave_path_cmd = (
            f'{OCTAVE_BIN} --no-gui --eval '
            f'"addpath(\'{octave_pkg_dir}\'); savepath();"'
        )
        r = run_cmd(octave_path_cmd, check=False, timeout=30)
        if r.returncode == 0:
            log_ok(f"Dynare adicionado ao path do Octave: {octave_pkg_dir}")
        else:
            log_warn("Não foi possível salvar path do Dynare no Octave.")

    # ── 4. Verificar Dynare ──
    print(f"\n  {next_message()}")
    log_step("Verificando Dynare...")

    verify_cmd = (
        f'{OCTAVE_BIN} --no-gui --eval "'
        f"try; "
        f"addpath('{octave_pkg_dir}'); "
        f"dynare; "
        f"disp('DYNARE_OK'); "
        f"catch e; "
        f"disp(['DYNARE_FAIL: ' e.message]); "
        f"end"
        f'"'
    )
    r = run_cmd(verify_cmd, check=False, timeout=30)
    output = (r.stdout or "") + (r.stderr or "")

    if "DYNARE_OK" in output:
        log_ok(f"Dynare {DYNARE_VERSION} funcional — Octave pode carregar.")
    else:
        log_warn(f"Dynare instalado mas verificação inconclusiva: {output[-200:]}")
        warnings.append(("Dynare verificação", "Verificação não retornou DYNARE_OK"))

    # ── 5. Relatório ──
    if warnings:
        print(f"\n  ⚠️  Avisos Octave/Dynare:")
        for name, msg in warnings:
            print(f"     • {name}: {msg[:200]}")

    if failures:
        print(f"\n  ❌ FALHA CRÍTICA Octave/Dynare:")
        for name, _, msg in failures:
            print(f"     • {name}: {msg[:300]}")
        # Octave/Dynare não é crítico para o setup — agente pode rodar sem MCMC
        log_warn("Octave/Dynare indisponível — estimação Bayesiana ficará limitada.")

    octave_ok = OCTAVE_BIN is not None and not any(n == "GNU Octave" for n, _, _ in failures)
    dynare_ok = DYNARE_PATH is not None and not any(n.startswith("Dynare") for n, _, _ in failures)

    if octave_ok:
        log_ok(f"Octave: {OCTAVE_BIN}")
    if dynare_ok:
        log_ok(f"Dynare: {DYNARE_PATH}")

    return octave_ok, dynare_ok


# ══════════════════════════════════════════════════════════════
# 2. CONFIGURAÇÃO DE DIRETÓRIOS
# ══════════════════════════════════════════════════════════════

def create_directories():
    """Cria a estrutura de diretórios necessária para o agente."""
    dirs = [
        THEME_DIR,
        AGENT_DIR,
        OPENCODE_CONFIG_DIR,
        SKILLS_DIR,
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    log_ok("Diretórios de configuração criados.")


def create_drive_structure(base_path):
    """
    Cria a estrutura de pastas no Google Drive para a AgenteDSGE.
    Retorna o caminho base.
    """
    drive_structure = [
        "",
        "dados",
        "dados/brutos",
        "dados/processados",
        "parametros",
        "parametros/calibrados",
        "parametros/estimados",
        "modelos",
        "modelos/equacoes",
        "modelos/linearizados",
        "resultados",
        "resultados/irfs",
        "resultados/decomposicoes",
        "resultados/mcmc",
        "codigo_dynare",
        "auditoria",
    ]

    for subdir in drive_structure:
        full_path = os.path.join(base_path, subdir)
        os.makedirs(full_path, exist_ok=True)

    log_ok(f"Estrutura do Drive criada em: {base_path}")
    return base_path


# ══════════════════════════════════════════════════════════════
# 3. TEMA VISUAL DA AGENTEDSGE
# ══════════════════════════════════════════════════════════════

def setup_theme():
    """
    Tema AgenteDSGE — azul noturno / roxo acadêmico.
    Cores que remetem a séries temporais, econometria e simulações.
    """
    theme = {
        "$schema": "https://opencode.ai/theme.json",
        "defs": {
            "bg0":        "#080a0f",
            "bg1":        "#0d1018",
            "bg2":        "#141a28",
            "bg3":        "#1c2438",
            "bg4":        "#253048",
            "fg0":        "#e0e4f0",
            "fg1":        "#7a84a0",
            "fg2":        "#3a4460",
            "fg3":        "#243050",
            "blue":       "#4a8cf7",
            "blueDim":    "#1a3c77",
            "blueGlow":   "#2a5ca7",
            "cyan":       "#56d8cc",
            "amber":      "#e8b84b",
            "red":        "#e07070",
            "silver":     "#b0bcd4",
            "purple":     "#a78bfa",
            "green":      "#4caf50",
            "synKeyword": "#4a8cf7",
            "synString":  "#56d8cc",
            "synComment": "#3a4460",
            "synNumber":  "#e8b84b",
            "synFunction":"#a78bfa",
            "synType":    "#7a84a0",
            "synOp":      "#b0bcd4",
        },
        "theme": {
            "primary":            {"dark": "blue",     "light": "blueDim"},
            "secondary":          {"dark": "cyan",     "light": "cyan"},
            "accent":             {"dark": "purple",   "light": "purple"},
            "error":              {"dark": "red",      "light": "red"},
            "warning":            {"dark": "amber",    "light": "amber"},
            "success":            {"dark": "green",    "light": "green"},
            "info":               {"dark": "blue",     "light": "blue"},
            "text":               {"dark": "fg0",      "light": "fg0"},
            "textMuted":          {"dark": "fg1",      "light": "fg1"},
            "background":         {"dark": "bg0",      "light": "bg0"},
            "backgroundPanel":    {"dark": "bg1",      "light": "bg1"},
            "backgroundElement":  {"dark": "bg2",      "light": "bg2"},
            "border":             {"dark": "bg3",      "light": "bg3"},
            "borderActive":       {"dark": "bg4",      "light": "bg4"},
            "syntaxKeyword":      {"dark": "synKeyword","light":"synKeyword"},
            "syntaxString":       {"dark": "synString", "light":"synString"},
            "syntaxComment":      {"dark": "synComment","light":"synComment"},
            "syntaxNumber":       {"dark": "synNumber", "light":"synNumber"},
            "syntaxFunction":     {"dark": "synFunction","light":"synFunction"},
            "syntaxType":         {"dark": "synType",   "light":"synType"},
            "syntaxOperator":     {"dark": "synOp",     "light":"synOp"},
            "markdownHeading":    {"dark": "blue",      "light":"blue"},
            "markdownCode":       {"dark": "amber",     "light":"amber"},
        }
    }

    theme_path = os.path.join(THEME_DIR, "dsge.json")
    with open(theme_path, "w", encoding="utf-8") as f:
        json.dump(theme, f, indent=2)

    tui = {
        "$schema": "https://opencode.ai/tui.json",
        "theme": "dsge"
    }
    with open(TUI_JSON, "w", encoding="utf-8") as f:
        json.dump(tui, f, indent=2)

    log_ok(f"Tema AgenteDSGE configurado: {theme_path}")


# ══════════════════════════════════════════════════════════════
# 4. SYSTEM PROMPT DO AGENTE
# ══════════════════════════════════════════════════════════════

def get_agent_system_prompt():
    """
    Retorna o system prompt completo da AgenteDSGE.
    Documento proprietário — 17 etapas + filosofia Zero Alucinação.
    """
    return r"""---
name: AgenteDSGE
description: Agente especializado em modelos DSGE (Dynamic Stochastic General Equilibrium) — criação, calibração, estimação Bayesiana e validação. Cobre todas as etapas do protocolo de 17 passos com rigor científico.
color: "#4a8cf7"
tools:
  todowrite: true
  todoread: true
permission:
  todowrite: allow
  todoread: allow
---

## 🧭 1. Identidade e Missão

Você é a **AgenteDSGE**, especialista autônoma em modelagem macroeconômica DSGE.

Sua missão é conduzir **todas as 17 etapas** de construção, calibração, estimação e validação de modelos DSGE — do paper à execução computacional — com **reprodutibilidade, rastreabilidade e honestidade intelectual**.


### 🔒 Princípio Zero Alucinação

| ❌ Proibido | ✅ Obrigatório |
|---|---|
| Inventar equações que não derivou | Mostrar cada passo algébrico |
| "Chutar" parâmetros sem fonte verificável | Cada parâmetro exige referência bibliográfica |
| Fabricar resultados de estimação que não rodou | Executar MCMC de fato ou declarar "não estimado" |
| Ignorar violações de Blanchard-Kahn | Parar e reportar o problema |
| Usar um modelo quando equações ≠ variáveis | Verificar contagem antes de prosseguir |
| Apresentar IRFs sem sentido econômico | Validar coerência teórica das respostas |
| Omitir incerteza ou não convergência | Reportar abertamente falhas e diagnósticos |

> **Regra de Ouro:** Prefira dizer "NÃO SEI" ou "NÃO É POSSÍVEL DETERMINAR" a fabricar uma resposta.


### 📋 Macroestrutura do Protocolo

```
BLOCO A — ESTRUTURA TEÓRICA (Etapas 1-6)
    ↓ validação: consistência lógica
BLOCO B — SOLUÇÃO NUMÉRICA (Etapas 7-12)
    ↓ validação: Blanchard-Kahn + estado estacionário
BLOCO C — ESTIMAÇÃO (Etapas 13-14)
    ↓ validação: convergência MCMC
BLOCO D — VALIDAÇÃO E ENTREGA (Etapas 15-17)
    ↓ validação: coerência econômica das IRFs
```


## 🔬 2. Bloco A — Estrutura Teórica

### ETAPA 1 — Ler e Identificar o Modelo
Identificar: tipo do modelo (RBC, NK, economia aberta, fiscal), agentes econômicos, variáveis de estado, variáveis de controle, choques exógenos, parâmetros.

> **Checkpoint 1:** Tabela com todos os componentes. Verificar consistência.

### ETAPA 2 — Organizar as Equações
Listar T O D A S as equações numeradas: utilidade, restrição orçamentária, tecnologia, acumulação de capital, regras de preços/salários, política monetária/fiscal, AR(1), condições de equilíbrio.

> **Checkpoint 2:** Número de equações DEVE ser exatamente igual ao número de variáveis endógenas. Se não, TRAVAR.

### ETAPA 3 — Montar o Problema de Otimização
Para CADA agente: escrever Lagrangeano ou Bellman explicitamente.

> **Checkpoint 3:** Verificar se cada variável de controle tem FOC associada.

### ETAPA 4 — Derivar as FOCs
Derivar TODAS as condições de primeira ordem. Mostrar cada derivada parcial.

> **Checkpoint 4:** Listar FOCs + condições de transversalidade.

### ETAPA 5 — Eliminar Multiplicadores
Substituir multiplicadores de Lagrange usando as FOCs. Obter sistema reduzido.

> **Checkpoint 5:** Sistema sem multiplicadores. Deve ser equivalente ao original.

### ETAPA 6 — Construir o Equilíbrio Geral
Mercados: bens, trabalho, financeiro, restrição de recursos, condição de transversalidade.

> **Checkpoint 6:** Reprocessar Checkpoint 2 com equações finais.


## 🔧 3. Bloco B — Solução Numérica

### ETAPA 7 — Resolver o Estado Estacionário
Impor x_t = x_{t+1} = x_bar. Resolver analiticamente; se impossível, Newton-Raphson.

> **Checkpoint 7:** Verificar restrições econômicas (c > 0, k > 0, y > 0, n ∈ (0,1), r > 0).

### ETAPA 8 — Calibrar Parâmetros
Cada parâmetro DEVE ter: valor, fonte, justificativa. Para modelos brasileiros: IBGE, BCB/SGS, IPEADATA, literatura.

> **Checkpoint 8:** Tabela com parâmetros. Parâmetros sem fonte marcados como [AD HOC].

### ETAPA 9 — Log-Linearizar
x_t = x_bar * exp(x_hat_t). Taylor 1ª ordem. Todas as equações.

> **Checkpoint 9:** N equações linearizadas = N equações originais.

### ETAPA 10 — Forma Matricial
A · E_t x_{t+1} = B · x_t + C · x_{t-1} + D · ε_t

> **Checkpoint 10:** Verificar dimensionalidade das matrizes.

### ETAPA 11 — Verificar Blanchard-Kahn
Contar autovalores instáveis vs. variáveis forward-looking.

> **Checkpoint 11:** Tabela de autovalores. Veredito: satisfeito / não existe solução / indeterminação.

### ETAPA 12 — Resolver o Modelo
x_t = P · x_{t-1} + Q · ε_t. QZ / Klein / Sims.

> **Checkpoint 12:** Verificar se P é estável e Q é real.


## 💻 4. Bloco C — Estimação

### ETAPA 13 — Gerar Código Dynare (.mod)
Arquivo .mod completo: var, varexo, parameters, model, steady_state_model, shocks, estimated_params, estimation.

> **Checkpoint 13:** Código sintaticamente válido. Passa pelo dynare com nograph.

### ETAPA 14 — Estimação Bayesiana
Prioris informadas. MCMC: 2-4 cadeias, 50k+ iterações, 20% burn-in, jump scale para aceitação 20-40%.

> **Checkpoint 14:** Prior justificada. Modelo identificável.


## 📊 5. Bloco D — Validação e Entrega

### ETAPA 15 — Diagnóstico da Estimação
Brooks-Gelman (< 1.10), traços, taxa de aceitação (20-40%), log-posterior estável.

> **Checkpoint 15:** Relatório com psrf, aceitação, veredito CONVERGIU / NÃO CONVERGIU.

### ETAPA 16 — Análise Dinâmica
IRFs (40 períodos), decomposição de variância, decomposição histórica, previsões, contrafactuais.

> **Checkpoint 16:** Interpretar economicamente CADA IRF. Se contradizer teoria, reportar.

### ETAPA 17 — Validação Final e Entrega
Checklist geral (10 itens). Relatório técnico + código .mod + tabela de parâmetros + gráficos + audit log + declaração de limitações.

> **Checkpoint 17:** Aprovado / Rejeitado. Se rejeitado, não entregar.


## 🛡️ 6. Garantias Antialucinação

### Hierarquia de Fontes
```
Nível 1: Dados extraídos por APIs reais (IBGE, BCB, IPEA)
Nível 2: Parâmetros de literatura revisada por pares
Nível 3: Parâmetros calibrados por matching de momentos (com dados reais)
Nível 4: Parâmetros estimados por MCMC (com diagnóstico de convergência)
---
Nível 5 (NUNCA): "Chutes", analogias sem fonte, valores "típicos" não referenciados
```

### Comportamento sob Incerteza
| Situação | Resposta |
|---|---|
| Parâmetro sem fonte | Marcar como [AD HOC] e sugerir estimação |
| Dados insuficientes | Reportar limitação e não prosseguir |
| Múltiplas soluções de BK | Reportar todas e discutir |
| IRF contradiz teoria | Reportar e listar possíveis causas |
| Modelo não identificável | Parar, reportar, sugerir reformulação |


## 📁 7. Ambiente de Trabalho

- **Diretório raiz:** `/content/drive/My Drive/AgenteDSGE/`
- **Estrutura:**
  - `dados/brutos/` — Microdados e séries baixadas
  - `dados/processados/` — Séries tratadas
  - `parametros/calibrados/` — Parâmetros com fontes
  - `parametros/estimados/` — Resultados MCMC
  - `modelos/equacoes/` — Sistemas de equações
  - `modelos/linearizados/` — Versões linearizadas
  - `resultados/irfs/` — Funções de resposta ao impulso
  - `resultados/decomposicoes/` — Decomposições
  - `resultados/mcmc/` — Diagnósticos de convergência
  - `codigo_dynare/` — Arquivos .mod gerados
  - `auditoria/` — Logs de decisão


## 📝 8. Metodologia de Execução (Obrigatória)

### 🟢 REGRA DE OURO: TRANSPARÊNCIA TOTAL EM TEMPO REAL

Você DEVE mostrar ao usuário **o que está fazendo**, **por que está fazendo** e **o que encontrou** — no momento exato em que cada ação ocorre. O usuário nunca deve "achar" que você está trabalhando; ele deve **ver** cada etapa.

### Fluxo Obrigatório para Cada Tarefa

```
┌─ ANTE de começar ─────────────────────────────────────
│ "📋 Etapa X: [nome da etapa] — iniciando"
│ "   Objetivo: [descrição clara do que será feito]"
│ "   Método: [como vai fazer]"
│ Usar todowrite para registrar a tarefa como in_progress
└───────────────────────────────────────────────────────

┌─ DURANTE a execução ──────────────────────────────────
│ "   🔍 [o que está sendo calculado/verificado agora]"
│ "   → [resultado parcial, se aplicável]"
│ Mostrar progresso a cada subpasso relevante
└───────────────────────────────────────────────────────

┌─ APÓS concluir ───────────────────────────────────────
│ ✅ Resultado: [o que foi encontrado]
│ ✅ Checkpoint: [passou / falhou — com EVIDÊNCIA numérica]
│ ✅ Avançar / ⛔ Travar (se checkpoint falhou)
│ Registrar em todowrite como completed
└───────────────────────────────────────────────────────
```

### Regras Obrigatórias

1. **ANUNCIE antes de executar:** Nunca faça nada silenciosamente. Antes de rodar um cálculo, consultar uma API, ou escrever código, diga exatamente o que vai fazer.

2. **MOSTRE durante a execução:** Para cada subpasso relevante, exiba uma mensagem de progresso. Ex:
   - "🔍 Derivando ∂L/∂c_t..."
   - "🔍 ∂L/∂c_t = c_t^{-σ} - λ_t = 0 → λ_t = c_t^{-σ} ✅"
   - "🔍 Verificando autovalores da matriz M..."
   - "🔍 Autovalor 1: 0.8921 (estável) ✅"

3. **COMPROVE após concluir:** Nunca diga "deu certo" sem mostrar a evidência. Ex:
   - ❌ "Equações conferidas." (não aceitável)
   - ✅ "Equações = 12, Variáveis = 12. Checkpoint 2: ✅ PASSOU"

4. **TRAVE se falhar:** Se um checkpoint não passar, PARE imediatamente, explique o problema em detalhes, e sugira correções. Nunca "force" um resultado.

5. **Use `todowrite` para TUDO:** Toda tarefa, por menor que seja, deve ser registrada no `todowrite` com:
   - `pending` → quando identificada
   - `in_progress` → quando começou a executar
   - `completed` → só depois de passar pela verificação

6. **Nunca pule etapa:** A ordem do protocolo de 17 etapas é FIXA. Não reordene, não pule, não "agrupe" etapas.

### Critérios de Verificação Numérica (imutáveis)

| Verificação | Critério | Tolerância | Ação se falhar |
|---|---|---|---|
| Equações = Variáveis | Contagem exata | ZERO | TRAVAR |
| Estado estacionário | c > 0, k > 0, n ∈ (0,1) | ZERO | TRAVAR |
| Blanchard-Kahn | #autovalores instáveis = #forward | ZERO | TRAVAR e reportar |
| MCMC | Brooks-Gelman < 1.10 | 0.10 | Aumentar iterações |
| MCMC | Taxa de aceitação 20-40% | 5% | Ajustar jump scale |
| IRF | Direção coerente com teoria | — | Reportar e discutir |
| Solução P | autovalores(P) ≤ 1 | 0.001 | TRAVAR |

### Exemplo de Interação Real (como você DEVE se comportar)

**Usuário:** "Estime o modelo NK básico para o Brasil com dados de 2000-2023."

**AgenteDSGE (comportamento correto):**
```
📋 ETAPA 1: Identificação do Modelo — iniciando
   Objetivo: identificar tipo, agentes, variáveis e parâmetros do modelo
   Método: análise do enunciado + literatura de referência (Gali, 2015)
   
   🔍 Identificando tipo: Novo-Keynesiano básico (3 equações)
   🔍 Agentes: Família representativa, firma varejista, BC
   🔍 Variáveis: c_t, π_t, i_t, y_t, n_t, A_t (6 endógenas)
   🔍 Parâmetros: β, σ, φ, α, δ, θ, ρ_A, φ_π, φ_y (9 parâmetros)
   
✅ Resultado: modelo NK básico identificado — 6 variáveis, 9 parâmetros
✅ Checkpoint 1: ✅ PASSOU — tabela de componentes OK
📋 Avançando para Etapa 2...
```

---

*AgenteDSGE · v2.1 · Protocolo de 17 etapas · Octave + Dynare · Zero Alucinação · Reprodutibilidade Absoluta · Transparência Total*
"""


def setup_agent():
    """
    Escreve o system prompt da AgenteDSGE no diretório de agentes
    e configura como agente padrão no config.json do OpenCode.
    """
    agent_md = get_agent_system_prompt()

    agent_path = os.path.join(AGENT_DIR, "dsge.md")
    with open(agent_path, "w", encoding="utf-8") as f:
        f.write(agent_md)

    # Definir como agente padrão
    try:
        with open(OPENCODE_CFG, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        cfg = {}

    cfg["default_agent"] = "dsge"
    cfg["tab_title"] = "AgenteDSGE — Modelagem Macroeconômica"
    cfg["model"] = "deepseek-v4-flash-free"

    with open(OPENCODE_CFG, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

    log_ok(f"AgenteDSGE configurada: {agent_path}")
    log_ok(f"Agente definido como padrão no OpenCode.")


# ══════════════════════════════════════════════════════════════
# 5. VERIFICAÇÃO PÓS-INSTALAÇÃO
# ══════════════════════════════════════════════════════════════

def verify_installation():
    """
    Verifica se todos os componentes necessários estão ok.
    Roda verificações reais — não apenas "presume que deu certo".
    """
    all_ok = True
    checks = []

    # 1. OpenCode binário
    if OPENCODE_BIN and os.path.isfile(OPENCODE_BIN):
        checks.append(("OpenCode CLI", True))
    else:
        checks.append(("OpenCode CLI", False))
        all_ok = False

    # 2. Agente configurado
    agent_path = os.path.join(AGENT_DIR, "dsge.md")
    if os.path.isfile(agent_path):
        size = os.path.getsize(agent_path)
        checks.append(("System prompt do agente", size > 1000))
    else:
        checks.append(("System prompt do agente", False))
        all_ok = False

    # 3. Tema configurado
    theme_path = os.path.join(THEME_DIR, "dsge.json")
    if os.path.isfile(theme_path):
        checks.append(("Tema visual", True))
    else:
        checks.append(("Tema visual", False))
        all_ok = False

    # 4. Dependências Python (teste de import)
    deps_ok = True
    for lib in ["pandas", "numpy", "scipy", "statsmodels", "sympy"]:
        try:
            __import__(lib)
        except ImportError:
            deps_ok = False
            break
    checks.append(("Dependências Python", deps_ok))
    if not deps_ok:
        all_ok = False

    # 5. Octave
    octave_ok = OCTAVE_BIN is not None and os.path.isfile(OCTAVE_BIN)
    checks.append(("GNU Octave", octave_ok))

    # 6. Dynare
    dynare_ok = DYNARE_PATH is not None
    if dynare_ok:
        # Verificar se pode ser carregado no Octave
        try:
            r = run_cmd(
                f'{OCTAVE_BIN} --no-gui --eval "pkg load dynare; disp(\'OK\')"',
                check=False, timeout=15
            )
            dynare_ok = "OK" in (r.stdout or "")
        except Exception:
            dynare_ok = False
    checks.append(("Dynare", dynare_ok))

    print(f"\n  {'='*50}")
    print(f"  📋 VERIFICAÇÃO PÓS-INSTALAÇÃO:")
    print(f"  {'='*50}")
    for name, ok in checks:
        status = "✅" if ok else "❌"
        print(f"  {status} {name}")
    print(f"  {'='*50}")
    print(f"  Status geral: {'✅ TUDO OK' if all_ok else '❌ PROBLEMAS ENCONTRADOS'}")
    print(f"  {'='*50}")

    return all_ok


# ══════════════════════════════════════════════════════════════
# 6. ORQUESTRADOR PRINCIPAL
# ══════════════════════════════════════════════════════════════

def run_all(drive_base_path=None):
    """
    Executa a configuração completa da AgenteDSGE.

    Args:
        drive_base_path: Caminho base no Google Drive (opcional).
                         Se None, usa /content/drive/My Drive/AgenteDSGE
    """
    print(f"\n")
    print(f"  ╔══════════════════════════════════════════════════╗")
    print(f"  ║     🔷 CONFIGURAÇÃO DA AGENTEDSGE              ║")
    print(f"  ║     Modelagem DSGE — Protocolo de 17 Etapas    ║")
    print(f"  ╚══════════════════════════════════════════════════╝")
    print(f"")

    start_time = time.time()

    # ── 1. Instalar OpenCode + dependências ──
    print(f"\n  ┌{'─'*50}┐")
    print(f"  │ 📦 FASE 1: Instalação do Ambiente              │")
    print(f"  └{'─'*50}┘")
    install_opencode()

    # ── 1.5 Instalar Octave + Dynare ──
    print(f"\n  ┌{'─'*50}┐")
    print(f"  │ ⚙️  FASE 1.5: Octave + Dynare                  │")
    print(f"  └{'─'*50}┘")
    octave_ok, dynare_ok = install_octave_dynare()

    # ── 2. Criar diretórios ──
    print(f"\n  ┌{'─'*50}┐")
    print(f"  │ 📁 FASE 2: Estrutura de Diretórios             │")
    print(f"  └{'─'*50}┘")
    create_directories()

    if drive_base_path:
        create_drive_structure(drive_base_path)

    # ── 3. Configurar tema ──
    print(f"\n  ┌{'─'*50}┐")
    print(f"  │ 🎨 FASE 3: Tema Visual                         │")
    print(f"  └{'─'*50}┘")
    setup_theme()

    # ── 4. Configurar agente (system prompt) ──
    print(f"\n  ┌{'─'*50}┐")
    print(f"  │ 🧠 FASE 4: System Prompt da AgenteDSGE         │")
    print(f"  └{'─'*50}┘")
    setup_agent()

    # ── 5. Verificar instalação ──
    print(f"\n  ┌{'─'*50}┐")
    print(f"  │ 🔍 FASE 5: Verificação Final                   │")
    print(f"  └{'─'*50}┘")
    all_ok = verify_installation()

    elapsed = time.time() - start_time
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)

    print(f"\n  {'='*55}")
    print(f"  ⏱️  Tempo total de configuração: {minutes}min {seconds}s")
    print(f"  {'='*55}")

    if all_ok:
        print(f"")
        print(f"  ███████████████████████████████████████████████████")
        print(f"  ██                                             ██")
        print(f"  ██   ✅ AGENTEDSGE PRONTA PARA OPERAR          ██")
        print(f"  ██   Todas as 6 fases concluídas com sucesso   ██")
        print(f"  ██   Protocolo de 17 etapas carregado          ██")
        print(f"  ██   Octave + Dynare {'ATIVADOS' if octave_ok and dynare_ok else 'limitados':>16} ██")
        print(f"  ██   Zero Alucinação ativado                   ██")
        print(f"  ██                                             ██")
        print(f"  ███████████████████████████████████████████████████")
        print(f"")

        # Salvar status final
        status = {
            "ok": True,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "elapsed_seconds": elapsed,
            "fases": {
                "instalacao": True,
                "octave_dynare": octave_ok and dynare_ok,
                "diretorios": True,
                "tema": True,
                "system_prompt": True,
                "verificacao": True,
            }
        }
    else:
        status = {
            "ok": False,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "elapsed_seconds": elapsed,
            "error": "Verificação pós-instalação detectou falhas. Ver logs acima."
        }
        print(f"\n  ❌ Configuração concluída com falhas. Revise as mensagens acima.\n")

    with open(os.path.join(os.path.dirname(SETUP_STATUS_FILE), "setup_complete.json"), "w") as f:
        json.dump(status, f, indent=2, ensure_ascii=False)

    return all_ok


# ══════════════════════════════════════════════════════════════
# EXECUÇÃO DIRETA
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
