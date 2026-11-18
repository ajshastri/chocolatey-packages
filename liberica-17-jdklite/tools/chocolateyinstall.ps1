$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/17.0.21.1+5/bellsoft-jdk17.0.21.1+5-windows-amd64-lite.msi'
  Checksum64 = '6ae6532fc1f43e0c1e3d9404247663c71c70ad9b5f028117b02d97954718d406'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
