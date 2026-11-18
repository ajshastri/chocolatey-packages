$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://corretto.aws/downloads/resources/8.514.01.1/amazon-corretto-8.514.01.1-windows-x64-jre.msi'
  Checksum64 = '2e907565e84aca4621ac2aac1c3532afe0b21625207c8f5072352bfcfe3f976d'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
