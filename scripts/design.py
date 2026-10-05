#!/usr/bin/env python3
"""Build the profile's original, self-contained SVG artwork (no dependencies)."""

import math
from html import escape
from pathlib import Path

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


def document(title, description, height, body, theme):
    p = PALETTES[theme]
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="{height}" viewBox="0 0 1200 {height}" role="img" aria-labelledby="title desc">
  <title id="title">{escape(title)}</title>
  <desc id="desc">{escape(description)}</desc>
  <defs>
    <pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse">
      <path d="M 32 0 L 0 0 0 32" fill="none" stroke="{p['line']}" stroke-width="0.6"/>
    </pattern>
    <radialGradient id="aura">
      <stop offset="0" stop-color="{p['accent']}" stop-opacity="0.13"/>
      <stop offset="1" stop-color="{p['accent']}" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <style>
    text {{ font-family: Arial, Helvetica, sans-serif; }}
    .mono {{ font-family: 'Courier New', Courier, monospace; }}
    .float {{ animation: float 8s ease-in-out infinite; }}
    .flow {{ stroke-dasharray: 5 18; animation: flow 24s linear infinite; }}
    .pulse {{ animation: pulse 5s ease-in-out infinite; }}
    .hero-mobile {{ display: none; }}
    @media (max-width: 600px) {{ .hero-desktop {{ display: none; }} .hero-mobile {{ display: inline; }} }}
    @keyframes float {{ 0%, 100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-8px); }} }}
    @keyframes flow {{ to {{ stroke-dashoffset: -276; }} }}
    @keyframes pulse {{ 0%, 100% {{ opacity: .45; }} 50% {{ opacity: 1; }} }}
    @media (prefers-reduced-motion: reduce) {{ .float, .flow, .pulse {{ animation: none; }} }}
  </style>
  <rect x="0.5" y="0.5" width="1199" height="{height - 1}" rx="18" fill="{p['bg']}" stroke="{p['line']}"/>
  {body}
</svg>
'''
    return "\n".join(line.rstrip() for line in svg.splitlines()) + "\n"


def cross(x, y, color, size=5):
    return f'<path d="M{x-size} {y}h{size*2}M{x} {y-size}v{size*2}" stroke="{color}" stroke-width="1"/>'


def cube(x, y, size, p, solid=False):
    half_width = size * math.sqrt(3) / 2
    top = [(x, y-size), (x+half_width, y-size/2), (x, y), (x-half_width, y-size/2)]
    left = [(x-half_width, y-size/2), (x, y), (x, y+size), (x-half_width, y+size/2)]
    right = [(x, y), (x+half_width, y-size/2), (x+half_width, y+size/2), (x, y+size)]
    colors = (p["accent"], p["soft"], p["accent"]) if solid else (p["panel"], p["bg"], p["soft"])
    parts = []
    for points, color in zip((left, right, top), (colors[1], colors[2], colors[0])):
        coords = " ".join(f"{px:.2f},{py:.2f}" for px, py in points)
        parts.append(f'<polygon points="{coords}" fill="{color}" stroke="{p["accent"]}" stroke-width="1.15"/>')
    return "".join(parts)


def core(p):
    parts = [
        f'<circle r="175" fill="url(#aura)"/>',
        f'<circle r="149" fill="none" stroke="{p["line"]}"/>',
        f'<circle r="166" fill="none" stroke="{p["line"]}" stroke-dasharray="1 9"/>',
        f'<path d="M-191 0h382M0-181v362" stroke="{p["line"]}" stroke-width="0.8"/>',
        f'<ellipse rx="185" ry="58" transform="rotate(-27)" fill="none" stroke="{p["line"]}"/>',
        f'<ellipse rx="185" ry="58" transform="rotate(-27)" fill="none" stroke="{p["accent"]}" class="flow" opacity=".7"/>',
        '<g class="float">',
        cube(0, -2, 102, p),
    ]
    for offset in (-48, -24, 0, 24, 48):
        parts.append(f'<path d="M-88 {offset-1} 0 {offset+50} 88 {offset-1}" fill="none" stroke="{p["accent"]}" opacity=".18"/>')
    parts.extend([
        f'<path d="M-44-79V75M44-79V75M0-104V100" fill="none" stroke="{p["accent"]}" opacity=".25"/>',
        cube(0, -15, 38, p, solid=True),
        '</g>',
        f'<circle cx="-165" cy="70" r="5" fill="{p["accent"]}" class="pulse"/>',
        f'<path d="M72-98 118-131h54M-75 108-117 137h-49" fill="none" stroke="{p["muted"]}" stroke-width=".8"/>',
        text(120, -139, "CORE / 01", 10, "muted", p, class_="mono"),
        text(-177, 153, "1337", 11, "muted", p, class_="mono"),
        cross(0, -166, p["accent"]),
        cross(149, 0, p["accent"]),
    ])
    return "".join(parts)


def hero(theme):
    p = PALETTES[theme]
    mobile_body = f'''
    <path d="M44 111H1156" stroke="{p['line']}"/>
    <path d="M53 36v43m18-43v43M53 58h18m23-22 14 43 14-43" fill="none" stroke="{p['accent']}" stroke-width="5"/>
    {text(155, 75, 'HVHBIGNAME', 46, 'fg', p, font_weight=700, letter_spacing=3)}
    {text(1150, 72, '1337', 25, 'muted', p, class_='mono', text_anchor='end')}
    {text(39, 257, 'VIBE IN.', 165, 'fg', p, font_weight=900, letter_spacing=-8, textLength=815, lengthAdjust='spacingAndGlyphs')}
    {text(41, 400, 'SYSTEMS OUT.', 128, 'accent', p, font_weight=900, letter_spacing=-5, textLength=1105, lengthAdjust='spacingAndGlyphs')}
    <g transform="translate(1016 211) scale(.40)">{core(p)}</g>
    '''
    desktop_body = f'''
    <path d="M32 76H1168M32 392H1168" stroke="{p['line']}"/>
    <rect x="739" y="95" width="421" height="278" fill="url(#grid)" opacity=".5"/>
    <path d="M44 29v24m10-24v24m-10-12h10m14-12 9 24 9-24" fill="none" stroke="{p['accent']}" stroke-width="3"/>
    {text(104, 49, 'HVHBIGNAME', 21, 'fg', p, font_weight=700, letter_spacing=2)}
    {text(1155, 46, 'INDEPENDENT DEVELOPER / EST. 2026', 12, 'muted', p, class_='mono', text_anchor='end')}
    {text(43, 123, 'CODE / CURIOSITY / CONTROL', 13, 'muted', p, class_='mono', letter_spacing=2)}
    {text(37, 234, 'VIBE IN.', 112, 'fg', p, font_weight=900, letter_spacing=-6, textLength=458, lengthAdjust='spacingAndGlyphs')}
    {text(38, 337, 'SYSTEMS OUT.', 89, 'accent', p, font_weight=900, letter_spacing=-4, textLength=652, lengthAdjust='spacingAndGlyphs')}
    <g transform="translate(948 230)">{core(p)}</g>
    <circle cx="49" cy="427" r="4" fill="{p['accent']}" class="pulse"/>
    {text(64, 432, 'RUST SYSTEMS + CREATIVE WEB', 13, 'fg', p, class_='mono', letter_spacing=1)}
    {text(1155, 432, 'IDEA → EXPERIMENT → COMMIT', 12, 'muted', p, class_='mono', text_anchor='end')}
    '''
    return document(
        "HVHBIGNAME — Vibe in. Systems out.",
        "Персональная инженерная лаборатория: игровые серверы, инструменты и веб-эксперименты. Геометрическое ядро плавно парит внутри орбит.",
        462, f'<g class="hero-desktop">{desktop_body}</g><g class="hero-mobile">{mobile_body}</g>', theme,
    )


def terrain(p):
    parts = []
    for depth in range(9):
        for a in range(5):
            b = depth - a
            if not 0 <= b < 5:
                continue
            height = max(1, 4 - abs(a-2) - abs(b-2))
            for z in range(height):
                x = (a-b) * 22
                y = (a+b) * 12.7 - z * 25.4
                parts.append(cube(x, y, 25.4, p, solid=(height >= 3 and z == height-1)))
    return "".join(parts)


def panel_blueprint(p):
    return f'''
    <rect x="-131" y="-73" width="262" height="147" rx="10" fill="{p['panel']}" stroke="{p['secondary']}" stroke-width="1.2"/>
    <path d="M-131-47H131" stroke="{p['line']}"/>
    <circle cx="-114" cy="-60" r="3" fill="{p['accent']}" class="pulse"/>
    <circle cx="-101" cy="-60" r="3" fill="{p['line']}"/>
    <circle cx="-88" cy="-60" r="3" fill="{p['line']}"/>
    <path d="M71-60h43" stroke="{p['muted']}" stroke-width="2"/>
    <rect x="-116" y="-31" width="51" height="90" rx="5" fill="{p['bg']}" stroke="{p['line']}"/>
    {cube(-90, -3, 18, p, solid=True)}
    <path d="M-105 31h30m-30 12h20" stroke="{p['muted']}" stroke-width="2"/>
    <rect x="-50" y="-31" width="74" height="35" rx="5" fill="{p['bg']}" stroke="{p['line']}"/>
    <rect x="36" y="-31" width="79" height="35" rx="5" fill="{p['bg']}" stroke="{p['line']}"/>
    <path d="M-38-18h24m-24 11h46M48-18h24M48-7h55" stroke="{p['secondary']}" stroke-width="2"/>
    <rect x="-50" y="17" width="165" height="42" rx="5" fill="{p['bg']}" stroke="{p['line']}"/>
    <path d="M-38 46h15l13-16 19 10 17-6 16 9 20-17 16 6h25" fill="none" stroke="{p['accent']}" stroke-width="1.8"/>
    '''


def project(theme, name):
    p = PALETTES[theme]
    is_core = name == "bcore"
    title = "BCore" if is_core else "emberdeck."
    label = "01 / NATIVE SYSTEMS" if is_core else "02 / MINECRAFT CONTROL"
    tagline = "A world, rebuilt in Rust." if is_core else "Your worlds, in good hands."
    tech = "RUST / MINECRAFT / PLUGIN RUNTIME" if is_core else "RUST / SELF-HOSTED / MINECRAFT"
    status = "ALPHA / IN DEVELOPMENT" if is_core else "EARLY RELEASE / AVAILABLE"
    art = terrain(p) if is_core else panel_blueprint(p)
    art_transform = "translate(962 65) scale(.84)" if is_core else "translate(962 98)"
    body = f'''
    <path d="M32 190H1168M748 24V171" stroke="{p['line']}"/>
    <rect x="778" y="22" width="342" height="156" fill="url(#grid)" opacity=".5"/>
    {text(39, 39, label, 12, 'muted', p, class_='mono', letter_spacing=2)}
    {text(35, 118, title, 77, 'fg', p, font_weight=900, letter_spacing=-3)}
    {text(40, 157, tagline, 19, 'muted', p)}
    <g transform="{art_transform}">{art}</g>
    <circle cx="1139" cy="45" r="17" fill="{p['panel']}" stroke="{p['line']}"/>
    <path d="M1133 51 1145 39m-10 0h10v10" fill="none" stroke="{p['accent']}" stroke-width="1.5"/>
    {text(40, 221, tech, 12, 'fg', p, class_='mono', letter_spacing=1)}
    {text(1156, 221, status, 11, 'muted', p, class_='mono', text_anchor='end')}
    '''
    return document(title, f"{tagline} {tech}. {status}.", 244, body, theme)


def footer(theme):
    p = PALETTES[theme]
    body = f'''
    {cross(45, 50, p['accent'], 9)}
    {text(75, 46, 'ALWAYS UNDER CONSTRUCTION.', 25, 'fg', p, font_weight=700, letter_spacing=-.6)}
    {text(76, 71, 'HVHBIGNAME / SEE YOU IN THE COMMIT LOG.', 11, 'muted', p, class_='mono', letter_spacing=1)}
    {text(1110, 55, 'EXPLORE THE SOURCE', 12, 'muted', p, class_='mono', text_anchor='end')}
    <path d="M1133 60 1149 44m-14 0h14v14" fill="none" stroke="{p['accent']}" stroke-width="2"/>
    '''
    return document("Always under construction.", "Посмотреть все публичные репозитории HVHBIGNAME.", 102, body, theme)


def main():
    assets = ROOT / "assets"
    assets.mkdir(exist_ok=True)
    for theme in PALETTES:
        for name, content in (
            ("hero", hero(theme)),
            ("bcore", project(theme, "bcore")),
            ("minecraft-panel", project(theme, "minecraft-panel")),
            ("footer", footer(theme)),
        ):
            path = assets / f"{name}-{theme}.svg"
            path.write_text(content, encoding="utf-8", newline="\n")
            print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
