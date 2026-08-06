"""Adaptive photo preprocessing for the frame's 6-color (Spectra6-class)
e-ink panel.

The panel (see frame/epd/epd7in3e.py) only has six solid primaries - black,
white, yellow, red, blue, green - no orange, no intermediate tones. The
frame quantizes+dithers down to that palette locally (PIL's Floyd-Steinberg
dither in EPD.getbuffer), but dithering only reads well when the source
image's contrast/saturation/midtones are already close to what the panel
can reproduce. A typical soft, moderately-saturated phone photo dithers
into a muddy, grainy mess; the same photo pre-corrected toward punchier
contrast, boosted saturation, and midtones pulled toward mid-gray dithers
into something that actually reads as the original image.

Rather than one fixed correction, each step below is *adaptive*: its
strength is derived from the image's own histogram/saturation/brightness (a
flat, hazy photo gets pushed harder than an already punchy one), and the
whole pipeline is then scaled by the single user-facing 0-100 `level` -
0 is a no-op passthrough, 100 applies the full adaptive correction for
that specific photo.

Everything tone-related (contrast stretch, midtone gamma) is done on the
HSV value channel only, and everything color-related (saturation) is done
on the HSV saturation channel only, with hue never touched. Keeping those
concerns on separate channels matters: doing either one directly in RGB
(independent per-channel autocontrast, or a gamma curve applied to R/G/B)
is a *nonlinear, per-channel* operation that quietly shifts hue/saturation
as a side effect - e.g. it can act as an unintended auto-white-balance that
cancels out the very saturation this module is trying to boost. Isolating
tone work to V and color work to S avoids that entirely.
"""

import math

from PIL import Image, ImageFilter, ImageOps, ImageStat

# Target mid-gray (0-1) that midtones are pulled toward. 0.5 splits the
# panel's available headroom evenly between its black point (a dark gray,
# not a true black) and its white point (an off-white, not a true white).
_GAMMA_TARGET = 0.5
# Clamp how far the adaptive gamma correction can push, so a photo that's
# already very dark or very bright (e.g. a night shot, a snow scene) isn't
# forced all the way to mid-gray.
_GAMMA_RANGE = (0.6, 1.8)
# Statistics (mean saturation/value) only need a rough per-image estimate -
# downsample first so they're cheap regardless of upload size.
_STAT_SAMPLE_SIZE = (128, 128)


def _downsampled(band: Image.Image) -> Image.Image:
    if band.width > _STAT_SAMPLE_SIZE[0] or band.height > _STAT_SAMPLE_SIZE[1]:
        return band.resize(_STAT_SAMPLE_SIZE)
    return band


def _mean_band(band: Image.Image) -> float:
    """Mean value of a single-band image, 0-1."""
    return ImageStat.Stat(_downsampled(band)).mean[0] / 255.0


def _lut(fn) -> list:
    return [max(0, min(255, round(fn(i)))) for i in range(256)]


def preprocess_for_eink(image: Image.Image, level: int) -> Image.Image:
    """Adaptively enhance `image` for the frame's 6-color e-ink panel.

    `level` is the user-facing 0-100 slider (FramilySettings.preprocess_level).
    0 returns the image unchanged; 100 applies the full adaptive correction.
    """
    level = max(0, min(100, round(level or 0)))
    if level == 0:
        return image

    strength = level / 100.0
    has_alpha = image.mode == "RGBA"
    alpha = image.split()[-1] if has_alpha else None
    rgb = image.convert("RGB")
    h, s, v = rgb.convert("HSV").split()
    saturation = _mean_band(s)

    # 1. Adaptive contrast stretch on the value channel: clip more of its
    #    histogram tail the higher the level, remapping the image's *actual*
    #    brightness range to fill 0-255. This is the single biggest factor
    #    in whether dithered output reads as "clean" or "muddy" on a panel
    #    whose own black/white points are already lower-contrast than a
    #    screen's.
    cutoff = strength * 2.0  # up to 2% clipped per tail at level=100
    stretched_v = ImageOps.autocontrast(v, cutoff=cutoff)
    v = Image.blend(v, stretched_v, strength)

    # 2. Midtone gamma pull toward mid-gray, also on the value channel:
    #    expands shadow/highlight separation so detail doesn't collapse
    #    into a single dithered blob once quantized down to 6 colors.
    #    Derived from the image's own mean brightness (post contrast-
    #    stretch), clamped so very dark/bright photos aren't forced all the
    #    way to mid-gray, then blended in by `strength`.
    brightness = min(0.95, max(0.05, _mean_band(v)))
    if abs(brightness - _GAMMA_TARGET) > 0.01:
        gamma = math.log(_GAMMA_TARGET) / math.log(brightness)
        gamma = min(_GAMMA_RANGE[1], max(_GAMMA_RANGE[0], gamma))
        blended_gamma = 1.0 + (gamma - 1.0) * strength
        v = v.point(_lut(lambda i, g=blended_gamma: 255 * ((i / 255.0) ** g)))

    # 3. Adaptive saturation boost, on the saturation channel: flatter/
    #    hazier photos (low measured saturation) get pushed hardest toward
    #    the panel's fully-saturated primaries; already-vivid photos get
    #    very little added boost, so they don't posterize or clip.
    headroom = max(0.0, 1.0 - saturation / 0.6)  # 1.0 at sat=0, 0 at sat>=0.6
    sat_factor = 1.0 + headroom * strength  # up to 2x at level=100 on a flat photo
    if sat_factor != 1.0:
        s = s.point(_lut(lambda i, f=sat_factor: i * f))

    rgb = Image.merge("HSV", (h, s, v)).convert("RGB")

    # 4. Light unsharp mask to counter the softening from downstream
    #    resizing and dithering. Already a 0-100 "amount" knob, so scale it
    #    directly by level rather than blending.
    sharpen_percent = round(60 * strength)
    if sharpen_percent > 0:
        rgb = rgb.filter(ImageFilter.UnsharpMask(radius=2, percent=sharpen_percent, threshold=3))

    if has_alpha:
        rgb = rgb.convert("RGBA")
        rgb.putalpha(alpha)
    return rgb
