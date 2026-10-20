"""Regression checks for the data that gets published automatically."""

import os
import re
import tempfile
import unittest
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

import generate_profile as profile
from brand import logo
from design import PALETTES, PROJECTS, VIEWS, VIEW_HEIGHT, activity_json, build_atlas, hero, load_activity, project


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
            paths = [root / "README.md", root / "assets/profile-dark.svg", root / "assets/profile-light.svg", root / "assets/activity.json"]
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
            for svg in (hero(theme), *(project(theme, name) for name in PROJECTS)):
                root = ET.fromstring(svg)
                self.assertEqual(root.attrib["viewBox"].split()[2], "1200")
                self.assertIn("prefers-reduced-motion: reduce", svg)
                self.assertNotIn("<script", svg)
                self.assertNotIn("foreignObject", svg)
                self.assertNotIn("<image", svg)

    def test_atlas_views_have_equal_aspect_ratio_and_no_duplicate_ids(self):
        days = profile.contribution_window(calendar_fixture())
        ns = {"svg": "http://www.w3.org/2000/svg"}
        for theme in ("dark", "light"):
            root = ET.fromstring(build_atlas(days, theme))
            views = root.findall("svg:view", ns)
            self.assertEqual([view.attrib["id"] for view in views], list(VIEWS))
            self.assertTrue(all(view.attrib["viewBox"].split()[2:] == ["1200", str(VIEW_HEIGHT)] for view in views))
            self.assertNotIn("height", root.attrib)
            ids = [node.attrib["id"] for node in root.iter() if "id" in node.attrib]
            self.assertEqual(len(ids), len(set(ids)))
            self.assertEqual(len(root.findall(".//svg:rect[svg:title]", ns)), 90)

    def test_logo_exports_match_the_atlas_and_local_svg_references_resolve(self):
        days = profile.contribution_window(calendar_fixture())
        for theme, palette in PALETTES.items():
            atlas = ET.fromstring(build_atlas(days, theme))
            mark = ET.fromstring(logo(palette))
            exported = [node.attrib for node in mark.iter() if 'data-letter' in node.attrib]
            embedded = [node.attrib for node in atlas.iter() if 'data-letter' in node.attrib]
            self.assertEqual([node['data-letter'] for node in exported], ['H', 'V', 'H'])
            self.assertEqual(exported, embedded)
            for root in (atlas, mark):
                ids = {node.attrib['id'] for node in root.iter() if 'id' in node.attrib}
                for node in root.iter():
                    if 'href' in node.attrib:
                        self.assertTrue(node.attrib['href'].startswith('#'))
                        self.assertIn(node.attrib['href'][1:], ids)
                    for value in node.attrib.values():
                        for reference in re.findall(r'url\(#([^)]*)\)', value):
                            self.assertIn(reference, ids)

    def test_refresh_publishes_atlases_and_cache_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "assets").mkdir()
            readme = root / "README.md"
            readme.write_text("curated cards\n" + profile.START_MARKER + "old log" + profile.END_MARKER + "\nfooter", encoding="utf-8")
            with patch.object(profile, "ROOT", root), patch.dict(os.environ, {"GITHUB_TOKEN": "test-token"}), \
                    patch.object(profile, "fetch_repos", return_value=[repo_fixture("public-build")]), \
                    patch.object(profile, "fetch_contribution_calendar", return_value=calendar_fixture()), \
                    patch("builtins.print"):
                profile.main()
                self.assertTrue(readme.read_text(encoding="utf-8").startswith("curated cards\n"))
                self.assertTrue(readme.read_text(encoding="utf-8").endswith("\nfooter"))
                self.assertEqual(len(load_activity(root / "assets/activity.json")), 90)
                for theme in ("dark", "light"):
                    atlas = ET.parse(root / f"assets/profile-{theme}.svg").getroot()
                    self.assertEqual(len(atlas.findall("{http://www.w3.org/2000/svg}view")), 6)
                before = {path: path.read_bytes() for path in root.rglob("*") if path.is_file()}
                profile.main()
                self.assertEqual(before, {path: path.read_bytes() for path in before})

    def test_activity_cache_round_trip_and_missing_day_rejection(self):
        days = profile.contribution_window(calendar_fixture())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "activity.json"
            path.write_text(activity_json(days), encoding="utf-8")
            self.assertEqual(load_activity(path), days)
            path.write_text(activity_json(days[:-1]), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_activity(path)


class MotionLayerTests(unittest.TestCase):
    def setUp(self):
        self.days = profile.contribution_window(calendar_fixture())
        self.ns = {"svg": "http://www.w3.org/2000/svg"}

    def test_each_scene_is_clipped_locally_and_relay_is_shared(self):
        for theme in ("dark", "light"):
            atlas = ET.fromstring(build_atlas(self.days, theme))
            frame = atlas.find('.//svg:clipPath[@id="scene-frame"]/svg:rect', self.ns)
            self.assertEqual(frame.get("height"), str(VIEW_HEIGHT - 2))
            for index, name in enumerate(VIEWS):
                scene = atlas.find(f'svg:g[@id="scene-{name}"]', self.ns)
                self.assertEqual(scene.get("transform"), f"translate(0 {index * VIEW_HEIGHT})")
                self.assertEqual(len(scene), 1)
                clipped = scene[0]
                self.assertEqual(clipped.get("clip-path"), f"url(#scene-frame-{name})")
                self.assertEqual(clipped[0].get("class"), "stage")
                self.assertEqual(len(clipped.findall('.//svg:g[@class="relay"]', self.ns)), 0)
            relays = atlas.findall('.//svg:g[@class="relay"]', self.ns)
            self.assertEqual(len(relays), 1)
            self.assertEqual(atlas[-1].get("clip-path"), "url(#atlas-clips)")
            self.assertIsNotNone(atlas[-1].find('.//svg:g[@class="relay"]', self.ns))

    def test_motion_does_not_replace_layout_transforms(self):
        animated = {"rise", "art-enter", "relay", "sheen", "shard", "world-voxel",
                    "server-card", "server-core", "handoff", "sapling", "debris", "fan"}
        for theme in PALETTES:
            root = ET.fromstring(build_atlas(self.days, theme))
            for element in root.iter():
                if animated.intersection(element.get("class", "").split()):
                    self.assertNotIn("transform", element.attrib, element.attrib)
            anchors = [e for scene in root if "motion-active" in scene.get("class", "").split()
                       for e in scene.iter() if "art-anchor" in e.get("class", "").split()]
            self.assertEqual(len(anchors), 10)
            for anchor in anchors:
                self.assertIn("transform", anchor.attrib)
                self.assertEqual(anchor[0].get("class"), "art-enter")

    def test_styles_have_no_unexpanded_template_braces(self):
        for theme in PALETTES:
            root = ET.fromstring(build_atlas(self.days, theme))
            css = root.find("svg:style", self.ns).text
            self.assertNotIn("{{", css)
            self.assertNotIn("}}", css)

    def test_card_order_cannot_offset_the_shared_clock(self):
        for theme in PALETTES:
            markup = build_atlas(self.days, theme)
            self.assertNotIn("--scene", markup)
            root = ET.fromstring(markup)
            for node in root.iter():
                style = node.get("style", "")
                self.assertNotIn("--phase:", style)
                self.assertNotIn("--cycle:", style)
            for name in VIEWS:
                scene = root.find(f'svg:g[@id="scene-{name}"]', self.ns)
                self.assertNotIn("style", scene.attrib)

    def test_standalone_cards_have_the_same_frame_clipping(self):
        for theme in PALETTES:
            cards = (hero(theme), *(project(theme, name) for name in PROJECTS),
                     profile.build_svg(calendar_fixture(), theme))
            for card in cards:
                root = ET.fromstring(card)
                self.assertEqual(root[-1].get("clip-path"), "url(#scene-frame)")

    def test_logo_exports_are_static(self):
        for theme in ("dark", "light"):
            markup = logo(PALETTES[theme])
            self.assertNotIn("animation:", markup)
            self.assertIn("<svg", markup)
            ET.fromstring(markup)

    def test_published_motion_uses_native_svg_timing(self):
        root = ET.fromstring(build_atlas(self.days, "dark"))
        css = root.find("svg:style", self.ns).text
        self.assertNotIn("@keyframes", css)
        self.assertNotRegex(css, r"animation(?:-[\w-]+)?\s*:")
        effects = root.findall('.//svg:animate', self.ns) + root.findall('.//svg:animateTransform', self.ns)
        self.assertGreater(len(effects), 100)
        for effect in effects:
            times = [float(t) for t in effect.get('keyTimes').split(';')]
            self.assertEqual(times, sorted(set(times)))
            self.assertEqual((times[0], times[-1]), (0, 1))
            self.assertEqual(len(times), len(effect.get('values').split(';')))
            if effect.get('calcMode') == 'spline':
                self.assertEqual(len(times)-1, len(effect.get('keySplines').split(';')))
        static = [g for g in root if 'motion-static' in g.get('class', '').split()]
        self.assertEqual(len(static), 7)
        for group in static:
            self.assertFalse(group.findall('.//svg:animate', self.ns))
            self.assertFalse(group.findall('.//svg:animateTransform', self.ns))
        for element in root.iter():
            if element.get('data-animation') in ('art-enter', 'bar-up'):
                for effect in element:
                    if effect.tag in ('{http://www.w3.org/2000/svg}animate', '{http://www.w3.org/2000/svg}animateTransform'):
                        self.assertEqual(effect.get('begin'), '0.45s')
                        self.assertEqual(effect.get('dur'), '2.2s')


if __name__ == "__main__":
    unittest.main()
