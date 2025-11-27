import math
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv


load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
PATH_RESULTS_METRICS = Path(__file__).resolve().parent / "results"


def _ensure_token_available():
    if not GITHUB_TOKEN:
        raise EnvironmentError(
            "A variável de ambiente GITHUB_TOKEN não foi configurada. Configure antes de continuar."
        )


def _percentile(values, percentile):
    if not values:
        return 0.0
    if len(values) == 1:
        return round(values[0], 6)
    ordered = sorted(values)
    k = (len(ordered) - 1) * percentile
    lower_index = math.floor(k)
    upper_index = math.ceil(k)
    if lower_index == upper_index:
        return round(ordered[int(k)], 6)
    lower_value = ordered[lower_index]
    upper_value = ordered[upper_index]
    interpolated = lower_value + (upper_value - lower_value) * (k - lower_index)
    return round(interpolated, 6)


def _finalize_metrics(api_type, num_repos, repos, latencies, payload_bytes, extra=None):
    request_count = len(latencies)
    total_latency = sum(latencies)
    avg_latency = total_latency / request_count if request_count else 0.0
    avg_payload = payload_bytes / request_count if request_count else 0.0
    payload_per_repo = payload_bytes / len(repos) if repos else 0.0
    metrics = {
        "api_type": api_type,
        "num_repos_requested": num_repos,
        "repos_returned": len(repos),
        "requests_count": request_count,
        "latency_total_s": round(total_latency, 6),
        "latency_avg_s": round(avg_latency, 6),
        "latency_min_s": round(min(latencies), 6) if latencies else 0.0,
        "latency_max_s": round(max(latencies), 6) if latencies else 0.0,
        "latency_p95_s": _percentile(latencies, 0.95),
        "payload_total_bytes": payload_bytes,
        "payload_avg_per_request_bytes": round(avg_payload, 2),
        "payload_avg_per_repo_bytes": round(payload_per_repo, 2),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    if extra:
        metrics.update(extra)
    return metrics


def get_popular_repositories_java(num_repos, delay_between_requests=1):
    """Busca repositórios Java mais populares usando a API REST."""
    _ensure_token_available()
    if num_repos < 1 or num_repos > 1000:
        raise ValueError("num_repos deve estar entre 1 e 1000 para a API REST.")

    all_repos = []
    per_page = 100
    latencies = []
    payload_bytes = 0
    rate_limit_remaining = None

    total_pages = math.ceil(num_repos / per_page)
    for page in range(1, total_pages + 1):
        url = (
            "https://api.github.com/search/repositories"
            "?q=language:Java+stars:>0&sort=stars&order=desc"
            f"&per_page={per_page}&page={page}"
        )
        headers = {"Authorization": f"Token {GITHUB_TOKEN}"}
        start = time.perf_counter()
        response = requests.get(url, headers=headers)
        latency = time.perf_counter() - start
        latencies.append(latency)
        payload_bytes += len(response.content or b"")
        rate_limit_remaining = response.headers.get("X-RateLimit-Remaining")

        if response.status_code != 200:
            raise Exception(
                f"Erro na chamada REST: {response.status_code} - {response.text}"
            )

        items = response.json().get("items", [])
        all_repos.extend(items)
        if len(all_repos) >= num_repos or not items:
            break

        time.sleep(delay_between_requests)

    repos = all_repos[:num_repos]
    metrics = _finalize_metrics(
        api_type="REST",
        num_repos=num_repos,
        repos=repos,
        latencies=latencies,
        payload_bytes=payload_bytes,
        extra={"rate_limit_remaining": rate_limit_remaining},
    )
    return repos, metrics


def get_popular_repositories_java_graphql(num_repos, delay_between_requests=1):
    """Busca repositórios Java mais populares usando a API GraphQL."""
    _ensure_token_available()
    if num_repos < 1:
        raise ValueError("num_repos deve ser maior que zero.")

    query = """
    query ($queryString: String!, $first: Int!, $after: String) {
      search(type: REPOSITORY, query: $queryString, first: $first, after: $after) {
        pageInfo {
          hasNextPage
          endCursor
        }
        nodes {
          ... on Repository {
            nameWithOwner
            stargazerCount
            primaryLanguage { name }
            url
          }
        }
      }
    }
    """

    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    query_string = "language:Java sort:stars-desc"
    latencies = []
    payload_bytes = 0
    repos = []
    cursor = None
    rate_limit_remaining = None

    while len(repos) < num_repos:
        remaining = num_repos - len(repos)
        first = remaining if remaining < 100 else 100
        variables = {"queryString": query_string, "first": first, "after": cursor}

        start = time.perf_counter()
        response = requests.post(
            "https://api.github.com/graphql",
            json={"query": query, "variables": variables},
            headers=headers,
        )
        latency = time.perf_counter() - start
        latencies.append(latency)
        payload_bytes += len(response.content or b"")
        rate_limit_remaining = response.headers.get("X-RateLimit-Remaining")

        if response.status_code != 200:
            raise Exception(
                f"Erro na chamada GraphQL: {response.status_code} - {response.text}"
            )

        payload = response.json()
        if payload.get("errors"):
            raise Exception(f"GraphQL retornou erros: {payload['errors']}")

        search_data = payload["data"]["search"]
        nodes = search_data.get("nodes", [])
        repos.extend(nodes)

        page_info = search_data.get("pageInfo", {})
        if not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")

        time.sleep(delay_between_requests)

    repos = repos[:num_repos]
    metrics = _finalize_metrics(
        api_type="GraphQL",
        num_repos=num_repos,
        repos=repos,
        latencies=latencies,
        payload_bytes=payload_bytes,
        extra={"rate_limit_remaining": rate_limit_remaining},
    )
    return repos, metrics


def run_experiments(num_repos_values):
    """Executa os cenários definindo métricas para REST e GraphQL."""
    resultados = []
    for num_repos in num_repos_values:
        print(f"Iniciando experimento com {num_repos} repositórios...")

        _, metrics_rest = get_popular_repositories_java(num_repos)
        resultados.append(metrics_rest)
        print(
            f"REST -> {metrics_rest['requests_count']} chamadas, latência total: {metrics_rest['latency_total_s']:.2f}s"
        )

        _, metrics_graphql = get_popular_repositories_java_graphql(num_repos)
        resultados.append(metrics_graphql)
        print(
            f"GraphQL -> {metrics_graphql['requests_count']} chamadas, latência total: {metrics_graphql['latency_total_s']:.2f}s"
        )

    return resultados


def salvar_dataset(resultados, base_dir=None):
    """Gera um arquivo XLSX com os resultados coletados."""
    if not resultados:
        raise ValueError("Nenhum resultado para salvar no dataset.")

    df = pd.DataFrame(resultados)
    destino_base = Path(base_dir or Path.cwd())
    destino_base.mkdir(parents=True, exist_ok=True)
    timestamp_label = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_path = destino_base / f"comparativo_github_rest_graphql_{timestamp_label}.xlsx"

    df.to_excel(output_path, index=False)
    print(f"Dataset salvo em {output_path}")
    return output_path


def main():
    cenarios = [100, 300, 1000]
    resultados = run_experiments(cenarios)
    salvar_dataset(resultados, PATH_RESULTS_METRICS)


if __name__ == "__main__":
    main()
