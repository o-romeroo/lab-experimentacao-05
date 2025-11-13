# lab-experimentacao-05
## Alunos: João Vitor Romero Sales

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

## C. Variáveis Independentes

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

## D. Tratamentos

Cada tratamento é a combinação dos níveis dos fatores relevantes. Para não gerar explosão combinatória, aplicaremos um delineamento fatorial parcial (selecionando combinações representativas):

Exemplo de conjunto mínimo de tratamentos (T):

| ID | API | Tipo Consulta | Dataset | Concorrência | Campos (GQL) |
|----|-----|---------------|---------|--------------|--------------|
| T1 | REST | Simples       | Pequeno | 1            | —            |
| T2 | GraphQL | Simples    | Pequeno | 1            | Subconjunto  |
| T3 | REST | Relacional    | Médio   | 10           | —            |
| T4 | GraphQL | Relacional | Médio   | 10           | Completo     |
| T5 | REST | Over-fetch    | Grande  | 50           | —            |
| T6 | GraphQL | Over-fetch | Grande  | 50           | Subconjunto  |
| T7 | REST | Deep nesting  | Médio   | 10           | —            |
| T8 | GraphQL | Deep nesting | Médio | 10           | Completo     |

Possíveis extensões:
- Repetir T1–T8 com variação de concorrência (1,10,50) para analisar sensibilidade.
- Adicionar cenário com compressão HTTP (gzip) para avaliar impacto relativo na economia de payload (não central para hipóteses principais; pode ser apêndice).

---

## E. Objetos Experimentais

1. Conjunto de Dados:
   - Estruturas: Users, Posts, Tags (ou Categories).
   - Users: id, name, email, bio, avatarUrl, createdAt.
   - Posts: id, title, body, createdAt, userId, tags[].
   - Tags: id, name.
   - Dados sintéticos gerados por script `data/seed.js` garantindo distribuição razoável (por exemplo, comprimento de textos variado para aumentar realismo do payload).
2. Endpoints REST:
   - GET /users/:id
   - GET /users/:id/posts
   - GET /posts/:id
   - GET /posts/:id/tags
   - (Possível agregação: /users/:id/with-posts para evitar múltiplas requisições — mas manter endpoints atômicos para refletir estilo REST típico.)
3. Schema GraphQL:
   - Query: user(id), post(id), users(limit, offset), posts(limit, offset)
   - Tipos: User, Post, Tag
   - Campos resolvidos com DataLoader para evitar N+1 (garante justiça comparativa).
4. Ambiente:
   - Mesmo servidor físico (ou mesmo container host).
   - Node.js versão única (ex.: 20.x).
   - Banco: PostgreSQL ou SQLite (SQLite in-memory para reduzir variabilidade, mas Postgres dá realismo; escolha e documente).
5. Ferramentas de Carga: k6 com scripts específicos por cenário (um por tratamento ou parametrizado).

---

## F. Tipo de Projeto Experimental

- Delineamento Intra-Sujeitos (paired design): Para cada tipo de consulta, medimos ambos os tratamentos (REST vs GraphQL) em condições idênticas.
- Estratégia de Bloqueio:
  - Bloqueio por Tipo de Consulta (cada bloco contém execuções REST e GraphQL para aquela consulta).
  - Randomização da ordem de execução dentro do bloco (para mitigar efeitos de aquecimento ou degradação temporal).
- Replicações:
  - Mínimo de 3 rodadas temporais independentes (rodas o bloco completo em momentos distintos) para reduzir viés acidental.
- Justificativa: O pareamento reduz variabilidade causada por flutuações sistêmicas (mesmo hardware / momento aproximado).

---

## G. Quantidade de Medições

### Por Tratamento (Exemplo Base)
- Warmup: Descartar primeiros 50–100 requests (dependendo da duração) para estabilizar JIT e caches.
- Amostras úteis: 500 requisições por tratamento por replicação (para cada combinação de API × Tipo Consulta × Dataset × Concorrência).
  - Se 8 tratamentos e 3 replicações: 8 × 3 × 500 = 12.000 medições primárias (por variável dependente latência cliente).
  - Mesmo número para latência servidor (paralelo) e tamanho de payload (coletado no lado do cliente).

### Justificativa Estatística
- Objetivo: Detectar diferença de, por exemplo, 5–10% na latência média.
- Piloto estimado: Desvio padrão intra-condição ≈ 15–25 ms (exemplo).
- Fórmula aproximada (teste t pareado) para diferença mínima detectável Δ:

  n ≈ ((Z_{1-α/2} + Z_{1-β}) * σ_d / Δ)²

  Com σ_d = 20 ms, Δ = 5 ms, α = 0.05 (Z=1.96), β = 0.2 (Z=0.84):
  n ≈ ((2.8 * 20) / 5)² = (56/5)² = 11.2² ≈ 125 pares.
  
  Como iremos além (500 pares por tratamento), teremos margem para:
  - Estimar percentis altos (p95, p99) com menor erro.
  - Aplicar bootstrap para intervalos de confiança robustos.

### Distribuição Temporal
- Interleaving (alternância) REST/GraphQL para reduzir deriva térmica (ex.: executar em blocos de 50 requisições alternadas em altos níveis de concorrência).
- Se usar k6 com duração em vez de número fixo, ajustar para garantir contagem mínima (ex.: 30s resultando em ≥500 requests).

---

## H. Ameaças à Validade

### 1. Validade Interna
- Variação de Carga do Sistema: Outros processos podem interferir. Mitigação: ambiente isolado / container dedicado.
- Efeito de Ordem / Aquecimento: Primeiro tratamento pode beneficiar de JIT e caches. Mitigação: warmup + randomização da ordem.
- N+1 em GraphQL: Resolvers mal implementados podem inflar latência injustamente. Mitigação: uso de DataLoader e consultas equivalentes.
- Caching de Banco Desigual: Após primeira execução, buffers de disco podem favorecer segundo tratamento. Mitigação: alternância e múltiplas replicações.

### 2. Validade de Construção
- Métrica de Latência: Medir apenas no cliente pode incluir overhead de rede irrelevante. Mitigação: coletar tanto latência cliente quanto servidor.
- Equivalência Funcional: Consultas podem não retornar exatamente o mesmo conjunto semântico de dados. Mitigação: especificar claramente campos comparados (subset controlado).
- Tamanho do Payload: Ignorar headers ou compressão pode distorcer comparações reais. Mitigação: documentar decisão (corpo puro sem compressão) e opcional análise com gzip.

### 3. Validade Externa
- Generalização: Domínio Users/Posts pode não representar padrões de acesso de sistemas mais complexos (ex.: grafos densos, agregações pesadas). Mitigação: explicitar limitações e sugerir replicação em outros domínios.
- Escala: Níveis de concorrência escolhidos podem não refletir produção. Mitigação: incluir pelo menos um nível moderado e um alto.

### 4. Validade Estatística / Conclusão
- Pseudorreplicação: Tratar requisições extremamente correlacionadas como independentes. Mitigação: múltiplas replicações temporais e análise da autocorrelação (opcional).
- Sobreinterpretação de p-valor: Focar apenas em significância e não em efeito prático. Mitigação: relatar effect size e redução percentual.
- Outliers extremos (picos de GC): Podem distorcer média. Mitigação: relatar mediana e percentis; avaliar remoção justificada de outliers mediante critério transparente (ex.: > Q3 + 3*IQR).

### 5. Outras Ameaças
- Versão de Node ou Bibliotecas: Pode afetar performance. Mitigação: fixar versões em package.json.
- Reprodutibilidade: Falta de scripts automatizados pode dificultar validação. Mitigação: incluir script run_all.sh e documentação do ambiente.
