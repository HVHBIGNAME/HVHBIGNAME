#!/usr/bin/env python3
"""Render one animated SVG atlas per theme, with independently linkable views."""

import json
from datetime import date
from html import escape
from pathlib import Path

from illustrations import ART, core, scene_styles

ROOT = Path(__file__).resolve().parents[1]
PALETTES = {
    "dark": {
        "bg": "#101310", "panel": "#171c16", "fg": "#f0f2e8",
        "muted": "#a1ad9b", "line": "#30392c", "accent": "#d2ff5a",
        "soft": "#344620", "secondary": "#c0a6ff", "empty": "#252e20",
        "levels": ["#252e20", "#486029", "#789c34", "#a6d546", "#d2ff5a"],
    },
    "light": {
        "bg": "#f3f2e9", "panel": "#e9ebdf", "fg": "#20271b",
        "muted": "#616d55", "line": "#cdd3c0", "accent": "#496817",
        "soft": "#dce8bd", "secondary": "#7050b4", "empty": "#dce1d0",
        "levels": ["#dce1d0", "#b7ca86", "#8aab4c", "#638726", "#496817"],
    },
}

VIEW_HEIGHT = 420
CYCLE_SECONDS = 16
PROJECTS = {
    "bcore": {
        "name": "BCore", "eyebrow": "01 / WORLD ENGINE", "status": "ALPHA",
        "description": ("Свой Minecraft-сервер на Rust.", "Миры, свет, нативные плагины и JVM-мост."),
        "mobile": ("Minecraft-сервер на Rust.", "Миры, свет, плагины и JVM-мост."),
        "tech": "RUST / WORLDGEN / NATIVE PLUGINS / JVM", "mobile_meta": "Rust · alpha",
        "dark": ("#d2ff5a", "#344620"), "light": ("#496817", "#dce8bd"),
    },
    "minecraft-panel": {
        "name": "emberdeck.", "eyebrow": "02 / CONTROL ROOM", "status": "EARLY RELEASE",
        "description": ("Minecraft-панель в одном Rust-бинарнике.", "Серверы, консоль, SFTP и резервные копии."),
        "mobile": ("Панель для Minecraft на Rust.", "Серверы, SFTP и резервные копии."),
        "tech": "SELF-HOSTED / LINUX / SFTP / CLI", "mobile_meta": "Rust · ранний релиз",
        "dark": ("#efac79", "#463327"), "light": ("#9b4d24", "#f0dccb"),
    },
    "softdownloader": {
        "name": "SoftDownloader", "eyebrow": "03 / DESKTOP KIT", "status": "WINDOWS APP",
        "description": ("Каталог программ в одном EXE.", "Установка очередью и перенос списка ПО."),
        "mobile": ("Менеджер программ для Windows.", "Установка и перенос списка ПО."),
        "tech": "RUST + EGUI / WINDOWS / ONE EXE", "mobile_meta": "Rust · egui · Windows",
        "dark": ("#91d8ff", "#233d4b"), "light": ("#21678b", "#d5e8ef"),
    },
    "opencode-pocket": {
        "name": "OpenCode Pocket", "eyebrow": "04 / CODE WITH YOU", "status": "MOBILE CLIENT",
        "description": ("OpenCode на Android и iOS.", "Сессии, промпты и подключение по QR."),
        "mobile": ("OpenCode на Android и iOS.", "Твои сессии с компьютера — по QR."),
        "tech": "REACT / TYPESCRIPT / COMPANION BRIDGE", "mobile_meta": "Android · iOS · QR",
        "dark": ("#c6adff", "#372b4e"), "light": ("#7550a7", "#e7def1"),
    },
}
VIEWS = ("hero", *PROJECTS, "signal")


def text(x, y, value, size=14, fill="fg", palette=None, **attrs):
    palette = palette or PALETTES["dark"]
    attributes = " ".join(
        f'{key.rstrip("_").replace("_", "-")}="{escape(str(value), quote=True)}"'
        for key, value in attrs.items()
    )
    return (
        f'<text x="{x}" y="{y}" font-size="{size}" '
        f'fill="{palette.get(fill, fill)}" {attributes}>{escape(str(value))}</text>'
    )


def stylesheet(height):
    return f'''
    text {{ font-family: Arial, Helvetica, sans-serif; }}
    .mono {{ font-family: 'Courier New', Courier, monospace; }}
    .mobile {{ display: none; }}
    .levitate {{ animation: levitate {CYCLE_SECONDS}s ease-in-out infinite; animation-delay: var(--phase, 0s); }}
    .orbit {{ stroke-dasharray: 7 24; animation: orbit {CYCLE_SECONDS}s linear infinite; }}
    .heartbeat {{ animation: heartbeat 4s ease-in-out infinite; }}
    .world-beam {{ animation: beam {CYCLE_SECONDS}s ease-in-out infinite; animation-delay: var(--phase, 0s); }}
    .relay {{ animation: relay {CYCLE_SECONDS}s linear infinite; }}
    .scan {{ animation: scan {CYCLE_SECONDS}s linear infinite; }}
    @keyframes levitate {{ 0%,100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-9px); }} }}
    @keyframes orbit {{ to {{ stroke-dashoffset: -248; }} }}
    @keyframes heartbeat {{ 0%,100% {{ opacity:.4; }} 50% {{ opacity:1; }} }}
    @keyframes beam {{ 0%,48%,100% {{ transform:translateY(-30px); opacity:0; }} 53% {{ opacity:.3; }} 77% {{ transform:translateY(40px); opacity:.3; }} 82% {{ transform:translateY(40px); opacity:0; }} }}
    @keyframes relay {{ from {{ transform:translateY(-200px); }} to {{ transform:translateY({height}px); }} }}
    @keyframes scan {{ 0% {{ transform:translateX(0); opacity:0; }} 10%,85% {{ opacity:.32; }} 100% {{ transform:translateX(1090px); opacity:0; }} }}
    {scene_styles(CYCLE_SECONDS)}
    @media (max-width: 600px) {{
      .desktop {{ display:none; }} .mobile {{ display:inline; }}
      .signal-title {{ font-size:44px; }} .signal-auto {{ font-size:29px; }}
      .signal-value {{ font-size:102px; }} .signal-label {{ font-size:34px; letter-spacing:0; }}
      .signal-date {{ font-size:27px; }} .month-label {{ display:none; }}
    }}
    @media (prefers-reduced-motion: reduce) {{ * {{ animation:none !important; }} .relay, .scan {{ display:none; }} }}
    '''


def document(title, description, height, body, theme, views=()):
    p = PALETTES[theme]
    height_attr = "" if views else f' height="{height}"'
    view_tags = "".join(f'<view id="{name}" viewBox="0 {i*VIEW_HEIGHT} 1200 {VIEW_HEIGHT}"/>' for i, name in enumerate(views))
    clips = "".join(f'<rect x="1" y="{i*VIEW_HEIGHT+1}" width="1198" height="{VIEW_HEIGHT-2}" rx="20"/>' for i in range(len(views)))
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200"{height_attr} viewBox="0 0 1200 {height}" role="img" aria-labelledby="title desc">
    <title id="title">{escape(title)}</title>
    <desc id="desc">{escape(description)}</desc>
    {view_tags}
    <defs>
      <pattern id="grid" width="30" height="30" patternUnits="userSpaceOnUse"><path d="M30 0H0V30" fill="none" stroke="{p['line']}" stroke-width=".7"/></pattern>
      <radialGradient id="aura"><stop offset="0" stop-color="{p['accent']}" stop-opacity=".16"/><stop offset="1" stop-color="{p['accent']}" stop-opacity="0"/></radialGradient>
      <linearGradient id="carrier" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{p['accent']}" stop-opacity="0"/><stop offset=".75" stop-color="{p['accent']}"/><stop offset="1" stop-color="{p['accent']}" stop-opacity="0"/></linearGradient>
      <clipPath id="atlas-clips">{clips}</clipPath>
    </defs>
    <style>{stylesheet(height)}</style>
    {body}
    </svg>'''
    return "\n".join(line.rstrip() for line in svg.splitlines()) + "\n"


def frame(p):
    return f'''
    <rect x=".5" y=".5" width="1199" height="419" rx="20" fill="{p['bg']}" stroke="{p['line']}"/>
    <path d="M26 22V398" stroke="{p['line']}" stroke-width="2"/>
    <circle class="heartbeat" cx="26" cy="42" r="5" fill="{p['accent']}" opacity=".55"/>
    '''


def button(p, mobile=False):
    x, y, width, height, font = (778, 318, 378, 66, 39) if mobile else (930, 331, 226, 52, 19)
    return (
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{height/2}" fill="{p["accent"]}"/>'
        + text(x+width/2, y+height*.65, "ОТКРЫТЬ ↗", font, "bg", p, font_weight=700, text_anchor="middle")
    )


def hero_body(theme):
    p = PALETTES[theme]
    return frame(p) + f'''
    <g class="desktop">
      <path d="M52 74H1156M52 352H1156" stroke="{p['line']}"/>
      <path d="M53 28v25m11-25v25M53 41h11m16-13 9 25 9-25" fill="none" stroke="{p['accent']}" stroke-width="3"/>
      {text(117, 50, 'HVHBIGNAME', 24, 'fg', p, font_weight=700, letter_spacing=2)}
      {text(1156, 48, 'ВАЙБКОДЕР1337 / INDEPENDENT SOFTWARE', 14, 'muted', p, class_='mono', text_anchor='end')}
      {text(53, 119, 'CODE / CURIOSITY / CONTROL', 14, 'muted', p, class_='mono', letter_spacing=2)}
      {text(47, 222, 'VIBE IN.', 110, 'fg', p, font_weight=900, letter_spacing=-6)}
      {text(48, 316, 'SYSTEMS OUT.', 86, 'accent', p, font_weight=900, letter_spacing=-4, textLength=655, lengthAdjust='spacingAndGlyphs')}
      <g transform="translate(951 216) scale(.86)">{core(p)}</g>
      {text(53, 391, 'RUST / TYPESCRIPT / MINECRAFT / DESKTOP / MOBILE', 15, 'fg', p, class_='mono')}
      {text(1156, 391, f'{len(PROJECTS):02d} SELECTED BUILDS ↓', 14, 'muted', p, class_='mono', text_anchor='end')}
    </g>
    <g class="mobile">
      {text(51, 66, 'HVHBIGNAME', 49, 'fg', p, font_weight=700, letter_spacing=2)}
      {text(1155, 64, '1337', 30, 'muted', p, class_='mono', text_anchor='end')}
      <path d="M52 96H1156" stroke="{p['line']}"/>
      {text(44, 242, 'VIBE IN.', 158, 'fg', p, font_weight=900, letter_spacing=-7, textLength=810, lengthAdjust='spacingAndGlyphs')}
      {text(47, 375, 'SYSTEMS OUT.', 126, 'accent', p, font_weight=900, letter_spacing=-5, textLength=1100, lengthAdjust='spacingAndGlyphs')}
      <g transform="translate(1035 198) scale(.4)">{core(p)}</g>
    </g>'''


def project_body(theme, name):
    item = PROJECTS[name]
    p = {**PALETTES[theme], **dict(zip(("accent", "soft"), item[theme]))}
    art = ART[name](p)
    title_size = 80 if name in ("bcore", "minecraft-panel") else 66
    return frame(p) + f'''
    <g class="desktop">
      <ellipse cx="960" cy="199" rx="192" ry="143" fill="{p['soft']}" opacity=".18"/>
      <rect x="779" y="88" width="353" height="220" fill="url(#grid)" opacity=".55"/>
      {text(53, 49, item['eyebrow'], 15, 'muted', p, class_='mono', letter_spacing=2)}
      {text(1156, 49, item['status'], 14, 'accent', p, class_='mono', text_anchor='end')}
      {text(49, 139, item['name'], title_size, 'fg', p, font_weight=900, letter_spacing=-3)}
      {text(53, 204, item['description'][0], 28, 'fg', p)}
      {text(53, 244, item['description'][1], 27, 'muted', p)}
      <g transform="translate(965 201)">{art}</g>
      <path d="M53 313H1156" stroke="{p['line']}"/>
      {text(53, 365, item['tech'], 17, 'muted', p, class_='mono')}
      {button(p)}
    </g>
    <g class="mobile">
      <g opacity=".18" transform="translate(990 193) scale(1.05)">{art}</g>
      {text(53, 45, item['eyebrow'], 26, 'muted', p, class_='mono', letter_spacing=1)}
      {text(47, 125, item['name'], 96 if name in ('bcore', 'minecraft-panel') else 85, 'fg', p, font_weight=900, letter_spacing=-3)}
      {text(53, 212, item['mobile'][0], 50, 'fg', p)}
      {text(53, 273, item['mobile'][1], 49, 'fg', p)}
      {text(53, 361, item['mobile_meta'], 38, 'muted', p)}
      {button(p, mobile=True)}
    </g>'''


def signal_body(days, theme):
    p = PALETTES[theme]
    total = sum(count for _, count in days)
    active = sum(count > 0 for _, count in days)
    peak = max(count for _, count in days)
    parts = [frame(p),
        text(53, 59, "BUILD SIGNAL / 90D", 30, "fg", p, class_="signal-title", font_weight=700),
        text(1156, 56, "↻ КАЖДЫЙ ЧАС", 18, "muted", p, class_="signal-auto", text_anchor="end"),
        f'<path d="M53 83H1156M53 227H1156" stroke="{p["line"]}"/>',
    ]
    for x, number, label in ((53, total, "CONTRIB."), (449, active, "АКТИВНЫХ ДНЕЙ"), (843, peak, "ПИК / ДЕНЬ")):
        parts.append(text(x, 174, number, 84, "fg", p, class_="signal-value", font_weight=700, letter_spacing=-3))
        parts.append(text(x+2, 210, label, 17, "muted", p, class_="mono signal-label", letter_spacing=1))
    step = 1097 / len(days)
    for y in (239, 290, 345):
        parts.append(f'<path d="M53 {y}H1150" stroke="{p["line"]}" stroke-dasharray="2 6"/>')
    for index, (day, count) in enumerate(days):
        x = 53 + index*step
        height = 2 if count == 0 else 103*count/peak
        y = 347 if count == 0 else 343-height
        level = min(4, (4*count+peak-1)//peak) if peak else 0
        parts.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{step-3:.2f}" height="{height:.2f}" rx="2" fill="{p["levels"][level]}"><title>{day.isoformat()}: {count} contributions</title></rect>')
    parts.extend([
        f'<path class="scan" d="M53 238V343" stroke="{p["accent"]}" opacity=".3"/>',
        text(53, 385, days[0][0].isoformat(), 15, "muted", p, class_="mono signal-date"),
        text(1156, 385, days[-1][0].isoformat() + " / UTC", 15, "muted", p, class_="mono signal-date", text_anchor="end"),
    ])
    return "\n".join(parts)


def hero(theme):
    return document("HVHBIGNAME — Vibe in. Systems out.", "Вайбкодер1337. Rust, TypeScript, Minecraft, desktop и mobile.", VIEW_HEIGHT, hero_body(theme), theme)


def project(theme, name):
    item = PROJECTS[name]
    return document(item["name"], " ".join(item["description"]) + " " + item["status"], VIEW_HEIGHT, project_body(theme, name), theme)


def build_atlas(days, theme):
    sections = [hero_body(theme), *(project_body(theme, name) for name in PROJECTS), signal_body(days, theme)]
    groups = []
    for index, (name, body) in enumerate(zip(VIEWS, sections)):
        phase = -(CYCLE_SECONDS-index*CYCLE_SECONDS/len(VIEWS))
        groups.append(f'<g id="scene-{name}" transform="translate(0 {index*VIEW_HEIGHT})" style="--phase:{phase:.4f}s">{body}</g>')
    groups.append('<g clip-path="url(#atlas-clips)"><g class="relay"><rect x="24" y="0" width="4" height="190" rx="2" fill="url(#carrier)"/></g></g>')
    return document(
        "HVHBIGNAME / connected builds",
        "Анимированное портфолио: BCore, emberdeck, SoftDownloader и OpenCode Pocket. Общий 16-секундный цикл; публичная активность GitHub обновляется каждый час.",
        len(VIEWS)*VIEW_HEIGHT, "\n".join(groups), theme, views=VIEWS,
    )


def activity_json(days):
    return json.dumps({"source": "GitHub public contributions", "days": [{"date": day.isoformat(), "count": count} for day, count in days]}, indent=2) + "\n"


def load_activity(path):
    payload = json.loads(path.read_text(encoding="utf-8"))
    days = [(date.fromisoformat(day["date"]), day["count"]) for day in payload["days"]]
    if len(days) != 90 or any(not isinstance(count, int) or count < 0 for _, count in days):
        raise ValueError("Activity cache must contain 90 non-negative daily counts")
    if any((right[0]-left[0]).days != 1 for left, right in zip(days, days[1:])):
        raise ValueError("Activity cache must be chronological and contiguous")
    return days


def main():
    days = load_activity(ROOT / "assets/activity.json")
    for theme in PALETTES:
        path = ROOT / "assets" / f"profile-{theme}.svg"
        path.write_text(build_atlas(days, theme), encoding="utf-8", newline="\n")
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
