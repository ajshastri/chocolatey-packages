$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://corretto.aws/downloads/resources/8.472.08.1/amazon-corretto-8.472.08.1-windows-x64-jdk.msi'
  Checksum64 = '6dcd9a0ee369f7d9ea9fce96c9f507ed'
  ChecksumType64 = 'md5'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
