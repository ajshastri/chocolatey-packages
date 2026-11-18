$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/21.0.13.1+5/bellsoft-jdk21.0.13.1+5-windows-amd64.msi'
  Checksum64 = '3340f97b56909808a8a5cb5296c5abd58fd64b999949fea604a592b1eb476295'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
