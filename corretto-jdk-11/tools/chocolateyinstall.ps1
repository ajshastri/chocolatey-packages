$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://corretto.aws/downloads/resources/11.0.33.0.9/amazon-corretto-11.0.33.0.9-windows-x64.msi'
  Checksum64 = '9759ed7ce0698f971cc04dc9c2d3a717b4f03182eff7121ca3586729fe2ecafa'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
