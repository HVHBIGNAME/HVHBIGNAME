"""Exercise SVG motion, responsive geometry and actual IMG fragment clocks.

python scripts/verify_visuals.py --output <review-directory>
Requires Playwright (Chromium) and Pillow; never changes published assets.
"""

import argparse
import copy
import io
import json
import math
import threading
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image, ImageChops, ImageDraw, ImageStat
from playwright.sync_api import sync_playwright

from design import ROOT, VIEWS, VIEW_HEIGHT
from motion import CYCLE_SECONDS, INTRO_END, animate
from svg_timeline import NS


def inline(atlas, view, width, isolated=False):
    root = copy.deepcopy(atlas)
    index = VIEWS.index(view)
    root.set('width', str(width))
    root.set('height', str(width*VIEW_HEIGHT/1200))
    root.set('viewBox', f'0 {index*VIEW_HEIGHT} 1200 {VIEW_HEIGHT}')
    for child in list(root):
        if child.tag == NS+'view':
            root.remove(child)
        elif isolated and child.tag == NS+'g' and child.get('transform') != f'translate(0 {index*VIEW_HEIGHT})':
            root.remove(child)
    return '<style>body{margin:0}svg{display:block}</style>' + ET.tostring(root, encoding='unicode')


def freeze(page, seconds):
    page.evaluate('''async t => {
      const svg=document.querySelector('svg'); svg.pauseAnimations();
      svg.setCurrentTime(1); svg.setCurrentTime(Math.max(t,.0001));
      await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
    }''', seconds)


def pixels(page):
    return Image.open(io.BytesIO(page.locator('svg').screenshot())).convert('RGB')


def contact_sheet(images, path, columns=1):
    w, h = images[0][1].size
    sheet = Image.new('RGB', (w*columns, (h+26)*((len(images)+columns-1)//columns)), '#0d1117')
    draw = ImageDraw.Draw(sheet)
    for i, (label, image) in enumerate(images):
        x, y = i%columns*w, i//columns*(h+26)
        draw.text((x+8,y+6), label, fill='white')
        sheet.paste(image, (x,y+26))
    sheet.save(path)


def text_geometry(page, view):
    return page.locator(f'#scene-{view}').evaluate('''scene => {
      const inverse=scene.getScreenCTM().inverse();
      return [...scene.querySelectorAll('.desktop-copy text,.mobile-copy text,.signal-value,.signal-label,.signal-date,.signal-title')]
        .filter(e=>e.getBoundingClientRect().width>0).map(e=>{
          const r=e.getBoundingClientRect();
          const a=new DOMPoint(r.left,r.top).matrixTransform(inverse);
          const b=new DOMPoint(r.right,r.bottom).matrixTransform(inverse);
          return {text:e.textContent,x1:a.x,y1:a.y,x2:b.x,y2:b.y};
        });
    }''')


def motion_state(page, view):
    return page.locator(f'#scene-{view}').evaluate('''scene =>
      [...new Set([...scene.querySelectorAll('animate,animateTransform')].map(e=>e.parentElement))].map(e=>{
        const m=e.getCTM(),s=getComputedStyle(e);
        return [m.a,m.b,m.c,m.d,m.e,m.f,Number(s.opacity),parseFloat(s.strokeDashoffset)];
      })''')


def layout_checks(browser, output):
    report = {'geometry': [], 'isolation': [], 'reduced_motion': [], 'entrances': [], 'cycles': []}
    for theme in ('dark', 'light'):
        atlas = ET.parse(ROOT/f'assets/profile-{theme}.svg').getroot()
        for width in (1200, 358):
            page = browser.new_page(viewport={'width':width,'height':600})
            stills = []
            for view in VIEWS:
                page.set_content(inline(atlas, view, width))
                freeze(page, 3)
                geometry = text_geometry(page, view)
                for box in geometry:
                    assert box['x1'] >= 35 and box['x2'] <= 1165 and box['y1'] >= 0 and box['y2'] <= VIEW_HEIGHT-15, (theme,width,view,box)
                report['geometry'].append({'theme':theme,'width':width,'view':view,'texts':geometry})
                stills.append((view, pixels(page)))
                for time in (.1, .85, 1.4, 3, 8):
                    page.set_content(inline(atlas, view, width))
                    freeze(page, time)
                    full = pixels(page)
                    page.set_content(inline(atlas, view, width, isolated=True))
                    freeze(page, time)
                    alone = pixels(page)
                    diff = ImageChops.difference(full, alone)
                    # Chromium's layer removal can change grayscale antialiasing by 3/255.
                    if max(v[1] for v in diff.getextrema()) > 3:
                        full.save(output/'failed-full.png')
                        alone.save(output/'failed-isolated.png')
                        diff.save(output/'failed-diff.png')
                        raise AssertionError((theme,width,view,time,'scene bleed',diff.getbbox(),diff.getextrema()))
                report['isolation'].append([theme,width,view])
            contact_sheet(stills, output/f'settled-{theme}-{width}.png')
            page.close()

        page = browser.new_page(viewport={'width':600,'height':400}, reduced_motion='reduce')
        for view in VIEWS:
            page.set_content(inline(atlas, view, 600))
            freeze(page, .1)
            before = pixels(page)
            freeze(page, 17)
            assert ImageChops.difference(before,pixels(page)).getbbox() is None, (theme,view,'reduced motion changed')
            report['reduced_motion'].append([theme,view])
        page.close()

        page = browser.new_page(viewport={'width':800,'height':500})
        frames = []
        for view in VIEWS:
            page.set_content(inline(atlas, view, 800))
            for time in (.1, .7, 1.2, 2.6):
                freeze(page,time)
                frames.append((f'{view} / {time}s',pixels(page)))
            freeze(page,.1)
            start = page.locator(f'#scene-{view} .entrance').first.evaluate('e=>getComputedStyle(e).opacity')
            freeze(page,INTRO_END)
            end = page.locator(f'#scene-{view} .entrance').first.evaluate('e=>getComputedStyle(e).opacity')
            assert (float(start),float(end)) == (0,1), (view,start,end)
            report['entrances'].append([theme,view,start,end])
            freeze(page,INTRO_END+2)
            baseline = pixels(page)
            state = motion_state(page,view)
            for cycle in (1,5):
                freeze(page,INTRO_END+2+cycle*CYCLE_SECONDS)
                repeated_state = motion_state(page,view)
                assert len(state) == len(repeated_state)
                assert all(math.isclose(a,b,abs_tol=.001) for original,repeated in zip(state,repeated_state)
                           for a,b in zip(original,repeated)), (theme,view,cycle,'numeric phase drift')
                repeated = pixels(page)
                difference = ImageChops.difference(baseline,repeated)
                # Float32 SVG clocks can move an edge by ~0.00001px after a loop:
                # a few antialiased edge pixels change even with equal measured geometry.
                mean_delta = max(ImageStat.Stat(difference).mean)
                thresholded = difference.convert('L').point(lambda v:255 if v>3 else 0)
                changed_ratio = ImageStat.Stat(thresholded).mean[0]/255
                if mean_delta > .01 or changed_ratio > .0001:
                    baseline.save(output/'cycle-baseline.png')
                    repeated.save(output/'cycle-repeated.png')
                    difference.save(output/'cycle-diff.png')
                    raise AssertionError((theme,view,cycle,'cycle raster drift',mean_delta,changed_ratio))
            report['cycles'].append([theme,view])
        contact_sheet(frames,output/f'entrance-{theme}.png',columns=4)
        page.close()
    return report


def clock_atlas(theme):
    root = ET.parse(ROOT/f'assets/profile-{theme}.svg').getroot()
    for name in VIEWS:
        scene = root.find(f'{NS}g[@id="scene-{name}"]')
        marker = ET.SubElement(scene,NS+'rect',{'x':'100','y':str(VIEW_HEIGHT-17),'width':'14','height':'10','fill':'#fa314f'})
        marker.append(ET.fromstring(animate('x',[100,1080],CYCLE_SECONDS,easing=None,repeat=True)))
    return ET.tostring(root,encoding='utf-8')


class PreviewHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/profile':
            cards = (ROOT/'README.md').read_text(encoding='utf-8').split('<details>')[0]
            data = ('<style>body{margin:0;background:#0d1117}img{display:block;width:100%;margin-bottom:12px}picture{display:block}</style>' + cards).encode()
            mime = 'text/html; charset=utf-8'
        elif path == '/clocks':
            theme = 'light' if 'light' in self.path else 'dark'
            data = ('<style>body{margin:0}img{display:block;width:100%}</style>' + ''.join(
                f'<img src="/clock-{theme}.svg#{name}" alt="{name}">' for name in VIEWS)).encode()
            mime = 'text/html; charset=utf-8'
        elif path in ('/clock-dark.svg','/clock-light.svg'):
            data = clock_atlas('light' if 'light' in path else 'dark')
            mime = 'image/svg+xml'
        elif path in ('/assets/profile-dark.svg','/assets/profile-light.svg'):
            data = (ROOT/path.lstrip('/')).read_bytes()
            mime = 'image/svg+xml'
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header('Content-Type',mime)
        self.send_header('Content-Length',str(len(data)))
        self.send_header('Cache-Control','public, max-age=600')
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


def marker_positions(frame, boxes):
    positions = []
    for box in boxes:
        top = math.floor(box['y']+(VIEW_HEIGHT-17)*box['width']/1200)
        bottom = math.ceil(box['y']+(VIEW_HEIGHT-7)*box['width']/1200)
        xs = [x for x in range(round(box['x']),round(box['x']+box['width']))
              for y in range(top,bottom)
              if (lambda c:c[0]>180 and c[0]>2*c[1] and c[0]>1.5*c[2])(frame.getpixel((x,y)))]
        assert xs, ('clock marker missing',box)
        positions.append((min(xs)+max(xs))/2-box['x'])
    return positions


def image_checks(browser, output, base):
    report = {'readme': [], 'synchronization': []}
    for theme in ('dark','light'):
        for width in (1000,358):
            page = browser.new_page(viewport={'width':width,'height':700},color_scheme=theme)
            page.goto(base+'/profile')
            page.wait_for_function('()=>[...document.images].length===6 && [...document.images].every(i=>i.complete&&i.naturalWidth)')
            assert page.locator('a').count() == 5
            for image in page.locator('img').all():
                assert f'profile-{theme}.svg?v=hvh6' in image.evaluate('e=>e.currentSrc')
                assert abs(image.bounding_box()['height']/width-VIEW_HEIGHT/1200) < .001
            page.set_viewport_size({'width':width,'height':int(6*(width*VIEW_HEIGHT/1200+12)+2)})
            page.wait_for_timeout(2700)
            page.screenshot(path=str(output/f'readme-{theme}-{width}.png'))
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            report['readme'].append([theme,width])
            page.close()
            for scroll in (False,True):
                page = browser.new_page(viewport={'width':width,'height':600})
                requests = []
                page.on('request',lambda request: requests.append(request.url) if '/clock-' in request.url else None)
                page.goto(base+'/clocks?'+theme)
                page.wait_for_function('()=>[...document.images].every(i=>i.complete&&i.naturalWidth)')
                page.wait_for_timeout(650)
                page.evaluate('()=>document.body.append(document.images[2].cloneNode())')
                if scroll:
                    page.locator('img').last.scroll_into_view_if_needed()
                    page.wait_for_timeout(300)
                page.set_viewport_size({'width':width,'height':int(7*width*VIEW_HEIGHT/1200)+2})
                page.evaluate('window.scrollTo(0,0)')
                page.wait_for_timeout(180)
                boxes = page.locator('img').evaluate_all('es=>es.map(e=>{let r=e.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width}})')
                frame = Image.open(io.BytesIO(page.screenshot())).convert('RGB')
                frame.save(output/f'clock-{theme}-{width}-{scroll}.png')
                positions = marker_positions(frame,boxes)
                spread = max(positions)-min(positions)
                assert spread <= 2, (theme,width,scroll,positions)
                assert len(requests) == 1, requests
                report['synchronization'].append({'theme':theme,'width':width,'scrolled':scroll,'late_duplicate':True,'spread_px':spread,'resource_requests':len(requests)})
                page.close()
    return report


def export_preview(browser, output):
    cards = (ROOT/'README.md').read_text(encoding='utf-8').split('<details>')[0]
    cards = cards.replace('./assets/', (ROOT/'assets').as_uri()+'/')
    style = '''<meta charset="utf-8"><title>HVH — motion preview</title>
    <style>body{max-width:1040px;margin:32px auto;padding:0 16px;background:#0d1117}
    img{width:100%;display:block;margin:0 0 16px}picture{display:block}
    @media(prefers-color-scheme:light){body{background:#fff}}</style>'''
    (output/'preview.html').write_text(style+cards,encoding='utf-8')
    atlas = ET.parse(ROOT/'assets/profile-dark.svg').getroot()
    for node in list(atlas):
        if node.tag == NS+'view':
            atlas.remove(node)
    atlas.set('width','900')
    atlas.set('height',str(3*VIEW_HEIGHT*900/1200))
    atlas.set('viewBox',f'0 0 1200 {3*VIEW_HEIGHT}')
    page = browser.new_page(viewport={'width':900,'height':1200})
    page.set_content('<style>body{margin:0}svg{display:block}</style>'+ET.tostring(atlas,encoding='unicode'))
    frames = []
    for index in range(66):
        freeze(page,index*.05)
        frames.append(pixels(page).resize((600,3*VIEW_HEIGHT//2),Image.Resampling.LANCZOS))
    frames[0].save(output/'intro.gif',save_all=True,append_images=frames[1:],duration=[50]*65+[1800],loop=0)
    page.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    output = parser.parse_args().output
    output.mkdir(parents=True,exist_ok=True)
    server = ThreadingHTTPServer(('127.0.0.1',0),PreviewHandler)
    thread = threading.Thread(target=server.serve_forever,daemon=True)
    thread.start()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(args=['--disable-lcd-text'])
            report = layout_checks(browser,output)
            report.update(image_checks(browser,output,f'http://127.0.0.1:{server.server_port}'))
            export_preview(browser,output)
            browser.close()
        (output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print('PASS: geometry, scene isolation, entrances, repeated cycles, reduced motion, README and shared image clocks')
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


if __name__ == '__main__':
    main()
