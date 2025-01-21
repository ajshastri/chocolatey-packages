$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://corretto.aws/downloads/resources/17.0.13.11.1/amazon-corretto-17.0.13.11.1-windows-x64.msi'
  Checksum64 = 'a263fa6274d694d5ca018a9c673ce684'
  ChecksumType64 = 'md5'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
