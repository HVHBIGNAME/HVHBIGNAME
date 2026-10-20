"""Browser regressions for SVG layout and motion. Requires playwright and Pillow.

python scripts/verify_visuals.py --output <review-directory>
"""

import argparse
import copy
import io
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image, ImageChops, ImageDraw
from playwright.sync_api import sync_playwright

from design import ROOT, VIEWS, VIEW_HEIGHT
from motion import CYCLE_SECONDS, LOOP_PHASE_SECONDS

NS = "{http://www.w3.org/2000/svg}"
ET.register_namespace("", NS[1:-1])


def inline(atlas, view, width, isolated=False, scenes_only=False):
    root = copy.deepcopy(atlas)
    index = VIEWS.index(view)
    root.set("width", str(width))
    root.set("height", str(width * VIEW_HEIGHT / 1200))
    root.set("viewBox", f"0 {index * VIEW_HEIGHT} 1200 {VIEW_HEIGHT}")
    for child in list(root):
        if child.tag == NS + "view":
            root.remove(child)
        elif scenes_only and child.tag == NS + "g" and not child.get("id", "").startswith("scene-"):
            root.remove(child)
        elif isolated and child.get("id", "").startswith("scene-") and child.get("id") != "scene-" + view:
            root.remove(child)
    return '<style>body{margin:0;background:#0d1117}svg{display:block}</style>' + ET.tostring(root, encoding="unicode")


def freeze(page, milliseconds):
    page.evaluate("""async time => {
      await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
      for (const svg of document.querySelectorAll('svg')) {
        svg.pauseAnimations(); svg.setCurrentTime(1); svg.setCurrentTime(Math.max(time, .1) / 1000);
      }
      const animations = document.getAnimations();
      for (const a of animations) { a.pause(); a.currentTime = time; }
      await Promise.all(animations.map(a => a.ready));
      await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
    }""", milliseconds)


def pixels(page):
    return Image.open(io.BytesIO(page.locator("svg").screenshot())).convert("RGB")


def contact_sheet(images, path, columns=3):
    width, height = images[0][1].size
    sheet = Image.new("RGB", (width * columns, (height + 26) * ((len(images) + columns - 1) // columns)), "#0d1117")
    draw = ImageDraw.Draw(sheet)
    for i, (label, image) in enumerate(images):
        x, y = i % columns * width, i // columns * (height + 26)
        draw.text((x + 8, y + 5), label, fill="white")
        sheet.paste(image, (x, y + 26))
    sheet.save(path)


def geometry(page):
    return page.evaluate("""() => {
      const svg = document.querySelector('svg'), inverse = svg.getScreenCTM().inverse();
      const box = e => {
        const r = e.getBoundingClientRect();
        const a = new DOMPoint(r.left,r.top).matrixTransform(inverse);
        const b = new DOMPoint(r.right,r.bottom).matrixTransform(inverse);
        return [a.x,a.y,b.x,b.y];
      };
      const visible = e => e.getBoundingClientRect().width > 0;
      return [...svg.querySelectorAll('[id^="scene-"]')].map(scene => ({
        name: scene.id,
        anchors: [...scene.querySelectorAll('.art-anchor')].filter(visible).map(e => ({
          base: [e.transform.baseVal.consolidate().matrix.e,e.transform.baseVal.consolidate().matrix.f],
          motion: getComputedStyle(e.firstElementChild).transform,
          name: e.firstElementChild.getAttribute('data-animation'),
          box: box(e)
        })),
        texts: [...scene.querySelectorAll('text')].filter(visible).map(e => ({text:e.textContent, box:box(e)}))
      }));
    }""")


def browser_checks(browser, output):
    report = {"geometry": [], "isolation": [], "reduced_motion": [], "entrances": [], "relay": []}
    for theme in ("dark", "light"):
        atlas = ET.parse(ROOT / f"assets/profile-{theme}.svg").getroot()
        for width in (1200, 358):
            page = browser.new_page(viewport={"width": width, "height": 600}, reduced_motion="no-preference")
            stills = []
            for view in VIEWS:
                page.set_content(inline(atlas, view, width))
                freeze(page, 3500)
                scene = next(g for g in geometry(page) if g["name"] == "scene-" + view)
                y0 = VIEWS.index(view) * VIEW_HEIGHT
                for anchor in scene["anchors"]:
                    assert anchor["name"] == "art-enter", anchor
                    assert anchor["motion"] == "matrix(1, 0, 0, 1, 0, 0)", anchor
                    assert anchor["base"][0] > 100, anchor
                for text in scene["texts"]:
                    # Exclude tiny labels inside the background illustration on mobile.
                    if width > 600 or (text["box"][2] - text["box"][0]) > 250:
                        x1, y1, x2, y2 = text["box"]
                        assert x1 >= 24 and x2 <= 1175 and y1 >= y0 and y2 <= y0 + 419, text
                report["geometry"].append({"theme": theme, "width": width, **scene})
                stills.append((view, pixels(page)))
                # Full atlas must render exactly like this scene with all neighbours removed.
                for time in (0, 900, 3500, 10000):
                    page.set_content(inline(atlas, view, width, scenes_only=True))
                    freeze(page, time)
                    all_scenes = pixels(page)
                    page.set_content(inline(atlas, view, width, isolated=True, scenes_only=True))
                    freeze(page, time)
                    alone = pixels(page)
                    difference = ImageChops.difference(all_scenes, alone)
                    # Layer removal changes grayscale antialiasing by up to 3/255
                    # in Chromium. Larger differences are visible scene leaks.
                    if max(channel[1] for channel in difference.getextrema()) > 3:
                        all_scenes.save(output / "failed-full.png")
                        alone.save(output / "failed-isolated.png")
                        difference.save(output / "failed-diff.png")
                        raise AssertionError((theme, width, view, time, "neighbour bleed", difference.getbbox(), difference.getextrema()))
                report["isolation"].append([theme, width, view])
            contact_sheet(stills, output / f"settled-{theme}-{width}.png", columns=1)
            page.close()

        page = browser.new_page(viewport={"width": 800, "height": 600}, reduced_motion="no-preference")
        frames = []
        for view in ("hero", "bcore", "minecraft-panel"):
            for time in (100, 900, 1600, 2800):
                page.set_content(inline(atlas, view, 800))
                freeze(page, time)
                frames.append((f"{view} / {time}ms", pixels(page)))
            page.set_content(inline(atlas, view, 800))
            freeze(page, 100)
            start = page.locator(f'#scene-{view} .desktop .art-enter').evaluate('e=>({opacity:getComputedStyle(e).opacity, transform:getComputedStyle(e).transform})')
            freeze(page, 3500)
            end = page.locator(f'#scene-{view} .desktop .art-enter').evaluate('e=>({opacity:getComputedStyle(e).opacity, transform:getComputedStyle(e).transform})')
            assert float(start["opacity"]) == 0 and float(end["opacity"]) == 1, (start, end)
            assert start["transform"] != end["transform"], (start, end)
            report["entrances"].append({"theme": theme, "view": view, "start": start, "end": end})
        contact_sheet(frames, output / f"entrance-{theme}.png", columns=4)
        # An ignored CSS rule (e.g. literal {{...}}) must not silently pass.
        assert page.locator('.motion-active .sheen').first.get_attribute('data-animation') == "sheen"
        for index in range(len(VIEWS)):
            time = 6250 + index * 1000
            freeze(page, time)
            position = page.locator('.relay').evaluate('''e => {
              const svg = e.ownerSVGElement;
              const p = new DOMPoint(0,0).matrixTransform(e.getScreenCTM()).matrixTransform(svg.getScreenCTM().inverse());
              return {x:p.x,y:p.y,opacity:getComputedStyle(e).opacity};
            }''')
            assert abs(position["x"] - 26) < .01, position
            assert index * VIEW_HEIGHT < position["y"] < (index + 1) * VIEW_HEIGHT, position
            assert float(position["opacity"]) > .95, position
            report["relay"].append({"theme": theme, "time": time, **position})
        page.close()

        page = browser.new_page(viewport={"width": 1200, "height": 600}, reduced_motion="reduce")
        for view in VIEWS:
            page.set_content(inline(atlas, view, 1200))
            assert page.evaluate('document.getAnimations().length') == 0
            before = pixels(page)
            page.wait_for_timeout(150)
            assert ImageChops.difference(before, pixels(page)).getbbox() is None
            assert page.locator('.motion-active').first.evaluate('e=>getComputedStyle(e).display') == "none"
            for node in page.locator('.motion-static .art-enter').all():
                assert node.evaluate('e=>getComputedStyle(e).opacity') == "1"
            report["reduced_motion"].append([theme, view])
        page.close()
    return report


def image_checks(browser, output):
    readme = (ROOT / "README.md").read_text(encoding="utf-8").split("<details>")[0]
    html = '<style>body{margin:0;padding:16px;background:#0d1117}main{max-width:980px;margin:auto}img{display:block;width:100%;height:auto}picture{display:block;margin-bottom:8px}</style><main>' + readme + '</main>'

    def route(request):
        path = urlparse(request.request.url).path
        if path == "/":
            request.fulfill(body=html, content_type="text/html")
        else:
            request.fulfill(body=(ROOT / path.lstrip("/")).read_bytes(), content_type="image/svg+xml")

    layouts = []
    for theme in ("dark", "light"):
        for width in (390, 1440):
            page = browser.new_page(viewport={"width": width, "height": 1100}, color_scheme=theme, reduced_motion="no-preference")
            page.route("http://profile.test/**", route)
            page.goto("http://profile.test/", wait_until="load")
            if theme == "dark" and width == 1440:
                frames = []
                for target in (150, 900, 1600, 3500):
                    page.wait_for_timeout(max(0, target - page.evaluate("performance.now()")))
                    image = page.locator("img").first
                    actual = round(page.evaluate("performance.now()"))
                    frames.append((f"img / {actual}ms", Image.open(io.BytesIO(image.screenshot())).convert("RGB")))
                contact_sheet(frames, output / "image-entrance.png", columns=2)
                first, last = frames[0][1], frames[-1][1]
                bounds = (int(last.width * .62), int(last.height * .18), int(last.width * .97), int(last.height * .8))
                difference = ImageChops.difference(first.crop(bounds), last.crop(bounds))
                assert max(channel[1] for channel in difference.getextrema()) > 100, "object entrance missing in img mode"
            else:
                page.wait_for_timeout(3500)
            state = page.evaluate('''() => ({overflow:document.documentElement.scrollWidth > innerWidth,
              images:[...document.images].map(e=>({src:e.getAttribute('src'), current:e.currentSrc, width:e.naturalWidth, height:e.naturalHeight}))})''')
            assert not state["overflow"] and len(state["images"]) == 6
            assert all(e["width"] == 1200 and e["height"] == 420 and f"profile-{theme}.svg" in e["current"] for e in state["images"])
            page.screenshot(path=str(output / f"readme-{theme}-{width}.png"), full_page=True)
            layouts.append({"theme": theme, "width": width, **state})
            page.close()
    return layouts


def synchronization_checks(browser, output):
    report = {"timing": [], "raster": []}
    for theme in ("dark", "light"):
        atlas = ET.parse(ROOT / f"assets/profile-{theme}.svg").getroot()
        page = browser.new_page(viewport={"width": 1200, "height": 600}, reduced_motion="no-preference")
        page.set_content(inline(atlas, "hero", 1200))
        timings = page.evaluate('''() => {
          const timing = e => ({delay:Number(e.dataset.delay)*1000,duration:Number(e.dataset.duration)*1000});
          const primary = new Set(['aura-breathe','relay','sheen','place-0','server-chart','install-progress','message-0']);
          return {entrances:[...document.querySelectorAll('.motion-active .desktop .art-enter,.motion-active .bar')].map(timing),
            loops:[...document.querySelectorAll('[repeatCount="indefinite"]')].map(e=>({duration:parseFloat(e.getAttribute('dur'))*1000})),
            primary:[...document.querySelectorAll('[data-animation]')].filter(e=>primary.has(e.dataset.animation)).map(timing)};
        }''')
        assert len(timings["entrances"]) == 95
        assert {(t["delay"], t["duration"]) for t in timings["entrances"]} == {(450, 2200)}, timings["entrances"]
        assert all(abs(CYCLE_SECONDS * 1000 % t["duration"]) < .01 for t in timings["loops"]), timings["loops"]
        assert all(t["delay"] == LOOP_PHASE_SECONDS * 1000 for t in timings["primary"]), timings["primary"]

        def state(time):
            freeze(page, time)
            return page.evaluate('''() => [...document.querySelectorAll('[data-animation]')].map(e => {
              const s = getComputedStyle(e);
              return [s.opacity,s.transform,s.strokeDashoffset,s.clipPath];
            })''')

        baseline = state(8500)
        for cycles in (1, 5):
            assert state(8500 + cycles * CYCLE_SECONDS * 1000) == baseline, "loop phase drift"
        report["timing"].append({"theme": theme, "entrances": len(timings["entrances"]), "loops": len(timings["loops"]), "phaseDrift": False})
        page.close()

        # Copy actual native effects into diagnostic marks in each scene. Capture
        # all IMG instances in ONE frame; never seek the resource's timeline.
        rise = next(e for e in atlas.iter() if e.get('data-animation') == 'rise' and e.get('data-delay') == '0.37')
        beat = next(e for e in atlas.iter() if e.get('data-animation') == 'beat')
        for scene in atlas.findall(NS + "g"):
            if not scene.get("id", "").startswith("scene-"):
                continue
            probes = ET.fromstring(f'''<g xmlns="{NS[1:-1]}">
              <rect x="1020" y="80" width="150" height="150" fill="#000"/>
              <rect x="1040" y="92" width="60" height="70" fill="#fff"/>
              <rect x="1120" y="92" width="30" height="70" fill="#fff"/>
              <rect x="100" y="190" width="8" height="12" fill="#ff00ff"><animate attributeName="x" values="100;1000" dur="16s" repeatCount="indefinite"/></rect>
            </g>''')
            for target, template in ((probes[1], rise), (probes[2], beat)):
                target.extend(copy.deepcopy(child) for child in template if child.tag in (NS+'animate', NS+'animateTransform', NS+'set'))
            scene[0].append(probes)
        source = ET.tostring(atlas, encoding="unicode")
        for width in (1200, 360):
            for delayed in (False, True):
                height = width * VIEW_HEIGHT // 1200
                images = [f'<img src="/atlas.svg#{v}" width="{width}" height="{height}">' for v in VIEWS]
                html = '<style>body{margin:0}img{display:block}</style>' + ''.join(images[:3] if delayed else images)
                requests = []

                def serve(route):
                    if '.svg' in route.request.url:
                        requests.append(route.request.url)
                        route.fulfill(body=source, content_type="image/svg+xml")
                    else:
                        route.fulfill(body=html, content_type="text/html")

                page = browser.new_page(viewport={"width": width + 20, "height": height * 2}, reduced_motion="no-preference")
                page.route("http://sync.test/**", serve)
                page.goto("http://sync.test/", wait_until="load")
                if delayed:
                    page.wait_for_timeout(1500)
                    page.evaluate("html=>document.body.insertAdjacentHTML('beforeend',html)", ''.join(images[3:]))
                page.wait_for_function('Array.from(document.images).every(i=>i.complete&&i.naturalWidth)')
                page.wait_for_timeout(650)
                for scrolled in (False, True):
                    if scrolled:
                        page.set_viewport_size({"width": width + 20, "height": height * 2})
                        page.evaluate('scrollTo(0,document.body.scrollHeight)')
                        page.wait_for_timeout(400)
                    # Full-page capture alone reuses stale offscreen rasters.
                    # Expose every IMG and let it paint before comparing clocks.
                    page.set_viewport_size({"width": width + 20, "height": height * 6})
                    page.wait_for_timeout(150)
                    frame = Image.open(io.BytesIO(page.screenshot())).convert("RGB")
                    crops = [frame.crop((int(1020*width/1200), i*height+int(80*width/1200), int(1170*width/1200), i*height+int(230*width/1200))) for i in range(6)]
                    assert max(crops[0].getextrema()[0]) > 20, "invisible sync probes"
                    intensities = [[frame.getpixel((int(x*width/1200), i*height+int(130*width/1200)))[0] for i in range(6)] for x in (1070, 1135)]
                    difference = max(max(values) - min(values) for values in intensities)
                    clocks = []
                    for i in range(6):
                        y = i*height + int(195*width/1200)
                        xs = [x for x in range(width) if (lambda p: p[0]>240 and p[1]<15 and p[2]>240)(frame.getpixel((x,y)))]
                        if not xs:
                            frame.save(output / "sync-failed-frame.png")
                        assert xs, ("native clock probe missing", theme, width, delayed, scrolled, i, y)
                        clocks.append(sum(xs)/len(xs))
                    spread = max(clocks) - min(clocks)
                    if difference > 20 or spread > 3:
                        frame.save(output / "sync-failed-frame.png")
                        contact_sheet(list(zip(VIEWS, crops)), output / "sync-failed-probes.png")
                    # Separate image rasters may be painted one frame apart.
                    assert difference <= 20 and spread <= 3, (theme, width, delayed, scrolled, "IMG phase mismatch", difference, spread)
                    report["raster"].append({"theme": theme, "width": width, "delayed": delayed, "scrolled": scrolled, "maxChannelDelta": difference, "clockSpreadPx": spread})
                assert len(requests) == 1, requests
                contact_sheet(list(zip(VIEWS, crops)), output / f"sync-{theme}-{width}-{'late' if delayed else 'initial'}.png")
                page.close()
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(args=['--disable-lcd-text'])
        report = browser_checks(browser, args.output)
        report["images"] = image_checks(browser, args.output)
        report["synchronization"] = synchronization_checks(browser, args.output)
        browser.close()
    (args.output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("PASS: geometry, isolation, entrances, reduced motion, README images and synchronized clocks")
    print(args.output)


if __name__ == "__main__":
    main()
