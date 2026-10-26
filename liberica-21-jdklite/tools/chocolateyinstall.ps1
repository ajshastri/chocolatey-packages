$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/21.0.13.0.2+5/bellsoft-jdk21.0.13.0.2+5-windows-amd64-lite.msi'
  Checksum64 = '9e3bc1e7872910d848d926809c46817625b43d34f464e981d17b36300fadecc2'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
