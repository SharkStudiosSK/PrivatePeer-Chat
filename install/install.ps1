# PrivatePeer Chat Windows Installer
Write-Host "Installing PrivatePeer Chat..." -ForegroundColor Green

# Install Python
if (-not (Test-Path "C:\Python310")) {
    Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.10.0/python-3.10.0-amd64.exe" -OutFile "$env:TEMP\python-installer.exe"
    Start-Process -Wait -FilePath "$env:TEMP\python-installer.exe" -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1"
}

# Install Tor
if (-not (Test-Path "C:\Tor")) {
    Invoke-WebRequest -Uri "https://torproject.org/dist/torbrowser/12.0.1/tor-win64-0.4.7.13.zip" -OutFile "$env:TEMP\tor.zip"
    Expand-Archive -Path "$env:TEMP\tor.zip" -DestinationPath "C:\Tor"
}

# Create virtual environment
python -m venv ppchat-env
.\ppchat-env\Scripts\activate
pip install -r requirements.txt

Write-Host "Installation complete!" -ForegroundColor Green
Write-Host "Run with: .\ppchat-env\Scripts\activate && python src\privatepeer_chat.py"