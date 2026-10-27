$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/21.0.13.0.3+5/bellsoft-jdk21.0.13.0.3+5-windows-amd64-full.msi'
  Checksum64 = '500f4f612f2ed3356c676b9f62fde5cc4216f5d82b6cc7ceca74315f013300a7'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
