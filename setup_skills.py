#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║  setup_skills.py — AgenteDSGE                              ║
║  Instalação de skills locais e remotas                     ║
║                                                            ║
║  Etapa 2 de 6: Habilidades especializadas do agente        ║
║  Versão: 2.0 — Julho 2026                                  ║
╚══════════════════════════════════════════════════════════════╝

Responsabilidades:
  1. Criar skills locais (leves, inline — sem dependência externa)
  2. Clonar skills externas (repositórios GitHub especializados)
  3. Verificar integridade de cada skill instalada
  4. Reportar falhas sem mascarar erros
"""

import os
import shutil
import subprocess
import json
import time
import sys

# ── Barra de progresso otimizada para Colab ──
try:
    from tqdm.notebook import tqdm
except ImportError:
    from tqdm import tqdm


# ══════════════════════════════════════════════════════════════
# CONSTANTES
# ══════════════════════════════════════════════════════════════

SKILLS_DIR = os.path.expanduser("~/.agents/skills")
SETUP_LOG  = os.path.expanduser("~/.agents/skills_install_log.json")


# ══════════════════════════════════════════════════════════════
# SKILLS EXTERNAS (REPOSITÓRIOS GITHUB SEPARADOS)
# ══════════════════════════════════════════════════════════════
# INSTRUÇÕES:
#   Cada skill externa é um repositório GitHub independente.
#   Para adicionar uma nova: inclua uma tupla (url, nome_da_pasta)
#   na lista REMOTE_SKILLS abaixo.
#
#   CONVENÇÃO DE NOMES:
#     - Repositório: "skill-<funcionalidade>-dsge"
#     - Pasta local: mantém o nome do repositório (sem .git)
#
#   ESTRUTURA MÍNIMA DE CADA SKILL REMOTA:
#     skill-nome/
#     ├── SKILL.md       ← Obrigatório: instruções para o agente
#     ├── __init__.py     ← Opcional: se for pacote Python
#     └── ... demais arquivos da skill
#
# ══════════════════════════════════════════════════════════════

REMOTE_SKILLS = [
    # ──────────────────────────────────────────────────────────
    # SKILL 1 — Estimação Bayesiana de DSGE
    # ──────────────────────────────────────────────────────────
    # Faz: MCMC (Metropolis-Hastings), diagnóstico Brooks-Gelman,
    #      cálculo de posteriores, HPDI, comparação de modelos.
    # Dados: não requer dados externos — opera sobre o .mod.
    # Status: ⬜ não implementada — placeholder para desenvolvimento.
    # URL_EXAMPLE: "https://github.com/usuario/skill-estimacao-bayesiana-dsge.git"
    # ──────────────────────────────────────────────────────────

    # ──────────────────────────────────────────────────────────
    # SKILL 2 — Calibração com Dados Brasileiros
    # ──────────────────────────────────────────────────────────
    # Faz: consulta IBGE/SIDRA, BCB/SGS, IPEADATA para extrair
    #      parâmetros de calibração (α, β, δ, etc.).
    # Dados: IBGE (SCN, PNAD), BCB (SGS), IPEADATA.
    # Status: ⬜ não implementada — placeholder para desenvolvimento.
    # URL_EXAMPLE: "https://github.com/usuario/skill-calibracao-dados-br.git"
    # ──────────────────────────────────────────────────────────

    # ──────────────────────────────────────────────────────────
    # SKILL 3 — Geração de Código Dynare
    # ──────────────────────────────────────────────────────────
    # Faz: a partir do sistema linearizado, monta o arquivo .mod
    #      completo com var, varexo, parameters, model, estimation.
    # Dados: não requer — gera código text.
    # Status: ⬜ não implementada — placeholder para desenvolvimento.
    # URL_EXAMPLE: "https://github.com/usuario/skill-geracao-dynare.git"
    # ──────────────────────────────────────────────────────────

    # ──────────────────────────────────────────────────────────
    # SKILL 4 — Biblioteca de Modelos DSGE Base
    # ──────────────────────────────────────────────────────────
    # Faz: fornece modelos prontos (RBC, NK, NK aberto, fiscal,
    #      financeiro) para usar como ponto de partida.
    # Dados: parâmetros calibrados e equações pré-definidas.
    # Status: ⬜ não implementada — placeholder para desenvolvimento.
    # URL_EXAMPLE: "https://github.com/usuario/skill-modelos-base-dsge.git"
    # ──────────────────────────────────────────────────────────

    # ──────────────────────────────────────────────────────────
    # SKILL 5 — Análise de IRFs e Decomposições
    # ──────────────────────────────────────────────────────────
    # Faz: gráficos profissionais de IRF, decomposição de variância,
    #      decomposição histórica, previsão, contrafactuais.
    # Dados: saída do Dynare ou das matrizes P e Q.
    # Status: ⬜ não implementada — placeholder para desenvolvimento.
    # URL_EXAMPLE: "https://github.com/usuario/skill-irf-analise.git"
    # ──────────────────────────────────────────────────────────

    # ──────────────────────────────────────────────────────────
    # SKILL 6 — Validação e Diagnóstico de DSGE
    # ──────────────────────────────────────────────────────────
    # Faz: testes de robustez, análise de identificação, cheque
    #      de momentos, validação cruzada, testes de especificação.
    # Dados: resultados da estimação + dados observados.
    # Status: ⬜ não implementada — placeholder para desenvolvimento.
    # URL_EXAMPLE: "https://github.com/usuario/skill-validacao-dsge.git"
    # ──────────────────────────────────────────────────────────

    # ──────────────────────────────────────────────────────────
    # SKILL 7 — Álgebra Linear para DSGE
    # ──────────────────────────────────────────────────────────
    # Faz: decomposição QZ, solução de Klein/Sims, verificação
    #      de Blanchard-Kahn, forma matricial.
    # Dados: sistema linearizado do modelo.
    # Status: ⬜ não implementada — placeholder para desenvolvimento.
    # URL_EXAMPLE: "https://github.com/usuario/skill-algebra-linear-dsge.git"
    # ──────────────────────────────────────────────────────────
]

# ── NOTA PARA O DESENVOLVEDOR ──
# Para ATIVAR uma skill externa, descomente a tupla correspondente
# e substitua URL_EXAMPLE pela URL real do repositório.
# Exemplo ativo:
#   ("https://github.com/meuuser/skill-estimacao-bayesiana-dsge.git",
#    "estimacao-bayesiana-dsge"),
#
# O nome da pasta (segundo elemento) DEVE ser o mesmo nome do
# repositório (sem o .git) para consistência.
# ══════════════════════════════════════════════════════════════


# ══════════════════════════════════════════════════════════════
# MENSAGENS TEMÁTICAS
# ══════════════════════════════════════════════════════════════

SKILL_MESSAGES = [
    "📈 Instalando motor de derivação de FOCs...",
    "📐 Configurando solvers de estado estacionário...",
    "🔧 Preparando decomposição QZ...",
    "📊 Calibrando parâmetros via dados oficiais...",
    "⚙️  Montando gerador de código Dynare...",
    "📉 Configurando analisador de IRFs...",
    "🎯 Instalando diagnósticos MCMC...",
]

_joke_index = 0

def next_message():
    global _joke_index
    msg = SKILL_MESSAGES[_joke_index % len(SKILL_MESSAGES)]
    _joke_index += 1
    return msg


# ══════════════════════════════════════════════════════════════
# UTILITÁRIOS
# ══════════════════════════════════════════════════════════════

def log_ok(msg):
    print(f"     ✅ {msg}")

def log_warn(msg):
    print(f"     ⚠️  {msg}")

def log_fail(msg):
    print(f"     ❌ {msg}")


def run_git_clone(repo_url, dest_path, timeout=120):
    """
    Clona um repositório Git com profundidade 1.
    Retorna (success: bool, error_msg: str).
    """
    try:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, dest_path],
            capture_output=True, text=True, timeout=timeout
        )
        if result.returncode == 0:
            return True, ""
        else:
            return False, result.stderr.strip()[-500:]
    except subprocess.TimeoutExpired:
        return False, "Timeout após 120s"
    except Exception as e:
        return False, str(e)[:500]


def verify_skill_folder(folder_path):
    """
    Verifica se uma pasta de skill tem o mínimo necessário.
    Retorna (ok: bool, diagnostics: dict).
    """
    diag = {"existe": os.path.isdir(folder_path)}
    if not diag["existe"]:
        return False, diag

    diag["tem_skilmd"]  = os.path.isfile(os.path.join(folder_path, "SKILL.md"))
    diag["tem_init"]    = os.path.isfile(os.path.join(folder_path, "__init__.py"))
    diag["tamanho_kb"]  = round(
        sum(os.path.getsize(os.path.join(dp, f))
            for dp, _, fn in os.walk(folder_path)
            for f in fn) / 1024, 1
    ) if os.path.isdir(folder_path) else 0

    ok = diag["existe"] and diag["tem_skilmd"]
    return ok, diag


# ══════════════════════════════════════════════════════════════
# SKILLS LOCAIS (CRIADAS INLINE)
# ══════════════════════════════════════════════════════════════

def create_local_skills(pbar):
    """
    Cria as skills que rodam localmente, sem depender de repositório externo.
    Cada skill é uma pasta com SKILL.md e, opcionalmente, código Python base.
    """
    os.makedirs(SKILLS_DIR, exist_ok=True)

    # ──────────────────────────────────────────────────────────
    # SKILL LOCAL 1: Gestão do Drive DSGE
    # ──────────────────────────────────────────────────────────
    pbar.set_description("📁 Instalando: gestao-drive-dsge")
    skill_dir = os.path.join(SKILLS_DIR, "gestao-drive-dsge")
    os.makedirs(skill_dir, exist_ok=True)

    with open(os.path.join(skill_dir, "SKILL.md"), "w", encoding="utf-8") as f:
        f.write("""# Skill: Gestão do Drive DSGE

Cria e organiza a estrutura de pastas para projetos DSGE no Google Drive.

## Estrutura Criada
```
AgenteDSGE/
├── dados/
│   ├── brutos/           ← Microdados e séries temporais baixados
│   └── processados/      ← Séries tratadas e ajustadas
├── parametros/
│   ├── calibrados/       ← Parâmetros com fontes documentadas
│   └── estimados/        ← Resultados de estimação MCMC
├── modelos/
│   ├── equacoes/         ← Sistemas de equações do modelo
│   └── linearizados/     ← Versões log-linearizadas
├── resultados/
│   ├── irfs/             ← Funções de Resposta ao Impulso
│   ├── decomposicoes/    ← Decomposições de variância/histórica
│   └── mcmc/             ← Diagnósticos de convergência
├── codigo_dynare/        ← Arquivos .mod gerados
└── auditoria/            ← Logs de decisão do agente
```

## Uso
Chame esta skill no início de cada projeto para garantir a estrutura padronizada.
""")
    time.sleep(0.3)
    pbar.update(1)

    # ──────────────────────────────────────────────────────────
    # SKILL LOCAL 2: Derivação Simbólica de FOCs
    # ──────────────────────────────────────────────────────────
    pbar.set_description("📐 Instalando: derivacao-focs")
    skill_dir = os.path.join(SKILLS_DIR, "derivacao-focs")
    os.makedirs(skill_dir, exist_ok=True)

    with open(os.path.join(skill_dir, "SKILL.md"), "w", encoding="utf-8") as f:
        f.write("""# Skill: Derivação Simbólica de FOCs

Usa SymPy para derivar automaticamente as Condições de Primeira Ordem
a partir do Lagrangeano do modelo DSGE.

## Funcionalidades
- Definição simbólica do Lagrangeano por agente
- Derivação parcial automática para cada variável de controle
- Eliminação de multiplicadores de Lagrange
- Simplificação algébrica do sistema reduzido
- Exportação do sistema de equações em formato TeX e Python

## Exemplo
```python
from sympy import symbols, diff, solve

# Definição simbólica
c, n, k, lam, beta, sigma, phi = symbols('c n k lam beta sigma phi')
U = c**(1-sigma)/(1-sigma) - n**(1+phi)/(1+phi)
L = U - lam * (c + k - ...)

# FOC
dL_dc = diff(L, c)
solve(dL_dc, lam)
```

## Limitações
- Modelos com expectativas racionais requerem tratamento manual do operador E_t.
- A simplificação final pode exigir intervenção do usuário.
""")
    time.sleep(0.3)
    pbar.update(1)

    # ──────────────────────────────────────────────────────────
    # SKILL LOCAL 3: Álgebra Linear para DSGE
    # ──────────────────────────────────────────────────────────
    pbar.set_description("🔢 Instalando: algebra-linear-dsge")
    skill_dir = os.path.join(SKILLS_DIR, "algebra-linear-dsge")
    os.makedirs(skill_dir, exist_ok=True)

    with open(os.path.join(skill_dir, "SKILL.md"), "w", encoding="utf-8") as f:
        f.write("""# Skill: Álgebra Linear para DSGE

Operações matriciais necessárias para solução de modelos DSGE.

## Funcionalidades
- Montagem das matrizes A, B, C, D (forma canônica)
- Decomposição QZ (Generalized Schur) para solução do modelo
- Verificação das condições de Blanchard-Kahn
- Cálculo da lei de movimento: x_t = P x_{t-1} + Q ε_t
- Decomposição de variância e IRFs a partir de P e Q

## Dependências
- numpy, scipy (já instaladas via setup_dependencies.py)

## Verificações Obrigatórias
1. det(I - A) ≠ 0 antes de inverter
2. Número de autovalores instáveis = número de variáveis forward
3. Matriz P com todos os autovalores ≤ 1 em módulo
4. Matriz Q real (não complexa)
""")
    time.sleep(0.3)
    pbar.update(1)

    # ──────────────────────────────────────────────────────────
    # SKILL LOCAL 4: Utilitários Dynare
    # ──────────────────────────────────────────────────────────
    pbar.set_description("⚙️  Instalando: utils-dynare")
    skill_dir = os.path.join(SKILLS_DIR, "utils-dynare")
    os.makedirs(skill_dir, exist_ok=True)

    with open(os.path.join(skill_dir, "SKILL.md"), "w", encoding="utf-8") as f:
        f.write("""# Skill: Utilitários Dynare

Geração e manipulação de arquivos .mod do Dynare.

## Funcionalidades
- Template de arquivo .mod com todas as seções obrigatórias
- Inserção automática de equações linearizadas
- Configuração de estimated_params com prioris
- Configuração de shocks (variâncias dos choques)
- Configuração de estimation (nº cadeias, iterações, scale)
- Comandos stoch_simul para IRFs e momentos

## Seções Obrigatórias do .mod
1. var
2. varexo
3. parameters
4. model (linear)
5. steady_state_model
6. shocks
7. estimated_params
8. estimation
9. stoch_simul

## Uso no Dynare
```matlab
dynare modelo.mod nograph
```
""")
    time.sleep(0.3)
    pbar.update(1)

    # ──────────────────────────────────────────────────────────
    # SKILL LOCAL 5: Calibração e Fontes
    # ──────────────────────────────────────────────────────────
    pbar.set_description("📊 Instalando: calibracao-fontes")
    skill_dir = os.path.join(SKILLS_DIR, "calibracao-fontes")
    os.makedirs(skill_dir, exist_ok=True)

    with open(os.path.join(skill_dir, "SKILL.md"), "w", encoding="utf-8") as f:
        f.write("""# Skill: Calibração e Fontes de Dados

Consulta fontes oficiais brasileiras para calibração de parâmetros DSGE.

## Fontes Disponíveis
| Fonte | Dados | API |
|---|---|---|
| IBGE/SIDRA | Contas Nacionais, PNAD, PIB | sidrapy |
| BCB/SGS | Selic, IPCA, câmbio, crédito | ipeadatapy |
| IPEADATA | Séries macroeconômicas históricas | ipeadatapy |
| FGV/IBRE | Expectativas, sondagens | — |

## Parâmetros Típicos por Fonte
- α (participação do capital): IBGE/SCN → contas nacionais
- δ (depreciação): IBGE/SCN → formação bruta de capital fixo
- β (fator de desconto): Selic real média (BCB/SGS)
- ρ_A (persistência tecnológica): estimar via AR(1) do PIB (IBGE)

## Regra
NUNCA usar parâmetro sem documentar: valor, fonte, justificativa.
""")
    time.sleep(0.3)
    pbar.update(1)

    # ──────────────────────────────────────────────────────────
    # SKILL LOCAL 6: Validação de Modelos DSGE
    # ──────────────────────────────────────────────────────────
    pbar.set_description("🎯 Instalando: validacao-dsge")
    skill_dir = os.path.join(SKILLS_DIR, "validacao-dsge")
    os.makedirs(skill_dir, exist_ok=True)

    with open(os.path.join(skill_dir, "SKILL.md"), "w", encoding="utf-8") as f:
        f.write("""# Skill: Validação de Modelos DSGE

Checklist automatizado de validação para cada etapa do protocolo.

## Checkpoints Implementados
| Etapa | Checkpoint | Critério |
|---|---|---|
| 2 | Equações = Variáveis | Contagem exata |
| 7 | Estado Estacionário | c>0, k>0, n∈(0,1), r>0 |
| 11 | Blanchard-Kahn | #autov inst = #forward |
| 12 | Solução | P estável, Q real |
| 15 | MCMC | Brooks-Gelman < 1.10 |
| 16 | IRFs | Coerência teórica |
| 17 | Final | 10/10 itens aprovados |

## Uso
```python
from validacao_dsge import check_all
relatorio = check_all(modelo, params, resultados)
```
""")
    time.sleep(0.3)
    pbar.update(1)


# ══════════════════════════════════════════════════════════════
# ORQUESTRADOR DE INSTALAÇÃO
# ══════════════════════════════════════════════════════════════

def install_skills():
    """
    Instala todas as skills da AgenteDSGE:
      1. Skills locais (6) — criadas inline neste arquivo
      2. Skills externas (N) — clonadas de repositórios GitHub
    """
    os.chdir("/tmp")

    print(f"\n")
    print(f"  ┌{'─'*50}┐")
    print(f"  │ 🔧 INSTALANDO SKILLS DA AGENTEDSGE             │")
    print(f"  └{'─'*50}┘")
    print(f"")

    # ── Contagem total para barra de progresso ──
    num_locais = 6  # skills locais definidas acima
    num_remotas = len(REMOTE_SKILLS)
    total_skills = num_locais + num_remotas

    skills_ok = []
    skills_falha = []

    with tqdm(
        total=total_skills,
        desc="Iniciando...",
        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}]",
        colour='cyan',
        unit=' skill'
    ) as pbar:

        # ── 1. Skills Locais ──
        pbar.set_description("📁 Instalando skills locais")
        create_local_skills(pbar)

        for nome in ["gestao-drive-dsge", "derivacao-focs",
                      "algebra-linear-dsge", "utils-dynare",
                      "calibracao-fontes", "validacao-dsge"]:
            pasta = os.path.join(SKILLS_DIR, nome)
            ok, diag = verify_skill_folder(pasta)
            if ok:
                skills_ok.append(nome)
            else:
                skills_falha.append((nome, "pasta não encontrada ou sem SKILL.md"))

        # ── 2. Skills Externas ──
        if num_remotas == 0:
            pbar.set_description("⏭️  Skills externas: nenhuma ativa")
            time.sleep(0.5)
            pbar.update(0)  # não há o que contar
        else:
            for repo_url, name in REMOTE_SKILLS:
                pbar.set_description(f"🌐 Baixando: {name}")
                tmp = f"/tmp/skill_ext_{name}"

                # Limpa download anterior, se houver
                if os.path.exists(tmp):
                    shutil.rmtree(tmp)

                success, error = run_git_clone(repo_url, tmp)

                if success:
                    dest = os.path.join(SKILLS_DIR, name)
                    if os.path.exists(dest):
                        shutil.rmtree(dest)
                    shutil.copytree(tmp, dest, dirs_exist_ok=True)

                    ok, diag = verify_skill_folder(dest)
                    if ok:
                        skills_ok.append(name)
                        log_ok(f"{name} instalada ({diag['tamanho_kb']} KB)")
                    else:
                        skills_falha.append((name, f"verificação falhou: {diag}"))
                        log_fail(f"{name} instalada mas SKILL.md não encontrado")
                else:
                    skills_falha.append((name, error))
                    log_fail(f"{name} falhou ao clonar: {error[:100]}")

                time.sleep(0.3)
                pbar.update(1)

    # ── Relatório Final ──
    print(f"\n  {'='*55}")
    print(f"  📋 RELATÓRIO DE INSTALAÇÃO DE SKILLS")
    print(f"  {'='*55}")
    print(f"     ✅ Skills instaladas : {len(skills_ok)}")
    print(f"     ❌ Skills com falha  : {len(skills_falha)}")
    if skills_ok:
        print(f"     📌 Instaladas: {', '.join(skills_ok)}")
    if skills_falha:
        print(f"     ⚠️  Falhas:")
        for nome, erro in skills_falha:
            print(f"        • {nome}: {erro[:150]}")
    print(f"  {'='*55}")

    # ── Salvar log JSON ──
    log = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "total": total_skills,
        "sucesso": len(skills_ok),
        "falhas": len(skills_falha),
        "skills_ok": skills_ok,
        "skills_falha": [{"nome": n, "erro": e} for n, e in skills_falha],
        "remotas_ativas": num_remotas > 0,
        "remotas_lista": [n for _, n in REMOTE_SKILLS],
    }
    os.makedirs(os.path.dirname(SETUP_LOG), exist_ok=True)
    with open(SETUP_LOG, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)

    if skills_falha:
        print(f"\n  ⚠️   {len(skills_falha)} skill(s) com falha. O agente pode operar, "
              f"mas funcionalidades específicas podem estar indisponíveis.\n")
    else:
        print(f"\n  ✅ Todas as skills da AgenteDSGE instaladas com sucesso!\n")

    return len(skills_falha) == 0


# ══════════════════════════════════════════════════════════════
# EXECUÇÃO DIRETA
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    success = install_skills()
    sys.exit(0 if success else 1)
