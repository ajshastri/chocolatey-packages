$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://corretto.aws/downloads/resources/11.0.33.0.10/amazon-corretto-11.0.33.0.10-windows-x64.msi'
  Checksum64 = 'bc45e70bee0c553ce47dd8987e93fc130eaa39fb00f5e40ede7d252aeda8a17e'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
