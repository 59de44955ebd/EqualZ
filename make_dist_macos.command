APP_NAME=EqualZ
APP_ICON=resources/app.icns

cd "$(dirname "$0")"

rm -R "dist/$APP_NAME" 2>/dev/null
rm -R "dist/$APP_NAME.app" 2>/dev/null
rm "dist/$APP_NAME.dmg" 2>/dev/null

echo
echo '****************************************'
echo 'Checking requirements...'
echo '****************************************'

pip install -r requirements.txt
pip install -r requirements_dist.txt

echo
echo '****************************************'
echo 'Running pyinstaller...'
echo '****************************************'

pyinstaller "${APP_NAME}_macos.spec"

echo
echo '****************************************'
echo 'Copying resources...'
echo '****************************************'

cp resources/main.ui "dist/$APP_NAME.app/Contents/Resources/"
cp resources/main.rcc "dist/$APP_NAME.app/Contents/Resources/"

cp -R  resources/symbols "dist/$APP_NAME.app/Contents/Resources/symbols/"
cp -R resources/templates "dist/$APP_NAME.app/Contents/Resources/templates/"


mkdir -p "dist/$APP_NAME.app/Contents/Frameworks/ziamath/fonts"
cp "resources/STIXTwoMath-Regular.ttf" "dist/$APP_NAME.app/Contents/Frameworks/ziamath/fonts/"

mkdir -p "dist/$APP_NAME.app/Contents/Frameworks/latex2mathml"
cp "resources/unimathsymbols.txt" "dist/$APP_NAME.app/Contents/Frameworks/latex2mathml/"

echo
echo '****************************************'
echo 'Optimizing application...'
echo '****************************************'

rm -R "dist/$APP_NAME.app/Contents/Frameworks/PyQt5/uic"
rm -R "dist/$APP_NAME.app/Contents/Frameworks/PyQt5/Qt5/translations"

rm -R "dist/$APP_NAME.app/Contents/Frameworks/PyQt5/Qt5/lib/QtNetwork.framework"
rm -R "dist/$APP_NAME.app/Contents/Frameworks/PyQt5/Qt5/lib/QtQml.framework"
rm -R "dist/$APP_NAME.app/Contents/Frameworks/PyQt5/Qt5/lib/QtQmlModels.framework"
rm -R "dist/$APP_NAME.app/Contents/Frameworks/PyQt5/Qt5/lib/QtQuick.framework"
rm -R "dist/$APP_NAME.app/Contents/Frameworks/PyQt5/Qt5/lib/QtSvg.framework"
rm -R "dist/$APP_NAME.app/Contents/Frameworks/PyQt5/Qt5/lib/QtWebSockets.framework"

rm "dist/$APP_NAME.app/Contents/Frameworks/QtNetwork"
rm "dist/$APP_NAME.app/Contents/Frameworks/QtQml"
rm "dist/$APP_NAME.app/Contents/Frameworks/QtQmlModels"
rm "dist/$APP_NAME.app/Contents/Frameworks/QtQuick"
rm "dist/$APP_NAME.app/Contents/Frameworks/QtSvg"
rm "dist/$APP_NAME.app/Contents/Frameworks/QtWebSockets"

rm "dist/$APP_NAME.app/Contents/Resources/QtNetwork"
rm "dist/$APP_NAME.app/Contents/Resources/QtQml"
rm "dist/$APP_NAME.app/Contents/Resources/QtQmlModels"
rm "dist/$APP_NAME.app/Contents/Resources/QtQuick"
rm "dist/$APP_NAME.app/Contents/Resources/QtSvg"
rm "dist/$APP_NAME.app/Contents/Resources/QtWebSockets"

rm "dist/$APP_NAME.app/Contents/Frameworks/libcrypto.3.dylib"
rm "dist/$APP_NAME.app/Contents/Frameworks/libssl.3.dylib"
rm "dist/$APP_NAME.app/Contents/Resources/libcrypto.3.dylib"
rm "dist/$APP_NAME.app/Contents/Resources/libssl.3.dylib"

#rm -R "dist/$APP_NAME.app/Contents/Frameworks/PyQt5/Qt5/plugins/bearer"
rm -R "dist/$APP_NAME.app/Contents/Frameworks/PyQt5/Qt5/plugins/generic"
rm -R "dist/$APP_NAME.app/Contents/Frameworks/PyQt5/Qt5/plugins/iconengines"
#rm -R "dist/$APP_NAME.app/Contents/Frameworks/PyQt5/Qt5/plugins/imageformats"
rm -R "dist/$APP_NAME.app/Contents/Frameworks/PyQt5/Qt5/plugins/platformthemes"

mv "dist/$APP_NAME.app/Contents/Frameworks/PyQt5/Qt5/plugins/imageformats/libqjpeg.dylib" ./libqjpeg.dylib
mv "dist/$APP_NAME.app/Contents/Frameworks/PyQt5/Qt5/plugins/imageformats/libqtiff.dylib" ./libqtiff.dylib
rm -R "dist/$APP_NAME.app/Contents/Frameworks/PyQt5/Qt5/plugins/imageformats"
mkdir "dist/$APP_NAME.app/Contents/Frameworks/PyQt5/Qt5/plugins/imageformats"
mv ./libqjpeg.dylib "dist/$APP_NAME.app/Contents/Frameworks/PyQt5/Qt5/plugins/imageformats/"
mv ./libqtiff.dylib "dist/$APP_NAME.app/Contents/Frameworks/PyQt5/Qt5/plugins/imageformats/"

rm -R "dist/$APP_NAME.app/Contents/Frameworks/PyQt5/Qt5/plugins/platforms/libqminimal.dylib"
rm -R "dist/$APP_NAME.app/Contents/Frameworks/PyQt5/Qt5/plugins/platforms/libqoffscreen.dylib"
rm -R "dist/$APP_NAME.app/Contents/Frameworks/PyQt5/Qt5/plugins/platforms/libqwebgl.dylib"

echo
echo '****************************************'
echo 'Creating DMG...'
echo '****************************************'

mkdir dist/dmg
mkdir "dist/dmg/$APP_NAME"
mv "dist/$APP_NAME.app" "dist/dmg/$APP_NAME/"
#mv "dist/presets.db" "dist/dmg/$APP_NAME/"

ln -s /Applications "dist/dmg/Applications"
hdiutil create -fs HFSX -format UDZO "dist/$APP_NAME.dmg" -imagekey zlib-level=9 -srcfolder "dist/dmg" -volname "$APP_NAME"

mv "dist/dmg/$APP_NAME/$APP_NAME.app" dist/
#mv "dist/dmg/$APP_NAME/presets.db" dist/

rm -R dist/dmg

echo
echo '****************************************'
echo 'Done.'
echo '****************************************'
echo
