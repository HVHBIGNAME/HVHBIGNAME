"""Produce a genuine static layer from explicitly authored SVG rest states."""

import copy
import xml.etree.ElementTree as ET

NS = '{http://www.w3.org/2000/svg}'
ET.register_namespace('', NS[1:-1])
ANIMATIONS = {NS + tag for tag in ('animate', 'animateTransform', 'animateMotion', 'set')}


def static_copy(element):
    static = copy.deepcopy(element)
    for node in list(static.iter()):
        node.attrib.pop('id', None)
        if 'data-reveal' in node.attrib:
            node.attrib.pop('clip-path', None)
        for attribute, value in list(node.attrib.items()):
            if attribute.startswith('data-rest-'):
                node.set(attribute.removeprefix('data-rest-'), value)
                del node.attrib[attribute]
        for child in list(node):
            if child.tag in ANIMATIONS or child.tag == NS + 'title' or 'transient' in child.get('class', '').split():
                node.remove(child)
    static.set('class', 'motion-static')
    return static


def with_static_layers(markup):
    root = ET.fromstring(markup)
    for scene in list(root):
        if scene.get('id', '').startswith('scene-'):
            root.insert(list(root).index(scene), static_copy(scene))
            scene.set('class', 'motion-active')
    return ET.tostring(root, encoding='unicode') + '\n'
