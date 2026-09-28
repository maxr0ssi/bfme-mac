"""Private troop sheets: preserve painted detail, alpha, faces and fur; use the building palette."""
import json
import struct
import subprocess
import tempfile
from pathlib import Path

from assets.dwarves.style import PALETTE

# Troops share the buildings' warm metals, with neutral wool instead of fixed blue.
TROOP_RAMPS = dict(PALETTE.ramps,
    cloth=[(0, (.07, .05, .035)), (.35, (.25, .20, .145)),
           (.6, (.46, .38, .28)), (.85, (.70, .61, .47)), (1, (.90, .83, .70))],
    ground=PALETTE.ramps["iron"])

# Normalized image rectangles, not W3D UV coordinates. Faces/hair stay byte-exact in PNG.
PROTECT = {
    "eudwarfgua": [(0.47,0,0.73,0.56)], "duphalanx_01": [(0.61,0.07,1,0.64)],
    "eudwarfaxe": [(0.64,0,1,0.58)], "ruarcher": [(0.85,0,1,0.24)],
    "rudwarf_b": [(0.49,0,0.70,0.46)], "duporter": [(0.62,0,1,0.90)],
    "eudwarfgua_banner": [(0.47,0,0.73,0.56)],
}
CLOTH_CUTOUT = {name: (.57,.28,.73,.40) for name in ("eudwarfgua", "eudwarfgua_banner")}
CLOTH = {
    "eudwarfgua": [(0.04,0,0.46,0.55)], "duphalanx_01": [(0.04,0.05,0.57,0.72)],
    "eudwarfaxe": [(0.06,0.09,0.65,0.74)], "ruarcher": [(0,0,0.52,0.59)],
    "rudwarf_b": [(0.17,0,0.5,0.11),(0.02,0.37,0.40,0.92),(0.71,0.60,0.92,1)],
    "duporter": [(0,0,0.63,1)], "duaxdban1": [(0,0,1,0.85)],
    "ruyeobanner": [(0,0,1,1)], "eudwarfgua_banner": [(0.04,0,0.46,0.55)],
}


def family(name):
    stem = Path(name).stem.lower()
    for suffix in ("_upgrade", "_ha", "ha", "_m"):
        if stem.endswith(suffix):
            stem = stem[:-len(suffix)]
            break
    return stem


def eligible(name):
    return family(name) in set(PROTECT)|set(CLOTH)|{
        "dubtlwagon", "ducatapult", "eudwarfram", "eudwarfram_shield",
        "eudwarfram_rhino", "dbhearth", "eudwarfeng"}


def paint(source, dest, name):
    """Called from Blender's bundled Python (numpy); original-size alpha-preserving output."""
    import numpy as np
    from sagekit.paint.fields import ramp
    w,h = map(int, subprocess.check_output(["magick","identify","-format","%w %h",str(source)]).split())
    raw = subprocess.check_output(["magick",str(source),"-depth","8","rgba:-"])
    original = np.frombuffer(raw,np.uint8).reshape(h,w,4).copy()
    rgb = original[:,:,:3].astype(float)/255
    r,g,b = [rgb[:,:,i] for i in range(3)]
    lum = .2126*r+.7152*g+.0722*b
    maximum,minimum = rgb.max(axis=2),rgb.min(axis=2)
    sat = (maximum-minimum)/np.maximum(maximum,.001)
    y,x = np.mgrid[:h,:w]; x=(x+.5)/w; y=(y+.5)/h

    def rects(boxes):
        out=np.zeros((h,w),bool)
        for a,c,d,e in boxes:out|=(x>=a)&(x<d)&(y>=c)&(y<e)
        return out

    f = family(name)
    protected = rects(PROTECT.get(f,[]))
    # This blue shoulder island sits beside the beard inside the broad face rectangle.
    if f in CLOTH_CUTOUT:
        protected &= ~(rects([CLOTH_CUTOUT[f]])&(b>r*1.03)&(b>g*.98)&(sat>.13))
    out = rgb.copy()

    def apply(mask, material, strength=.72, gain=1, lift=0):
        mask = mask&~protected&(maximum>.035)
        target = ramp(np.clip(lum*gain+lift,0,1),TROOP_RAMPS[material])
        out[mask] = rgb[mask]*(1-strength)+target[mask]*strength

    # Bronze/gold follows original warm metal pixels; don't turn leather or flesh into metal.
    metal=(r>g*1.07)&(g>b*1.16)&(lum>.26)&(sat>.18)&(sat<.64)
    if f in PROTECT or f in CLOTH:
        apply(metal,"bronze",.56,1.08,.06)
        cloth=rects(CLOTH.get(f,[]))
        if f in ("eudwarfgua","duporter","duaxdban1","ruyeobanner","eudwarfgua_banner"):
            cloth &= (b>r*1.03)&(b>g*.98)&(sat>.13)
        elif f=="duphalanx_01":cloth&=(g>r*.99)&(g>b*1.08)&(sat>.12)
        elif f in ("eudwarfaxe","rudwarf_b"):
            cloth&=(r>g*1.12)&(b>g*.88)&(sat>.13)
        elif f=="ruarcher":cloth&=(r>g*1.1)&(g>b*1.1)&(r<g*1.85)&(lum<.50)
        apply(cloth,"cloth",1,1.05,.05)
        # Temper existing silver rather than crush its painted highlight range into dark iron.
        silver=(sat<.17)&(lum>.16)
        warm=rgb*np.array([1.025,1.0,.94])
        out[silver&~protected]=warm[silver&~protected]
    else:
        from .siege import UV_PATCHES
        patches=UV_PATCHES.get(f,{})
        for tag,box in patches.items():
            apply(rects([box]),tag,1 if tag=="ground" else .8,1.05,.08 if tag=="bronze" else 0)
        # Source grain and carved pattern remain the high-frequency signal.
        apply((sat<.23)&(lum>.13),"bronze",.35,1.05,.04)
        brown=(r>g*1.08)&(g>b*1.07)&(lum<.45)&(sat>.22)
        apply(brown,"wood",.36,.92,0)
    # Remove remaining blue on shields, hems and banners outside the cloth rectangles.
    # Natural mount fur and protected faces/hair remain exact.
    blue=(b>r*1.03)&(b>g*.98)&(sat>.13)&(maximum>.035)&~protected
    apply(blue,"cloth",1,1.05,.05)
    assert np.all(out[blue,0]>=out[blue,1]) and np.all(out[blue,1]>=out[blue,2])
    result=original.copy()
    result[:,:,:3]=np.round(np.clip(out,0,1)*255).astype(np.uint8)
    result[protected]=original[protected]
    assert np.array_equal(result[:,:,3],original[:,:,3])
    assert np.array_equal(result[protected],original[protected])
    subprocess.run(["magick","-size",f"{w}x{h}","-depth","8","rgba:-",str(dest)],
                   input=result.tobytes(),check=True)
    return dict(width=w,height=h,changed_pixels=int(np.any(result!=original,axis=2).sum()),
                protected_pixels=int(protected.sum()),alpha_preserved=True,
                palette="warm neutral cloth, bronze and gold; no fixed blue")


def run(manifest):
    data=json.loads(Path(manifest).read_text());report={}
    for name,item in data["textures"].items():
        dest=Path(item["output"])
        png=dest.with_suffix(".png")
        report[name]=paint(item["source"],png,name)
        write_sheet(png,dest,Path(item["source"]))
    Path(manifest).with_name("paint-checks.json").write_text(json.dumps(report,indent=2)+"\n")


def write_sheet(png,dest,source):
    """Keep source mip count and compressed alpha blocks, including the non-power-of-two sheet."""
    from sagekit.formats.textures import write_dds,dds_info,dds_size
    before=dds_info(source)
    staged=dest.with_name(dest.stem+'.staged.dds')
    result=write_dds(str(png),str(staged),alpha=True)
    target=before['mips'] or 1
    data=bytearray(staged.read_bytes())
    if result['mips']!=target:
        header=data[:128];payload=bytearray()
        with tempfile.TemporaryDirectory() as tmp:
            for level in range(target):
                w,h=max(1,before['width']>>level),max(1,before['height']>>level)
                path=Path(tmp)/'level.dds'
                subprocess.run(['magick',str(png),'-resize',f'{w}x{h}!',
                    '-define','dds:compression=dxt5','-define','dds:mipmaps=0',str(path)],check=True)
                block=path.read_bytes();size=((w+3)//4)*((h+3)//4)*16
                assert len(block)>=128+size
                payload+=block[128:128+size]
        struct.pack_into('<I',header,8,struct.unpack_from('<I',header,8)[0]|0x20000)
        struct.pack_into('<I',header,28,target)
        struct.pack_into('<I',header,108,struct.unpack_from('<I',header,108)[0]|0x400008)
        data=header+payload
    # DXT3 and DXT5 store alpha separately from the identically encoded RGB block.
    # Copying those bytes retains even translucent banner edges exactly at every mip.
    if before['fourcc'] in ('DXT3','DXT5'):
        original=source.read_bytes();offset=128
        data[84:88]=before['fourcc'].encode()
        for level in range(target):
            w,h=max(1,before['width']>>level),max(1,before['height']>>level)
            for _ in range(((w+3)//4)*((h+3)//4)):
                assert offset+16<=min(len(original),len(data))
                data[offset:offset+8]=original[offset:offset+8]
                offset+=16
        assert offset==dds_size(before['width'],before['height'],target,'DXT5')
    staged.write_bytes(data)
    result=dds_info(staged)
    assert result['mips']==target
    assert (result['width'],result['height'])==(before['width'],before['height'])
    staged.replace(dest)


if __name__=="__main__":
    import sys
    run(sys.argv[-1])
