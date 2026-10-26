$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/17.0.21.0.2+5/bellsoft-jdk17.0.21.0.2+5-windows-amd64.msi'
  Checksum64 = '149c595848d7c60dd7de91417bac5967c01712f7e61eb87c39cc781f9a5dcde0'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
