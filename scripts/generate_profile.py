#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Автогенерация секций профиля GitHub.

Обновляет:
  1) «Мои проекты» — репозитории, отсортированные по дате последнего коммита (push).
  2) «Активность GitHub» — SVG-тепловая карта коммитов за последний год (GraphQL API).

Запускается из GitHub Actions по расписанию, при пуше и вручную (workflow_dispatch).
"""

import html
import json
import os
import re
import urllib.request
from datetime import datetime, timezone

USERNAME = os.environ.get("GH_USERNAME", "HVHBIGNAME")
GH_PAT = os.environ.get("GH_PAT", "") or ""
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "") or ""
TOKEN = GH_PAT or GITHUB_TOKEN

API = "https://api.github.com"
README_PATH = "README.md"
GRAPH_PATH = "assets/activity-graph.svg"
MAX_PROJECTS = 8

# Зелёная палитра в стиле GitHub (тёмная тема)
LEVEL_COLORS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
MONTHS = ["янв", "фев", "мар", "апр", "май", "июн",
          "июл", "авг", "сен", "окт", "ноя", "дек"]


def http_get_json(url, token=""):
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "github-profile-generator")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def http_graphql(query, variables, token):
    req = urllib.request.Request(API + "/graphql", method="POST")
    req.add_header("Authorization", "Bearer " + token)
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "github-profile-generator")
    body = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    with urllib.request.urlopen(req, data=body, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if data.get("errors"):
        raise RuntimeError("GraphQL errors: " + json.dumps(data["errors"]))
    return data["data"]


def days_ago(pushed_at):
    if not pushed_at:
        return "недавно"
    dt = datetime.strptime(pushed_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    days = (datetime.now(timezone.utc) - dt).days
    if days <= 0:
        return "сегодня"
    if days == 1:
        return "1 день назад"
    return f"{days} дн. назад"


def fetch_repos():
    repos = {}
    # Публичные репозитории (токен нужен только чтобы не упереться в rate limit)
    public = http_get_json(
        f"{API}/users/{USERNAME}/repos?per_page=100&sort=pushed&type=owner",
        token=TOKEN,
    )
    for r in public:
        if r.get("fork"):
            continue
        repos[r["full_name"]] = r

    # Приватные репозитории доступны только с персональным токеном (PAT)
    if GH_PAT:
        try:
            private = http_get_json(
                f"{API}/user/repos?per_page=100&sort=pushed&type=owner&affiliation=owner",
                token=GH_PAT,
            )
            for r in private:
                if r.get("fork"):
                    continue
                repos.setdefault(r["full_name"], r)
        except Exception as exc:
            print("Не удалось получить приватные репозитории:", exc)

    # Сам профильный репозиторий не показываем
    repos.pop(f"{USERNAME}/{USERNAME}", None)

    items = list(repos.values())
    items.sort(key=lambda r: r.get("pushed_at") or "", reverse=True)
    return items[:MAX_PROJECTS]


def build_projects_md(repos):
    lines = []
    for r in repos:
        name = r["name"]
        url = r["html_url"]
        desc = (r.get("description") or "").strip()
        if len(desc) > 120:
            desc = desc[:117].rstrip() + "..."
        lang = r.get("language") or "—"
        stars = r.get("stargazers_count", 0)
        updated = days_ago(r.get("pushed_at"))

        head = f"- **[{name}]({url})**"
        if desc:
            head += f" — {desc}"
        lines.append(head)
        lines.append(f"  `{lang}` · ⭐ {stars} · обновлён {updated}")
    return "\n".join(lines)


def update_readme(projects_md):
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    if "<!-- PROJECTS:START -->" not in content or "<!-- PROJECTS:END -->" not in content:
        raise RuntimeError("Маркеры PROJECTS не найдены в README.md")

    pattern = re.compile(
        r"<!-- PROJECTS:START -->.*?<!-- PROJECTS:END -->",
        re.DOTALL,
    )
    replacement = "<!-- PROJECTS:START -->\n" + projects_md + "\n<!-- PROJECTS:END -->"
    new_content = pattern.sub(lambda m: replacement, content)

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)


def fetch_contribution_calendar():
    query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                date
                contributionCount
              }
            }
          }
        }
      }
    }
    """
    data = http_graphql(query, {"login": USERNAME}, TOKEN)
    return data["user"]["contributionsCollection"]["contributionCalendar"]


def color_for(count):
    if count <= 0:
        return LEVEL_COLORS[0]
    if count <= 2:
        return LEVEL_COLORS[1]
    if count <= 5:
        return LEVEL_COLORS[2]
    if count <= 9:
        return LEVEL_COLORS[3]
    return LEVEL_COLORS[4]


def build_svg(calendar):
    weeks = calendar["weeks"]
    total = calendar["totalContributions"]

    cell = 11
    gap = 3
    left = 34
    top = 20
    rows = 7
    cols = len(weeks)

    grid_w = cols * (cell + gap)
    grid_h = rows * (cell + gap)
    width = left + grid_w + 8
    height = top + grid_h + 40

    parts = []
    parts.append(
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        'xmlns="http://www.w3.org/2000/svg" '
        'font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif">'
    )
    parts.append(f'<rect x="0" y="0" width="{width}" height="{height}" rx="8" fill="#0d1117"/>')

    # Подписи дней недели (неделя начинается с воскресенья)
    labels = {1: "Пн", 3: "Ср", 5: "Пт"}
    for row in (1, 3, 5):
        y = top + row * (cell + gap) + cell / 2
        parts.append(
            f'<text x="{left - 6}" y="{y:.1f}" fill="#7d8590" font-size="10" '
            'text-anchor="end" dominant-baseline="middle">' + labels[row] + "</text>"
        )

    # Подписи месяцев
    prev_month = None
    for i, week in enumerate(weeks):
        days = week["contributionDays"]
        if not days:
            continue
        month = datetime.strptime(days[0]["date"], "%Y-%m-%d").month
        if month != prev_month:
            x = left + i * (cell + gap)
            parts.append(
                f'<text x="{x}" y="{top - 6}" fill="#7d8590" font-size="10">'
                + MONTHS[month - 1] + "</text>"
            )
            prev_month = month

    # Ячейки
    for i, week in enumerate(weeks):
        x = left + i * (cell + gap)
        for j, day in enumerate(week["contributionDays"]):
            y = top + j * (cell + gap)
            color = color_for(day["contributionCount"])
            parts.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" fill="{color}"/>')

    # Итоговая строка
    parts.append(
        f'<text x="{left}" y="{height - 14}" fill="#7d8590" font-size="12">'
        f"{total} коммитов за последний год</text>"
    )

    parts.append("</svg>")
    return "\n".join(parts)


def build_fallback_svg(message=""):
    msg = html.escape((message or "нет данных")[:80])
    return (
        '<svg width="480" height="60" xmlns="http://www.w3.org/2000/svg">'
        '<rect width="480" height="60" rx="8" fill="#0d1117"/>'
        '<text x="240" y="34" fill="#7d8590" font-size="12" text-anchor="middle" '
        'font-family="sans-serif">Не удалось загрузить график: ' + msg + "</text></svg>"
    )


def main():
    # 1) Проекты
    try:
        repos = fetch_repos()
        projects_md = build_projects_md(repos)
        if projects_md.strip():
            update_readme(projects_md)
            print("Секция «Мои проекты» обновлена.")
    except Exception as exc:
        print("Не удалось обновить проекты:", exc)

    # 2) График активности (файл создаём всегда, чтобы git add не падал)
    try:
        calendar = fetch_contribution_calendar()
        svg = build_svg(calendar)
        print("График активности сгенерирован.")
    except Exception as exc:
        print("Не удалось сгенерировать график:", exc)
        svg = build_fallback_svg(str(exc))

    os.makedirs(os.path.dirname(GRAPH_PATH), exist_ok=True)
    with open(GRAPH_PATH, "w", encoding="utf-8") as f:
        f.write(svg)


if __name__ == "__main__":
    main()
