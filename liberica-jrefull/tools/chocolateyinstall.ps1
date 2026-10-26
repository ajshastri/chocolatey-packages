$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/25.0.5.0.3+5/bellsoft-jre25.0.5.0.3+5-windows-amd64-full.msi'
  Checksum64 = 'dc38479e5e2d51c9aa459d108de8c40f56d03b16123085218874bd8d01cb3ec5'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
