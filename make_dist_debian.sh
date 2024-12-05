#!/bin/bash

APP_NAME=EqualZ

cd "$(dirname "$0")"

rm -R "build/$APP_NAME" 2>/dev/null
rm -R "dist/$APP_NAME" 2>/dev/null
rm "dist/$APP_NAME-debian-x64.tar.xz" 2>/dev/null

echo
echo '****************************************'
echo 'Checking requirements...'
echo '****************************************'

#pip install -r requirements.txt
#pip install -r requirements_dist.txt

echo
echo '****************************************'
echo 'Running pyinstaller...'
echo '****************************************'

#env/bin/pyinstaller -F --noupx -w -n EqualZ --hidden-import ziamath.fonts --hidden-import colorbutton --hidden-import latexeditor --hidden-import renderlabel -D main.py
env/bin/pyinstaller "${APP_NAME}_debian.spec"

echo
echo '****************************************'
echo 'Copying resources...'
echo '****************************************'

mkdir "dist/$APP_NAME/_internal/resources"
cp resources/main.ui "dist/$APP_NAME/_internal/resources/"
cp resources/main.rcc "dist/$APP_NAME/_internal/resources/"

cp -R  resources/symbols "dist/$APP_NAME/_internal/resources/symbols/"
cp -R resources/templates "dist/$APP_NAME/_internal/resources/templates/"

mkdir -p "dist/$APP_NAME/_internal/ziamath/fonts"
cp "resources/STIXTwoMath-Regular.ttf" "dist/$APP_NAME/_internal/ziamath/fonts/"

mkdir -p "dist/$APP_NAME/_internal/latex2mathml"
cp "resources/unimathsymbols.txt" "dist/$APP_NAME/_internal/latex2mathml/"

echo
echo '****************************************'
echo 'Optimizing application...'
echo '****************************************'

rm -R "dist/$APP_NAME/_internal/PyQt5/uic"
rm -R "dist/$APP_NAME/_internal/PyQt5/Qt5/translations"

rm "dist/$APP_NAME/_internal/PyQt5/Qt5/lib/libQt5Network.so.5"
rm "dist/$APP_NAME/_internal/PyQt5/Qt5/lib/libQt5Qml.so.5"
rm "dist/$APP_NAME/_internal/PyQt5/Qt5/lib/libQt5QmlModels.so.5"
rm "dist/$APP_NAME/_internal/PyQt5/Qt5/lib/libQt5Quick.so.5"
rm "dist/$APP_NAME/_internal/PyQt5/Qt5/lib/libQt5Svg.so.5"
rm "dist/$APP_NAME/_internal/PyQt5/Qt5/lib/libQt5WebSockets.so.5"

rm "dist/$APP_NAME/_internal/libQt5Network.so.5"
rm "dist/$APP_NAME/_internal/libQt5Qml.so.5"
rm "dist/$APP_NAME/_internal/libQt5QmlModels.so.5"
rm "dist/$APP_NAME/_internal/libQt5Quick.so.5"
rm "dist/$APP_NAME/_internal/libQt5Svg.so.5"
rm "dist/$APP_NAME/_internal/libQt5WebSockets.so.5"

rm -R "dist/$APP_NAME/_internal/PyQt5/Qt5/plugins/generic"
rm -R "dist/$APP_NAME/_internal/PyQt5/Qt5/plugins/iconengines"
rm -R "dist/$APP_NAME/_internal/PyQt5/Qt5/plugins/platforminputcontexts"

mv "dist/$APP_NAME/_internal/PyQt5/Qt5/plugins/imageformats/libqjpeg.so" ./libqjpeg.so
mv "dist/$APP_NAME/_internal/PyQt5/Qt5/plugins/imageformats/libqtiff.so" ./libqtiff.so
rm -R "dist/$APP_NAME/_internal/PyQt5/Qt5/plugins/imageformats"
mkdir "dist/$APP_NAME/_internal/PyQt5/Qt5/plugins/imageformats"
mv ./libqjpeg.so "dist/$APP_NAME/_internal/PyQt5/Qt5/plugins/imageformats/"
mv ./libqtiff.so "dist/$APP_NAME/_internal/PyQt5/Qt5/plugins/imageformats/"

rm "dist/$APP_NAME/_internal/PyQt5/Qt5/plugins/platforms/libqvnc.so"
rm "dist/$APP_NAME/_internal/PyQt5/Qt5/plugins/platforms/libqoffscreen.so"
rm "dist/$APP_NAME/_internal/PyQt5/Qt5/plugins/platforms/libqwebgl.so"

rm "dist/$APP_NAME/_internal/libcrypto.so.3"
rm "dist/$APP_NAME/_internal/libssl.so.3"

rm -R "dist/$APP_NAME/_internal/setuptools-66.1.1.dist-info"

echo
echo '****************************************'
echo 'Creating .tar.xz...'
echo '****************************************'

cd dist
tar -cJf "$APP_NAME-debian-x64.tar.xz" "$APP_NAME/"
cd ..

echo
echo '****************************************'
echo 'Done.'
echo '****************************************'
echo


