$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/17.0.21.1+5/bellsoft-jre17.0.21.1+5-windows-amd64-full.msi'
  Checksum64 = 'c9b654f18b9decfc8ee00feac3f4458233642813b894de926e76144462d50576'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
