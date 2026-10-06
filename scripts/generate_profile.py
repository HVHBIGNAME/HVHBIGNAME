#!/usr/bin/env python3
"""Refresh the 90-day signal and public project log, preserving curated content."""

import json
import os
import urllib.request
from datetime import date, timedelta
from html import escape

from design import ROOT, VIEW_HEIGHT, activity_json, build_atlas, document, signal_body

USERNAME = os.environ.get("GH_USERNAME", "HVHBIGNAME")
API = "https://api.github.com"
MAX_PROJECTS = 5
WINDOW_DAYS = 90
START_MARKER = "<!-- PROJECTS:START -->"
END_MARKER = "<!-- PROJECTS:END -->"


def github_json(path, token, payload=None):
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        API + path,
        data=body,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
            "User-Agent": "HVHBIGNAME-profile",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.load(response)
    if isinstance(data, dict) and data.get("errors"):
        raise RuntimeError("GitHub GraphQL: " + json.dumps(data["errors"]))
    return data


def public_projects(repos):
    projects = [
        repo for repo in repos
        if not repo.get("private", True)
        and repo.get("visibility", "public") == "public"
        and not repo.get("fork")
        and not repo.get("archived")
        and repo["owner"]["login"].casefold() == USERNAME.casefold()
        and repo["name"].casefold() != USERNAME.casefold()
    ]
    return sorted(projects, key=lambda repo: repo.get("pushed_at") or "", reverse=True)[:MAX_PROJECTS]


def fetch_repos(token):
    repos = []
    page = 1
    while True:
        batch = github_json(
            f"/users/{USERNAME}/repos?per_page=100&sort=pushed&type=owner&page={page}",
            token,
        )
        repos.extend(batch)
        if len(batch) < 100:
            return public_projects(repos)
        page += 1


def table_cell(value):
    return escape(str(value)).replace("|", "&#124;").replace("\n", " ")


def build_projects_md(repos):
    if not repos:
        return "Новые публичные проекты появятся здесь после первого push."
    lines = ["| Репозиторий | Язык | Последний push |", "| :-- | :-- | :-- |"]
    for repo in repos:
        name = table_cell(repo["name"])
        language = table_cell(repo.get("language") or "—")
        pushed = (repo.get("pushed_at") or "—")[:10]
        lines.append(f'| [{name}]({repo["html_url"]}) | {language} | {pushed} |')
    return "\n".join(lines)


def update_readme(content, projects_md):
    if content.count(START_MARKER) != 1 or content.count(END_MARKER) != 1:
        raise ValueError("README must contain exactly one pair of PROJECTS markers")
    before, rest = content.split(START_MARKER)
    if END_MARKER not in rest:
        raise ValueError("PROJECTS markers are out of order")
    _, after = rest.split(END_MARKER)
    return before + START_MARKER + "\n" + projects_md + "\n" + END_MARKER + after


def fetch_contribution_calendar(token):
    query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar {
            weeks {
              contributionDays { date contributionCount }
            }
          }
        }
      }
    }
    """
    response = github_json("/graphql", token, {"query": query, "variables": {"login": USERNAME}})
    user = response["data"]["user"]
    if user is None:
        raise ValueError(f"GitHub user {USERNAME} was not found")
    return user["contributionsCollection"]["contributionCalendar"]


def contribution_window(calendar):
    counts = {}
    for week in calendar["weeks"]:
        for day in week["contributionDays"]:
            day_date = date.fromisoformat(day["date"])
            count = day["contributionCount"]
            if not isinstance(count, int) or count < 0 or day_date in counts:
                raise ValueError("Invalid or duplicate contribution day")
            counts[day_date] = count
    if not counts:
        raise ValueError("Contribution calendar is empty")
    end = max(counts)
    start = end - timedelta(days=WINDOW_DAYS - 1)
    days = [start + timedelta(days=index) for index in range(WINDOW_DAYS)]
    if any(day not in counts for day in days):
        raise ValueError("Contribution calendar does not cover the complete 90-day window")
    return [(day, counts[day]) for day in days]


def build_svg(calendar, theme="dark"):
    days = contribution_window(calendar)
    total = sum(count for _, count in days)
    active = sum(count > 0 for _, count in days)
    peak = max(count for _, count in days)
    start, end = days[0][0].isoformat(), days[-1][0].isoformat()
    description = (
        f"{start} — {end}: {total} GitHub contributions, "
        f"{active} active days, {peak} contributions on the busiest day. "
        "Each bar represents one day; bar height is proportional to contributions."
    )
    return document("Build signal — last 90 days", description, VIEW_HEIGHT, signal_body(days, theme), theme)


def main():
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise RuntimeError("Set GITHUB_TOKEN or GH_TOKEN to refresh the profile")
    repos = fetch_repos(token)
    calendar = fetch_contribution_calendar(token)
    days = contribution_window(calendar)
    readme_path = ROOT / "README.md"
    readme = update_readme(readme_path.read_text(encoding="utf-8"), build_projects_md(repos))
    outputs = {
        readme_path: readme,
        ROOT / "assets/profile-dark.svg": build_atlas(days, "dark"),
        ROOT / "assets/profile-light.svg": build_atlas(days, "light"),
        ROOT / "assets/activity.json": activity_json(days),
    }
    # Finish every fetch and render before replacing any of the published files.
    for path, content in outputs.items():
        path.write_text(content, encoding="utf-8", newline="\n")
    print(f"Updated 90-day signal and {len(repos)} public projects for {USERNAME}.")


if __name__ == "__main__":
    main()
