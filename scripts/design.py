#!/usr/bin/env python3
"""Render one animated SVG atlas per theme, with independently linkable views."""

import json
from datetime import date
from html import escape
from pathlib import Path

from brand import duel, logo, styles as brand_styles, symbol
from illustrations import ART, scene_styles

ROOT = Path(__file__).resolve().parents[1]
PALETTES = {
    "dark": {
        "bg": "#151719", "panel": "#1e2225", "fg": "#eeeae2",
        "muted": "#a5a7a4", "line": "#343a3d", "accent": "#df8f61",
        "soft": "#43352e", "empty": "#282d2e",
        "levels": ["#282d2e", "#4b4d3e", "#877452", "#b5865b", "#df8f61"],
    },
    "light": {
        "bg": "#f0eee7", "panel": "#e5e3db", "fg": "#242b2d",
        "muted": "#656d6b", "line": "#c8cdc6", "accent": "#a44c28",
        "soft": "#e6d4c6", "empty": "#daddd5",
        "levels": ["#daddd5", "#d2bc9d", "#bf9770", "#b3754b", "#a44c28"],
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
        "dark": ("#a9bc80", "#343e30"), "light": ("#506934", "#dae2cb"),
    },
    "minecraft-panel": {
        "name": "emberdeck.", "eyebrow": "02 / CONTROL ROOM", "status": "EARLY RELEASE",
        "description": ("Minecraft-панель в одном Rust-бинарнике.", "Серверы, консоль, SFTP и резервные копии."),
        "mobile": ("Панель для Minecraft на Rust.", "Серверы, SFTP и резервные копии."),
        "tech": "SELF-HOSTED / LINUX / SFTP / CLI", "mobile_meta": "Rust · ранний релиз",
        "dark": ("#dc9870", "#43372e"), "light": ("#9b4d24", "#e9d7c7"),
    },
    "softdownloader": {
        "name": "SoftDownloader", "eyebrow": "03 / DESKTOP KIT", "status": "WINDOWS APP",
        "description": ("Каталог программ в одном EXE.", "Установка очередью и перенос списка ПО."),
        "mobile": ("Менеджер программ для Windows.", "Установка и перенос списка ПО."),
        "tech": "RUST + EGUI / WINDOWS / ONE EXE", "mobile_meta": "Rust · egui · Windows",
        "dark": ("#91b7c5", "#2d3b40"), "light": ("#376574", "#d4e1e3"),
    },
    "opencode-pocket": {
        "name": "OpenCode Pocket", "eyebrow": "04 / CODE WITH YOU", "status": "MOBILE CLIENT",
        "description": ("OpenCode на Android и iOS.", "Сессии, промпты и подключение по QR."),
        "mobile": ("OpenCode на Android и iOS.", "Твои сессии с компьютера — по QR."),
        "tech": "REACT / TYPESCRIPT / COMPANION BRIDGE", "mobile_meta": "Android · iOS · QR",
        "dark": ("#b4a7c6", "#39343f"), "light": ("#745983", "#e1d9e5"),
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
    svg {{ --cycle:{CYCLE_SECONDS}s; }}
    text {{ font-family: Arial, Helvetica, sans-serif; }}
    .mono {{ font-family: 'Courier New', Courier, monospace; }}
    .mobile {{ display: none; }}
    .levitate {{ animation: levitate {CYCLE_SECONDS}s ease-in-out infinite; animation-delay: var(--phase, 0s); }}
    .orbit {{ stroke-dasharray: 7 24; animation: orbit {CYCLE_SECONDS}s linear infinite; }}
    .heartbeat {{ animation: heartbeat 4s ease-in-out infinite; }}
    .world-beam {{ animation: beam {CYCLE_SECONDS}s ease-in-out infinite; animation-delay: var(--phase, 0s); }}
    .relay {{ animation: relay {CYCLE_SECONDS}s linear infinite; }}
    .scan {{ animation: scan {CYCLE_SECONDS}s linear infinite; }}
    @keyframes levitate {{ 0%,100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-3px); }} }}
    @keyframes orbit {{ to {{ stroke-dashoffset: -248; }} }}
    @keyframes heartbeat {{ 0%,100% {{ opacity:.4; }} 50% {{ opacity:1; }} }}
    @keyframes beam {{ 0%,48%,100% {{ transform:translateY(-30px); opacity:0; }} 53% {{ opacity:.3; }} 77% {{ transform:translateY(40px); opacity:.3; }} 82% {{ transform:translateY(40px); opacity:0; }} }}
    @keyframes relay {{ from {{ transform:translateY(-200px); }} to {{ transform:translateY({height}px); }} }}
    @keyframes scan {{ 0% {{ transform:translateX(0); opacity:0; }} 10%,85% {{ opacity:.32; }} 100% {{ transform:translateX(1090px); opacity:0; }} }}
    {scene_styles(CYCLE_SECONDS)}
    {brand_styles(CYCLE_SECONDS)}
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
    clips = "".join(f'<rect x="1" y="{i*VIEW_HEIGHT+1}" width="1198" height="{VIEW_HEIGHT-2}" rx="6"/>' for i in range(len(views)))
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200"{height_attr} viewBox="0 0 1200 {height}" role="img" aria-labelledby="title desc">
    <title id="title">{escape(title)}</title>
    <desc id="desc">{escape(description)}</desc>
    {view_tags}
    <defs>
      {symbol(p)}
      <linearGradient id="carrier" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{p['accent']}" stop-opacity="0"/><stop offset=".75" stop-color="{p['accent']}"/><stop offset="1" stop-color="{p['accent']}" stop-opacity="0"/></linearGradient>
      <clipPath id="atlas-clips">{clips}</clipPath>
    </defs>
    <style>{stylesheet(height)}</style>
    {body}
    </svg>'''
    return "\n".join(line.rstrip() for line in svg.splitlines()) + "\n"


def frame(p):
    return f'''
    <rect x=".5" y=".5" width="1199" height="419" rx="6" fill="{p['bg']}" stroke="{p['line']}"/>
    <path d="M26 22V398" stroke="{p['line']}" stroke-width="2"/>
    <circle class="heartbeat" cx="26" cy="42" r="5" fill="{p['accent']}" opacity=".55"/>
    '''


def button(p, mobile=False):
    x, y, width, height, font = (778, 318, 378, 66, 39) if mobile else (930, 331, 226, 52, 19)
    return (
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="3" fill="{p["panel"]}" stroke="{p["line"]}"/>'
        + text(x+width/2, y+height*.65, "ОТКРЫТЬ ↗", font, "fg", p, font_weight=700, text_anchor="middle")
    )


def hero_body(theme):
    p = PALETTES[theme]
    return frame(p) + f'''
    <g class="desktop">
      {text(53, 48, 'HVHBIGNAME', 17, 'fg', p, class_='mono', letter_spacing=2)}
      {text(1156, 48, 'ЛИЧНАЯ МАСТЕРСКАЯ / 1337', 14, 'muted', p, class_='mono', text_anchor='end')}
      <path d="M53 72H1156M413 104V305M53 349H1156" stroke="{p['line']}"/>
      <g transform="translate(67 127) scale(1.17)">{duel(p)}</g>
      {text(446, 196, 'BIGNAME', 96, 'fg', p, font_weight=900, letter_spacing=-5)}
      {text(451, 249, 'Игровые серверы. Утилиты. Свои проекты.', 27, 'muted', p)}
      {text(451, 293, 'RUST + TYPESCRIPT', 17, 'accent', p, class_='mono', letter_spacing=2)}
      {text(53, 390, 'MINECRAFT / DESKTOP / MOBILE', 15, 'muted', p, class_='mono')}
      {text(1156, 390, f'{len(PROJECTS):02d} ПРОЕКТА НИЖЕ ↓', 14, 'muted', p, class_='mono', text_anchor='end')}
    </g>
    <g class="mobile">
      {text(53, 64, 'HVHBIGNAME', 40, 'fg', p, class_='mono', letter_spacing=2)}
      {text(1156, 62, '1337', 32, 'muted', p, class_='mono', text_anchor='end')}
      <path d="M53 90H1156M53 322H1156" stroke="{p['line']}"/>
      <g transform="translate(63 137) scale(1.18)">{duel(p)}</g>
      {text(420, 246, 'BIGNAME', 132, 'fg', p, font_weight=900, letter_spacing=-6)}
      {text(53, 382, 'RUST / TYPESCRIPT / СВОИ ПРОЕКТЫ', 40, 'muted', p, class_='mono')}
    </g>'''


def project_body(theme, name):
    item = PROJECTS[name]
    p = {**PALETTES[theme], **dict(zip(("accent", "soft"), item[theme]))}
    art = ART[name](p)
    title_size = 80 if name in ("bcore", "minecraft-panel") else 66
    reverse = name in ("minecraft-panel", "opencode-pocket")
    art_x, divider_x, text_shift = (238, 418, 396) if reverse else (965, 748, 0)
    art_y, art_scale = {"minecraft-panel": (191, .9), "softdownloader": (190, .92), "opencode-pocket": (188, .85)}.get(name, (201, 1))
    return frame(p) + f'''
    <g class="desktop">
      <path d="M{divider_x} 88V278m-6-190h12m-12 190h12" stroke="{p['line']}"/>
      {text(53, 49, item['eyebrow'], 15, 'muted', p, class_='mono', letter_spacing=2)}
      {text(1156, 49, item['status'], 14, 'accent', p, class_='mono', text_anchor='end')}
      <g transform="translate({text_shift} 0)">
      {text(49, 139, item['name'], title_size, 'fg', p, font_weight=900, letter_spacing=-3)}
      {text(53, 204, item['description'][0], 28, 'fg', p)}
      {text(53, 244, item['description'][1], 27, 'muted', p)}
      </g>
      <g transform="translate({art_x} {art_y}) scale({art_scale})">{art}</g>
      <path d="M53 313H1156" stroke="{p['line']}"/>
      {text(53, 365, item['tech'], 17, 'muted', p, class_='mono')}
      {button(p)}
    </g>
    <g class="mobile">
      <g opacity=".24" transform="translate(995 193) scale(1.05)">{art}</g>
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
    return document("HVH / BIGNAME", "Личная мастерская HVHBIGNAME. Игровые серверы, утилиты и свои проекты. Rust и TypeScript.", VIEW_HEIGHT, hero_body(theme), theme)


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
        (ROOT / "assets" / f"hvh-mark-{theme}.svg").write_text(logo(PALETTES[theme]), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
