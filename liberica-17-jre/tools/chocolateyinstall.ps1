$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/17.0.21.1+5/bellsoft-jre17.0.21.1+5-windows-amd64.msi'
  Checksum64 = '319854647bc8d60dde9afc578b7602b8fb3ad4de3dfcacff85b86ef39a437751'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
