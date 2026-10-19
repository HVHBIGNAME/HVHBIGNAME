#!/usr/bin/env python3
"""Render one animated SVG atlas per theme, with independently linkable views."""

import json
from datetime import date
from html import escape
from pathlib import Path

import motion
from brand import defs as brand_defs
from brand import logo, plate, styles as brand_styles, symbol
from illustrations import ART, scene_styles

ROOT = Path(__file__).resolve().parents[1]
PALETTES = {
    "dark": {
        "bg": "#0d1117", "panel": "#161c24", "fg": "#f1f3f5",
        "muted": "#a0a8b2", "line": "#2a323d", "accent": "#bef264",
        "shadow": "#000000",
        "soft": "#202d23", "empty": "#202832",
        "metal": ("#f7fafb", "#a6b0b8", "#404c56"),
        "levels": ["#202832", "#344b30", "#587b39", "#85b44b", "#bef264"],
    },
    "light": {
        "bg": "#f6f7f9", "panel": "#e9edf1", "fg": "#202730",
        "muted": "#535e68", "line": "#d7dce2", "accent": "#427018",
        "shadow": "#617080",
        "soft": "#e1e9d8", "empty": "#d9dfe5",
        "metal": ("#fdfefe", "#9aa6b2", "#4d5c6a"),
        "levels": ["#d9ddcc", "#b4c296", "#8aa861", "#6c8f3a", "#4f7d0a"],
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
        "dark": ("#c6ff3d", "#22330f"), "light": ("#4f7d0a", "#dce9c2"),
    },
    "minecraft-panel": {
        "name": "emberdeck.", "eyebrow": "02 / CONTROL ROOM", "status": "EARLY RELEASE",
        "description": ("Minecraft-панель в одном Rust-бинарнике.", "Серверы, консоль, SFTP и резервные копии."),
        "mobile": ("Панель для Minecraft на Rust.", "Серверы, SFTP и резервные копии."),
        "tech": "SELF-HOSTED / LINUX / SFTP / CLI", "mobile_meta": "Rust · ранний релиз",
        "dark": ("#ffab5e", "#33220f"), "light": ("#9a4d12", "#f2e0c8"),
    },
    "softdownloader": {
        "name": "SoftDownloader", "eyebrow": "03 / DESKTOP KIT", "status": "WINDOWS APP",
        "description": ("Каталог программ в одном EXE.", "Установка очередью и перенос списка ПО."),
        "mobile": ("Менеджер программ для Windows.", "Установка и перенос списка ПО."),
        "tech": "RUST + EGUI / WINDOWS / ONE EXE", "mobile_meta": "Rust · egui · Windows",
        "dark": ("#6fe3ff", "#0d2f38"), "light": ("#1c6675", "#d3e8ea"),
    },
    "opencode-pocket": {
        "name": "OpenCode Pocket", "eyebrow": "04 / CODE WITH YOU", "status": "MOBILE CLIENT",
        "description": ("OpenCode на Android и iOS.", "Сессии, промпты и подключение по QR."),
        "mobile": ("OpenCode на Android и iOS.", "Твои сессии с компьютера — по QR."),
        "tech": "REACT / TYPESCRIPT / COMPANION BRIDGE", "mobile_meta": "Android · iOS · QR",
        "dark": ("#c8a8ff", "#221a33"), "light": ("#64409c", "#e4dbf2"),
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
    text {{ font-family: 'Inter', 'Segoe UI', Arial, Helvetica, sans-serif; }}
    .mono {{ font-family: 'JetBrains Mono', 'Cascadia Mono', Consolas, 'Courier New', monospace; }}
    .mobile {{ display: none; }}
    .orbit {{ stroke-dasharray: 7 24; animation: orbit {CYCLE_SECONDS}s linear infinite; }}
    .heartbeat {{ animation: heartbeat 4s ease-in-out infinite; }}
    @keyframes orbit {{ to {{ stroke-dashoffset: -248; }} }}
    @keyframes heartbeat {{ 0%,100% {{ opacity:.4; }} 50% {{ opacity:1; }} }}
    {motion.styles(height)}
    {scene_styles(CYCLE_SECONDS)}
    {brand_styles()}
    @media (max-width: 600px) {{
      .desktop {{ display:none; }} .mobile {{ display:inline; }}
      .signal-title {{ font-size:44px; }} .signal-auto {{ font-size:29px; }}
      .signal-value {{ font-size:102px; }} .signal-label {{ font-size:34px; letter-spacing:0; }}
      .signal-date {{ font-size:27px; }} .month-label {{ display:none; }}
    }}
    '''


def document(title, description, height, body, theme, views=()):
    p = PALETTES[theme]
    height_attr = "" if views else f' height="{height}"'
    view_tags = "".join(f'<view id="{name}" viewBox="0 {i*VIEW_HEIGHT} 1200 {VIEW_HEIGHT}"/>' for i, name in enumerate(views))
    clips = "".join(f'<rect x="1" y="{i*VIEW_HEIGHT+1}" width="1198" height="{VIEW_HEIGHT-2}" rx="10"/>' for i in range(max(1, len(views))))
    backdrops = "".join(motion.backdrop_defs(scene_palette(theme, name), name) for name in VIEWS)
    if not views:
        body = f'<g clip-path="url(#scene-frame)">{body}</g>'
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200"{height_attr} viewBox="0 0 1200 {height}" role="img" aria-labelledby="title desc">
    <title id="title">{escape(title)}</title>
    <desc id="desc">{escape(description)}</desc>
    {view_tags}
    <defs>
      {symbol(p)}
      {brand_defs(p)}
      {motion.grain(p)}
      {motion.grain_clip()}
      {motion.sweep_defs(p)}
      {backdrops}
      <clipPath id="scene-frame" clipPathUnits="userSpaceOnUse"><rect x="1" y="1" width="1198" height="{VIEW_HEIGHT-2}" rx="10"/></clipPath>
      <clipPath id="atlas-clips">{clips}</clipPath>
    </defs>
    <style>{stylesheet(height)}</style>
    {body}
    </svg>'''
    return "\n".join(line.rstrip() for line in svg.splitlines()) + "\n"


def rail(p):
    return f'''
    <g class="rail">
      <path d="M26 1V419" stroke="{p['line']}" stroke-width="1"/>
      <circle class="beat" cx="26" cy="42" r="5" fill="{p['accent']}"/>
    </g>'''


def plate_art(p, scale, rotate, origin):
    return f'''
    <g class="art-anchor plate-holder" transform="translate({origin}) rotate({rotate}) scale({scale})">
      <g class="art-enter"><g transform="translate(-126 -64)">{plate(p)}</g></g>
    </g>'''


def hero_body(theme):
    p = PALETTES[theme]
    return f'''
    <g class="desktop" style="--idx:0">
      <g class="rise">
        {text(64, 52, 'HVHBIGNAME', 18, 'fg', p, class_='mono', letter_spacing=2.4)}
        {text(1156, 52, 'ЛИЧНАЯ МАСТЕРСКАЯ / 1337', 14, 'muted', p, class_='mono', text_anchor='end')}
      </g>
      <path class="wipe" pathLength="100" stroke-dasharray="100" d="M64 74H1156" stroke="{p['line']}"/>
      {plate_art(p, 1.62, -7, '925 214')}
      <g transform="translate(66 152)">
        <text class="rise" y="68" font-size="104" font-weight="900" letter-spacing="-5" fill="{p['fg']}" style="--idx:0">BIGNAME</text>
        <text class="rise" y="112" font-size="25" fill="{p['muted']}" style="--idx:1">Игровые серверы. Утилиты. Свои проекты.</text>
        <g class="rise" style="--idx:2">
          <rect x="0" y="132" width="52" height="3" rx="1.5" fill="{p['accent']}"/>
          {text(62, 137, 'RUST / TYPESCRIPT / СВОИ ПРОЕКТЫ', 15, 'accent', p, class_='mono', letter_spacing=2)}
        </g>
      </g>
      <path class="wipe" pathLength="100" stroke-dasharray="100" d="M64 336H1156" stroke="{p['line']}"/>
      <g class="rise" style="--idx:3">
        {text(64, 378, 'MINECRAFT / DESKTOP / MOBILE', 15, 'muted', p, class_='mono', letter_spacing=1)}
        {text(1156, 378, f'{len(PROJECTS):02d} ПРОЕКТА НИЖЕ ↓', 14, 'muted', p, class_='mono', text_anchor='end')}
      </g>
      <rect class="sweep" x="-260" y="0" width="240" height="420" fill="url(#sweep-fade)" opacity=".5"/>
    </g>
    <g class="mobile" style="--idx:1">
      <g class="rise">
        {text(53, 66, 'HVHBIGNAME', 38, 'fg', p, class_='mono', letter_spacing=2)}
        {text(1156, 64, '1337', 30, 'muted', p, class_='mono', text_anchor='end')}
      </g>
      <path class="wipe" pathLength="100" stroke-dasharray="100" d="M53 92H1156" stroke="{p['line']}"/>
      {plate_art(p, .88, -6, '995 205')}
      <g transform="translate(50 180)"><g class="rise" style="--idx:1">
        <text y="86" font-size="128" font-weight="900" letter-spacing="-6" fill="{p['fg']}">BIGNAME</text>
      </g>
      </g>
      <g class="rise" style="--idx:2">
        {text(53, 356, 'RUST / TYPESCRIPT / СВОИ ПРОЕКТЫ', 32, 'muted', p, class_='mono')}
      </g>
    </g>
    {rail(p)}'''


def scene_palette(theme, name):
    if name in PROJECTS:
        return {**PALETTES[theme], **dict(zip(("accent", "soft"), PROJECTS[name][theme]))}
    return PALETTES[theme]


def project_body(theme, name, index):
    item = PROJECTS[name]
    p = scene_palette(theme, name)
    art = ART[name](p)
    title_size = 80 if name in ("bcore", "minecraft-panel") else 66
    reverse = name in ("minecraft-panel", "opencode-pocket")
    art_x, divider_x, text_shift = (238, 418, 396) if reverse else (965, 748, 0)
    art_y, art_scale = {"minecraft-panel": (191, .9), "softdownloader": (190, .92), "opencode-pocket": (188, .85)}.get(name, (201, 1))
    return f'''
    <g class="desktop" style="--idx:{index}">
      <g class="rise" style="--idx:0">
        {text(53, 49, item['eyebrow'], 15, 'muted', p, class_='mono', letter_spacing=2)}
        {text(1156, 49, item['status'], 14, 'accent', p, class_='mono', text_anchor='end')}
      </g>
      <path class="wipe" pathLength="100" stroke-dasharray="100" d="M53 72H1156" stroke="{p['line']}"/>
      <path class="draw" pathLength="100" stroke-dasharray="100" d="M{divider_x} 88V310m-6-222h12m-12 222h12" stroke="{p['line']}"/>
      <g transform="translate({text_shift} 0)">
        <g class="rise" style="--idx:1">
          {text(49, 139, item['name'], title_size, 'fg', p, font_weight=900, letter_spacing=-3)}
        </g>
        <g class="rise" style="--idx:2">
          {text(53, 204, item['description'][0], 28, 'fg', p)}
          {text(53, 244, item['description'][1], 27, 'muted', p)}
        </g>
      </g>
      <g class="art-anchor {'from-left' if reverse else 'from-right'}" transform="translate({art_x} {art_y}) scale({art_scale})">
        <g class="art-enter"><g class="art-detail" style="--phase:-10s">{art}</g></g>
      </g>
      <path class="wipe" pathLength="100" stroke-dasharray="100" d="M53 313H1156" stroke="{p['line']}"/>
      <g class="rise" style="--idx:3">
        {text(53, 365, item['tech'], 17, 'muted', p, class_='mono')}
        {button(p)}
      </g>
      <rect class="sweep" x="-260" y="0" width="240" height="420" fill="url(#sweep-fade)" opacity=".35"/>
    </g>
    <g class="mobile" style="--idx:{index}">
      <g class="art-anchor" opacity=".14" transform="translate(995 193) scale(1.05)">
        <g class="art-enter"><g class="art-detail" style="--phase:-10s">{art}</g></g>
      </g>
      <g class="rise" style="--idx:0">
        {text(53, 45, item['eyebrow'], 26, 'muted', p, class_='mono', letter_spacing=1)}
      </g>
      <g class="rise" style="--idx:1">
        {text(47, 125, item['name'], 96 if name in ('bcore', 'minecraft-panel') else 85, 'fg', p, font_weight=900, letter_spacing=-3)}
      </g>
      <g class="rise" style="--idx:2">
        {text(53, 212, item['mobile'][0], 50, 'fg', p)}
        {text(53, 273, item['mobile'][1], 49, 'fg', p)}
      </g>
      <g class="rise" style="--idx:3">
        {text(53, 361, item['mobile_meta'], 38, 'muted', p)}
        {button(p, mobile=True)}
      </g>
    </g>
    {rail(p)}'''


def signal_body(days, theme, index=0):
    p = PALETTES[theme]
    total = sum(count for _, count in days)
    active = sum(count > 0 for _, count in days)
    peak = max(count for _, count in days)
    parts = [
        text(53, 59, "BUILD SIGNAL / 90D", 30, "fg", p, class_="signal-title rise", font_weight=700),
        text(1156, 56, "↻ КАЖДЫЙ ЧАС", 18, "muted", p, class_="signal-auto mono rise", text_anchor="end"),
        f'<path class="wipe" pathLength="100" stroke-dasharray="100" d="M53 83H1156M53 227H1156" stroke="{p["line"]}"/>',
    ]
    for position, (x, number, label) in enumerate(((53, total, "CONTRIB."), (449, active, "АКТИВНЫХ ДНЕЙ"), (843, peak, "ПИК / ДЕНЬ"))):
        parts.append(f'<g class="rise" style="--idx:{position + 1}">')
        parts.append(text(x, 174, number, 84, "fg", p, class_="signal-value", font_weight=700, letter_spacing=-3))
        parts.append(text(x+2, 210, label, 17, "muted", p, class_="mono signal-label", letter_spacing=1))
        parts.append('</g>')
    step = 1097 / len(days)
    for y in (239, 290, 345):
        parts.append(f'<path d="M53 {y}H1150" stroke="{p["line"]}" stroke-dasharray="2 6"/>')
    parts.append('<g class="bars">')
    for day_index, (day, count) in enumerate(days):
        x = 53 + day_index*step
        height = 2 if count == 0 else 103*count/peak
        y = 347 if count == 0 else 343-height
        level = min(4, (4*count+peak-1)//peak) if peak else 0
        parts.append(
            f'<rect class="bar" style="--n:{day_index}" x="{x:.2f}" y="{y:.2f}" '
            f'width="{step-3:.2f}" height="{height:.2f}" rx="2" fill="{p["levels"][level]}">'
            f'<title>{day.isoformat()}: {count} contributions</title></rect>'
        )
    parts.append('</g>')
    parts.extend([
        f'<path class="scan" d="M53 238V343" stroke="{p["accent"]}" opacity=".3"/>',
        text(53, 385, days[0][0].isoformat(), 15, "muted", p, class_="mono signal-date"),
        text(1156, 385, days[-1][0].isoformat() + " / UTC", 15, "muted", p, class_="mono signal-date", text_anchor="end"),
    ])
    return f'<g style="--idx:{index}">' + "\n".join(parts) + '</g>' + rail(p)


def button(p, mobile=False):
    x, y, width, height, font = (778, 318, 378, 66, 39) if mobile else (930, 331, 226, 52, 19)
    return (
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="3" fill="{p["panel"]}" stroke="{p["line"]}"/>'
        + f'<rect x="{x}" y="{y}" width="3" height="{height}" fill="{p["accent"]}"/>'
        + text(x+width/2+1, y+height*.65, "ОТКРЫТЬ ↗", font, "fg", p, font_weight=700, text_anchor="middle")
    )


def hero(theme):
    return document(
        "HVH / BIGNAME",
        "Личная мастерская HVHBIGNAME. Игровые серверы, утилиты и свои проекты. Rust и TypeScript.",
        VIEW_HEIGHT,
        motion.stage(PALETTES[theme], theme) + hero_body(theme),
        theme,
    )


def project(theme, name):
    item = PROJECTS[name]
    body = motion.stage(scene_palette(theme, name), theme, name) + project_body(theme, name, 0)
    return document(item["name"], " ".join(item["description"]) + " " + item["status"], VIEW_HEIGHT, body, theme)


def build_atlas(days, theme):
    sections = [
        hero_body(theme),
        *(project_body(theme, name, index + 1) for index, name in enumerate(PROJECTS)),
        signal_body(days, theme, len(VIEWS) - 1),
    ]
    groups = []
    for index, (name, body) in enumerate(zip(VIEWS, sections)):
        groups.append(
            f'<g id="scene-{name}" transform="translate(0 {index*VIEW_HEIGHT})" style="--scene:{index}">'
            f'<g clip-path="url(#scene-frame)">{motion.stage(scene_palette(theme, name), theme, name)}{body}</g></g>'
        )
    groups.append(motion.packet(PALETTES[theme]))
    return document(
        "HVHBIGNAME / connected builds",
        "Анимированное портфолио: BCore, emberdeck, SoftDownloader и OpenCode Pocket. "
        "Световой пакет переходит из карточки в карточку при загрузке; публичная активность GitHub обновляется каждый час.",
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
