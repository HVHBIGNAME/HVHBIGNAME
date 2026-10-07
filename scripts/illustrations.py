"""Original SVG illustrations; motion is driven by the shared atlas stylesheet."""

import math

WORLD_BLOCKS = tuple(
    sorted(
        ((a, b, z) for a in range(5) for b in range(5)
         for z in range(max(1, 4 - abs(a-2) - abs(b-2)))),
        key=lambda block: (block[2], block[0]+block[1], block[0]),
    )
)


def scene_styles(duration):
    """Shared scene clock, with individual landing/reveal windows within a loop."""
    rules = [f'''
    .world-voxel, .server-card, .server-core, .boot-progress, .server-ready,
    .server-chart, .server-live, .package-arrival, .package-installed,
    .package-check, .install-progress, .install-done, .paired-mark,
    .handoff, .chat-line, .typing-dots, .qr-scan {{
      animation-duration:{duration}s; animation-iteration-count:infinite;
      animation-timing-function:linear; animation-delay:var(--phase, 0s);
      animation-fill-mode:both;
    }}
    .server-core {{ animation-name:server-core; transform-box:fill-box; transform-origin:center; }}
    .server-card {{ animation-name:server-card; }}
    .server-card.second, .server-card.second .boot-progress,
    .server-card.second .server-ready {{ animation-delay:calc(var(--phase, 0s) + 1.6s); }}
    .boot-progress {{ stroke-dasharray:100; animation-name:boot-progress; }}
    .server-ready {{ animation-name:server-ready; }}
    .server-chart {{ stroke-dasharray:100; animation-name:server-chart; }}
    .server-live {{ animation-name:server-live; }}
    .package-arrival, .handoff, .typing-dots {{ opacity:0; }}
    .package-check {{ stroke-dasharray:100; }}
    .install-progress {{ stroke-dasharray:100; animation-name:install-progress; }}
    .install-done {{ stroke-dasharray:100; animation-name:install-done; }}
    .qr-scan {{ opacity:0; animation-name:qr-pair; }}
    .paired-mark {{ animation-name:paired; transform-box:fill-box; transform-origin:center; }}
    .handoff {{ animation-name:handoff; }}
    .typing-dots {{ animation-name:typing; }}
    @keyframes server-core {{
      0%,3% {{ opacity:0; transform:scale(.2); }}
      12% {{ opacity:1; transform:scale(1.12); }}
      16%,87% {{ opacity:1; transform:scale(1); }}
      96%,100% {{ opacity:0; transform:scale(.7); }}
    }}
    @keyframes server-card {{
      0%,12% {{ opacity:0; transform:translateY(19px); }}
      22%,80% {{ opacity:1; transform:translateY(0); }}
      90%,100% {{ opacity:0; transform:translateY(-9px); }}
    }}
    @keyframes boot-progress {{
      0%,22% {{ stroke-dashoffset:100; }} 40%,100% {{ stroke-dashoffset:0; }}
    }}
    @keyframes server-ready {{
      0%,39% {{ opacity:0; }} 42%,84% {{ opacity:1; }} 93%,100% {{ opacity:0; }}
    }}
    @keyframes server-chart {{
      0%,42% {{ opacity:.15; stroke-dashoffset:100; }}
      67%,86% {{ opacity:1; stroke-dashoffset:0; }}
      96%,100% {{ opacity:0; stroke-dashoffset:0; }}
    }}
    @keyframes server-live {{ 0%,67%,96%,100% {{ opacity:0; }} 70%,88% {{ opacity:1; }} }}
    @keyframes install-progress {{
      0%,7% {{ stroke-dashoffset:100; }} 70%,90% {{ stroke-dashoffset:0; }} 98%,100% {{ stroke-dashoffset:100; }}
    }}
    @keyframes install-done {{ 0%,70% {{ opacity:0; stroke-dashoffset:100; }} 77%,90% {{ opacity:1; stroke-dashoffset:0; }} 98%,100% {{ opacity:0; stroke-dashoffset:0; }} }}
    @keyframes qr-pair {{
      0% {{ opacity:0; transform:translateY(0); }}
      3% {{ opacity:1; transform:translateY(0); }}
      12% {{ opacity:1; transform:translateY(65px); }}
      21% {{ opacity:1; transform:translateY(0); }}
      24%,100% {{ opacity:0; transform:translateY(0); }}
    }}
    @keyframes paired {{
      0%,21% {{ opacity:0; transform:scale(.2); }}
      25% {{ opacity:1; transform:scale(1.2); }}
      29%,89% {{ opacity:1; transform:scale(1); }}
      98%,100% {{ opacity:0; transform:scale(.8); }}
    }}
    @keyframes handoff {{
      0%,25% {{ opacity:0; transform:translate(0,0); }}
      27% {{ opacity:1; transform:translate(0,0); }}
      32% {{ opacity:1; transform:translate(55px,-28px); }}
      37% {{ opacity:1; transform:translate(121px,-14px); }}
      39%,100% {{ opacity:0; transform:translate(125px,-14px); }}
    }}
    @keyframes typing {{
      0%,36%,44%,53%,65%,100% {{ opacity:0; }}
      38%,42%,47%,51%,57%,62% {{ opacity:1; }}
    }}
    ''']
    for index, _ in enumerate(WORLD_BLOCKS):
        start = 4 + index*.85
        rules.append(f'''
        .voxel-{index} {{ animation-name:place-{index}; }}
        @keyframes place-{index} {{
          0%,{start:.2f}% {{ opacity:0; transform:translateY(-48px); }}
          {start+1:.2f}% {{ opacity:1; transform:translateY(-43px); }}
          {start+4:.2f}% {{ opacity:1; transform:translateY(3px); }}
          {start+5.5:.2f}%,86% {{ opacity:1; transform:translateY(0); }}
          96%,100% {{ opacity:0; transform:translateY(18px); }}
        }}''')
    for index in range(6):
        start = 6 + index*10
        dx = 126 - (-134 + index % 3 * 55 + 21)
        dy = 88 - (-36 + index // 3 * 54 + 20)
        rules.append(f'''
        .parcel-{index} {{ animation-name:parcel-{index}; }}
        .installed-{index} {{ animation-name:installed-{index}; }}
        .check-{index} {{ animation-name:check-{index}; }}
        @keyframes parcel-{index} {{
          0%,{start}% {{ opacity:0; transform:translate({dx}px,{dy}px) scale(.5); }}
          {start+1}% {{ opacity:1; transform:translate({dx}px,{dy}px) scale(1); }}
          {start+4}% {{ opacity:1; transform:translate({dx/2:.1f}px,-28px) scale(1); }}
          {start+7}% {{ opacity:1; transform:translate(0,0) scale(.7); }}
          {start+8}%,100% {{ opacity:0; transform:translate(0,0) scale(.15); }}
        }}
        @keyframes installed-{index} {{
          0%,{start+6}% {{ opacity:0; }} {start+8}%,88% {{ opacity:1; }} 98%,100% {{ opacity:0; }}
        }}
        @keyframes check-{index} {{
          0%,{start+7}% {{ opacity:0; stroke-dashoffset:100; }}
          {start+10}%,88% {{ opacity:1; stroke-dashoffset:0; }}
          98%,100% {{ opacity:0; stroke-dashoffset:0; }}
        }}''')
    for index, start in enumerate((41, 52, 64)):
        rules.append(f'''
        .message-{index} {{ animation-name:message-{index}; }}
        @keyframes message-{index} {{
          0%,{start}% {{ opacity:0; transform:translateY(18px); }}
          {start+4}% {{ opacity:1; transform:translateY(-2px); }}
          {start+6}%,89% {{ opacity:1; transform:translateY(0); }}
          98%,100% {{ opacity:0; transform:translateY(-8px); }}
        }}''')
    rules.append('''
    @media (prefers-reduced-motion: reduce) {
      .package-arrival, .handoff, .typing-dots, .qr-scan { display:none; }
    }''')
    return "\n".join(rules)


def cube(x, y, size, p, solid=False):
    half = size * math.sqrt(3) / 2
    faces = (
        ([(x-half, y-size/2), (x, y), (x, y+size), (x-half, y+size/2)], p["soft"] if solid else p["bg"]),
        ([(x, y), (x+half, y-size/2), (x+half, y+size/2), (x, y+size)], p["accent"] if solid else p["soft"]),
        ([(x, y-size), (x+half, y-size/2), (x, y), (x-half, y-size/2)], p["accent"] if solid else p["panel"]),
    )
    return "".join(
        f'<polygon points="{" ".join(f"{a:.2f},{b:.2f}" for a, b in points)}" '
        f'fill="{fill}" stroke="{p["accent"]}" stroke-width="1.2"/>'
        for points, fill in faces
    )


def core(p):
    return f'''
    <circle r="169" fill="url(#aura)"/>
    <circle r="143" fill="none" stroke="{p['line']}"/>
    <circle r="161" fill="none" stroke="{p['muted']}" stroke-dasharray="1 11" opacity=".4"/>
    <path d="M-184 0h368M0-176v352" stroke="{p['line']}"/>
    <ellipse rx="182" ry="59" transform="rotate(-27)" fill="none" stroke="{p['line']}"/>
    <ellipse class="orbit" rx="182" ry="59" transform="rotate(-27)" fill="none" stroke="{p['accent']}" opacity=".7"/>
    <g class="levitate">
      {cube(0, -5, 98, p)}
      <path d="M-85-5 0 44 85-5M-85 20 0 69 85 20M0-103V93" fill="none" stroke="{p['accent']}" opacity=".28"/>
      {cube(0, -17, 39, p, solid=True)}
    </g>
    <circle class="heartbeat" cx="-156" cy="66" r="5" fill="{p['accent']}"/>
    <path d="M-6-161h12M0-167v12M137 0h12M143-6v12" stroke="{p['accent']}"/>
    '''


def world(p):
    pieces = []
    order = {block: index for index, block in enumerate(WORLD_BLOCKS)}
    for depth in range(9):
        for a in range(5):
            b = depth - a
            if not 0 <= b < 5:
                continue
            height = max(1, 4 - abs(a-2) - abs(b-2))
            for z in range(height):
                pieces.append(f'<g class="world-voxel voxel-{order[a, b, z]}" data-layer="{z}">')
                pieces.append(cube((a-b)*25, (a+b)*14.43-z*28.86, 28.86, p, solid=height >= 3 and z == height-1))
                pieces.append('</g>')
    return f'''
    <ellipse cx="0" cy="103" rx="175" ry="55" fill="{p['soft']}" opacity=".24"/>
    <path d="M-164 52 0-43 164 52 0 147Z" fill="none" stroke="{p['line']}"/>
    <g transform="translate(0 -72)">
      {''.join(pieces)}
      <g class="world-beam" opacity=".22">
        <path d="M-107 58 0-4 107 58 0 120Z" fill="{p['accent']}"/>
        <path d="M-107 58V-23L0-85 107-23V58" fill="none" stroke="{p['accent']}"/>
      </g>
    </g>
    <path d="M-177 156h29m133 32h28m128-33h28" stroke="{p['accent']}" opacity=".5"/>
    '''


def panel(p):
    return f'''
    <g>
      <rect x="-166" y="-106" width="332" height="217" rx="14" fill="{p['panel']}" stroke="{p['accent']}" stroke-width="1.4"/>
      <path d="M-166-73H166" stroke="{p['line']}"/>
      <circle cx="-145" cy="-90" r="4" fill="{p['accent']}" class="heartbeat"/>
      <circle cx="-128" cy="-90" r="4" fill="{p['line']}"/>
      <circle cx="-111" cy="-90" r="4" fill="{p['line']}"/>
      <path d="M88-90h55" stroke="{p['muted']}" stroke-width="2"/>
      <rect x="-145" y="-53" width="67" height="142" rx="7" fill="{p['bg']}" stroke="{p['line']}"/>
      <g class="server-core">{cube(-112, -12, 22, p, solid=True)}</g>
      <path d="M-131 43h38m-38 16h29m-29 16h34" stroke="{p['muted']}" stroke-width="2"/>
      <g class="server-card">
        <rect x="-57" y="-53" width="89" height="49" rx="7" fill="{p['bg']}" stroke="{p['line']}"/>
        <path d="M-43-36h28" stroke="{p['muted']}" stroke-width="2"/>
        <path class="boot-progress" pathLength="100" d="M-43-20h59" stroke="{p['accent']}" stroke-width="3"/>
        <circle class="server-ready" cx="17" cy="-37" r="4" fill="{p['accent']}"/>
      </g>
      <g class="server-card second">
        <rect x="46" y="-53" width="98" height="49" rx="7" fill="{p['bg']}" stroke="{p['line']}"/>
        <path d="M60-36h30" stroke="{p['muted']}" stroke-width="2"/>
        <path class="boot-progress" pathLength="100" d="M60-20h68" stroke="{p['accent']}" stroke-width="3"/>
        <circle class="server-ready" cx="129" cy="-37" r="4" fill="{p['accent']}"/>
      </g>
      <rect x="-57" y="12" width="201" height="77" rx="7" fill="{p['bg']}" stroke="{p['line']}"/>
      <path d="M-43 69H130M-43 38H130" stroke="{p['line']}" stroke-dasharray="2 5"/>
      <path class="server-chart" pathLength="100" d="M-43 65-25 65-8 34 15 56 36 45 57 64 79 27 100 42 130 42" fill="none" stroke="{p['accent']}" stroke-width="2.5"/>
      <g class="server-live"><circle cx="130" cy="42" r="4" fill="{p['accent']}"/><circle class="heartbeat" cx="130" cy="42" r="9" fill="none" stroke="{p['accent']}"/></g>
    </g>
    <path d="M-184 131H84m15 0h42" stroke="{p['line']}"/>
    <circle class="heartbeat" cx="153" cy="131" r="4" fill="{p['accent']}"/>
    '''


def software(p):
    tiles = []
    parcels = []
    for index in range(6):
        x = -134 + index % 3 * 55
        y = -36 + index // 3 * 54
        tiles.append(f'''
        <g>
          <rect x="{x}" y="{y}" width="43" height="42" rx="7" fill="{p['bg']}" stroke="{p['line']}"/>
          <rect class="package-installed installed-{index}" x="{x}" y="{y}" width="43" height="42" rx="7" fill="{p['soft']}" stroke="{p['accent']}"/>
          <path class="package-check check-{index}" pathLength="100" d="M{x+11} {y+21} {x+19} {y+29} {x+33} {y+12}" fill="none" stroke="{p['accent']}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
        </g>''')
        parcels.append(f'<g transform="translate({x+21} {y+20})"><g class="package-arrival parcel-{index}">{cube(0,0,14,p,solid=True)}</g></g>')
    return f'''
    <rect x="-156" y="-95" width="316" height="202" rx="13" fill="{p['panel']}" stroke="{p['accent']}" stroke-width="1.3"/>
    <path d="M-156-63H160" stroke="{p['line']}"/>
    <rect x="-135" y="-82" width="147" height="8" rx="4" fill="{p['line']}"/>
    <path d="M111-79h13m-6.5-6.5v13M138-82h9v8h-9Z" fill="none" stroke="{p['muted']}"/>
    {''.join(tiles)}
    <path d="M49-36v109" stroke="{p['line']}"/>
    <path d="M70-25h66M70-6h49M70 14h56" stroke="{p['muted']}" stroke-width="3"/>
    <path d="M70 40h66" stroke="{p['line']}" stroke-width="4"/>
    <path class="install-progress" pathLength="100" d="M70 40h66" stroke="{p['accent']}" stroke-width="4"/>
    <path class="install-done" pathLength="100" d="M77 64 88 76 104 55" fill="none" stroke="{p['accent']}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
    <g transform="translate(126 88)">{cube(0, 0, 37, p, solid=True)}</g>
    {''.join(parcels)}
    <path d="M-169 129h190m16 0h24" stroke="{p['line']}"/>
    '''


def pocket(p):
    finders = "".join(
        f'<rect x="{x}" y="{y}" width="24" height="24" rx="2" fill="none" stroke="{p["accent"]}" stroke-width="3"/>'
        f'<rect x="{x+7}" y="{y+7}" width="10" height="10" fill="{p["accent"]}"/>'
        for x, y in ((-136, -5), (-104, -5), (-136, 27))
    )
    return f'''
    <g transform="translate(-27 -19) rotate(-5)">
      <rect x="-160" y="-70" width="234" height="158" rx="11" fill="{p['panel']}" stroke="{p['line']}" stroke-width="1.5"/>
      <path d="M-160-42H74" stroke="{p['line']}"/>
      <circle cx="-143" cy="-56" r="3" fill="{p['accent']}"/>
      <path d="M-131-56h41M-65-14h112M-65 5h93M-65 24h106M-65 44h59" stroke="{p['muted']}" stroke-width="2"/>
      {finders}
      <path class="qr-scan" d="M-143-10h70" stroke="{p['accent']}" stroke-width="2"/>
      <g class="paired-mark"><circle cx="-83" cy="44" r="12" fill="{p['accent']}"/><path d="M-89 44-84 49-77 39" fill="none" stroke="{p['bg']}" stroke-width="2.5"/></g>
    </g>
    <path class="orbit" d="M-13 85C13 145 96 159 138 104" fill="none" stroke="{p['accent']}" stroke-width="2"/>
    <g transform="translate(-62 -39)"><g class="handoff">{cube(0,0,9,p,solid=True)}</g></g>
    <g transform="translate(87 -3) rotate(7)"><g class="levitate">
      <rect x="-64" y="-131" width="132" height="262" rx="24" fill="{p['bg']}" stroke="{p['accent']}" stroke-width="2"/>
      <rect x="-53" y="-116" width="110" height="230" rx="15" fill="{p['panel']}"/>
      <rect x="-19" y="-121" width="43" height="7" rx="3.5" fill="{p['accent']}" opacity=".55"/>
      <circle cx="-31" cy="-85" r="9" fill="{p['soft']}" stroke="{p['accent']}"/>
      <path d="M-12-89h48M-12-79h31" stroke="{p['muted']}" stroke-width="2"/>
      <g class="chat-line message-0"><rect x="-39" y="-53" width="83" height="31" rx="9" fill="{p['soft']}"/><path d="M-28-40h51M-28-31h34" stroke="{p['accent']}" stroke-width="2"/></g>
      <g class="chat-line message-1"><rect x="-27" y="-9" width="73" height="43" rx="9" fill="{p['bg']}"/><path d="M-16 4h51M-16 14h37M-16 24h44" stroke="{p['muted']}" stroke-width="2"/></g>
      <g class="chat-line message-2"><rect x="-39" y="47" width="82" height="27" rx="9" fill="{p['soft']}"/><path d="M-27 60h52" stroke="{p['accent']}" stroke-width="2"/></g>
      <rect x="-39" y="89" width="83" height="15" rx="7" fill="{p['bg']}"/>
      <circle class="heartbeat" cx="35" cy="96.5" r="4" fill="{p['accent']}"/>
      <g class="typing-dots" fill="{p['accent']}"><circle cx="-27" cy="96.5" r="2.5"/><circle cx="-17" cy="96.5" r="2.5"/><circle cx="-7" cy="96.5" r="2.5"/></g>
      <path d="M-19 120h42" stroke="{p['muted']}" stroke-width="3" stroke-linecap="round"/>
    </g></g>
    '''


ART = {"bcore": world, "minecraft-panel": panel, "softdownloader": software, "opencode-pocket": pocket}
