"""EA's MappedImages and who shows them, read from the game's INIs (no EA text in git).

A MappedImage (data\\ini\\mappedimages\\**.ini) names a texture page, the size the INI declares
for it and a pixel rect: `Coords = Left:192 Top:0 Right:256 Bottom:64` covers x 192..255 (right
and bottom exclusive, as EA's Generals source cuts its UVs). A CommandButton's ButtonImage and an
object's SelectPortrait name one.
"""
import re
from dataclasses import dataclass

from ..formats.textures import compiled_path

BLOCK = r"^[ \t]*%s[ \t]+(\S+)(.*?)^[ \t]*End\b"


@dataclass(frozen=True)
class Image:
    name: str
    texture: str            # the page, as the INI names it (buildingradialbuttons_133.tga)
    size: tuple             # (TextureWidth, TextureHeight) the INI declares
    rect: tuple             # (left, top, right, bottom), right and bottom exclusive
    ini: str

    @property
    def width(self):
        return self.rect[2] - self.rect[0]

    @property
    def height(self):
        return self.rect[3] - self.rect[1]

    @property
    def page(self):
        return self.texture.lower().rsplit(".", 1)[0]


def _field(body, key):
    m = re.search(r"^\s*%s\s*=\s*([^;\r\n]+)" % key, body, re.M | re.I)
    return m.group(1).strip() if m else None


def images(g):
    """{name (lower): Image} of every MappedImage the game reads."""
    if "_icon_images" in g.__dict__:
        return g._icon_images
    out = {}
    for member in g.members("data\\ini\\mappedimages"):
        if not member.endswith(".ini"):
            continue
        text = g.read(member).decode("latin-1")
        for m in re.finditer(BLOCK % "MappedImage", text, re.M | re.S | re.I):
            body = m.group(2)
            c = re.search(r"Left:\s*(-?\d+)\s+Top:\s*(-?\d+)\s+Right:\s*(-?\d+)\s+Bottom:\s*(-?\d+)", body)
            tex = _field(body, "Texture")
            if not (c and tex):
                continue
            size = (int(_field(body, "TextureWidth") or 0), int(_field(body, "TextureHeight") or 0))
            out[m.group(1).lower()] = Image(m.group(1), tex, size, tuple(int(x) for x in c.groups()), member)
    g._icon_images = out
    return out


def page_member(g, page):
    """The archive member the game reads page `page` (buildingradialbuttons_133) from."""
    for ext in (".dds", ".tga"):
        member = compiled_path(page, ext)
        if g.owner(member):
            return member
    raise FileNotFoundError("no archive provides the page %s" % page)


def on_page(g, page):
    """[Image] on one page, in rect order."""
    return sorted((i for i in images(g).values() if i.page == page.lower()), key=lambda i: (i.rect[1], i.rect[0]))


def users(g):
    """{image name (lower): {(how, object)}}: how is 'portrait' (the object's SelectPortrait) or the
    CommandButton that shows it with `Object = <object>` ('-' when it names none)."""
    if "_icon_users" in g.__dict__:
        return g._icon_users
    out = {}
    text = g.read("data\\ini\\commandbutton.ini").decode("latin-1")
    for m in re.finditer(BLOCK % "CommandButton", text, re.M | re.S | re.I):
        img = _field(m.group(2), "ButtonImage")
        if img:
            out.setdefault(img.lower(), set()).add((m.group(1), _field(m.group(2), "Object") or "-"))
    for member in sorted(set(g.object_index().values())):
        t = g.read(member).decode("latin-1")
        heads = list(re.finditer(r"^(?:Object|ChildObject)[ \t]+(\S+)", t, re.M))
        for k, h in enumerate(heads):
            body = t[h.end():heads[k + 1].start() if k + 1 < len(heads) else len(t)]
            img = _field(body, "SelectPortrait")
            if img:
                out.setdefault(img.lower(), set()).add(("portrait", h.group(1)))
    g._icon_users = out
    return out


def candidates(g, buildings):
    """{image name (lower): {building id}}: the images shown for the objects each building draws
    the body of (its SelectPortrait, and every CommandButton whose Object it is). A proposal for
    the faction's table (an upgrade button names the object it turns into, not always the one the
    player builds: the Dwarven wall buttons name the map's castle walls)."""
    body = {}
    for b in buildings:
        for obj, draws in b.objects(g).items():
            if any(b.is_body(d) and b.covers(d) for d in draws):
                body.setdefault(obj, set()).add(b.id)
    out = {}
    for img, who in users(g).items():
        for _, obj in who:
            for bid in body.get(obj, ()):
                out.setdefault(img, set()).add(bid)
    return out
