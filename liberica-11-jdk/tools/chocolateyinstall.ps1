$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/11.0.23+10/bellsoft-jdk11.0.23+10-windows-amd64.msi'
  Checksum64 = 'd45c5cc04b60fc22c43c8cbe8ff5ac4d6535b6ca'
  ChecksumType64 = 'sha1'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
