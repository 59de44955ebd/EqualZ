"""
CairoSVG API test suite.

These tests can be used as deployment tests.

"""

import io
import os
import shutil
import sys
import tempfile

import cairocffi_min as cairo
import pytest

from . import SURFACES, VERSION, parser, surface, svg2pdf, svg2png
from .__main__ import main

MAGIC_NUMBERS = {
    'SVG': b'<?xml',
    'PNG': b'\211PNG\r\n\032\n',
    'PDF': b'%PDF',
    'PS': b'%!',
}

SVG_SAMPLE = b'''\
<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="4in" height="5in">
  <rect x="5" y="10" width="13" height="15"
        fill="lime" stroke="black" stroke-width="1" />
</svg>
'''


@pytest.mark.parametrize('format_name', MAGIC_NUMBERS)
def test_formats(format_name):
    """Convert to a given format and test that output looks right."""
    content = SURFACES[format_name].convert(SVG_SAMPLE)
    assert content.startswith(MAGIC_NUMBERS[format_name])


def read_file(filename):
    """Shortcut to return the whole content of a file as a byte string."""
    with open(filename, 'rb') as file_object:
        return file_object.read()


def test_api():
    """Test the Python API with various parameters."""
    expected_content = svg2png(SVG_SAMPLE)
    # Already tested above: just a sanity check:
    assert expected_content.startswith(MAGIC_NUMBERS['PNG'])

    # Read from a byte string
    assert svg2png(SVG_SAMPLE) == expected_content
    assert svg2png(bytestring=SVG_SAMPLE) == expected_content

    file_like = io.BytesIO(SVG_SAMPLE)
    # Read from a file-like object
    assert svg2png(file_obj=file_like) == expected_content

    file_like = io.BytesIO()
    # Write to a file-like object
    svg2png(SVG_SAMPLE, write_to=file_like)
    assert file_like.getvalue() == expected_content

    temp = tempfile.mkdtemp()
    try:
        temp_0 = os.path.join(temp, 'sample_0.svg')
        with open(temp_0, 'wb') as file_object:
            file_object.write(SVG_SAMPLE)

        # Read from a filename
        assert svg2png(url=temp_0) == expected_content
        assert svg2png(
            url=f'file://{temp_0}') == expected_content

        with open(temp_0, 'rb') as file_object:
            # Read from a real file object
            assert svg2png(file_obj=file_object) == expected_content

        temp_1 = os.path.join(temp, 'result_1.png')
        with open(temp_1, 'wb') as file_object:
            # Write to a real file object
            svg2png(SVG_SAMPLE, write_to=file_object)
        assert read_file(temp_1) == expected_content

        temp_2 = os.path.join(temp, 'result_2.png')
        # Write to a filename
        svg2png(SVG_SAMPLE, write_to=temp_2)
        assert read_file(temp_2) == expected_content

    finally:
        shutil.rmtree(temp)

    file_like = io.BytesIO()
    try:
        svg2png(write_to=file_like)
    except TypeError:
        pass
    else:  # pragma: no cover
        raise Exception('TypeError not raised')


def test_low_level_api():
    """Test the low-level Python API with various parameters."""
    expected_content = svg2png(SVG_SAMPLE)

    # Same as above, longer version
    tree = parser.Tree(bytestring=SVG_SAMPLE)
    file_like = io.BytesIO()
    png_surface = surface.PNGSurface(tree, file_like, 96)
    png_surface.finish()
    assert file_like.getvalue() == expected_content

    png_result = cairo.ImageSurface.create_from_png(
        io.BytesIO(expected_content))
    expected_width = png_result.get_width()
    expected_height = png_result.get_height()

    # Abstract surface
    png_surface = surface.PNGSurface(tree, None, 96)
    assert png_surface.width == expected_width
    assert png_surface.height == expected_height
    assert cairo.SurfacePattern(png_surface.cairo)


def test_script():
    """Test the ``cairosvg`` script and the ``main`` function."""
    expected_png = svg2png(SVG_SAMPLE)[:100]
    expected_pdf = svg2pdf(SVG_SAMPLE)[:100]

    def test_main(args, exit_=False, input_=None, full=False):
        """Test main called with given ``args``.

        If ``exit_`` is ``True``, check that ``SystemExit`` is raised. We then
        assume that the program output is an unicode string.

        If ``input_`` is given, use this stream as input stream.

        """
        sys.argv = ['cairosvg'] + args
        old_stdin, old_stdout = sys.stdin, sys.stdout

        output_buffer = io.BytesIO()
        sys.stdout = io.TextIOWrapper(output_buffer)

        if input_:
            sys.stdin = open(input_, 'rb')
            sys.stdin.buffer = sys.stdin

        if exit_:
            try:
                main()
            except SystemExit:
                pass
            else:  # pragma: no cover
                raise Exception('CairoSVG did not exit')
        else:
            main()

        sys.stdout.flush()
        output = output_buffer.getvalue()
        sys.stdin, sys.stdout = old_stdin, old_stdout
        return output if full else output[:100]

    with tempfile.NamedTemporaryFile(delete=False) as file_object:
        file_object.write(SVG_SAMPLE)
        file_object.flush()
        svg_filename = file_object.name
        file_object.close()

        assert test_main(['--help'], exit_=True).startswith(b'usage: ')
        assert test_main(['--version'], exit_=True).strip() == (
            VERSION.encode('ascii'))

        assert test_main([svg_filename]) == expected_pdf
        assert test_main([svg_filename, '-d', '96', '-f', 'pdf']) == (
            expected_pdf)
        assert test_main([svg_filename, '-f', 'png']) == expected_png
        assert test_main(['-'], input_=svg_filename) == expected_pdf

        # Test DPI
        output = test_main([svg_filename, '-d', '10', '-f', 'png'], full=True)
        image = cairo.ImageSurface.create_from_png(io.BytesIO(output))
        assert image.get_width() == 40
        assert image.get_height() == 50

        temp = tempfile.mkdtemp()
        try:
            temp_1 = os.path.join(temp, 'result_1')
            # Default to PDF
            assert not test_main([svg_filename, '-o', temp_1])
            assert read_file(temp_1)[:100] == expected_pdf

            temp_2 = os.path.join(temp, 'result_2.png')
            # Guess from the file extension
            assert not test_main([svg_filename, '-o', temp_2])
            assert read_file(temp_2)[:100] == expected_png

            temp_3 = os.path.join(temp, 'result_3.png')
            # Explicit -f wins
            assert not test_main([svg_filename, '-o', temp_3, '-f', 'pdf'])
            assert read_file(temp_3)[:100] == expected_pdf
        finally:
            shutil.rmtree(temp)

        try:
            os.remove(svg_filename)
        except PermissionError:
            # On Windows/NT systems, the temporary file sometimes fails to
            # get deleted due to ``PermissionError`` exception. This is due
            # to how Windows/NT handles the same file being opened twice at
            # the same time.
            pass
