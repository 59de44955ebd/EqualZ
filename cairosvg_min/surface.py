"""
Cairo surface creators.

"""

import copy
import io

import cairocffi_min as cairo

from .colors import color, negate_color
from .defs import (
    apply_filter_after_painting, apply_filter_before_painting, clip_path,
    filter_, gradient_or_pattern, linear_gradient, marker, mask, paint_mask,
    parse_all_defs, pattern, prepare_filter, radial_gradient, use)
from .helpers import (
    UNITS, PointError, clip_rect, node_format, normalize, paint,
    preserve_ratio, size, transform)
from .image import image #, invert_image
from .parser import Tree
from .path import draw_markers, path
from .shapes import circle, ellipse, line, polygon, polyline, rect
from .svg import svg
from .text import text
from .url import parse_url

SHAPE_ANTIALIAS = {
    'optimizeSpeed': cairo.ANTIALIAS_FAST,
    'crispEdges': cairo.ANTIALIAS_NONE,
    'geometricPrecision': cairo.ANTIALIAS_BEST,
}

TEXT_ANTIALIAS = {
    'crispEdges': cairo.ANTIALIAS_NONE,
    'optimizeSpeed': cairo.ANTIALIAS_FAST,
    'optimizeLegibility': cairo.ANTIALIAS_GOOD,
    'geometricPrecision': cairo.ANTIALIAS_BEST,
}

TEXT_HINT_STYLE = {
    'geometricPrecision': cairo.HINT_STYLE_NONE,
    'optimizeLegibility': cairo.HINT_STYLE_FULL,
}

TEXT_HINT_METRICS = {
    'geometricPrecision': cairo.HINT_METRICS_OFF,
    'optimizeLegibility': cairo.HINT_METRICS_ON,
}

TAGS = {
    'a': text,
    'circle': circle,
    'clipPath': clip_path,
    'ellipse': ellipse,
    'filter': filter_,
    'image': image,
    'line': line,
    'linearGradient': linear_gradient,
    'marker': marker,
    'mask': mask,
    'path': path,
    'pattern': pattern,
    'polyline': polyline,
    'polygon': polygon,
    'radialGradient': radial_gradient,
    'rect': rect,
    'svg': svg,
    'text': text,
    'textPath': text,
    'tspan': text,
    'use': use,
}

PATH_TAGS = frozenset((
    'circle', 'ellipse', 'line', 'path', 'polygon', 'polyline', 'rect'))

INVISIBLE_TAGS = frozenset((
    'clipPath', 'filter', 'linearGradient', 'marker', 'mask', 'pattern',
    'radialGradient', 'symbol'))


class Surface(object):
    """Abstract base class for CairoSVG surfaces.

    The ``width`` and ``height`` attributes are in device units (pixels for
    PNG, else points).

    The ``context_width`` and ``context_height`` attributes are in user units
    (i.e. in pixels), they represent the size of the active viewport.

    """

    # Subclasses must either define this or override _create_surface()
    surface_class = None

    @classmethod
    def convert(cls, bytestring=None, *, file_obj=None, url=None, dpi=96,
                parent_width=None, parent_height=None, scale=1, unsafe=False,
                background_color=None, negate_colors=False,
                invert_images=False, write_to=None, output_width=None,
                output_height=None, **kwargs):
        """Convert an SVG document to the format for this class.

        Specify the input by passing one of these:

        :param bytestring: The SVG source as a byte-string.
        :param file_obj: A file-like object.
        :param url: A filename.

        Give some options:

        :param dpi: The ratio between 1 inch and 1 pixel.
        :param parent_width: The width of the parent container in pixels.
        :param parent_height: The height of the parent container in pixels.
        :param scale: The ouptut scaling factor.
        :param unsafe: A boolean allowing external file access, XML entities
                       and very large files
                       (WARNING: vulnerable to XXE attacks and various DoS).

        Specifiy the output with:

        :param write_to: The filename of file-like object where to write the
                         output. If None or not provided, return a byte string.

        Only ``bytestring`` can be passed as a positional argument, other
        parameters are keyword-only.

        """
        tree = Tree(
            bytestring=bytestring, file_obj=file_obj, url=url, unsafe=unsafe,
            **kwargs)
        output = write_to or io.BytesIO()
        instance = cls(
            tree, output, dpi, None, parent_width, parent_height, scale,
            output_width, output_height, background_color,
            map_rgba=negate_color if negate_colors else None,
#            map_image=invert_image if invert_images else None
            map_image=None
            )
        instance.finish()
        if write_to is None:
            return output.getvalue()

    def __init__(self, tree, output, dpi, parent_surface=None,
                 parent_width=None, parent_height=None,
                 scale=1, output_width=None, output_height=None,
                 background_color=None, map_rgba=None, map_image=None):
        """Create the surface from a filename or a file-like object.

        The rendered content is written to ``output`` which can be a filename,
        a file-like object, ``None`` (render in memory but do not write
        anything) or the built-in ``bytes`` as a marker.

        Call the ``.finish()`` method to make sure that the output is
        actually written.

        """
        self.cairo = None
        self.context_width, self.context_height = parent_width, parent_height
        self.cursor_position = [0, 0]
        self.cursor_d_position = [0, 0]
        self.text_path_width = 0
        self.tree_cache = {(tree.url, tree.get('id')): tree}
        if parent_surface:
            self.markers = parent_surface.markers
            self.gradients = parent_surface.gradients
            self.patterns = parent_surface.patterns
            self.masks = parent_surface.masks
            self.paths = parent_surface.paths
            self.filters = parent_surface.filters
            self.images = parent_surface.images
        else:
            self.markers = {}
            self.gradients = {}
            self.patterns = {}
            self.masks = {}
            self.paths = {}
            self.filters = {}
            self.images = {}
        self._old_parent_node = self.parent_node = None
        self.output = output
        self.dpi = dpi
        self.font_size = size(self, '12pt')
        self.stroke_and_fill = True
        width, height, viewbox = node_format(self, tree)
        if viewbox is None:
            viewbox = (0, 0, width, height)

        if output_width and output_height:
            width, height = output_width, output_height
        elif output_width:
            if width:
                # Keep the aspect ratio
                height *= output_width / width
            width = output_width
        elif output_height:
            if height:
                # Keep the aspect ratio
                width *= output_height / height
            height = output_height
        else:
            width *= scale
            height *= scale

        # Actual surface dimensions: may be rounded on raster surfaces types
        self.cairo, self.width, self.height = self._create_surface(
            width * self.device_units_per_user_units,
            height * self.device_units_per_user_units)

        if 0 in (self.width, self.height):
            raise ValueError('The SVG size is undefined')

        self.context = cairo.Context(self.cairo)
        # We must scale the context as the surface size is using physical units
        self.context.scale(
            self.device_units_per_user_units, self.device_units_per_user_units)
        # Initial, non-rounded dimensions
        self.set_context_size(width, height, viewbox, tree)
        self.context.move_to(0, 0)

        if background_color:
            self.context.set_source_rgba(*color(background_color))
            self.context.paint()

        self.map_rgba = map_rgba
        self.map_image = map_image
        self.draw(tree)

    @property
    def points_per_pixel(self):
        """Surface resolution."""
        return 1 / (self.dpi * UNITS['pt'])

    @property
    def device_units_per_user_units(self):
        """Ratio between Cairo device units and user units.

        Device units are points for everything but PNG, and pixels for
        PNG. User units are pixels.

        """
        return self.points_per_pixel

    def _create_surface(self, width, height):
        """Create and return ``(cairo_surface, width, height)``."""
        cairo_surface = self.surface_class(self.output, width, height)
        return cairo_surface, width, height

    def set_context_size(self, width, height, viewbox, tree):
        """Set the Cairo context size, set the SVG viewport size."""
        if viewbox:
            rect_x, rect_y = viewbox[0:2]
            tree.image_width = viewbox[2]
            tree.image_height = viewbox[3]
        else:
            rect_x, rect_y = 0, 0
            tree.image_width = width
            tree.image_height = height

        scale_x, scale_y, translate_x, translate_y = preserve_ratio(
            self, tree, width, height)
        rect_x, rect_y = rect_x * scale_x, rect_y * scale_y
        rect_width, rect_height = width, height
        self.context.translate(*self.context.get_current_point())
        self.context.translate(-rect_x, -rect_y)
        if tree.get('overflow', 'hidden') != 'visible':
            self.context.rectangle(rect_x, rect_y, rect_width, rect_height)
            self.context.clip()
        self.context.scale(scale_x, scale_y)
        self.context.translate(translate_x, translate_y)
        self.context_width = rect_width / scale_x
        self.context_height = rect_height / scale_y

    def finish(self):
        """Read the surface content."""
        self.cairo.finish()

    def map_color(self, string, opacity=1):
        """Parse a color ``string`` and apply ``map_rgba`` function to it."""
        rgba = color(string, opacity)
        return self.map_rgba(rgba) if self.map_rgba else rgba

    def draw(self, node):
        """Draw ``node`` and its children."""

        # Parse definitions first
        if node.tag == 'svg':
            parse_all_defs(self, node)

        # Do not draw defs
        if node.tag == 'defs':
            return

        # Do not draw elements with width or height of 0
        if (('width' in node and size(self, node['width']) == 0) or
                ('height' in node and size(self, node['height']) == 0)):
            return

        # Save context and related attributes
        old_parent_node = self.parent_node
        old_font_size = self.font_size
        old_context_size = self.context_width, self.context_height
        self.parent_node = node

        if "font" in node:
            font = parse_font(node["font"])
            for att in font:
                if att not in node:
                    node[att] = font[att]

        self.font_size = size(self, node.get('font-size', '12pt'))
        self.context.save()

        # Apply transformations
        transform(
            self, node.get('transform'),
            transform_origin=node.get('transform-origin'))

        # Find and prepare opacity, masks and filters
        mask = parse_url(node.get('mask')).fragment
        filter_ = parse_url(node.get('filter')).fragment
        opacity = float(node.get('opacity', 1))

        if filter_:
            prepare_filter(self, node, filter_)

        if filter_ or mask or (opacity < 1 and node.children):
            self.context.push_group()

        # Move to (node.x, node.y)
        self.context.move_to(
            size(self, node.get('x'), 'x'),
            size(self, node.get('y'), 'y'))

        # Set node's drawing informations if the ``node.tag`` method exists
        line_cap = node.get('stroke-linecap')
        if line_cap == 'square':
            self.context.set_line_cap(cairo.LINE_CAP_SQUARE)
        if line_cap == 'round':
            self.context.set_line_cap(cairo.LINE_CAP_ROUND)

        join_cap = node.get('stroke-linejoin')
        if join_cap == 'round':
            self.context.set_line_join(cairo.LINE_JOIN_ROUND)
        if join_cap == 'bevel':
            self.context.set_line_join(cairo.LINE_JOIN_BEVEL)

        dash_array = normalize(node.get('stroke-dasharray', '')).split()
        if dash_array:
            dashes = [size(self, dash) for dash in dash_array]
            if sum(dashes):
                offset = size(self, node.get('stroke-dashoffset'))
                self.context.set_dash(dashes, offset)

        miter_limit = float(node.get('stroke-miterlimit', 4))
        self.context.set_miter_limit(miter_limit)

        # Clip
        rect_values = clip_rect(node.get('clip'))
        if len(rect_values) == 4:
            top = size(self, rect_values[0], 'y')
            right = size(self, rect_values[1], 'x')
            bottom = size(self, rect_values[2], 'y')
            left = size(self, rect_values[3], 'x')
            x = size(self, node.get('x'), 'x')
            y = size(self, node.get('y'), 'y')
            width = size(self, node.get('width'), 'x')
            height = size(self, node.get('height'), 'y')
            self.context.save()
            self.context.translate(x, y)
            self.context.rectangle(
                left, top, width - left - right, height - top - bottom)
            self.context.restore()
            self.context.clip()
        clip_path = parse_url(node.get('clip-path')).fragment
        if clip_path:
            path = self.paths.get(clip_path)
            if path:
                self.context.save()
                if path.get('clipPathUnits') == 'objectBoundingBox':
                    x = size(self, node.get('x'), 'x')
                    y = size(self, node.get('y'), 'y')
                    width = size(self, node.get('width'), 'x')
                    height = size(self, node.get('height'), 'y')
                    self.context.translate(x, y)
                    self.context.scale(width, height)
                path.tag = 'g'
                self.stroke_and_fill = False
                self.draw(path)
                self.stroke_and_fill = True
                path.tag = 'clipPath'
                self.context.restore()
                # TODO: fill rules are not handled by cairo for clips
                # if node.get('clip-rule') == 'evenodd':
                #     self.context.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
                self.context.clip()
                self.context.set_fill_rule(cairo.FILL_RULE_WINDING)

        save_cursor = copy.deepcopy(
            (self.cursor_position, self.cursor_d_position,
             self.text_path_width))

        # Only draw known tags
        if node.tag in TAGS:
            try:
                TAGS[node.tag](self, node)
            except PointError:
                # Error in point parsing, do nothing
                pass

        # Get stroke and fill opacity
        stroke_opacity = float(node.get('stroke-opacity', 1))
        fill_opacity = float(node.get('fill-opacity', 1))
        if opacity < 1 and not node.children:
            stroke_opacity *= opacity
            fill_opacity *= opacity

        # Manage display and visibility
        display = node.get('display', 'inline') != 'none'
        visible = display and (node.get('visibility', 'visible') != 'hidden')

        # Set font rendering properties
        self.context.set_antialias(SHAPE_ANTIALIAS.get(
            node.get('shape-rendering'), cairo.ANTIALIAS_DEFAULT))

        font_options = self.context.get_font_options()
        font_options.set_antialias(TEXT_ANTIALIAS.get(
            node.get('text-rendering'), cairo.ANTIALIAS_DEFAULT))
        font_options.set_hint_style(TEXT_HINT_STYLE.get(
            node.get('text-rendering'), cairo.HINT_STYLE_DEFAULT))
        font_options.set_hint_metrics(TEXT_HINT_METRICS.get(
            node.get('text-rendering'), cairo.HINT_METRICS_DEFAULT))
        self.context.set_font_options(font_options)

        # Fill and stroke
        if self.stroke_and_fill and visible and node.tag in TAGS:
            # Fill
            self.context.save()
            paint_source, paint_color = paint(node.get('fill', 'black'))
            if node.get('fill-rule') == 'evenodd':
                self.context.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
            if not gradient_or_pattern(self, node, paint_source, fill_opacity):
                self.context.set_source_rgba(
                    *self.map_color(paint_color, fill_opacity))
            if TAGS[node.tag] == text:
                self.cursor_position = save_cursor[0]
                self.cursor_d_position = save_cursor[1]
                self.text_path_width = save_cursor[2]
                text(self, node, draw_as_text=True)
            else:
                self.context.fill_preserve()
            self.context.restore()

            # Stroke
            self.context.save()
            self.context.set_line_width(
                size(self, node.get('stroke-width', '1')))
            paint_source, paint_color = paint(node.get('stroke'))
            if not gradient_or_pattern(
                    self, node, paint_source, stroke_opacity):
                self.context.set_source_rgba(
                    *self.map_color(paint_color, stroke_opacity))
            self.context.stroke()
            self.context.restore()
        elif not visible:
            self.context.new_path()

        # Draw path markers
        draw_markers(self, node)

        # Draw children
        if display and node.tag not in INVISIBLE_TAGS:
            for child in node.children:
                self.draw(child)

        # Apply filter, mask and opacity
        if filter_ or mask or (opacity < 1 and node.children):
            self.context.pop_group_to_source()
            if filter_:
                apply_filter_before_painting(self, node, filter_)
            if mask in self.masks:
                paint_mask(self, node, mask, opacity)
            else:
                self.context.paint_with_alpha(opacity)
            if filter_:
                apply_filter_after_painting(self, node, filter_)

        # Clean cursor's position after 'text' tags
        if node.tag == 'text':
            self.cursor_position = [0, 0]
            self.cursor_d_position = [0, 0]
            self.text_path_width = 0

        self.context.restore()
        self.parent_node = old_parent_node
        self.font_size = old_font_size
        self.context_width, self.context_height = old_context_size


class PDFSurface(Surface):
    """A surface that writes in PDF format."""
    surface_class = cairo.PDFSurface


class PSSurface(Surface):
    """A surface that writes in PostScript format."""
    surface_class = cairo.PSSurface


class EPSSurface(Surface):
    """A surface that writes in Encapsulated PostScript format."""

    def _create_surface(self, width, height):
        """Create and return ``(cairo_surface, width, height)``."""
        cairo_surface = cairo.PSSurface(self.output, width, height)
        cairo_surface.set_eps(True)
        return cairo_surface, width, height


class PNGSurface(Surface):
    """A surface that writes in PNG format."""
    device_units_per_user_units = 1

    def _create_surface(self, width, height):
        """Create and return ``(cairo_surface, width, height)``."""
        width = int(width)
        height = int(height)
        cairo_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        return cairo_surface, width, height

    def finish(self):
        """Read the PNG surface content."""
        if self.output is not None:
            self.cairo.write_to_png(self.output)
        return super().finish()


class SVGSurface(Surface):
    """A surface that writes in SVG format.

    It may seem pointless to render SVG to SVG, but this can be used
    with ``output=None`` to get a vector-based single page cairo surface.

    """
    surface_class = cairo.SVGSurface


def parse_font(value):
    ret = {"font-family": "", "font-size": "", "font-style": "normal",
           "font-variant": "normal", "font-weight": "normal",
           "line-height": "normal"}

    font_styles = ["italic", "oblique"]
    font_variants = ["small-caps"]
    font_weights = ["bold", "bolder", "lighter", "100", "200", "300", "400",
                    "500", "600", "700", "800", "900"]

    for element in value.split():
        if element == "normal":
            continue
        elif ret["font-family"]:
            ret["font-family"] += " " + element
        elif element in font_styles:
            ret["font-style"] = element
        elif element in font_variants:
            ret["font-variant"] = element
        elif element in font_weights:
            ret["font-weight"] = element
        else:
            if not ret["font-size"]:
                parts = element.split("/")
                ret["font-size"] = parts[0]
                if len(parts) > 1:
                    ret["line-height"] = parts[1]
                continue
            else:
                ret["font-family"] = element

    return ret
