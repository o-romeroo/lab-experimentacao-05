# lab-experimentacao-05
## Alunos: João Vitor Romero Sales e Lucas Randazzo

# 1. Desenho do Experimento

## A. Hipóteses Nula e Alternativa

### RQ1: Latência (tempo de resposta)
- H0₁ (Hipótese Nula): Não há diferença estatisticamente significativa entre a latência média (e distribuição) das respostas REST e GraphQL para consultas equivalentes.
- H1₁ (Hipótese Alternativa): Há diferença estatisticamente significativa entre as latências; espera-se que GraphQL apresente menor latência média em cenários de sobrecarga (over-fetch) típica do REST OU que REST seja superior em cenários onde o resolver GraphQL introduza custo adicional. (A direção será observada; teste bicaudal.)

### RQ2: Tamanho do Payload (bytes)
- H0₂: Não há diferença estatisticamente significativa entre o tamanho médio das respostas REST e GraphQL para consultas equivalentes.
- H1₂: Há diferença estatisticamente significativa; espera-se que GraphQL produza respostas menores quando o cliente solicita subconjunto de campos, reduzindo over-fetch presente em REST.

Nota: Como não garantimos a direção a priori para latência (pode depender da complexidade dos resolvers), usamos testes bicaudais. Para tamanho de payload, há expectativa direcional (GraphQL menor), mas manteremos abordagem bicaudal para neutralidade científica.

---

## B. Variáveis Dependentes

1. Latência Cliente (ms): tempo total percebido entre envio da requisição e recebimento completo da resposta (TTC).
2. Latência Servidor (ms): tempo interno medido via middleware (timestamp antes e depois do processamento).
3. Percentis de latência: p50, p90, p95, p99.
4. Tamanho do Payload (bytes): comprimento do corpo de resposta (antes de compressão).
5. Eficiência de Seleção (ratio): número de campos retornados / número de campos potencialmente disponíveis (para evidenciar redução de over-fetch no GraphQL).
6. Throughput (request/seg) sob cenários de carga (apenas para contexto interpretativo, não é variável primária para hipóteses).

---

## B. Variáveis Independentes

1. Tipo de API (Fator Principal): REST vs GraphQL.
2. Tipo de Consulta (Cenário):
   - Simples (entidade única, p.ex. User por ID).
   - Relacional (User + lista de Posts).
   - Over-fetch (REST retorna todos os campos; GraphQL solicita subconjunto).
   - Deep nesting (User → Posts → Tags ou similar).
3. Tamanho do Dataset:
   - Pequeno (100 repos)
   - Médio (300 repos)
   - Grande (1.000 repos)
4. Nível de Concorrência:
   - 1 token (sequencial)
   - 3 tokens (moderado)
   - 5 tokens (alto)
5. Subconjunto de Campos Solicitados (somente para GraphQL): completo vs reduzido (controla magnitude da economia de payload)

---

## C. Tratamentos

Cada tratamento é a combinação dos níveis dos fatores relevantes. Para não gerar explosão combinatória, aplicaremos um delineamento fatorial parcial (selecionando combinações representativas):

Exemplo de conjunto mínimo de tratamentos (T):

| ID | API | Tipo Consulta | Dataset | Concorrência | Campos (GQL) |
|----|-----|---------------|---------|--------------|--------------|
| T1 | REST | Simples       | Pequeno | 1            | —            |
| T2 | GraphQL | Simples    | Pequeno | 1            | Subconjunto  |
| T3 | REST | Relacional    | Médio   | 3           | —            |
| T4 | GraphQL | Relacional | Médio   | 3           | Completo     |
| T5 | REST | Over-fetch    | Grande  | 5           | —            |
| T6 | GraphQL | Over-fetch | Grande  | 5           | Subconjunto  |
| T7 | REST | Deep nesting  | Médio   | 3           | —            |
| T8 | GraphQL | Deep nesting | Médio | 3           | Completo     |

Possíveis extensões:
- Repetir T1–T8 com variação de concorrência (1,3,5) para analisar sensibilidade.

---

## D. Objetos Experimentais

1. Conjunto de Dados:
   - Repositório GitHub
      - id, full_name, owner.login, owner.type, html_url
      - stargazers_count, forks_count, open_issues_count, watchers_count
      - language (língua principal reportada pelo GitHub)
      - size (em KB, do GitHub), topics, license.spdx_id
      - created_at, updated_at, pushed_at
   - Métricas CK (saída bruta por repositório)
      - resultsclass.csv: métricas por classe (inclui CBO, DIT, LCOM, LOC por classe etc.)
      - resultsmethod.csv: métricas por método
      - resultsfield.csv: campos/atributos
      - resultsvariable.csv: variáveis locais
      - Observação: a lista completa de colunas segue o padrão da ferramenta CK; o foco analítico deste laboratório está em CBO, DIT, LCOM e LOC.
   
3. Endpoints REST:

| Objetivo | Método | Endpoint Base | Exemplo / Observações |
|----------|--------|---------------|-----------------------|
| Buscar repositórios Java populares | GET | `https://api.github.com/search/repositories` | `q=language:Java+stars:>0&sort=stars&order=desc&per_page=100&page={n}` |
| Detalhes de repositório | GET | `https://api.github.com/repos/{owner}/{repo}` | Campos usados: `stargazers_count`, `created_at` |
| Releases (paginação completa) | GET | `https://api.github.com/repos/{owner}/{repo}/releases` | Paginação: `?page={n}&per_page=100` |

Cabeçalhos:
```
Authorization: Token <GITHUB_TOKEN>
```

Tratamento de erros:
- Verificação de `status_code == 200`
- Interrupção de paginação em resposta vazia
- Exceções logadas com mensagem de status + texto da resposta

3. Schema GraphQL:
   
4. Ambiente:
   - Mesmo servidor físico (ou mesmo container host).
   - Python versão 3.12.7.
   - Banco em memória.

---

## E. Tipo de Projeto Experimental

- Delineamento Intra-Sujeitos: Para cada tipo de consulta, medimos ambos os tratamentos (REST vs GraphQL) em condições idênticas.
- Estratégia de Bloqueio:
  - Bloqueio por Tipo de Consulta (cada bloco contém execuções REST e GraphQL para aquela consulta).
  - Randomização da ordem de execução dentro do bloco (para mitigar efeitos de degradação temporal).
- Replicações:
  - Mínimo de 3 rodadas temporais independentes (rodas o bloco completo em momentos distintos) para reduzir viés acidental.
- Justificativa: O pareamento reduz variabilidade causada por flutuações sistêmicas (mesmo hardware / momento aproximado).

---

## F. Quantidade de Medições

### Por Tratamento (Exemplo Base)
- Warmup: Descartar primeiros 50–100 requests (dependendo da duração) para estabilizar JIT e caches.
- Amostras úteis: 500 requisições por tratamento por replicação (para cada combinação de API × Tipo Consulta × Dataset × Concorrência).
  - Mesmo número para latência servidor (paralelo) e tamanho de payload (coletado no lado do cliente).

### Justificativa Estatística
- Objetivo: Detectar diferença de latência média.
- Piloto estimado: Desvio padrão intra-condição ≈ 15–25 ms.

### Distribuição Temporal
- Interleaving (alternância) REST/GraphQL para reduzir degradação temporal (ex.: executar em blocos de 50 requisições alternadas em altos níveis de concorrência).

---

## G. Ameaças à Validade

| Tipo | Ameaça | Mitigação |
|------|--------|-----------|
| Interna | Falhas na coleta (timeouts, rate limit) | Retry + delays + token |
| Construção | Interpretação incorreta de métricas CK | Referenciar definição oficial CK; usar documentação |
| Externa | Repositórios populares não representam todo o ecossistema Java | Explicitar critério de seleção (estrelas > 0 ordenado por popularidade) |
| Estatística | Outliers extremos afetando coeficientes | Uso de medidas robustas (mediana) |
| Reprodutibilidade | Dependência de estado do GitHub (popularidade dinâmica) | Registrar data/hora da coleta do repositório |
| Ética / Licença | Uso de repositórios sem verificação de licenças | Apenas leitura de metadados públicos; citar política de uso da API |
