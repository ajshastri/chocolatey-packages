$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://corretto.aws/downloads/resources/8.512.09.1/amazon-corretto-8.512.09.1-windows-x64-jre.msi'
  Checksum64 = '99fc8e0e277517b9201162940b7c5f6db7feb583f6d561e2fe1aa01ceb065d04'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
