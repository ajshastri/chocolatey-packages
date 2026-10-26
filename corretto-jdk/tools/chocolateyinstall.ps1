$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://corretto.aws/downloads/resources/25.0.5.0.9/amazon-corretto-25.0.5.0.9-windows-x64.msi'
  Checksum64 = '5f3e65eabbca922507117bdcd6831357822aed36cd020a08ec61e44d8afbb77b'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
