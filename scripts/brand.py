"""HVH monogram: mirrored opponents, with the V cut into the centre."""

import math


def symbol(p):
    return f'''
    <symbol id="hvh-symbol" viewBox="0 0 252 128">
      <path data-letter="H" d="M18 31 29 20h6v32h29V20h17v88H64V70H35v38H18Z" fill="{p['fg']}"/>
      <path data-letter="V" d="M88 20h20l18 57 18-57h20l-30 88h-16Z" fill="{p['accent']}"/>
      <path data-letter="H" d="M171 20h17v32h29V20h6l11 11v77h-17V70h-29v38h-17Z" fill="{p['fg']}"/>
    </symbol>'''


def duel(p):
    sparks = []
    for index, angle in enumerate((-158, -124, -76, -32, 22, 63, 114, 157)):
        radius = 27 + index % 3 * 11
        dx = math.cos(math.radians(angle)) * radius
        dy = math.sin(math.radians(angle)) * radius
        color = p['accent'] if index % 2 else p['fg']
        sparks.append(f'<path class="duel-spark" d="M-1-4h2v8h-2Z" fill="{color}" style="--dx:{dx:.1f}px;--dy:{dy:.1f}px;--turn:{angle}deg"/>')
    return f'''
    <path d="M0 34V8h26m200 0h26v26M0 94v26h26m200 0h26V94" fill="none" stroke="{p['line']}" stroke-width="1.4"/>
    <use href="#hvh-symbol" width="252" height="128"/>
    <path class="duel-trace" pathLength="100" d="M-22 64H121" fill="none" stroke="{p['accent']}" stroke-width="1.5"/>
    <path class="duel-trace" pathLength="100" d="M274 64H131" fill="none" stroke="{p['fg']}" stroke-width="1.5"/>
    <g transform="translate(126 64)">
      {''.join(sparks)}
      <path class="duel-impact" d="M-9-15h6m-12 6v6M9 15H3m12-6V3" fill="none" stroke="{p['accent']}"/>
    </g>'''


def styles(duration):
    return f'''
    .duel-trace, .duel-spark, .duel-impact {{
      opacity:0; animation-duration:{duration}s; animation-iteration-count:infinite;
      animation-delay:var(--phase, 0s); animation-fill-mode:both;
    }}
    .duel-trace {{ stroke-dasharray:18 100; animation-name:duel-trace; }}
    .duel-spark {{ animation-name:duel-spark; animation-timing-function:cubic-bezier(.12,.65,.3,1); }}
    .duel-impact {{ animation-name:duel-impact; }}
    @keyframes duel-trace {{
      0%,22% {{ stroke-dashoffset:20; opacity:0; }}
      24% {{ stroke-dashoffset:20; opacity:.9; }}
      42% {{ stroke-dashoffset:-100; opacity:.9; }}
      43%,100% {{ stroke-dashoffset:-100; opacity:0; }}
    }}
    @keyframes duel-spark {{
      0%,41% {{ opacity:0; transform:translate(0,0) scale(.3); }}
      43% {{ opacity:1; }}
      58%,100% {{ opacity:0; transform:translate(var(--dx),var(--dy)) rotate(var(--turn)) scale(.2); }}
    }}
    @keyframes duel-impact {{
      0%,41% {{ opacity:0; transform:scale(.4); }}
      43% {{ opacity:.8; }}
      53%,100% {{ opacity:0; transform:scale(2.5); }}
    }}
    @media (prefers-reduced-motion: reduce) {{ .duel-trace, .duel-spark, .duel-impact {{ display:none; }} }}
    '''


def logo(p):
    """Standalone, static logo; the same paths are used in both atlas themes."""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512" role="img" aria-labelledby="title desc">
    <title id="title">HVH</title>
    <desc id="desc">Две зеркальные H и центральная V. Знак HVHBIGNAME.</desc>
    <defs>{symbol(p)}</defs>
    <rect width="512" height="512" fill="{p['bg']}"/>
    <path d="M40 96V40h56m320 0h56v56M40 416v56h56m320 0h56v-56" fill="none" stroke="{p['line']}" stroke-width="2"/>
    <use href="#hvh-symbol" x="22" y="137" width="468" height="238"/>
    </svg>''' + '\n'
