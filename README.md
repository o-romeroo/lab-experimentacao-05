# lab-experimentacao-05
## Alunos: João Vitor Romero Sales e Lucas Randazzo

# 1. Desenho do Experimento

## A. Hipóteses Nula e Alternativa

### RQ1: Latência (tempo de resposta)
- **H0₁ (Hipótese Nula):** Não há diferença estatisticamente significativa entre a latência média das respostas REST e GraphQL para consultas equivalentes.
  - Formalmente: μ_REST = μ_GraphQL
- **H1₁ (Hipótese Alternativa):** Há diferença estatisticamente significativa entre as latências; espera-se que GraphQL apresente menor latência média em cenários de múltiplas requisições devido à redução do número de chamadas necessárias. 
  - Formalmente: μ_REST ≠ μ_GraphQL

### RQ2: Tamanho do Payload (bytes)
- **H0₂ (Hipótese Nula):** Não há diferença estatisticamente significativa entre o tamanho médio das respostas REST e GraphQL para consultas equivalentes. 
  - Formalmente: μ_payload_REST = μ_payload_GraphQL
- **H1₂ (Hipótese Alternativa):** Há diferença estatisticamente significativa; espera-se que GraphQL produza respostas menores quando o cliente solicita subconjunto de campos, reduzindo over-fetch presente em REST.
  - Formalmente: μ_payload_REST ≠ μ_payload_GraphQL

**Nota:** Como não garantimos a direção a priori para latência (pode depender da complexidade dos resolvers e condições de rede), usamos testes bicaudais.  Para tamanho de payload, há expectativa direcional (GraphQL menor), mas mantemos teste bicaudal para rigor científico.

---

## B. Variáveis Dependentes

| Variável | Descrição | Unidade | Tipo |
|----------|-----------|---------|------|
| `latency_total_s` | Tempo total de todas as requisições | segundos | Contínua |
| `latency_avg_s` | Latência média por requisição | segundos | Contínua |
| `latency_min_s` | Menor latência observada | segundos | Contínua |
| `latency_max_s` | Maior latência observada | segundos | Contínua |
| `latency_p95_s` | Percentil 95 da latência | segundos | Contínua |
| `payload_total_bytes` | Tamanho total do payload recebido | bytes | Contínua |
| `payload_avg_per_request_bytes` | Tamanho médio por requisição | bytes | Contínua |
| `payload_avg_per_repo_bytes` | Tamanho médio por repositório retornado | bytes | Contínua |
| `requests_count` | Número de requisições HTTP realizadas | inteiro | Discreta |

---

## C.  Variáveis Independentes

| Variável | Níveis | Descrição |
|----------|--------|-----------|
| **Tipo de API (Fator Principal)** | REST, GraphQL | Tecnologia de API sendo avaliada |
| **Tamanho do Dataset** | 100, 300, 1000 repositórios | Quantidade de repositórios Java populares consultados |
| **Período do Dia** | Madrugada, Manhã, Tarde, Noite | Momento da execução (para controle de variabilidade de rede) |

### Variáveis Controladas (Constantes)
- Linguagem de programação dos repositórios: **Java**
- Critério de ordenação: **Estrelas (decrescente)**
- Token de autenticação: **Mesmo token GitHub para todas as execuções**
- Ambiente de execução: **Mesmo hardware e sistema operacional**
- Delay entre requisições: **1 segundo**

---

## D.  Tratamentos

Cada tratamento representa uma combinação única dos fatores experimentais:

| ID | API | Dataset (repos) | Período | Descrição |
|----|-----|-----------------|---------|-----------|
| T1 | REST | 100 | Madrugada | Consulta REST pequena - madrugada |
| T2 | GraphQL | 100 | Madrugada | Consulta GraphQL pequena - madrugada |
| T3 | REST | 300 | Madrugada | Consulta REST média - madrugada |
| T4 | GraphQL | 300 | Madrugada | Consulta GraphQL média - madrugada |
| T5 | REST | 1000 | Madrugada | Consulta REST grande - madrugada |
| T6 | GraphQL | 1000 | Madrugada | Consulta GraphQL grande - madrugada |
| T7 | REST | 100 | Manhã | Consulta REST pequena - manhã |
| T8 | GraphQL | 100 | Manhã | Consulta GraphQL pequena - manhã |
| T9 | REST | 300 | Manhã | Consulta REST média - manhã |
| T10 | GraphQL | 300 | Manhã | Consulta GraphQL média - manhã |
| T11 | REST | 1000 | Manhã | Consulta REST grande - manhã |
| T12 | GraphQL | 1000 | Manhã | Consulta GraphQL grande - manhã |
| T13 | REST | 100 | Tarde | Consulta REST pequena - tarde |
| T14 | GraphQL | 100 | Tarde | Consulta GraphQL pequena - tarde |
| T15 | REST | 300 | Tarde | Consulta REST média - tarde |
| T16 | GraphQL | 300 | Tarde | Consulta GraphQL média - tarde |
| T17 | REST | 1000 | Tarde | Consulta REST grande - tarde |
| T18 | GraphQL | 1000 | Tarde | Consulta GraphQL grande - tarde |
| T19 | REST | 100 | Noite | Consulta REST pequena - noite |
| T20 | GraphQL | 100 | Noite | Consulta GraphQL pequena - noite |
| T21 | REST | 300 | Noite | Consulta REST média - noite |
| T22 | GraphQL | 300 | Noite | Consulta GraphQL média - noite |
| T23 | REST | 1000 | Noite | Consulta REST grande - noite |
| T24 | GraphQL | 1000 | Noite | Consulta GraphQL grande - noite |

**Total de Tratamentos:** 24 (2 APIs × 3 tamanhos × 4 períodos)

---

## E.  Objetos Experimentais

### 1. Conjunto de Dados
- **Fonte:** API do GitHub (REST e GraphQL)
- **Domínio:** Repositórios públicos com linguagem principal Java
- **Critério de seleção:** Ordenados por número de estrelas (decrescente)
- **Campos coletados:**
  - REST: `full_name`, `stargazers_count`, `language`, `html_url`, metadados completos
  - GraphQL: `nameWithOwner`, `stargazerCount`, `primaryLanguage. name`, `url`

### 2.  Endpoints Utilizados

**REST API:**
```
GET https://api.github.com/search/repositories
    ?q=language:Java+stars:>0
    &sort=stars
    &order=desc
    &per_page=100
    &page={n}

Headers: Authorization: Token <GITHUB_TOKEN>
```

**GraphQL API:**
```graphql
query ($queryString: String!, $first: Int!, $after: String) {
  search(type: REPOSITORY, query: $queryString, first: $first, after: $after) {
    pageInfo {
      hasNextPage
      endCursor
    }
    nodes {
      ...  on Repository {
        nameWithOwner
        stargazerCount
        primaryLanguage { name }
        url
      }
    }
  }
}
```

### 3. Ambiente Experimental
- **Sistema Operacional:** Windows 11
- **Python:** 3.12.7
- **Bibliotecas:** requests, pandas, python-dotenv
- **Conexão:** Internet doméstica/institucional
- **Hardware:** CPU = RX 6750XT, Memória = 32GB DDR5

---

## F. Tipo de Projeto Experimental

### Delineamento Experimental
- **Tipo:** Experimento controlado com delineamento fatorial completo
- **Design:** 2 × 3 × 4 (API × Tamanho × Período)
- **Abordagem:** Intra-sujeitos pareado (mesmas consultas para REST e GraphQL)

### Estratégias de Controle
1. **Bloqueio por Período:** Execuções em 4 momentos distintos do dia para capturar variabilidade temporal
2. **Randomização:** Ordem de execução REST/GraphQL alternada
3. **Pareamento:** Cada cenário executado com ambas as APIs sequencialmente

### Justificativa
O pareamento reduz variabilidade causada por:
- Flutuações de rede
- Carga dos servidores GitHub
- Condições do sistema local

---

## G. Quantidade de Medições

### Resumo das Medições

| Métrica | Por Tratamento | Total (24 tratamentos) |
|---------|----------------|------------------------|
| Latência total | 1 | 24 |
| Latência média | 1 | 24 |
| Latência p95 | 1 | 24 |
| Payload total | 1 | 24 |
| Payload médio/request | 1 | 24 |
| Requisições HTTP | Variável | ~120 |

### Distribuição por Cenário

| Dataset | Requisições REST | Requisições GraphQL |
|---------|------------------|---------------------|
| 100 repos | 1 página | 1 página |
| 300 repos | 3 páginas | 3 páginas |
| 1000 repos | 10 páginas | 10 páginas |

### Replicações
- **4 replicações temporais** (madrugada, manhã, tarde, noite)
- **Objetivo:** Detectar variabilidade relacionada à carga dos servidores

---

## H.  Ameaças à Validade

### Validade Interna
| Ameaça | Descrição | Mitigação |
|--------|-----------|-----------|
| Rate Limiting | GitHub limita requisições por hora | Uso de token autenticado; delay entre requisições |
| Timeouts | Falhas de conexão podem distorcer medições | Tratamento de exceções; retry logic |
| Efeito de ordem | Execução sequencial pode favorecer segunda API | Alternância de ordem em replicações |
| Caching | Respostas cacheadas podem acelerar segunda execução | Delay entre execuções pareadas |

### Validade de Construção
| Ameaça | Descrição | Mitigação |
|--------|-----------|-----------|
| Medição de latência | `time.perf_counter()` pode incluir overhead | Uso de high-resolution timer; medição consistente |
| Payload diferente | GraphQL retorna apenas campos solicitados | Documentar diferença semântica |

### Validade Externa
| Ameaça | Descrição | Mitigação |
|--------|-----------|-----------|
| Generalização | Resultados específicos para API do GitHub | Explicitar limitação; sugerir replicação |
| Tipo de consulta | Apenas busca de repositórios | Reconhecer escopo limitado |
| Condições de rede | Variabilidade geográfica/temporal | Múltiplas replicações em horários diferentes |

### Validade de Conclusão
| Ameaça | Descrição | Mitigação |
|--------|-----------|-----------|
| Tamanho amostral | Poucas replicações | Testes estatísticos apropriados |
| Outliers | Valores extremos distorcendo médias | Uso de medianas e percentis |

---

# 2. Preparação do Experimento

## Scripts Desenvolvidos
- `consuilt_repo.py`: Script principal que executa consultas REST e GraphQL

## Dependências
```toml
[project]
dependencies = [
    "pandas>=2.2.3",
    "python-dotenv>=1.0.1",
    "requests>=2.32.3",
    "openpyxl>=3.1.0"
]
```

## Configuração
1.  Criar arquivo `.env` com `GITHUB_TOKEN=<seu_token>`
2. Instalar dependências: `uv sync` ou `pip install -r requirements.txt`
3. Executar: `python consuilt_repo.py`

---

# 3. Execução do Experimento

## Rodadas Realizadas
- **Madrugada:** `comparativo_github_rest_graphql_madrugada.xlsx`
- **Manhã:** `comparativo_github_rest_graphql_manha.xlsx`
- **Tarde:** `comparativo_github_rest_graphql_tarde.xlsx`
- **Noite:** `comparativo_github_rest_graphql_noite.xlsx`

## Cenários Testados
- 100 repositórios Java (pequeno)
- 300 repositórios Java (médio)
- 1000 repositórios Java (grande)
