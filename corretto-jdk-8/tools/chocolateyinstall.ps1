$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://corretto.aws/downloads/resources/8.512.09.1/amazon-corretto-8.512.09.1-windows-x64-jdk.msi'
  Checksum64 = '26c8e757404aff06370b427c59315b48bcc78d41377aec068c6e99709aede2d2'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
