$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://corretto.aws/downloads/resources/11.0.26.4.1/amazon-corretto-11.0.26.4.1-windows-x64.msi'
  Checksum64 = 'cdd32bc5de24fff746f909811fad5725'
  ChecksumType64 = 'md5'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
