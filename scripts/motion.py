"""Cinematic stage, one-shot intro and the packet that travels between cards.

Every card is a separate <img> pointing at one fragment of the same SVG file, so
there is no shared DOM between them.  Continuity is produced by timing: all views
carry the same clock and differ only by an index, so an object that leaves the
bottom of card *k* reappears at the top of card *k+1* in the same animation frame.
"""

TRAVEL = 0.92
SLOT = 1.05


def stage(p, theme="dark", grain_id="grain", scale_id="grain-scale"):
    """Backdrop layers, painted under the card contents and clipped to the frame."""
    return f'''
    <g class="stage" style="--idx:0">
      <circle class="aura aura-a" cx="880" cy="120" r="330" fill="url(#aura-a)"/>
      <circle class="aura aura-b" cx="300" cy="330" r="300" fill="url(#aura-b)"/>
      <rect width="1200" height="420" fill="url(#stars)" opacity=".55"/>
      <rect x="1" y="1" width="1198" height="418" fill="url(#vignette)"/>
      {grain_rect(theme)}
    </g>'''


def grain_clip():
    return '<clipPath id="grain-clip"><rect x="1" y="1" width="1198" height="418" rx="10"/></clipPath>'


def grain_rect(theme="dark"):
    """Film grain. Plain blending, because overlay collapses against near-black."""
    opacity = ".11" if theme == "dark" else ".08"
    return (
        '<g clip-path="url(#grain-clip)"><rect class="grain" x="-4" y="-4" width="1208" height="428" '
        f'filter="url(#grain-filter)" opacity="{opacity}"/></g>'
    )


def sweep_defs(p):
    return (
        '<linearGradient id="sweep-fade" x1="0" y1="0" x2="1" y2="0">'
        '<stop offset="0" stop-color="#fff" stop-opacity="0"/>'
        f'<stop offset=".5" stop-color="{p["fg"]}" stop-opacity=".10"/>'
        '<stop offset="1" stop-color="#fff" stop-opacity="0"/>'
        '</linearGradient>'
    )


def grain(p):
    return f'''
      <filter id="grain-filter" x="0" y="0" width="100%" height="100%">
        <feTurbulence type="fractalNoise" baseFrequency=".8" numOctaves="3" seed="17" stitchTiles="stitch"/>
        <feColorMatrix type="saturate" values="0"/>
      </filter>
      <pattern id="stars" width="140" height="140" patternUnits="userSpaceOnUse">
        <circle cx="18" cy="26" r=".9" fill="#fff" opacity=".5"/>
        <circle cx="74" cy="12" r=".6" fill="#fff" opacity=".35"/>
        <circle cx="112" cy="58" r="1.1" fill="#fff" opacity=".55"/>
        <circle cx="46" cy="88" r=".7" fill="#fff" opacity=".3"/>
        <circle cx="96" cy="118" r=".5" fill="#fff" opacity=".4"/>
        <circle cx="24" cy="126" r=".8" fill="#fff" opacity=".25"/>
      </pattern>
      <radialGradient id="aura-a"><stop offset="0" stop-color="{p['accent']}" stop-opacity=".34"/><stop offset="1" stop-color="{p['accent']}" stop-opacity="0"/></radialGradient>
      <radialGradient id="aura-b"><stop offset="0" stop-color="{p['glow']}" stop-opacity=".26"/><stop offset="1" stop-color="{p['glow']}" stop-opacity="0"/></radialGradient>
      <radialGradient id="vignette" cx=".5" cy=".46" r=".78">
        <stop offset=".45" stop-color="{p['shadow']}" stop-opacity="0"/>
        <stop offset="1" stop-color="{p['shadow']}" stop-opacity=".82"/>
      </radialGradient>'''


def styles(views):
    return f'''
    :root {{ --travel:{TRAVEL}s; --slot:{SLOT}s; }}
    .stage {{ animation:fade-in 1.1s ease-out both; }}
    .aura {{ transform-box:fill-box; transform-origin:center; }}
    .aura-a {{ animation:drift-a 19s ease-in-out infinite; }}
    .aura-b {{ animation:drift-b 25s ease-in-out infinite; }}
    .grain {{ mix-blend-mode:overlay; animation:grain-shift 5.5s steps(2) infinite; }}
    /* Intro: every element starts at its final value, so a frozen document still reads. */
    .rise {{ animation:rise .78s cubic-bezier(.16,.84,.28,1) both; animation-delay:calc(var(--idx,0)*.09s + .06s); }}
    .wipe {{ animation:wipe 1.1s cubic-bezier(.3,.7,.2,1) both; animation-delay:calc(var(--idx,0)*.09s + .3s); }}
    .pop {{ animation:pop .7s cubic-bezier(.2,.85,.25,1) both; animation-delay:calc(var(--idx,0)*.09s + .12s); transform-box:fill-box; transform-origin:center; }}
    .draw {{ animation:draw 1s cubic-bezier(.3,.7,.2,1) both; animation-delay:calc(var(--idx,0)*.09s + .22s); }}
    .sweep {{ animation:sweep 1.5s cubic-bezier(.4,0,.2,1) both; animation-delay:calc(var(--idx,0)*.09s + .5s); }}
    .bar {{ animation:bar-up .6s cubic-bezier(.2,.8,.2,1) both; animation-delay:calc(var(--idx,0)*.09s + .35s + var(--n)*.006s); transform-box:fill-box; transform-origin:50% 100%; }}
    .beat {{ animation:beat 2.6s ease-in-out infinite; animation-delay:calc(var(--idx,0)*.09s + .5s); }}
    @keyframes fade-in {{ from {{ opacity:0; }} to {{ opacity:1; }} }}
    @keyframes rise {{ from {{ opacity:0; transform:translateY(16px); }} to {{ opacity:1; transform:translateY(0); }} }}
    @keyframes pop {{ from {{ opacity:0; transform:scale(.86); }} to {{ opacity:1; transform:scale(1); }} }}
    @keyframes wipe {{ from {{ clip-path:inset(0 100% 0 0); }} to {{ clip-path:inset(0 0 0 0); }} }}
    @keyframes draw {{ from {{ stroke-dashoffset:100; }} to {{ stroke-dashoffset:0; }} }}
    @keyframes sweep {{ 0% {{ transform:translateX(-40px); opacity:0; }} 30% {{ opacity:.75; }} 100% {{ transform:translateX(1260px); opacity:0; }} }}
    @keyframes bar-up {{ from {{ opacity:0; transform:scaleY(.05); }} to {{ opacity:1; transform:scaleY(1); }} }}
    @keyframes beat {{ 0%,100% {{ opacity:.35; }} 50% {{ opacity:.85; }} }}
    @keyframes drift-a {{ 0%,100% {{ transform:translate(0,0) scale(1); }} 50% {{ transform:translate(-70px,26px) scale(1.08); }} }}
    @keyframes drift-b {{ 0%,100% {{ transform:translate(0,0) scale(1.05); }} 50% {{ transform:translate(64px,-22px) scale(.94); }} }}
    @keyframes grain-shift {{ 0% {{ transform:translate(0,0); }} 50% {{ transform:translate(-2.5px,1.5px); }} 100% {{ transform:translate(2px,-2px); }} }}
    /* The travelling packet: leaves one card, enters the next one slot later. */
    .relay {{ opacity:0; animation:relay {TRAVEL}s linear both; animation-delay:calc(var(--idx,0) * {SLOT}s); }}
    @keyframes relay {{
      0% {{ opacity:0; transform:translateY(-26px) scale(.7); }}
      8% {{ opacity:1; transform:translateY(-6px) scale(1); }}
      88% {{ opacity:1; transform:translateY(392px) scale(1); }}
      100% {{ opacity:0; transform:translateY(432px) scale(.7); }}
    }}
    @media (prefers-reduced-motion: reduce) {{
      .relay, .grain, .sweep {{ display:none; }}
      /* Blanket: every decorative loop must stop, including scene classes. */
      *, *::before, *::after {{ animation:none !important; transition:none !important; }}
    }}
    '''


def packet(p):
    """Small shard riding the rail at x=26; drawn at the seam so both halves line up."""
    return f'''
    <g class="relay" transform="translate(26 0)">
      <path d="M-9-4h18v-9H-9Z" fill="{p['accent']}"/>
      <path d="M-12 0h24" stroke="{p['accent']}" stroke-width="2" stroke-linecap="round"/>
      <path d="M0-30v-16" stroke="{p['accent']}" stroke-width="1.6" opacity=".4"/>
      <circle cy="-4" r="9" fill="{p['accent']}" opacity=".22"/>
    </g>'''
