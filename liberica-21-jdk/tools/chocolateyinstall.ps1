$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/21.0.13.0.3+5/bellsoft-jdk21.0.13.0.3+5-windows-amd64.msi'
  Checksum64 = 'd5b6b0514ab0f3b31e1960e0f9733fe41e87880a3bec6d0827a7072248fc41d8'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
