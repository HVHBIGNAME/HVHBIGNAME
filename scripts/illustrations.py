"""Original product sculptures, drawn as self-contained SVG rather than screenshots."""

from motion import CYCLE_SECONDS, INTRO_END, animate, drift, enter


def label(x, y, value, size=12, color='#9daaa4', **attrs):
    extra = ' '.join(f'{key.rstrip("_").replace("_", "-")}="{value}"' for key, value in attrs.items())
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" {extra}>{value}</text>'


def shadow(width=190):
    return f'<ellipse cy="178" rx="{width}" ry="18" fill="#000" opacity=".25" filter="url(#shadow)"/>'


def voxel(x, y, elevation, top, left, right, size=48):
    half = size / 2
    return f'''
    <g transform="translate({x} {y})" stroke-linejoin="round">
      <path d="M{-size} 0 0 {half}V{half+elevation}L{-size} {elevation}Z" fill="{left}" stroke="{left}"/>
      <path d="M0 {half} {size} 0V{elevation}L0 {half+elevation}Z" fill="{right}" stroke="{right}"/>
      <path d="M0 {-half} {size} 0 0 {half} {-size} 0Z" fill="{top}" stroke="#e5f2ba" stroke-opacity=".16"/>
      <path d="M{-size+2} 1 0 {half} {size-2} 1" stroke="#dffaaa" stroke-opacity=".22" fill="none"/>
    </g>'''


def bcore(p):
    blocks = []
    colors = ('#7c9c55', '#8eac64', '#687f47', '#9ab571')
    for row in range(4):
        for col in range(4):
            x, y = (col-row)*48, (col+row)*24-75
            elevation = 50 + ((row*3+col*5) % 4)*9
            tile = voxel(x, y-elevation, elevation, colors[(row+col)%4], '#34472d', '#202e23')
            tile += f'<path d="M{x-37} {y-elevation+22}l23 11v14l-23-11Z" fill="#111e17" opacity=".32"/>'
            blocks.append(enter(tile, offset=f'{(col-row)*23} {130+(row+col)*9}',
                                begin=.35, duration=1.85, name='voxel-build'))
    core = voxel(0, -133, 60, '#dffcb0', '#89bb51', '#4e7c36', size=46)
    core += '<path d="M0-151v36m-16-27 16-9 16 9M0-115l-16-9m16 9 16-9" fill="none" stroke="#f4ffe4" stroke-width="3"/>'
    crystal = enter(core, offset='0 -105', begin=.35, duration=1.85, name='core-build')
    return shadow(150) + drift(''.join(blocks) + crystal, 7)


def panel_shell(x, y, width, height, radius=14):
    return (f'<rect x="{x+5}" y="{y+7}" width="{width}" height="{height}" rx="{radius}" fill="#050a08"/>'
            f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{radius}" fill="url(#glass)" stroke="#627066" stroke-width="1.3"/>'
            f'<path d="M{x+radius} {y+1}H{x+width-radius}" stroke="#dce4dd" stroke-opacity=".5"/>')


def emberdeck(p):
    back = []
    for index in (2, 1):
        plate = panel_shell(-183, -100+index*27, 370, 226)
        back.append(enter(plate, offset=f'{index*18} {index*42}', begin=.35, duration=1.85, name='panel-build'))
    content = panel_shell(-202, -152, 404, 256)
    content += '<path d="M-200-111H200M-102-111V102" stroke="#33433a"/>'
    content += label(-180, -128, 'emberdeck', 17, '#edf3ea', font_weight='650')
    content += ''.join(f'<circle cx="{154+i*13}" cy="-133" r="3" fill="#718077"/>' for i in range(3))
    for i, title in enumerate(('Overview', 'Console', 'Backups', 'Files')):
        y = -73+i*35
        if i == 1:
            content += f'<rect x="-191" y="{y-18}" width="78" height="28" rx="5" fill="#e6a671" fill-opacity=".1"/>'
        content += label(-180, y, title, 11, '#efb886' if i == 1 else '#81958a')
    content += label(-78, -79, 'SERVER CONSOLE', 11, '#d0dcd1', letter_spacing='1.8')
    for i, (line, color) in enumerate((('> starting world...', '#8faaa0'), ('> loading plugins', '#8faaa0'), ('> server ready_', '#eabe90'))):
        content += enter(label(-77, -41+i*27, line, 13, color, class_='mono'), begin=.9+i*.18, offset='0 10', duration=.7)
    content += '<rect x="-77" y="53" width="248" height="27" rx="5" fill="#080f0b" stroke="#314137"/>'
    content += label(-66, 71, '> _', 12, '#efb886')
    front = enter(content, offset='-42 -72', turn=-8, begin=.35, duration=1.85, name='panel-build')
    floating = panel_shell(25, 78, 186, 68, 12)
    floating += '<circle cx="48" cy="112" r="6" fill="#bcdb95"/>'
    floating += label(65, 108, 'WORLD ONLINE', 11, '#eff1e7', letter_spacing='1.3')
    floating += label(65, 128, 'ready to connect', 10, '#81958a')
    floating = enter(floating, offset='85 55', begin=.35, duration=1.85, name='panel-build')
    return shadow() + drift('<g transform="rotate(-9)">' + ''.join(back) + front + floating + '</g>', 6)


def app_tile(x, y, color, glyph, index):
    tile = (f'<rect x="{x+3}" y="{y+6}" width="72" height="72" rx="17" fill="#030907"/>'
            f'<rect x="{x}" y="{y}" width="72" height="72" rx="17" fill="{color}" stroke="#f4fffc" stroke-opacity=".25"/>'
            f'<g transform="translate({x+36} {y+36})" fill="none" stroke="#1b302c" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">{glyph}</g>')
    return enter(tile, offset=f'{(-1 if index%2 else 1)*(70+index*18)} {-100+index*20}',
                 turn=(index-1)*18, begin=.35, duration=1.85, name='app-build')


def softdownloader(p):
    tray = panel_shell(-193, -80, 386, 224, 24)
    tray += label(-164, -45, 'SOFTWARE LIBRARY', 11, '#a7b4ab', letter_spacing='2')
    tray += '<path d="M-163-28H163" stroke="#34443a"/>'
    tray += '<rect x="-162" y="-8" width="98" height="106" rx="16" fill="#d9e9dc"/>'
    tray += '<path d="M-113 15v48m-17-17 17 17 17-17m-39 34h44" fill="none" stroke="#20382f" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>'
    tray += label(-36, 21, 'One executable.', 18, '#eff6ed', font_weight='600')
    tray += label(-36, 48, 'Your everyday toolkit.', 12, '#839d8e')
    tray += '<rect x="-36" y="70" width="198" height="6" rx="3" fill="#33423a"/>'
    tray += '<rect x="-36" y="70" width="0" data-rest-width="198" height="6" rx="3" fill="#a7d9d0">' + animate('width', [0, 198], 1.2, .85) + '</rect>'
    tray = enter(tray, offset='0 90', begin=.35, duration=1.85, name='dock-build')
    tiles = ''.join(app_tile(x, y, color, glyph, i) for i, (x, y, color, glyph) in enumerate((
        (-164, -162, '#d8e5dd', '<path d="m-15-12-12 12 12 12m30-24 12 12-12 12m-10-31-10 38"/>'),
        (-39, -199, '#a1cec2', '<path d="M-20-18h40v36h-40Z M-20-6h40M-8-18v12"/>'),
        (87, -149, '#cad3bc', '<path d="m-8-19 24 19-24 19Z"/>'),
    )))
    return shadow() + drift('<g transform="rotate(-8)">' + tray + tiles + '</g>', 7)


def pocket(p):
    desktop = panel_shell(-217, -112, 208, 139, 14)
    desktop += '<path d="M-215-78H-11" stroke="#435248"/>'
    desktop += label(-198, -90, 'opencode / desktop', 11, '#c9d7cb')
    desktop += label(-196, -48, '> continue session', 12, '#abc89e')
    desktop += '<path d="M-195-23h83m-83 17h112" stroke="#4f6659" stroke-width="4" stroke-linecap="round"/>'
    desktop = enter(desktop, offset='-100 -35', turn=-10, begin=.35, duration=1.85, name='device-build')
    phone = '<rect x="-48" y="-181" width="184" height="349" rx="35" fill="url(#titanium)" stroke="#dfe8da" stroke-width=".9"/>'
    phone += '<rect x="-43" y="-176" width="174" height="339" rx="30" fill="#070f0b"/>'
    phone += '<rect x="-38" y="-169" width="164" height="324" rx="27" fill="url(#glass)"/>'
    phone += '<rect x="13" y="-160" width="65" height="15" rx="8" fill="#040906"/>'
    phone += label(-20, -109, 'opencode', 21, '#eaf4e8', font_weight='650')
    phone += label(-19, -86, 'YOUR SESSIONS', 9, '#8da193', letter_spacing='1.6')
    for i, line in enumerate(('Build the next thing', 'Review changes', 'Ship it.')):
        y = -65+i*55
        phone += f'<rect x="-23" y="{y}" width="133" height="44" rx="8" fill="#1b2d22" stroke="#354b3b"/>'
        phone += label(-12, y+20, line, 10, '#dee9d9')
        phone += f'<path d="M-12 {y+31}h{50-i*12}" stroke="#668170" stroke-width="2"/>'
    phone += '<rect x="-23" y="112" width="133" height="26" rx="13" fill="#354937"/>'
    phone += label(-10, 129, 'Ask anything...', 10, '#b5c5b2')
    phone += '<rect x="18" y="145" width="58" height="3" rx="2" fill="#bacbbd"/>'
    phone = enter(phone, offset='80 115', turn=20, begin=.35, duration=1.85, name='device-build')
    bridge = '<path d="M-155 44v26q0 21 21 21h54" fill="none" stroke="#b7c7aa" stroke-opacity=".65" stroke-dasharray="4 8">'
    bridge += animate('stroke-dashoffset', [0, -120], CYCLE_SECONDS, INTRO_END, easing=None, repeat=True) + '</path>'
    badge = '<circle cx="-142" cy="111" r="25" fill="#cbd9bb" stroke="#eaf4df"/>'
    badge += '<path d="m-153 112 7 7 14-16" fill="none" stroke="#263e2c" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>'
    return shadow(148) + drift('<g transform="rotate(-10)">' + desktop + bridge + phone
                              + enter(badge, begin=1.35, duration=.7, offset='0 15') + '</g>', 6)


ART = {'bcore': bcore, 'minecraft-panel': emberdeck, 'softdownloader': softdownloader, 'opencode-pocket': pocket}
