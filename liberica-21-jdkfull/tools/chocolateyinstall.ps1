$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/21.0.13.1+5/bellsoft-jdk21.0.13.1+5-windows-amd64-full.msi'
  Checksum64 = '2e890cbbb510fbbdfc226f641c9484c1f73e7b0172ddfb0cc0360bf5c77424ec'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
