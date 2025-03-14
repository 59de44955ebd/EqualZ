"""
CairoSVG - A simple SVG converter based on Cairo.

"""

import os
import sys
from pathlib import Path

if hasattr(sys, 'frozen'):
    if hasattr(sys, '_MEIPASS'):
        # Frozen with PyInstaller
        # See https://github.com/Kozea/WeasyPrint/pull/540
        ROOT = Path(sys._MEIPASS) / 'cairosvg'
    else:
        # Frozen with something else (py2exe, etc.)
        # See https://github.com/Kozea/WeasyPrint/pull/269
        ROOT = Path(os.path.dirname(sys.executable))
else:
    ROOT = Path(os.path.dirname(__file__))

VERSION = __version__ = '2.7.1'


# VERSION is used in the "url" module imported by "surface"
from . import surface  # noqa isort:skip


SURFACES = {
    'PDF': surface.PDFSurface,
    'PNG': surface.PNGSurface,
    'PS': surface.PSSurface,
    'EPS': surface.EPSSurface,
    'SVG': surface.SVGSurface,
}


def svg2svg(bytestring=None, *, file_obj=None, url=None, dpi=96,
            parent_width=None, parent_height=None, scale=1, unsafe=False,
            background_color=None, negate_colors=False, invert_images=False,
            write_to=None, output_width=None, output_height=None):
    return surface.SVGSurface.convert(
        bytestring=bytestring, file_obj=file_obj, url=url, dpi=dpi,
        parent_width=parent_width, parent_height=parent_height, scale=scale,
        background_color=background_color,
        negate_colors=negate_colors, invert_images=invert_images,
        unsafe=unsafe, write_to=write_to, output_width=output_width,
        output_height=output_height)


def svg2png(bytestring=None, *, file_obj=None, url=None, dpi=96,
            parent_width=None, parent_height=None, scale=1, unsafe=False,
            background_color=None, negate_colors=False, invert_images=False,
            write_to=None, output_width=None, output_height=None):
    return surface.PNGSurface.convert(
        bytestring=bytestring, file_obj=file_obj, url=url, dpi=dpi,
        parent_width=parent_width, parent_height=parent_height, scale=scale,
        background_color=background_color, negate_colors=negate_colors,
        invert_images=invert_images, unsafe=unsafe, write_to=write_to,
        output_width=output_width, output_height=output_height)


def svg2pdf(bytestring=None, *, file_obj=None, url=None, dpi=96,
            parent_width=None, parent_height=None, scale=1, unsafe=False,
            background_color=None, negate_colors=False, invert_images=False,
            write_to=None, output_width=None, output_height=None):
    return surface.PDFSurface.convert(
        bytestring=bytestring, file_obj=file_obj, url=url, dpi=dpi,
        parent_width=parent_width, parent_height=parent_height, scale=scale,
        background_color=background_color, negate_colors=negate_colors,
        invert_images=invert_images, unsafe=unsafe, write_to=write_to,
        output_width=output_width, output_height=output_height)


def svg2ps(bytestring=None, *, file_obj=None, url=None, dpi=96,
           parent_width=None, parent_height=None, scale=1, unsafe=False,
           background_color=None, negate_colors=False, invert_images=False,
           write_to=None, output_width=None, output_height=None):
    return surface.PSSurface.convert(
        bytestring=bytestring, file_obj=file_obj, url=url, dpi=dpi,
        parent_width=parent_width, parent_height=parent_height, scale=scale,
        background_color=background_color, negate_colors=negate_colors,
        invert_images=invert_images, unsafe=unsafe, write_to=write_to,
        output_width=output_width, output_height=output_height)


def svg2eps(bytestring=None, *, file_obj=None, url=None, dpi=96,
            parent_width=None, parent_height=None, scale=1, unsafe=False,
            background_color=None, negate_colors=False, invert_images=False,
            write_to=None, output_width=None, output_height=None):
    return surface.EPSSurface.convert(
        bytestring=bytestring, file_obj=file_obj, url=url, dpi=dpi,
        parent_width=parent_width, parent_height=parent_height, scale=scale,
        background_color=background_color, negate_colors=negate_colors,
        invert_images=invert_images, unsafe=unsafe, write_to=write_to,
        output_width=output_width, output_height=output_height)


if __debug__:
    svg2svg.__doc__ = surface.Surface.convert.__doc__.replace(
        'the format for this class', 'SVG')
    svg2png.__doc__ = surface.Surface.convert.__doc__.replace(
        'the format for this class', 'PNG')
    svg2pdf.__doc__ = surface.Surface.convert.__doc__.replace(
        'the format for this class', 'PDF')
    svg2ps.__doc__ = surface.Surface.convert.__doc__.replace(
        'the format for this class', 'PS')
    svg2eps.__doc__ = surface.Surface.convert.__doc__.replace(
        'the format for this class', 'EPS')
