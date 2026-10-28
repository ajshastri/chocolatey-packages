$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/17.0.21.0.3+5/bellsoft-jdk17.0.21.0.3+5-windows-amd64-lite.msi'
  Checksum64 = '4a16be568be982ccf4ba25c407ec3890b6f2378fa6ef99f9304408a3f6f63a13'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
