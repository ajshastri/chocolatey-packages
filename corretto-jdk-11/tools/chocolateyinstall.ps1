$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://corretto.aws/downloads/resources/11.0.33.1.1/amazon-corretto-11.0.33.1.1-windows-x64.msi'
  Checksum64 = '0eacaf8e4ecbcdb363e91a8483d41a6b4d00ff9999d391b92b139cba4ac72a79'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
