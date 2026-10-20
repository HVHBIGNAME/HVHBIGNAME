"""Compile the generator's CSS animation subset onto the SVG document clock.

Native SVG timing survives deferred painting of IMG fragment views. The input
stylesheet is generated locally; unsupported animation constructs fail the build.
"""

import ast
import copy
import operator
import re
import xml.etree.ElementTree as ET

from motion import CYCLE_SECONDS, LOOP_PHASE_SECONDS

NS = "{http://www.w3.org/2000/svg}"
ET.register_namespace("", NS[1:-1])
FRAME = re.compile(r"@keyframes\s+([\w-]+)\s*\{((?:[^{}]*\{[^{}]*\}\s*)+)\}")
OPERATORS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}
EASING = {"ease": ".25 .1 .25 1", "ease-in": ".42 0 1 1", "ease-out": "0 0 .58 1", "ease-in-out": ".42 0 .58 1"}


def arithmetic(expression):
    def visit(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            return (-1 if isinstance(node.op, ast.USub) else 1) * visit(node.operand)
        if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
            return OPERATORS[type(node.op)](visit(node.left), visit(node.right))
        raise ValueError(f"Unsupported arithmetic: {expression}")
    return visit(ast.parse(expression.strip(), mode="eval").body)


def resolve(value, variables):
    variable = re.compile(r"var\((--[\w-]+)(?:,\s*([^()]+))?\)")
    for _ in range(10):
        if "var(" not in value:
            break
        def substitute(match):
            key, fallback = match.groups()
            if key not in variables and fallback is None:
                raise ValueError(f"Missing animation variable: {key}")
            return variables.get(key, fallback)
        value = variable.sub(substitute, value)
    while "calc(" in value:
        def calculate(match):
            expression = match.group(1)
            units = re.findall(r"(?:[\d.])(px|deg|s)\b", expression)
            number = arithmetic(re.sub(r"(?<=[\d.])(?:px|deg|s)\b", "", expression))
            return f"{number:g}" + (units[0] if units else "")
        changed = re.sub(r"calc\(([^()]*)\)", calculate, value)
        if changed == value:
            raise ValueError(f"Unsupported animation expression: {value}")
        value = changed
    if "var(" in value:
        raise ValueError(f"Unresolved animation expression: {value}")
    return value


def declarations(text):
    return dict(part.strip().split(":", 1) for part in text.split(";") if ":" in part)


def without_media(css):
    while "@media" in css:
        start = css.index("@media")
        end = css.index("{", start) + 1
        depth = 1
        while depth:
            depth += (css[end] == "{") - (css[end] == "}")
            end += 1
        css = css[:start] + css[end:]
    return css


def matches(selector, lineage):
    parts = selector.strip().split()
    if not all(re.fullmatch(r"(?:\.[\w-]+)+", part) for part in parts):
        raise ValueError(f"Unsupported animation selector: {selector}")
    position = len(lineage) - 1
    for index, part in enumerate(reversed(parts)):
        wanted = set(part.split(".")[1:])
        while position >= 0 and not wanted <= set(lineage[position].get("class", "").split()):
            if index == 0:
                return False
            position -= 1
        if position < 0:
            return False
        position -= 1
    return True


def timing(properties, variables):
    shorthand = resolve(properties.get("animation", ""), variables)
    tokens = re.findall(r"cubic-bezier\([^)]*\)|\S+", shorthand)
    name = properties.get("animation-name", tokens[0] if tokens else "")
    duration = resolve(properties.get("animation-duration", tokens[1] if len(tokens) > 1 else "0s"), variables)
    easing = properties.get("animation-timing-function", next((t for t in tokens if t in EASING or t.startswith("cubic-bezier") or t == "linear"), "ease"))
    repeated = properties.get("animation-iteration-count", "infinite" if "infinite" in tokens else "1") == "infinite"
    fill = properties.get("animation-fill-mode", "both" if "both" in tokens else "none")
    delay = resolve(properties.get("animation-delay", "0s"), variables)
    if not name or not duration.endswith("s") or not delay.endswith("s"):
        raise ValueError(f"Invalid animation timing: {properties}")
    return name, float(duration[:-1]), float(delay[:-1]), easing, repeated, fill


def origin(element):
    classes = element.get("class", "").split()
    if "server-core" in classes:
        return (-112, -12)
    if "paired-mark" in classes:
        return (-83, 44)
    if "bar" in classes:
        return (float(element.get("x")) + float(element.get("width")) / 2,
                float(element.get("y")) + float(element.get("height")))
    return (0, 0)


def transforms(value):
    result = {"translate": [0, 0], "rotate": [0], "scale": [1, 1]}
    for function, arguments in re.findall(r"(\w+)\(([^()]*)\)", value):
        numbers = [float(v) for v in re.findall(r"-?(?:\d*\.)?\d+", arguments)]
        if function in ("translate", "translateX", "translateY"):
            result["translate"] = ([0, numbers[0]] if function == "translateY" else [numbers[0], numbers[1] if len(numbers) > 1 else 0])
        elif function in ("scale", "scaleX", "scaleY"):
            result["scale"] = ([1, numbers[0]] if function == "scaleY" else [numbers[0], 1 if function == "scaleX" else numbers[-1]])
        elif function == "rotate":
            result["rotate"] = numbers
        else:
            raise ValueError(f"Unsupported animated transform: {function}")
    return result


def animate(element, frames, properties, variables):
    name, duration, delay, easing, repeated, fill = timing(properties, variables)
    element.set("data-animation", name)
    element.set("data-duration", f"{duration:g}")
    element.set("data-delay", f"{delay:g}")
    common = {"begin": f"{delay:g}s", "dur": f"{duration:g}s", "fill": "freeze" if fill in ("both", "forwards") else "remove"}
    if repeated:
        common["repeatCount"] = "indefinite"
    spline = EASING.get(easing)
    if easing.startswith("cubic-bezier"):
        spline = easing.removeprefix("cubic-bezier(").removesuffix(")").replace(",", " ")
    if not spline and easing != "linear":
        raise ValueError(f"Unsupported easing: {easing}")

    def emit(attribute, points, transform_type=None, additive=None):
        attrs = {**common, "attributeName": attribute, "values": ";".join(points.values()), "keyTimes": ";".join(f"{key:g}" for key in points), "calcMode": "spline" if spline else "linear"}
        if spline:
            attrs["keySplines"] = ";".join([spline] * (len(points) - 1))
        if transform_type:
            attrs.update(type=transform_type, additive=additive)
        ET.SubElement(element, NS + ("animateTransform" if transform_type else "animate"), attrs)
        # SMIL's backwards fill is explicit; native attributes remain the fallback.
        if delay > 0 and fill in ("both", "backwards") and not transform_type:
            ET.SubElement(element, NS + "set", {"attributeName": attribute, "to": next(iter(points.values())), "begin": "0s", "dur": f"{delay:g}s"})

    attributes = sorted({key for frame in frames.values() for key in frame})
    for attribute in attributes:
        points = {t: resolve(frame[attribute], variables) for t, frame in sorted(frames.items()) if attribute in frame}
        if 0 not in points:
            points[0] = "rotate(0)" if attribute == "transform" else element.get(attribute, "0")
        if 1 not in points:
            points[1] = element.get(attribute, "0")
        points = dict(sorted(points.items()))
        if attribute == "transform":
            matrix_parts = {t: transforms(v) for t, v in points.items()}
            pivot = origin(element)
            additive = "replace"
            if pivot != (0, 0):
                emit("transform", {0: f"{pivot[0]:g} {pivot[1]:g}", 1: f"{pivot[0]:g} {pivot[1]:g}"}, "translate", additive)
                additive = "sum"
            for kind, default in (("translate", [0, 0]), ("rotate", [0]), ("scale", [1, 1])):
                if any(parts[kind] != default for parts in matrix_parts.values()):
                    emit("transform", {t: " ".join(f"{v:g}" for v in parts[kind]) for t, parts in matrix_parts.items()}, kind, additive)
                    additive = "sum"
            if pivot != (0, 0):
                emit("transform", {0: f"{-pivot[0]:g} {-pivot[1]:g}", 1: f"{-pivot[0]:g} {-pivot[1]:g}"}, "translate", "sum")
        elif attribute == "clip-path":
            emit("stroke-dashoffset", {t: "100" if "100%" in value else "0" for t, value in points.items()})
        elif attribute in ("opacity", "stroke-dashoffset"):
            emit(attribute, points)
        else:
            raise ValueError(f"Unsupported animated property: {attribute}")


def compile_timeline(markup):
    root = ET.fromstring(markup)
    style = root.find(NS + "style")
    css = re.sub(r"/\*.*?\*/", "", style.text, flags=re.S)
    keyframes = {}
    for name, body in FRAME.findall(css):
        frames = {}
        for times, properties in re.findall(r"([^{}]+)\{([^{}]*)\}", body):
            for time in times.split(","):
                time = time.strip().replace("from", "0%").replace("to", "100%")
                frames.setdefault(float(time.rstrip("%")) / 100, {}).update(declarations(properties))
        keyframes[name] = frames
    rules = []
    for selector, body in re.findall(r"([^{}]+)\{([^{}]*)\}", without_media(FRAME.sub("", css))):
        properties = {key: value.strip() for key, value in declarations(body).items() if key.startswith("animation")}
        if properties:
            rules.extend((part.strip(), properties) for part in selector.split(","))

    def visit(element, lineage, inherited):
        variables = dict(inherited)
        classes = element.get("class", "").split()
        if "art-anchor" in classes:
            variables.update({"--enter-x": "-280px" if "from-left" in classes else "280px", "--enter-turn": "-16deg" if "from-left" in classes else "16deg"})
        variables.update({key: value.strip() for key, value in declarations(element.get("style", "")).items() if key.startswith("--")})
        lineage = [*lineage, element]
        for child in list(element):
            visit(child, lineage, variables)
        properties = {}
        for selector, values in rules:
            if matches(selector, lineage):
                if "animation" in values:
                    properties.clear()
                properties.update(values)
        if properties:
            name = timing(properties, variables)[0]
            animate(element, keyframes[name], properties, variables)

    variables = {"--cycle": f"{CYCLE_SECONDS}s", "--phase": f"{LOOP_PHASE_SECONDS}s"}
    atlas = root.find(NS + "view") is not None
    for element in list(root):
        if element.tag != NS + "g":
            continue
        static = copy.deepcopy(element)
        element.set("class", (element.get("class", "") + " motion-active").strip())
        visit(element, [], variables)
        if not atlas or element.get("id", "").startswith("scene-") or element.get("id") == "shared-rail":
            for node in static.iter():
                node.attrib.pop("id", None)
                for child in list(node):
                    if child.tag == NS + "title":
                        node.remove(child)
            static.set("class", (static.get("class", "") + " motion-static").strip())
            root.insert(list(root).index(element), static)
    style.text = re.sub(r"(?:animation(?:-[\w-]+)?|transform-box|transform-origin)\s*:[^;{}]*;", "", FRAME.sub("", css))
    style.text = re.sub(r"[^{}]+\{\s*\}", "", style.text)
    style.text += "\n.motion-static {display:none;} @media (prefers-reduced-motion:reduce) { .motion-active {display:none;} .motion-static {display:inline;} }\n"
    return "\n".join(line.rstrip() for line in ET.tostring(root, encoding="unicode").splitlines()) + "\n"
