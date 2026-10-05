$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://corretto.aws/downloads/resources/11.0.32.12.1/amazon-corretto-11.0.32.12.1-windows-x64.msi'
  Checksum64 = '0eb7d099a841480ecc9d5303948c174b4fe60448f375f4289a150d4d3628c193'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
