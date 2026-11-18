$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://corretto.aws/downloads/resources/17.0.21.1.2/amazon-corretto-17.0.21.1.2-windows-x64.msi'
  Checksum64 = 'c9dbb603e5b4dc3566e1988417755cdebe5a44069cd83f94933c2c3429ab1851'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
