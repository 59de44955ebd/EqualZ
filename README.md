# EqualZ - a simple standalone LaTeX Math Equation editor based on Python, PyQt5, Ziamath and CairoSVG
EqualZ is a simplified clone of [EqualX](https://equalx.sourceforge.io/), but written in Python and standalone, i.e. without depending on external tools. In other words, you don't have to install a full LaTeX stack and bloat your disk with another 900 MB (as in case of MiKTeX) if you only want to render some simple math equations. 

It instead uses bundled versions of [Ziamath](https://github.com/cdelker/ziamath) to render LaTeX Math to SVG and [CairoSVG](https://cairosvg.org/) to convert SVG to other formats. Since no external processes have to be started, equations are also rendered way faster (instantly) than in EqualX.

## Supported export formats
* BMP
* JPEG
* PNG
* PDF
* SVG
* TeX
* TIFF

## Screenshot
*EqualZ in Windows 11*  
![EqualZ in Windows 131](screenshots/equalz_win11.png)

## Notes
* To keep the file size and memory consumption of the frozen .exe small, it uses a slightly adjusted private copy of CairoSVG (renamed to "cairosvg_min") that has the dependancy on Pillow (which in turn would depend on Numpy) removed - CairoSVG uses Pillow only for a feature that EqualZ doesn't need anyway. But EqualZ works perfectly fine also with the original unaltered version of CairoSVG, just change the import at the top of main.py accordingly.
* The portable version for Windows saves bookmarks and history in a local folder called "data", whereas the installer version creates and uses the folder `C:\Users\<Username>\.equalz`.  
The app detects at runtime if it runs in portable or installer mode by looking for a file called "portable" next to the .exe.

## ToDos
* Create frozen release for macOS as well
* Possibly add support for MathML in addition to LaTeX Math
