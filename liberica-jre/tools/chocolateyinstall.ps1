$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/25.0.5.1+5/bellsoft-jre25.0.5.1+5-windows-amd64.msi'
  Checksum64 = '26b11419ada30fad02ca744fe29171d128378e6d573abacfd245f247471e4f78'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
