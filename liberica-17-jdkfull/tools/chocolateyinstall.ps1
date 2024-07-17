$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/17.0.12+10/bellsoft-jdk17.0.12+10-windows-amd64-full.msi'
  Checksum64 = 'c2803e4c79f61a36a3737b65b9e50d06b28f5302'
  ChecksumType64 = 'sha1'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
