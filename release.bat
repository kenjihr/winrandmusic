pyinstaller main.py --onefile --name wintimeweatherteller
xcopy .\translations .\dist\translations /E /I /Y
copy .\config.json .\dist\
powershell.exe Compress-Archive -Path .\dist\* -DestinationPath .\dist.zip