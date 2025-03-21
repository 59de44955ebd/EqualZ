@echo off
setlocal EnableDelayedExpansion
cd /d %~dp0

:: config
set APP_NAME=EqualZ
set APP_ICON=resources\app.ico
set DIR=%CD%
set APP_DIR=%CD%\dist\%APP_NAME%\

:: cleanup
rmdir /s /q "dist\%APP_NAME%" 2>nul
del "dist\%APP_NAME%-windows-x64-setup.exe" 2>nul
del "dist\%APP_NAME%-windows-x64-portable.7z" 2>nul

echo.
echo ****************************************
echo Running pyinstaller...
echo ****************************************

::pyinstaller --noupx -w -i "%APP_ICON%" -n "%APP_NAME%" --version-file=version_res.txt --hidden-import ziamath.fonts --hidden-import colorbutton --hidden-import latexeditor --hidden-import renderlabel -D main.py
pyinstaller %APP_NAME%_windows.spec

echo.
echo ****************************************
echo Copying resources...
echo ****************************************

mkdir "dist\%APP_NAME%\_internal\resources"
copy resources\main.ui "dist\%APP_NAME%\_internal\resources\"
copy resources\main.rcc "dist\%APP_NAME%\_internal\resources\"
xcopy /e /q resources\symbols "dist\%APP_NAME%\_internal\resources\symbols\"
xcopy /e /q resources\templates "dist\%APP_NAME%\_internal\resources\templates\"

mkdir "dist\%APP_NAME%\_internal\ziamath\fonts"
copy "resources\STIXTwoMath-Regular.ttf" "dist\%APP_NAME%\_internal\ziamath\fonts\"

mkdir "dist\%APP_NAME%\_internal\latex2mathml"
copy "resources\unimathsymbols.txt" "dist\%APP_NAME%\_internal\latex2mathml\"

copy cairo.dll "dist\%APP_NAME%\_internal\"

echo.
echo ****************************************
echo Optimizing dist folder...
echo ****************************************

rmdir /s /q "dist\%APP_NAME%\_internal\wheel-0.43.0.dist-info"

del "dist\%APP_NAME%\_internal\libssl-3.dll"
del "dist\%APP_NAME%\_internal\unicodedata.pyd"
del "dist\%APP_NAME%\_internal\_bz2.pyd"
del "dist\%APP_NAME%\_internal\_decimal.pyd"
del "dist\%APP_NAME%\_internal\_elementtree.pyd"
del "dist\%APP_NAME%\_internal\_hashlib.pyd"
del "dist\%APP_NAME%\_internal\_lzma.pyd"
del "dist\%APP_NAME%\_internal\_ssl.pyd"
del "dist\%APP_NAME%\_internal\_wmi.pyd"

del "dist\%APP_NAME%\_internal\api-ms-win-*.dll"

del "dist\%APP_NAME%\_internal\libcrypto-3.dll"
del "dist\%APP_NAME%\_internal\ucrtbase.dll"

del "dist\%APP_NAME%\_internal\PyQt5\Qt5\bin\d3dcompiler_47.dll"
del "dist\%APP_NAME%\_internal\PyQt5\Qt5\bin\libEGL.dll"
del "dist\%APP_NAME%\_internal\PyQt5\Qt5\bin\libGLESv2.dll"
del "dist\%APP_NAME%\_internal\PyQt5\Qt5\bin\opengl32sw.dll"
del "dist\%APP_NAME%\_internal\PyQt5\Qt5\bin\Qt5DBus.dll"
del "dist\%APP_NAME%\_internal\PyQt5\Qt5\bin\Qt5Network.dll"
del "dist\%APP_NAME%\_internal\PyQt5\Qt5\bin\Qt5Qml.dll"
del "dist\%APP_NAME%\_internal\PyQt5\Qt5\bin\Qt5QmlModels.dll"
del "dist\%APP_NAME%\_internal\PyQt5\Qt5\bin\Qt5Quick.dll"
del "dist\%APP_NAME%\_internal\PyQt5\Qt5\bin\Qt5Svg.dll"
del "dist\%APP_NAME%\_internal\PyQt5\Qt5\bin\Qt5WebSockets.dll"

rmdir /s /q "dist\%APP_NAME%\_internal\PyQt5\uic"
rmdir /s /q "dist\%APP_NAME%\_internal\PyQt5\Qt5\translations"

rmdir /s /q "dist\%APP_NAME%\_internal\PyQt5\Qt5\plugins\generic"
rmdir /s /q "dist\%APP_NAME%\_internal\PyQt5\Qt5\plugins\iconengines"
rmdir /s /q "dist\%APP_NAME%\_internal\PyQt5\Qt5\plugins\platformthemes"

ren "dist\%APP_NAME%\_internal\PyQt5\Qt5\plugins\imageformats\qjpeg.dll" qjpeg
ren "dist\%APP_NAME%\_internal\PyQt5\Qt5\plugins\imageformats\qtiff.dll" qtiff
del /q "dist\%APP_NAME%\_internal\PyQt5\Qt5\plugins\imageformats\*.dll"
ren "dist\%APP_NAME%\_internal\PyQt5\Qt5\plugins\imageformats\qjpeg" qjpeg.dll
ren "dist\%APP_NAME%\_internal\PyQt5\Qt5\plugins\imageformats\qtiff" qtiff.dll

del "dist\%APP_NAME%\_internal\PyQt5\Qt5\plugins\platforms\qminimal.dll"
del "dist\%APP_NAME%\_internal\PyQt5\Qt5\plugins\platforms\qoffscreen.dll"
del "dist\%APP_NAME%\_internal\PyQt5\Qt5\plugins\platforms\qwebgl.dll"

call :create_7z
call :create_installer

:done
echo.
echo ****************************************
echo Done.
echo ****************************************
echo.
pause

endlocal
goto :eof


:create_7z
if not exist "C:\Program Files\7-Zip\" (
	echo.
	echo ****************************************
	echo 7z.exe not found at default location, omitting .7z creation...
	echo ****************************************
	exit /B
)
echo.
echo ****************************************
echo Creating .7z archive...
echo ****************************************
cd dist
echo.>"%APP_NAME%\portable"
set PATH=C:\Program Files\7-Zip;%PATH%
7z a "%APP_NAME%-windows-x64-portable.7z" "%APP_NAME%\*"
del "%APP_NAME%\portable"
cd ..
exit /B


:create_installer
if not exist "C:\Program Files (x86)\NSIS\" (
	echo.
	echo ****************************************
	echo NSIS not found at default location, omitting installer creation...
	echo ****************************************
	exit /B
)
echo.
echo ****************************************
echo Creating installer...
echo ****************************************

:: get length of APP_DIR
set TF=%TMP%\x
echo %APP_DIR%> %TF%
for %%? in (%TF%) do set /a LEN=%%~z? - 2
del %TF%

call :make_abs_nsh nsis\uninstall_list.nsh

del "%NSH%" 2>nul

cd "%APP_DIR%"

for /F %%f in ('dir /b /a-d') do (
	echo Delete "$INSTDIR\%%f" >> "%NSH%"
)

for /F %%d in ('dir /s /b /aD') do (
	cd "%%d"
	set DIR_REL=%%d
	for /F %%f IN ('dir /b /a-d 2^>nul') do (
		echo Delete "$INSTDIR\!DIR_REL:~%LEN%!\%%f" >> "%NSH%"
	)
)

cd "%APP_DIR%"

for /F %%d in ('dir /s /b /ad^|sort /r') do (
	set DIR_REL=%%d
	echo RMDir "$INSTDIR\!DIR_REL:~%LEN%!" >> "%NSH%"
)

cd "%DIR%"
set PATH=C:\Program Files (x86)\NSIS;%PATH%
makensis nsis\make-installer.nsi
exit /B


:make_abs_nsh
set NSH=%~dpnx1%
exit /B