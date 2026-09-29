"""Regression checks for the data that gets published automatically."""

import os
import tempfile
import unittest
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

import generate_profile as profile
from design import footer, hero, project


def calendar_fixture():
    start = date(2026, 1, 1)
    days = [
        {"date": (start + timedelta(days=i)).isoformat(), "contributionCount": i % 9}
        for i in range(123)
    ]
    return {
        "totalContributions": 99999,
        "weeks": [{"contributionDays": days[i:i+7]} for i in range(0, len(days), 7)],
    }


def repo_fixture(name, **overrides):
    return {
        "name": name, "private": False, "fork": False, "archived": False,
        "owner": {"login": profile.USERNAME}, "language": "Rust",
        "html_url": f"https://github.com/{profile.USERNAME}/{name}",
        "pushed_at": "2026-09-01T00:00:00Z", **overrides,
    }


class ProfileTests(unittest.TestCase):
    def test_only_public_owned_original_active_repositories_are_published(self):
        repos = [
            repo_fixture("public-build"),
            repo_fixture("private-work", private=True),
            repo_fixture("private-visibility", visibility="private"),
            repo_fixture("fork", fork=True),
            repo_fixture("archived", archived=True),
            repo_fixture(profile.USERNAME.lower()),
            repo_fixture("someone-elses", owner={"login": "someone-else"}),
            repo_fixture("new-build", pushed_at="2026-09-29T12:00:00Z"),
        ]
        selected = profile.public_projects(repos)
        self.assertEqual([repo["name"] for repo in selected], ["new-build", "public-build"])

    def test_repository_pagination(self):
        first = [repo_fixture(f"build-{i}") for i in range(100)]
        last = [repo_fixture("newest", pushed_at="2026-09-29T12:00:00Z")]
        with patch.object(profile, "github_json", side_effect=[first, last]) as api:
            repos = profile.fetch_repos("test-token")
        self.assertEqual(repos[0]["name"], "newest")
        self.assertEqual(len(repos), profile.MAX_PROJECTS)
        self.assertIn("page=2", api.call_args.args[0])

    def test_exact_90_day_window_including_partial_week(self):
        days = profile.contribution_window(calendar_fixture())
        self.assertEqual(len(days), 90)
        self.assertEqual(days[0], (date(2026, 2, 3), 33 % 9))
        self.assertEqual(days[-1], (date(2026, 5, 3), 122 % 9))
        self.assertEqual(sum(count for _, count in days), sum(i % 9 for i in range(33, 123)))

    def test_missing_duplicate_negative_and_empty_calendar_fail(self):
        missing = calendar_fixture()
        missing["weeks"][-1]["contributionDays"].pop(0)
        duplicate = calendar_fixture()
        duplicate["weeks"][-1]["contributionDays"].append(duplicate["weeks"][-1]["contributionDays"][-1])
        negative = calendar_fixture()
        negative["weeks"][-1]["contributionDays"][-1]["contributionCount"] = -1
        for calendar in (missing, duplicate, negative, {"weeks": []}):
            with self.subTest(calendar=calendar), self.assertRaises(ValueError):
                profile.contribution_window(calendar)

    def test_curated_readme_is_preserved_and_updates_are_idempotent(self):
        before = "Hero & curated projects\n<details>\n"
        after = "\n</details>\nFooter\n"
        original = before + profile.START_MARKER + "old" + profile.END_MARKER + after
        result = profile.update_readme(original, "new table")
        self.assertEqual(result, before + profile.START_MARKER + "\nnew table\n" + profile.END_MARKER + after)
        self.assertEqual(profile.update_readme(result, "new table"), result)

    def test_malformed_markers_are_not_repaired_silently(self):
        for content in ("no markers", profile.START_MARKER, profile.END_MARKER + profile.START_MARKER,
                        profile.START_MARKER * 2 + profile.END_MARKER):
            with self.subTest(content=content), self.assertRaises(ValueError):
                profile.update_readme(content, "table")

    def test_signal_is_valid_svg_with_90_daily_values_and_real_totals(self):
        calendar = calendar_fixture()
        ns = {"svg": "http://www.w3.org/2000/svg"}
        expected = sum(i % 9 for i in range(33, 123))
        for theme in ("dark", "light"):
            svg = profile.build_svg(calendar, theme)
            root = ET.fromstring(svg)
            bars = root.findall(".//svg:rect[svg:title]", ns)
            self.assertEqual(len(bars), 90)
            self.assertIn(f"{expected} GitHub contributions", root.find("svg:desc", ns).text)
            self.assertNotIn("99999", svg)

    def test_zero_activity_is_rendered_without_inventing_activity(self):
        calendar = calendar_fixture()
        for week in calendar["weeks"]:
            for day in week["contributionDays"]:
                day["contributionCount"] = 0
        svg = profile.build_svg(calendar)
        self.assertIn("0 GitHub contributions, 0 active days, 0 contributions", svg)
        ET.fromstring(svg)

    def test_network_failure_preserves_last_successful_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "assets").mkdir()
            paths = [root / "README.md", root / "assets/activity-graph.svg", root / "assets/activity-graph-light.svg"]
            for path in paths:
                path.write_text("last successful content", encoding="utf-8")
            with patch.object(profile, "ROOT", root), patch.dict(os.environ, {"GITHUB_TOKEN": "test-token"}), \
                    patch.object(profile, "fetch_repos", return_value=[]), \
                    patch.object(profile, "fetch_contribution_calendar", side_effect=RuntimeError("API unavailable")):
                with self.assertRaisesRegex(RuntimeError, "API unavailable"):
                    profile.main()
            for path in paths:
                self.assertEqual(path.read_text(encoding="utf-8"), "last successful content")

    def test_artwork_is_self_contained_and_supports_reduced_motion(self):
        for theme in ("dark", "light"):
            for svg in (hero(theme), project(theme, "bcore"), project(theme, "minecraft-panel"), footer(theme)):
                root = ET.fromstring(svg)
                self.assertEqual(root.attrib["viewBox"].split()[2], "1200")
                self.assertIn("prefers-reduced-motion: reduce", svg)
                self.assertNotIn("<script", svg)
                self.assertNotIn("foreignObject", svg)
                self.assertNotIn("<image", svg)


if __name__ == "__main__":
    unittest.main()
