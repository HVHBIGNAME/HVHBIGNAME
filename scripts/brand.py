"""Machined HVH letterforms, assembled into one solid mark."""

import xml.etree.ElementTree as ET

from motion import CYCLE_SECONDS, INTRO_END, animate, enter
from svg_timeline import static_copy

LETTERS = (
    ('H', 'M18 31 29 20h6v32h29V20h17v88H64V70H35v38H18Z'),
    ('V', 'M88 20h20l18 57 18-57h20l-30 88h-16Z'),
    ('H', 'M171 20h17v32h29V20h6l11 11v77h-17V70h-29v38h-17Z'),
)


def defs():
    outlines = ''.join(f'<path d="{d}"/>' for _, d in LETTERS)
    return f'''
    <linearGradient id="hvh-metal" x1="0" y1="0" x2=".35" y2="1">
      <stop stop-color="#fcfff8"/><stop offset=".32" stop-color="#9ea99c"/>
      <stop offset=".49" stop-color="#445147"/><stop offset=".51" stop-color="#eaf1e2"/>
      <stop offset="1" stop-color="#8c9a85"/>
    </linearGradient>
    <linearGradient id="hvh-core" x2=".5" y2="1">
      <stop stop-color="#f2ffd6"/><stop offset=".5" stop-color="#c4f471"/><stop offset="1" stop-color="#669030"/>
    </linearGradient>
    <linearGradient id="hvh-sheen" x2="1" y2="0">
      <stop stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".8"/>
      <stop offset="1" stop-color="#fff" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="hvh-clip">{outlines}</clipPath>'''


def sculpture():
    letters = []
    for index, (letter, d) in enumerate(LETTERS):
        depth = ''.join(f'<path d="{d}" transform="translate({i*.65} {i})"/>' for i in range(12, 0, -1))
        faces = (f'<g fill="#344037" stroke="#66735c" stroke-width=".4">{depth}</g>'
                 f'<path data-letter="{letter}" d="{d}" fill="url(#hvh-{"core" if index == 1 else "metal"})"/>'
                 f'<path d="{d}" fill="none" stroke="#f2f8e5" stroke-opacity=".5" stroke-width=".7"/>')
        letters.append(enter(faces, offset=('-75 -40', '0 80', '85 -25')[index],
                             turn=(-12, 8, 15)[index], begin=.35, duration=1.9, name='letter-build'))
    sheen = ('<g class="transient" clip-path="url(#hvh-clip)"><g transform="skewX(-20)">'
             '<rect x="-100" y="0" width="65" height="130" fill="url(#hvh-sheen)">'
             + animate('transform', ['0 0', '420 0', '420 0'], CYCLE_SECONDS, INTRO_END,
                       times=[0, .18, 1], kind='translate', repeat=True) + '</rect></g></g>')
    return '<g transform="translate(-126 -64)">' + ''.join(letters) + sheen + '</g>'


def logo(p):
    art = ET.fromstring('<g xmlns="http://www.w3.org/2000/svg">' + sculpture() + '</g>')
    art = ET.tostring(static_copy(art), encoding='unicode')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512" role="img" aria-label="HVH">
    <title>HVH / BIGNAME</title><defs>{defs()}</defs>
    <rect width="512" height="512" rx="100" fill="{p['bg']}"/>
    <g transform="translate(242 244) rotate(-12) scale(1.8)">{art}</g>
    </svg>\n'''
