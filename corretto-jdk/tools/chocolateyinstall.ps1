$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://corretto.aws/downloads/resources/21.0.5.11.1/amazon-corretto-21.0.5.11.1-windows-x64.msi'
  Checksum64 = 'ea3bd8e18bbc5e0ea1cd3c47e690ea2b'
  ChecksumType64 = 'md5'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
