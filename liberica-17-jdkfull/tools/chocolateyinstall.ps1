$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/17.0.21.0.2+5/bellsoft-jdk17.0.21.0.2+5-windows-amd64-full.msi'
  Checksum64 = '3e412fc921bb06c56fbed623c1822ddb0e1a1242f1b6873c27ca9cb0f6d81fbb'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
