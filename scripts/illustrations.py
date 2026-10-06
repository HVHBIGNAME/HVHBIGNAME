"""Original SVG illustrations; motion is driven by the shared atlas stylesheet."""

import math


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
    for depth in range(9):
        for a in range(5):
            b = depth - a
            if not 0 <= b < 5:
                continue
            height = max(1, 4 - abs(a-2) - abs(b-2))
            pieces.append(f'<g class="world-column" style="--lag:{(a+b)*.12:.2f}s">')
            for z in range(height):
                pieces.append(cube((a-b)*25, (a+b)*14.43-z*28.86, 28.86, p, solid=height >= 3 and z == height-1))
            pieces.append('</g>')
    return f'''
    <ellipse cx="0" cy="103" rx="175" ry="55" fill="{p['soft']}" opacity=".24"/>
    <path d="M-181 100 0-4 181 100 0 204Z" fill="none" stroke="{p['line']}"/>
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
    <g class="levitate">
      <rect x="-166" y="-106" width="332" height="217" rx="14" fill="{p['panel']}" stroke="{p['accent']}" stroke-width="1.4"/>
      <path d="M-166-73H166" stroke="{p['line']}"/>
      <circle cx="-145" cy="-90" r="4" fill="{p['accent']}" class="heartbeat"/>
      <circle cx="-128" cy="-90" r="4" fill="{p['line']}"/>
      <circle cx="-111" cy="-90" r="4" fill="{p['line']}"/>
      <path d="M88-90h55" stroke="{p['muted']}" stroke-width="2"/>
      <rect x="-145" y="-53" width="67" height="142" rx="7" fill="{p['bg']}" stroke="{p['line']}"/>
      {cube(-112, -12, 22, p, solid=True)}
      <path d="M-131 43h38m-38 16h29m-29 16h34" stroke="{p['muted']}" stroke-width="2"/>
      <rect x="-57" y="-53" width="89" height="49" rx="7" fill="{p['bg']}" stroke="{p['line']}"/>
      <rect x="46" y="-53" width="98" height="49" rx="7" fill="{p['bg']}" stroke="{p['line']}"/>
      <path d="M-43-36h28M60-36h30" stroke="{p['muted']}" stroke-width="2"/>
      <path class="trace" pathLength="100" d="M-43-20h59M60-20h68" stroke="{p['accent']}" stroke-width="3"/>
      <rect x="-57" y="12" width="201" height="77" rx="7" fill="{p['bg']}" stroke="{p['line']}"/>
      <path d="M-43 69H130M-43 38H130" stroke="{p['line']}" stroke-dasharray="2 5"/>
      <path class="trace" pathLength="100" d="M-43 65-25 65-8 34 15 56 36 45 57 64 79 27 100 42 130 42" fill="none" stroke="{p['accent']}" stroke-width="2.5"/>
    </g>
    <path d="M-184 131H84m15 0h42" stroke="{p['line']}"/>
    <circle class="heartbeat" cx="153" cy="131" r="4" fill="{p['accent']}"/>
    '''


def software(p):
    tiles = []
    for index in range(6):
        x = -134 + index % 3 * 55
        y = -36 + index // 3 * 54
        tiles.append(f'''
        <g class="package-tile" style="--lag:{index*.35}s">
          <rect x="{x}" y="{y}" width="43" height="42" rx="7" fill="{p['soft']}" stroke="{p['accent']}" stroke-opacity=".45"/>
          <path d="M{x+13} {y+13}h17v17h-17Z" fill="none" stroke="{p['accent']}"/>
          <path d="M{x+17} {y+20}  {x+21} {y+24} {x+27} {y+17}" fill="none" stroke="{p['accent']}" stroke-width="1.5"/>
        </g>''')
    return f'''
    <rect x="-156" y="-95" width="316" height="202" rx="13" fill="{p['panel']}" stroke="{p['accent']}" stroke-width="1.3"/>
    <path d="M-156-63H160" stroke="{p['line']}"/>
    <rect x="-135" y="-82" width="147" height="8" rx="4" fill="{p['line']}"/>
    <path d="M111-79h13m-6.5-6.5v13M138-82h9v8h-9Z" fill="none" stroke="{p['muted']}"/>
    {''.join(tiles)}
    <path d="M49-36v109" stroke="{p['line']}"/>
    <path d="M70-25h66M70-6h49M70 14h56" stroke="{p['muted']}" stroke-width="3"/>
    <path class="trace" pathLength="100" d="M70 40h66" stroke="{p['accent']}" stroke-width="4"/>
    <path class="download" d="M103 54v30m-11-11 11 11 11-11" fill="none" stroke="{p['accent']}" stroke-width="3" stroke-linecap="round"/>
    <g transform="translate(126 88)"><g class="levitate">{cube(0, 0, 47, p, solid=True)}</g></g>
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
    </g>
    <path class="orbit" d="M-13 85C13 145 96 159 138 104" fill="none" stroke="{p['accent']}" stroke-width="2"/>
    <g transform="translate(87 -3) rotate(7)"><g class="levitate">
      <rect x="-64" y="-131" width="132" height="262" rx="24" fill="{p['bg']}" stroke="{p['accent']}" stroke-width="2"/>
      <rect x="-53" y="-116" width="110" height="230" rx="15" fill="{p['panel']}"/>
      <rect x="-19" y="-121" width="43" height="7" rx="3.5" fill="{p['accent']}" opacity=".55"/>
      <circle cx="-31" cy="-85" r="9" fill="{p['soft']}" stroke="{p['accent']}"/>
      <path d="M-12-89h48M-12-79h31" stroke="{p['muted']}" stroke-width="2"/>
      <g class="chat-line" style="--lag:0s"><rect x="-39" y="-53" width="83" height="31" rx="9" fill="{p['soft']}"/><path d="M-28-40h51M-28-31h34" stroke="{p['accent']}" stroke-width="2"/></g>
      <g class="chat-line" style="--lag:1s"><rect x="-27" y="-9" width="73" height="43" rx="9" fill="{p['bg']}"/><path d="M-16 4h51M-16 14h37M-16 24h44" stroke="{p['muted']}" stroke-width="2"/></g>
      <g class="chat-line" style="--lag:2s"><rect x="-39" y="47" width="82" height="27" rx="9" fill="{p['soft']}"/><path d="M-27 60h52" stroke="{p['accent']}" stroke-width="2"/></g>
      <rect x="-39" y="89" width="83" height="15" rx="7" fill="{p['bg']}"/>
      <circle class="heartbeat" cx="35" cy="96.5" r="4" fill="{p['accent']}"/>
      <path d="M-19 120h42" stroke="{p['muted']}" stroke-width="3" stroke-linecap="round"/>
    </g></g>
    '''


ART = {"bcore": world, "minecraft-panel": panel, "softdownloader": software, "opencode-pocket": pocket}
