$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/17.0.13+12/bellsoft-jdk17.0.13+12-windows-amd64-lite.msi'
  Checksum64 = '5c1c93bed0192a5b7e6536f99d6f5f35d7539fdc'
  ChecksumType64 = 'sha1'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
