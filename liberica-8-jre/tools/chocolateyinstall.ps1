$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/8u513+5/bellsoft-jre8u513+5-windows-amd64.msi'
  Checksum64 = '0805ecb7a426b14e03601d73b4acc233cf487a25e9671402752ef9f84cc2e98a'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
