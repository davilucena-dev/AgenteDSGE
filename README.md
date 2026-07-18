# 🔷 AgenteDSGE — Modelagem Macroeconômica com Rigor Científico

**Agente de IA autônomo especializado em modelos DSGE (Dynamic Stochastic General Equilibrium).**

Conduz **todas as 17 etapas** do protocolo — da identificação do modelo à entrega do relatório final — com **Zero Alucinação**, reprodutibilidade absoluta e validação em cada etapa.

---

## 🧠 O que o Agente Faz

| Etapa | Descrição |
|---|---|
| **1-6** | Estrutura Teórica — Identifica o modelo, organiza equações, deriva FOCs |
| **7-12** | Solução Numérica — Estado estacionário, calibração, linearização, BK |
| **13-14** | Estimação — Gera código Dynare, executa MCMC Bayesiano via Octave |
| **15-17** | Validação — Diagnóstico MCMC, IRFs, relatório final |

---

## 🛡️ Princípios de Operação

1. **Zero Alucinação** — O agente prefere dizer "NÃO SEI" a fabricar um resultado
2. **Cada parâmetro tem fonte** — Nada é "chutado", tudo é referenciado
3. **Checkpoints obrigatórios** — Cada etapa só avança após validação
4. **Full audit trail** — Cada decisão documentada em log
5. **Dados reais** — IBGE, BCB/SGS, IPEADATA para modelos brasileiros

---

## 🚀 Como Iniciar (Google Colab)

### 1. Abra o Google Colab

Acesse [colab.research.google.com](https://colab.research.google.com) e crie um novo notebook.

### 2. Cole esta célula e execute

```python
import os, sys, subprocess, shutil

REPO_URL = "https://github.com/gustavo-bbraga/AgenteDSGE.git"
WORK_DIR = "/tmp/agentedsge"
CLONE_DIR = os.path.join(WORK_DIR, "repo")

print("=" * 60)
print("  🔷 INICIANDO AGENTEDSGE v2.1")
print("  Modelagem DSGE · Protocolo 17 Etapas")
print("  Octave + Dynare · Zero Alucinação")
print("=" * 60)

print("\n  ⏳ Preparando ambiente...")
if os.path.exists(WORK_DIR):
    shutil.rmtree(WORK_DIR)
os.makedirs(WORK_DIR, exist_ok=True)

print(f"  📥 Baixando AgenteDSGE de: {REPO_URL}")
result = subprocess.run(
    ["git", "clone", "--depth", "1", REPO_URL, CLONE_DIR],
    capture_output=True, text=True,
)
if result.returncode != 0:
    print(f"  ❌ Falha ao clonar: {result.stderr.strip()}")
    raise RuntimeError(f"git clone falhou: {result.stderr[:300]}")

print("  ✅ Repositório clonado com sucesso.")

os.chdir(CLONE_DIR)
sys.path.insert(0, CLONE_DIR)
print(f"  📁 Diretório de trabalho: {CLONE_DIR}")

print("\n  🚀 Iniciando AgenteDSGE...")
print("  ⏳ Isso pode levar ~2 minutos na primeira vez...\n")

from main import run
run()
```

### 3. O que acontece em seguida

```
① Autenticação Google Drive  →  monta e pede permissões
② Instalação OpenCode        →  motor do agente
③ Dependências Python        →  pandas, numpy, scipy, sympy...
④ Octave + Dynare            →  engine de cálculo DSGE (FASE 1.5)
⑤ Instalação de skills       →  6 locais + 8 externas
⑥ Interface web              →  terminal + botão de acesso
⑦ Botão "ABRIR AGENTEDSGE"   →  clica e abre o chatbot
```

### 4. Conecte um provedor de IA

Na interface que abrir, clique em **+ provedor IA** e insira sua chave de API (Anthropic, OpenAI, Groq, etc.).

---

## 📁 Estrutura Criada no Google Drive

```
Meu Drive/
└── AgenteDSGE/
    ├── dados/
    │   ├── brutos/           ← Microdados e séries baixados
    │   └── processados/      ← Séries tratadas
    ├── parametros/
    │   ├── calibrados/       ← Parâmetros com fontes
    │   └── estimados/        ← Resultados MCMC
    ├── modelos/
    │   ├── equacoes/         ← Sistemas de equações
    │   └── linearizados/     ← Versões log-linearizadas
    ├── resultados/
    │   ├── irfs/             ← Funções de Resposta ao Impulso
    │   ├── decomposicoes/    ← Decomposição de variância
    │   └── mcmc/             ← Diagnósticos de convergência
    ├── codigo_dynare/        ← Arquivos .mod
    └── auditoria/            ← Logs de decisão
```

---

## 💬 Exemplos de Comandos

```
"Estime o modelo NK básico para o Brasil (2000-2023) com dados do BCB."

"Derive as FOCs de um modelo RBC e verifique Blanchard-Kahn."

"Calibre os parâmetros para o Brasil usando IBGE e IPEADATA."

"Gere o código Dynare para o modelo com 3 equações e estime por MCMC."

"Faça a decomposição histórica do PIB brasileiro nos últimos 10 anos."
```

---

## 📦 Skills Inclusas

### Locais (6 — nativas, instaladas inline)

| Skill | Função |
|---|---|
| `gestao-drive-dsge` | Cria estrutura de pastas padronizada |
| `derivacao-focs` | Derivação simbólica de FOCs (SymPy) |
| `algebra-linear-dsge` | Decomposição QZ, BK, lei de movimento |
| `utils-dynare` | Geração de código .mod |
| `calibracao-fontes` | Consulta IBGE, BCB, IPEADATA |
| `validacao-dsge` | Checkpoints de 7 etapas |

### Externas (8 — com especificações PDF)

| Skill | Função | Status |
|---|---|---|
| `skill-estimacao-bayesiana-dsge` | MCMC, Brooks-Gelman, posteriores | 📄 PDF spec |
| `skill-calibracao-dados-br` | Dados IBGE/BCB/IPEA | 📄 PDF spec |
| `skill-geracao-dynare` | .mod avançado | 📄 PDF spec |
| `skill-modelos-base-dsge` | Modelos prontos (RBC, NK) | 📄 PDF spec |
| `skill-irf-analise` | Gráficos IRF profissionais | 📄 PDF spec |
| `skill-validacao-dsge` | Testes de robustez | 📄 PDF spec |
| `skill-algebra-linear-dsge` | Klein/Sims/QZ | 📄 PDF spec |
| `skill-octave-dsge` | Integração Python → Octave → Dynare | 📄 PDF spec |

---

## ⚙️ Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────┐
│  GITHUB (repositório)              ── o "cérebro"       │
│                                                         │
│  main.py                Orquestrador principal          │
│  setup_dependencies.py  Instala OpenCode + deps + tema  │
│  setup_skills.py        Instala skills locais/externas  │
│  launch_app.py          Interface web + botão de start  │
│  cell_colab.py          Célula Colab completa           │
│  README.md              Documentação + célula Colab     │
└──────────────────────┬──────────────────────────────────┘
                       │ git clone
                       ▼
┌─────────────────────────────────────────────────────────┐
│  COLAB (notebook)                   ── o "start button" │
│                                                         │
│  1 célula → git clone + from main import run + run()   │
│             ↓                                           │
│        FASE 1:   Instalação do Ambiente                 │
│        FASE 1.5: Octave + Dynare (NOVO)                │
│        FASE 2:   Estrutura de Diretórios                │
│        FASE 3:   Tema Visual                            │
│        FASE 4:   System Prompt                          │
│        FASE 5:   Verificação Final                      │
│             ↓                                           │
│        Botão "ABRIR AGENTEDSGE"                         │
│             ↓                                           │
│        Nova guia → OpenCode chatbot                     │
└─────────────────────────────────────────────────────────┘
```

---

## 🧪 Requisitos

- **Google Colab** (gratuito)
- **Conta Google** (para Drive)
- **API Key** de provedor de IA (Anthropic, OpenAI, etc.)
- **Navegador:** Google Chrome (recomendado)

---

## ℹ️ Informações Importantes

- ⏱️ **Tempo de inicialização:** ~3-5 minutos (primeira vez)
- 🌐 **Internet:** Conexão estável obrigatória
- 💾 **Dados:** Ficam salvos em `Meu Drive/AgenteDSGE/`
- 🔒 **Privacidade:** O agente nunca envia dados para fora do seu Drive
- 🛑 **Rigor:** O agente **PÁRA** se encontrar inconsistência — não "força" resultados
- ⚙️ **Octave + Dynare:** Instalados automaticamente na FASE 1.5

---

## 📄 Licença

MIT — uso livre e aberto para fins acadêmicos e de pesquisa.

---

*AgenteDSGE · v2.1 · Protocolo de 17 Etapas · Octave + Dynare · Zero Alucinação · Reprodutibilidade Absoluta*

## Créditos
# Davi Lucena da Silva - Doutorando em Economia Aplicada (UFV)
