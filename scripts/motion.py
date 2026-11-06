"""Native SVG choreography. Layout and animated transforms live on separate groups."""

from html import escape

CYCLE_SECONDS = 12
INTRO_END = 2.6
EASE_OUT = '.16 1 .3 1'
EASE_IN_OUT = '.45 0 .25 1'


def animate(attribute, values, duration, begin=0, *, times=None, easing=EASE_OUT, repeat=False, kind=None):
    values = [str(value) for value in values]
    if len(values) < 2:
        raise ValueError('An animation needs at least two values')
    times = [i / (len(values) - 1) for i in range(len(values))] if times is None else times
    if len(times) != len(values) or times[0] != 0 or times[-1] != 1:
        raise ValueError('An animation needs matching values and normalized endpoints')
    if any(a >= b for a, b in zip(times, times[1:])):
        raise ValueError('Animation key times must be strictly increasing')
    attrs = {
        'attributeName': attribute, 'values': ';'.join(values),
        'keyTimes': ';'.join(f'{t:g}' for t in times), 'begin': f'{begin:g}s',
        'dur': f'{duration:g}s', 'fill': 'freeze', 'calcMode': 'spline' if easing else 'linear',
    }
    if easing:
        attrs['keySplines'] = ';'.join([easing] * (len(values) - 1))
    if repeat:
        attrs['repeatCount'] = 'indefinite'
    if kind:
        attrs['type'] = kind
    tag = 'animateTransform' if kind else 'animate'
    return f'<{tag} ' + ' '.join(f'{key}="{escape(value, quote=True)}"' for key, value in attrs.items()) + '/>'


def enter(body, *, offset='0 36', begin=.45, duration=1.4, turn=0, name='entrance'):
    """Every motion group declares its rest state for reduced-motion rendering."""
    if turn:
        body = (f'<g transform="rotate({turn})" data-rest-transform="rotate(0)">'
                + animate('transform', [turn, 0], duration, begin, kind='rotate') + body + '</g>')
    return (f'<g class="{name}" opacity="0" transform="translate({offset})" '
            'data-rest-opacity="1" data-rest-transform="translate(0 0)">'
            + animate('opacity', [0, 1], .5, begin)
            + animate('transform', [offset, '0 0'], duration, begin, kind='translate') + body + '</g>')


def drift(body, amplitude=6):
    return ('<g class="drift">' + animate('transform', ['0 0', f'0 {-amplitude}', '0 0'],
            CYCLE_SECONDS, INTRO_END, kind='translate', easing=EASE_IN_OUT, repeat=True) + body + '</g>')


def draw_line(path, color, *, width=1, begin=.2, duration=1.5):
    return (f'<path d="{path}" fill="none" stroke="{color}" stroke-width="{width}" '
            'pathLength="100" stroke-dasharray="100" stroke-dashoffset="100" data-rest-stroke-dashoffset="0">'
            + animate('stroke-dashoffset', [100, 0], duration, begin) + '</path>')


def materials(p):
    return f'''
    <linearGradient id="surface" x2=".8" y2="1">
      <stop stop-color="{p['panel']}"/><stop offset="1" stop-color="{p['bg']}"/>
    </linearGradient>
    <linearGradient id="glass" x2=".6" y2="1">
      <stop stop-color="#303937"/><stop offset=".48" stop-color="#111816"/><stop offset="1" stop-color="#070c0b"/>
    </linearGradient>
    <linearGradient id="titanium" x1="0" y1="0" x2=".8" y2="1">
      <stop stop-color="#e8ede8"/><stop offset=".23" stop-color="#7c8984"/>
      <stop offset=".45" stop-color="#222d2a"/><stop offset=".49" stop-color="#e6f0e8"/>
      <stop offset=".65" stop-color="#85928a"/><stop offset="1" stop-color="#24302b"/>
    </linearGradient>
    <filter id="shadow" x="-40%" y="-50%" width="180%" height="220%">
      <feGaussianBlur stdDeviation="14"/>
    </filter>
    <pattern id="texture" width="7" height="7" patternUnits="userSpaceOnUse">
      <circle cx="1" cy="1" r=".5" fill="{p['fg']}" opacity=".035"/>
    </pattern>'''


def scene_defs(p, name, height):
    return f'''
    <radialGradient id="light-{name}">
      <stop stop-color="{p['accent']}" stop-opacity="{p['aura']}"/>
      <stop offset="1" stop-color="{p['accent']}" stop-opacity="0"/>
    </radialGradient>
    <clipPath id="scene-frame-{name}" clipPathUnits="userSpaceOnUse">
      <rect x="1" y="1" width="1198" height="{height-2}" rx="22"/>
    </clipPath>
    <clipPath id="reveal-{name}" clipPathUnits="userSpaceOnUse">
      <path d="M-180 0H1400L1580 {height}H0Z" transform="translate(-1600 0)">
        {animate('transform', ['-1600 0', '0 0'], 1.65, .2, kind='translate', easing=EASE_IN_OUT)}
      </path>
    </clipPath>'''


def stage(p, name, height):
    return f'''
    <g class="stage">
      <rect x="1" y="1" width="1198" height="{height-2}" rx="22" fill="url(#surface)"/>
      <ellipse cx="950" cy="225" rx="435" ry="350" fill="url(#light-{name})"/>
      <rect width="1200" height="{height}" fill="url(#texture)"/>
      <path d="M650 1H1100L1199 100" fill="none" stroke="{p['fg']}" opacity=".055"/>
      <rect x="1" y="1" width="1198" height="{height-2}" rx="22" fill="none" stroke="{p['line']}"/>
    </g>'''
