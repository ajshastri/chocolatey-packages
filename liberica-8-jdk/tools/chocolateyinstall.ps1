$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/8u513+9/bellsoft-jdk8u513+9-windows-amd64.msi'
  Checksum64 = '5aa8a1cecd1b2f89ac9e66f64fcfb938722c88f30e8e8c96f2080ae59b9c61fa'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
