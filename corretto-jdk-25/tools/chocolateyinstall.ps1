$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://corretto.aws/downloads/resources/25.0.5.0.10/amazon-corretto-25.0.5.0.10-windows-x64.msi'
  Checksum64 = 'd6b85a0562080ade28c7b757c0b1902cc8e71687b8fbad36c5a6c1b3c4f0f167'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
