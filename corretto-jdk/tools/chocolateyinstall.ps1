$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://corretto.aws/downloads/resources/21.0.8.9.1/amazon-corretto-21.0.8.9.1-windows-x64.msi'
  Checksum64 = 'befa040ebc0d3073cd11454db9e27237'
  ChecksumType64 = 'md5'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
