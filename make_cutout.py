"""Cuts the character out of avatar.png (removes the blue background + smoke) -> avatar_cut.png (RGBA).
Needs: pip install pillow numpy scipy   (only run this when you change avatar.png)"""
from PIL import Image
import numpy as np
from scipy import ndimage as ndi

im = Image.open("avatar.png").convert("RGB")
a = np.array(im).astype(int)
r, g, b = a[..., 0], a[..., 1], a[..., 2]
m = (b - np.maximum(r, g)) < 30                         # not blue-dominant = character
m = ndi.binary_opening(m, structure=np.ones((3, 3)))     # break hairline leaks into the background
lab, _ = ndi.label(m)
sub = lab == lab[170, 150]                               # component containing the face (change seed for other pics)
sub = ndi.binary_closing(sub, structure=np.ones((9, 9)))
sub = ndi.binary_fill_holes(sub)
# give removed pixels the nearest character colour so resizing doesn't blend in the blue background
idx = ndi.distance_transform_edt(~sub, return_distances=False, return_indices=True)
rgb = np.array(im)[idx[0], idx[1]]
rgba = np.dstack([rgb, (sub * 255).astype("uint8")])
Image.fromarray(rgba.astype("uint8"), "RGBA").save("avatar_cut.png")
print("cutout saved", sub.sum(), "px")
