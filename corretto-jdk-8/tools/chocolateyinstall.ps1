$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://corretto.aws/downloads/resources/8.432.06.1/amazon-corretto-8.432.06.1-windows-x64-jdk.msi'
  Checksum64 = '1ae4f87b20ac4536b51161dc0d472fca'
  ChecksumType64 = 'md5'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
