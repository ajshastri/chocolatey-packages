$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/25.0.5.1+5/bellsoft-jdk25.0.5.1+5-windows-amd64.msi'
  Checksum64 = '09a92e0f821b1bf2ae838ff9d67cbe07cc05925305e65127c2089a9c456d63ad'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
