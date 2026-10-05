$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://corretto.aws/downloads/resources/8.504.04.1/amazon-corretto-8.504.04.1-windows-x64-jre.msi'
  Checksum64 = '9dd9d6c9024f34b93ca75026ceffe8f934865cf0eed338c2ad35950b3e03885c'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
