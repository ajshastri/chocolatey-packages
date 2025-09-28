$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://corretto.aws/downloads/resources/25.0.0.36.2/amazon-corretto-25.0.0.36.2-windows-x64.msi'
  Checksum64 = '85c20c042c24407a550bd5171755aaf5'
  ChecksumType64 = 'md5'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
