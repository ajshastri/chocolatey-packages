$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/17.0.21.1+5/bellsoft-jdk17.0.21.1+5-windows-amd64-full.msi'
  Checksum64 = '80bfd8967bf5363b6dd7a348da865b66d74e375cecb7518ca1a65dc1ccbfe4b2'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
