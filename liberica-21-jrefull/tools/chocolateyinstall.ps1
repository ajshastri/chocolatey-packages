$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/21.0.13.0.3+5/bellsoft-jre21.0.13.0.3+5-windows-amd64-full.msi'
  Checksum64 = '987925937968530801f41dba27c3374650bad273e9a20aac749ecd35434c5c80'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
