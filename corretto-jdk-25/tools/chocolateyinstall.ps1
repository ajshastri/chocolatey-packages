$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://corretto.aws/downloads/resources/25.0.1.9.1/amazon-corretto-25.0.1.9.1-windows-x64.msi'
  Checksum64 = '9577a43930de43c6ca85356c62bcb8be'
  ChecksumType64 = 'md5'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
