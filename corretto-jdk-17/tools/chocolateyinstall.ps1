$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://corretto.aws/downloads/resources/17.0.21.0.10/amazon-corretto-17.0.21.0.10-windows-x64.msi'
  Checksum64 = '76898bd3270b47f580f2f9193552780138abd71aa653e01784305bce1732696c'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
