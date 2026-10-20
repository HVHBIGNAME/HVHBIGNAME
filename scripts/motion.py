"""Clipped backdrops, one-shot object entrances and one atlas-wide travelling shard."""

FLIGHT_SECONDS = 6.3
CYCLE_SECONDS = 16
LOOP_PHASE_SECONDS = -10


def stage(p, theme="dark", name="hero"):
    x = 238 if name in ("minecraft-panel", "opencode-pocket") else 925
    return f'''
    <g class="stage">
      <rect x="1" y="1" width="1198" height="418" rx="10" fill="{p['bg']}"/>
      <ellipse class="aura" cx="{x}" cy="202" rx="330" ry="215" fill="url(#aura-{name})"/>
      <rect x="1" y="1" width="1198" height="418" fill="url(#stars)" opacity=".16"/>
      <rect x="1" y="1" width="1198" height="418" fill="url(#vignette)"/>
      {grain_rect(theme)}
      <rect x="1" y="1" width="1198" height="418" rx="10" fill="none" stroke="{p['line']}"/>
    </g>'''


def backdrop_defs(p, name):
    return f'''<radialGradient id="aura-{name}">
      <stop offset="0" stop-color="{p['accent']}" stop-opacity=".14"/>
      <stop offset="1" stop-color="{p['accent']}" stop-opacity="0"/>
    </radialGradient>'''


def grain_clip():
    return '<clipPath id="grain-clip"><rect x="1" y="1" width="1198" height="418" rx="10"/></clipPath>'


def grain_rect(theme="dark"):
    opacity = ".035" if theme == "dark" else ".025"
    return (
        '<g clip-path="url(#grain-clip)"><rect class="grain" x="-4" y="-4" width="1208" height="428" '
        f'filter="url(#grain-filter)" opacity="{opacity}"/></g>'
    )


def sweep_defs(p):
    return (
        '<linearGradient id="sweep-fade" x1="0" y1="0" x2="1" y2="0">'
        '<stop offset="0" stop-color="#fff" stop-opacity="0"/>'
        f'<stop offset=".5" stop-color="{p["fg"]}" stop-opacity=".06"/>'
        '<stop offset="1" stop-color="#fff" stop-opacity="0"/>'
        '</linearGradient>'
    )


def grain(p):
    return f'''
      <filter id="grain-filter" x="0" y="0" width="100%" height="100%">
        <feTurbulence type="fractalNoise" baseFrequency=".8" numOctaves="3" seed="17" stitchTiles="stitch"/>
        <feColorMatrix type="saturate" values="0"/>
      </filter>
      <pattern id="stars" width="240" height="180" patternUnits="userSpaceOnUse">
        <circle cx="18" cy="26" r=".7" fill="{p['fg']}" opacity=".5"/>
        <circle cx="112" cy="58" r=".8" fill="{p['fg']}" opacity=".4"/>
        <circle cx="196" cy="138" r=".6" fill="{p['fg']}" opacity=".4"/>
      </pattern>
      <radialGradient id="vignette" cx=".5" cy=".46" r=".78">
        <stop offset=".45" stop-color="{p['shadow']}" stop-opacity="0"/>
        <stop offset="1" stop-color="{p['shadow']}" stop-opacity=".22"/>
      </radialGradient>'''


def styles(height):
    flight_end = FLIGHT_SECONDS / CYCLE_SECONDS * 100
    return f'''
    .stage {{ animation:fade-in 1.2s ease-out both; }}
    .aura {{ animation:aura-breathe var(--cycle) ease-in-out infinite; animation-delay:var(--phase); }}
    .grain {{ mix-blend-mode:normal; }}
    .rise {{ animation:rise 1s cubic-bezier(.22,.7,.25,1) both; animation-delay:calc(.25s + var(--idx,0)*.12s); }}
    .wipe {{ animation:wipe 1.4s ease-out both; animation-delay:.4s; }}
    /* Layout transforms belong to the parent; this group owns only motion. */
    .art-anchor {{ --enter-x:280px; --enter-turn:16deg; }}
    .art-anchor.from-left {{ --enter-x:-280px; --enter-turn:-16deg; }}
    .art-enter {{ animation:art-enter 2.2s cubic-bezier(.16,.7,.2,1) both; animation-delay:.45s; transform-box:view-box; transform-origin:0 0; }}
    .draw {{ animation:draw 1.4s ease-out both; animation-delay:.5s; }}
    .sweep {{ opacity:0; animation:sweep 1.8s ease-in-out both; animation-delay:1.4s; }}
    .bar {{ animation:bar-up 2.2s cubic-bezier(.16,.7,.2,1) both; animation-delay:.45s; transform-box:fill-box; transform-origin:50% 100%; }}
    .beat {{ animation:beat calc(var(--cycle) / 4) ease-in-out infinite; animation-delay:var(--phase); }}
    @keyframes fade-in {{ from {{ opacity:0; }} to {{ opacity:1; }} }}
    @keyframes rise {{ from {{ opacity:0; transform:translateY(28px); }} to {{ opacity:1; transform:translateY(0); }} }}
    @keyframes art-enter {{
      0% {{ opacity:0; transform:translate(var(--enter-x),100px) rotate(var(--enter-turn)) scale(.72); }}
      28% {{ opacity:1; }}
      76% {{ opacity:1; transform:translate(-6px,-4px) rotate(-1deg) scale(1.015); }}
      100% {{ opacity:1; transform:translate(0,0) rotate(0) scale(1); }}
    }}
    @keyframes wipe {{ from {{ opacity:0; clip-path:inset(0 100% 0 0); }} to {{ opacity:1; clip-path:inset(0); }} }}
    @keyframes draw {{ from {{ stroke-dashoffset:100; }} to {{ stroke-dashoffset:0; }} }}
    @keyframes sweep {{ 0% {{ transform:translateX(-40px); opacity:0; }} 30% {{ opacity:.5; }} 100% {{ transform:translateX(1460px); opacity:0; }} }}
    @keyframes bar-up {{ from {{ opacity:0; transform:scaleY(.05); }} to {{ opacity:1; transform:scaleY(1); }} }}
    @keyframes beat {{ 0%,100% {{ opacity:.35; }} 50% {{ opacity:.85; }} }}
    @keyframes aura-breathe {{ 0%,100% {{ opacity:.65; }} 50% {{ opacity:1; }} }}
    .relay {{ opacity:0; animation:relay var(--cycle) linear infinite; animation-delay:var(--phase); }}
    @keyframes relay {{
      0% {{ opacity:0; transform:translateY(-54px); }}
      1% {{ opacity:1; }}
      {flight_end - 1:.3f}% {{ opacity:1; }}
      {flight_end:.3f}%,100% {{ opacity:0; transform:translateY({height + 54}px); }}
    }}
    @media (prefers-reduced-motion: reduce) {{
      .relay, .grain, .sweep {{ display:none; }}
      *, *::before, *::after {{ animation:none !important; transition:none !important; }}
    }}
    '''


def packet(p):
    """One moving object in atlas coordinates, seen through all six view windows."""
    return f'''
    <g clip-path="url(#atlas-clips)"><g transform="translate(26 0)">
      <g class="relay">
        <path d="M0-42V-14" stroke="{p['accent']}" stroke-width="2" opacity=".45"/>
        <path d="M0-13 6-5 0 3-6-5Z" fill="{p['accent']}"/>
        <circle cy="-5" r="10" fill="{p['accent']}" opacity=".14"/>
      </g>
    </g></g>'''
