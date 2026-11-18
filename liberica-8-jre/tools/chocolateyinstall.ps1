$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/8u514+5/bellsoft-jre8u514+5-windows-amd64.msi'
  Checksum64 = 'a18c3082008f185570770d57fedb676fcaf00f66ac236277e797c359f40f2304'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
