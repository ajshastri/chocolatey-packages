$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://corretto.aws/downloads/resources/21.0.12.12.1/amazon-corretto-21.0.12.12.1-windows-x64.msi'
  Checksum64 = '1e60e8033e843b29692a56a4dbaf5bcff13f39968fdd467699c14ae4ac88fad6'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
