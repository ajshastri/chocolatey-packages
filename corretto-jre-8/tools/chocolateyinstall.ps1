$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://corretto.aws/downloads/resources/8.402.08.1/amazon-corretto-8.402.08.1-windows-x64-jre.msi'
  Checksum64 = '2ae97e38ae5b96ba65ae303cf91f36e0'
  ChecksumType64 = 'md5'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
