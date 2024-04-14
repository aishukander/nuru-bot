Invoke-WebRequest -Uri "https://github.com/git-for-windows/git/releases/download/v2.33.1.windows.1/Git-2.33.1-64-bit.exe" -OutFile "git-installer.exe"
Start-Process -FilePath "git-installer.exe" -ArgumentList "/VERYSILENT /NORESTART /NOCANCEL /SP- /CLOSEAPPLICATIONS /RESTARTAPPLICATIONS /NOICONS /COMPONENTS=`"icons,ext\reg\shellhere,assoc,assoc_sh`"" -Wait

Remove-Item "git-installer.exe"

Start-Process powershell -ArgumentList "-Command pip install -r requirements.txt"