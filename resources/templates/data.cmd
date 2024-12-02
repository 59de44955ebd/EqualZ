@echo off

for /R %%f in (*.png) do (
	echo %%f
	exiftool -Latex "%%f"
)
