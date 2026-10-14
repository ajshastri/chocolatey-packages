$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/17.0.20.1+1/bellsoft-jdk17.0.20.1+1-windows-amd64-full.msi'
  Checksum64 = '518a70659066353fa6958bbed6f1e88f4bfd758827e17d96f0cfdabbda58290f'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
