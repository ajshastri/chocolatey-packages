$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://corretto.aws/downloads/resources/8.514.01.1/amazon-corretto-8.514.01.1-windows-x64-jdk.msi'
  Checksum64 = '4372a4f791779128da79bf59fa832dcbc1439edeafbb9be5df64881c220696fa'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
