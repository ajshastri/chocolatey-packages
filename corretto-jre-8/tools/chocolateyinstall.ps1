$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://corretto.aws/downloads/resources/8.432.06.1/amazon-corretto-8.432.06.1-windows-x64-jre.msi'
  Checksum64 = '50c16f085ab89b70f0c0aa3b7c2034ea'
  ChecksumType64 = 'md5'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
