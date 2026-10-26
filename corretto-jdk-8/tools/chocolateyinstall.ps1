$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://corretto.aws/downloads/resources/8.512.08.1/amazon-corretto-8.512.08.1-windows-x64-jdk.msi'
  Checksum64 = '0211103254488c5795b392629fb28d93e1a37ec39bab02ce873b0fc465cb54cf'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
