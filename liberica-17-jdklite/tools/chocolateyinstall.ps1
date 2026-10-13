$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/17.0.20.1+1/bellsoft-jdk17.0.20.1+1-windows-amd64-lite.msi'
  Checksum64 = '0c0f4ef917aa2afa4d8eef2d47d8022d82c2fc1ac9e182ee2e6ff3b78c3b4fc5'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
