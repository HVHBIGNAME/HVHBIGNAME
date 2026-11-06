#!/usr/bin/env python3
"""Editorial project portfolio: six views of a single SVG clock per theme."""

import json
from datetime import date
from html import escape
from pathlib import Path

import brand
import motion
from illustrations import ART
from svg_timeline import with_static_layers

ROOT = Path(__file__).resolve().parents[1]
VIEW_HEIGHT = 520
PALETTES = {
    'dark': {
        'bg': '#0c100e', 'panel': '#171d19', 'fg': '#eff2e8', 'muted': '#a2ada3',
        'line': '#303a31', 'accent': '#c4ec91', 'aura': '.13',
        'levels': ['#2a342d', '#465b3b', '#69844d', '#93b86c', '#c4ec91'],
    },
    'light': {
        'bg': '#f2f3ec', 'panel': '#fcfcf6', 'fg': '#202a22', 'muted': '#59675b',
        'line': '#d4dccf', 'accent': '#56763f', 'aura': '.12',
        'levels': ['#d6dfcf', '#bccdaf', '#94ae80', '#6e9258', '#486d34'],
    },
}
PROJECTS = {
    'bcore': {
        'name': 'BCore', 'eyebrow': '01 / WORLD ENGINE', 'status': 'ALPHA',
        'description': ('Minecraft-сервер, написанный на Rust.', 'Свои миры. Свой движок. Свои правила.'),
        'mobile': ('Minecraft-сервер на Rust.', 'Миры, освещение и плагины.'),
        'mobile_title': ('BCore',),
        'tech': 'RUST / WORLDGEN / NATIVE PLUGINS', 'mobile_meta': 'Rust · alpha',
        'dark': '#c4ec91', 'light': '#557835',
    },
    'minecraft-panel': {
        'name': 'emberdeck', 'eyebrow': '02 / SERVER CONTROL', 'status': 'EARLY RELEASE',
        'description': ('Твой сервер. Всё под контролем.', 'Консоль, SFTP и бэкапы в одном бинарнике.'),
        'mobile': ('Minecraft-панель на Rust.', 'Консоль, SFTP и резервные копии.'),
        'mobile_title': ('emberdeck',),
        'tech': 'RUST / SELF-HOSTED / LINUX', 'mobile_meta': 'Rust · self-hosted',
        'dark': '#eab88a', 'light': '#975b2b',
    },
    'softdownloader': {
        'name': 'SoftDownloader', 'eyebrow': '03 / DESKTOP UTILITY', 'status': 'WINDOWS',
        'description': ('Нужный софт. Одной очередью.', 'Каталог программ и установка в одном EXE.'),
        'mobile': ('Весь нужный софт в одном EXE.', 'Установка очередью и перенос списка.'),
        'mobile_title': ('Soft', 'Downloader'),
        'tech': 'RUST / EGUI / WINDOWS', 'mobile_meta': 'Rust · egui · Windows',
        'dark': '#a1d3c6', 'light': '#326e60',
    },
    'opencode-pocket': {
        'name': 'OpenCode Pocket', 'eyebrow': '04 / MOBILE COMPANION', 'status': 'ANDROID + IOS',
        'description': ('Твои сессии. Теперь в кармане.', 'Подключись по QR и продолжай с телефона.'),
        'mobile': ('OpenCode на Android и iOS.', 'Сессии с компьютера — по QR.'),
        'mobile_title': ('OpenCode', 'Pocket'),
        'tech': 'TYPESCRIPT / REACT / COMPANION BRIDGE', 'mobile_meta': 'Android · iOS · QR',
        'dark': '#c9d8b7', 'light': '#647c48',
    },
}
VIEWS = ('hero', *PROJECTS, 'signal')


def text(x, y, value, size=18, fill='fg', palette=None, **attrs):
    p = palette or PALETTES['dark']
    attributes = ' '.join(f'{key.rstrip("_").replace("_", "-")}="{escape(str(value), quote=True)}"' for key, value in attrs.items())
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{p.get(fill, fill)}" {attributes}>{escape(str(value))}</text>'


def scene_palette(theme, name):
    p = dict(PALETTES[theme])
    if name in PROJECTS:
        p.update(accent=PROJECTS[name][theme])
    return p


def stylesheet():
    return '''
    text { font-family: 'Segoe UI', Arial, sans-serif; }
    .mono { font-family: 'Cascadia Mono', Consolas, monospace; }
    .mobile-copy, .motion-static { display:none; }
    .art-anchor { transform:translate(920px,260px); }
    [data-art="minecraft-panel"] { transform:translate(925px,237px) scale(.94); }
    .hero-art { transform:translate(943px,250px) rotate(-12deg) scale(1.8); }
    .headline { font-weight:750; letter-spacing:-3px; }
    @media (max-width:600px) {
      .desktop-copy { display:none; } .mobile-copy { display:inline; }
      .art-anchor { transform:translate(948px,211px) scale(.72); }
      [data-art="minecraft-panel"] { transform:translate(948px,201px) scale(.66); }
      .hero-art { transform:translate(975px,199px) rotate(-12deg) scale(1.2); }
      .signal-title { font-size:43px; }
      .signal-value { font-size:102px; }
      .signal-label { font-size:29px; }
      .signal-date { font-size:26px; }
      .signal-auto { display:none; }
    }
    @media (prefers-reduced-motion: reduce) {
      .motion-active { display:none; } .motion-static { display:inline; }
    }
    '''


def document(title, description, height, body, theme, views=(), scene='signal'):
    p = PALETTES[theme]
    names = views or (scene,)
    view_tags = ''.join(f'<view id="{name}" viewBox="0 {i*VIEW_HEIGHT} 1200 {VIEW_HEIGHT}"/>' for i, name in enumerate(views))
    height_attr = '' if views else f' height="{height}"'
    defs = ''.join(motion.scene_defs(scene_palette(theme, name), name, VIEW_HEIGHT) for name in names)
    if not views:
        body = scene_group(scene, body, 0)
    markup = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200"{height_attr} viewBox="0 0 1200 {height}" role="img" aria-labelledby="title desc">
    <title id="title">{escape(title)}</title><desc id="desc">{escape(description)}</desc>
    {view_tags}
    <defs>{motion.materials(p)}{brand.defs()}{defs}</defs>
    <style>{stylesheet()}</style>
    {body}
    </svg>'''
    return with_static_layers(markup)


def copy_reveal(body, name):
    return f'<g data-reveal="true" clip-path="url(#reveal-{name})">{body}</g>'


def masthead(p, left, right, mobile=False):
    font, y = (26, 58) if mobile else (16, 57)
    body = text(58, y, left, font, 'muted', p, class_='mono', letter_spacing=1.5)
    if not mobile:
        body += text(1142, y, right, 15, 'accent', p, class_='mono', text_anchor='end', letter_spacing=1)
    return motion.enter(body, offset='0 12', begin=.15, duration=.8)


def footer(p, left, right='СМОТРЕТЬ ПРОЕКТ', mobile=False):
    y, font = 475, (33 if mobile else 17)
    body = text(59, y, left, font, 'muted', p, class_='mono')
    if not mobile:
        body += text(1076, y, right, 16, 'fg', p, text_anchor='end', letter_spacing=1)
    body += f'<circle cx="1120" cy="468" r="{28 if mobile else 22}" fill="none" stroke="{p["line"]}"/>'
    body += f'<path d="M1109 478l21-21m-21 0h21v21" fill="none" stroke="{p["accent"]}" stroke-width="2"/>'
    return motion.draw_line('M58 431H1142', p['line'], begin=.55) + motion.enter(body, offset='0 20', begin=.8, duration=1)


def hero_body(theme):
    p = PALETTES[theme]
    copies = []
    for mobile in (False, True):
        cls = 'mobile-copy' if mobile else 'desktop-copy'
        title = text(53, 205, 'BIGNAME', 111 if not mobile else 106, 'fg', p, class_='headline')
        title = motion.enter(title, offset='0 45', begin=.3, duration=1.5)
        intro = (text(58, 329 if mobile else 282, 'Игровые миры.', 47 if mobile else 32, 'fg', p)
                 + text(58, 387 if mobile else 326, 'Инструменты на каждый день.', 45 if mobile else 30, 'muted', p))
        copies.append(f'<g class="{cls}">' + masthead(p, 'HVHBIGNAME', 'RUST / TYPESCRIPT', mobile)
                      + copy_reveal(title + motion.enter(intro, begin=.6, offset='0 24'), 'hero')
                      + footer(p, 'СВОИ ПРОЕКТЫ' if mobile else 'INDEPENDENT DEVELOPER', 'ИЗБРАННЫЕ ПРОЕКТЫ НИЖЕ', mobile) + '</g>')
    art = '<g class="art-anchor hero-art">' + motion.drift(brand.sculpture(), 3) + '</g>'
    return ''.join(copies) + art


def project_body(theme, name):
    p, item = scene_palette(theme, name), PROJECTS[name]
    copies = []
    for mobile in (False, True):
        cls = 'mobile-copy' if mobile else 'desktop-copy'
        if mobile:
            lines = item['mobile_title']
            title = ''.join(text(52, (191 if len(lines) == 1 else 156)+i*85, line,
                                 100 if len(lines) == 1 else 86, 'fg', p, class_='headline') for i, line in enumerate(lines))
        else:
            title = text(53, 196, item['name'], 89 if len(item['name']) < 10 else 65, 'fg', p, class_='headline')
        descriptions = ''.join(text(58, (340 if mobile else 268)+i*(57 if mobile else 43), line,
                                   43 if mobile else 27, 'fg' if i == 0 else 'muted', p)
                               for i, line in enumerate(item['mobile'] if mobile else item['description']))
        copy = motion.enter(title, begin=.3, offset='0 42') + motion.enter(descriptions, begin=.6, offset='0 24')
        copies.append(f'<g class="{cls}">' + masthead(p, item['eyebrow'], item['status'], mobile)
                      + copy_reveal(copy, name) + footer(p, item['mobile_meta'] if mobile else item['tech'], mobile=mobile) + '</g>')
    art = f'<g class="art-anchor" data-art="{name}">' + ART[name](p) + '</g>'
    return ''.join(copies) + art


def signal_body(days, theme):
    p = PALETTES[theme]
    total, active, peak = sum(v for _, v in days), sum(v > 0 for _, v in days), max(v for _, v in days)
    title = text(57, 64, 'В процессе.', 35, 'fg', p, class_='signal-title', font_weight=650)
    title += text(1142, 60, 'GITHUB / ПОСЛЕДНИЕ 90 ДНЕЙ', 16, 'muted', p, class_='signal-auto mono', text_anchor='end')
    parts = [motion.enter(title, offset='0 12', begin=.15, duration=.8)]
    for x, value, name in ((57, total, 'CONTRIBUTIONS'), (477, active, 'АКТИВНЫХ ДНЕЙ'), (856, peak, 'ПИК ЗА ДЕНЬ')):
        number = text(x, 201, value, 94, 'fg', p, class_='signal-value', font_weight=650, letter_spacing=-4)
        number += text(x+3, 237, name, 17, 'muted', p, class_='signal-label mono', letter_spacing=1)
        parts.append(motion.enter(number, begin=.3, offset='0 35'))
    for y in (288, 351, 414):
        parts.append(f'<path d="M58 {y}H1142" stroke="{p["line"]}" stroke-dasharray="2 7"/>')
    bars = []
    step = 1084 / len(days)
    for i, (day, count) in enumerate(days):
        height = 2 if count == 0 else 124*count/peak
        level = min(4, (4*count+peak-1)//peak) if peak else 0
        bars.append(f'<rect class="bar" x="{58+i*step:.2f}" y="{414-height:.2f}" width="{step-3:.2f}" height="{height:.2f}" rx="2" fill="{p["levels"][level]}">'
                    f'<title>{day.isoformat()}: {count} contributions</title></rect>')
    parts.append('<g transform="translate(0 414)"><g class="chart-grow" transform="scale(1 0)" data-rest-transform="scale(1 1)">'
                 + motion.animate('transform', ['1 0', '1 1'], 1.85, .35, kind='scale')
                 + '<g transform="translate(0 -414)">' + ''.join(bars) + '</g></g></g>')
    parts.append(text(58, 478, days[0][0].isoformat(), 17, 'muted', p, class_='signal-date mono'))
    parts.append(text(1142, 478, days[-1][0].isoformat()+' / UTC', 17, 'muted', p, class_='signal-date mono', text_anchor='end'))
    return ''.join(parts)


def scene_group(name, body, index):
    return (f'<g id="scene-{name}" transform="translate(0 {index*VIEW_HEIGHT})">'
            f'<g clip-path="url(#scene-frame-{name})">{body}</g></g>')


def hero(theme):
    body = motion.stage(PALETTES[theme], 'hero', VIEW_HEIGHT) + hero_body(theme)
    return document('HVH / BIGNAME', 'Игровые миры. Инструменты на каждый день. Rust и TypeScript.', VIEW_HEIGHT, body, theme, scene='hero')


def project(theme, name):
    body = motion.stage(scene_palette(theme, name), name, VIEW_HEIGHT) + project_body(theme, name)
    return document(PROJECTS[name]['name'], ' '.join(PROJECTS[name]['description']), VIEW_HEIGHT, body, theme, scene=name)


def build_atlas(days, theme):
    bodies = [hero_body(theme), *(project_body(theme, name) for name in PROJECTS), signal_body(days, theme)]
    groups = [scene_group(name, motion.stage(scene_palette(theme, name), name, VIEW_HEIGHT)+body, index)
              for index, (name, body) in enumerate(zip(VIEWS, bodies))]
    return document('HVHBIGNAME / selected work',
                    'BCore, emberdeck, SoftDownloader и OpenCode Pocket. Общее вступление и объёмные иллюстрации. Публичная активность обновляется каждый час.',
                    len(VIEWS)*VIEW_HEIGHT, ''.join(groups), theme, views=VIEWS)


def activity_json(days):
    return json.dumps({'source': 'GitHub public contributions', 'days': [{'date': day.isoformat(), 'count': count} for day, count in days]}, indent=2) + '\n'


def load_activity(path):
    payload = json.loads(path.read_text(encoding='utf-8'))
    days = [(date.fromisoformat(day['date']), day['count']) for day in payload['days']]
    if len(days) != 90 or any(type(count) is not int or count < 0 for _, count in days):
        raise ValueError('Activity cache must contain 90 non-negative daily counts')
    if any((right[0]-left[0]).days != 1 for left, right in zip(days, days[1:])):
        raise ValueError('Activity cache must be chronological and contiguous')
    return days


def main():
    days = load_activity(ROOT / 'assets/activity.json')
    for theme, p in PALETTES.items():
        path = ROOT / 'assets' / f'profile-{theme}.svg'
        path.write_text(build_atlas(days, theme), encoding='utf-8', newline='\n')
        (ROOT / 'assets' / f'hvh-mark-{theme}.svg').write_text(brand.logo(p), encoding='utf-8', newline='\n')
        print(path.relative_to(ROOT))


if __name__ == '__main__':
    main()
