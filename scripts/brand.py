"""HVH monogram: mirrored opponents, with the V cut into the centre."""

import math

LETTERS = (
    ("H", "M18 31 29 20h6v32h29V20h17v88H64V70H35v38H18Z"),
    ("V", "M88 20h20l18 57 18-57h20l-30 88h-16Z"),
    ("H", "M171 20h17v32h29V20h6l11 11v77h-17V70h-29v38h-17Z"),
)
CENTER = (126, 64)


def symbol(p):
    fills = (p["fg"], p["accent"], p["fg"])
    paths = "".join(
        f'<path data-letter="{letter}" d="{d}" fill="{fill}"/>'
        for (letter, d), fill in zip(LETTERS, fills)
    )
    return f'<symbol id="hvh-symbol" viewBox="0 0 252 128">{paths}</symbol>'


def defs(p):
    light, mid, dark = p["metal"]
    outlines = "".join(f'<path d="{d}"/>' for _, d in LETTERS)
    return f'''
    <linearGradient id="hvh-metal" x1="0" y1="0" x2=".5" y2="1">
      <stop offset="0" stop-color="{light}"/>
      <stop offset=".36" stop-color="{mid}"/>
      <stop offset=".55" stop-color="{dark}"/>
      <stop offset=".72" stop-color="{light}"/>
      <stop offset="1" stop-color="{mid}"/>
    </linearGradient>
    <linearGradient id="hvh-sheen" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#fff" stop-opacity="0"/>
      <stop offset=".42" stop-color="#fff" stop-opacity=".9"/>
      <stop offset=".58" stop-color="#fff" stop-opacity=".9"/>
      <stop offset="1" stop-color="#fff" stop-opacity="0"/>
    </linearGradient>
    <filter id="hvh-glow" x="-25%" y="-45%" width="150%" height="190%"><feGaussianBlur stdDeviation="6"/></filter>
    <clipPath id="hvh-clip">{outlines}</clipPath>'''


def plate(p):
    """Extruded lettering: neon rim, cast shadow, brushed fill and a moving specular."""
    outlines = "".join(f'<path d="{d}"/>' for _, d in LETTERS)
    cx, cy = CENTER
    sparks = []
    for index, angle in enumerate((-166, -138, -104, -68, -26, 18, 62, 112, 148)):
        radius = 34 + index % 3 * 13
        sparks.append(
            f'<path class="shard" d="M-1.5-7h3v14h-3Z" fill="{p["accent"]}" '
            f'style="--dx:{math.cos(math.radians(angle))*radius:.1f}px;'
            f'--dy:{math.sin(math.radians(angle))*radius:.1f}px;'
            f'--turn:{angle}deg;--i:{index}"/>'
        )
    return f'''
    <g class="plate">
      <g filter="url(#hvh-glow)" opacity=".16" fill="{p['accent']}">{outlines}</g>
      <g transform="translate(7 11)" opacity=".5" fill="#000">{outlines}</g>
      <g fill="url(#hvh-metal)">{outlines}</g>
      <g fill="none" stroke="#fff" stroke-opacity=".28" stroke-width=".9" transform="translate(0 -1)">{outlines}</g>
      <g clip-path="url(#hvh-clip)"><g transform="skewX(-16)">
        <rect class="sheen" x="-300" y="-40" width="104" height="220" fill="url(#hvh-sheen)"/>
      </g></g>
      <g class="sparks" transform="translate({cx} {cy})">{''.join(sparks)}</g>
    </g>'''


def styles():
    return '''
    .sheen { animation:sheen var(--cycle) ease-in-out infinite; animation-delay:var(--phase); }
    .shard { opacity:0; animation:shard 1.15s cubic-bezier(.12,.66,.28,1) both; animation-delay:1.9s; }
    @keyframes sheen { 0% { transform:translateX(0); } 22%,100% { transform:translateX(700px); } }
    @keyframes shard {
      0% { opacity:0; transform:translate(0,0) rotate(0) scale(.2); }
      12% { opacity:.7; }
      100% { opacity:0; transform:translate(var(--dx),var(--dy)) rotate(var(--turn)) scale(.35); }
    }
    @media (prefers-reduced-motion: reduce) { .shard, .sheen { display:none; } }
    '''


def logo(p):
    """Standalone, static logo; the same paths are used in both atlas themes."""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512" role="img" aria-labelledby="title desc">
    <title id="title">HVH</title>
    <desc id="desc">Две зеркальные H и центральная V. Знак HVHBIGNAME.</desc>
    <defs>{defs(p)}{symbol(p)}</defs>
    <rect width="512" height="512" fill="{p['bg']}"/>
    <path d="M40 96V40h56m320 0h56v56M40 416v56h56m320 0h56v-56" fill="none" stroke="{p['line']}" stroke-width="2"/>
    <style>.sparks, .sheen {{ display:none; }}</style>
    <g transform="translate(22 137)">
      <g transform="scale(1.85714)">{plate(p)}</g>
    </g>
    </svg>''' + '\n'
