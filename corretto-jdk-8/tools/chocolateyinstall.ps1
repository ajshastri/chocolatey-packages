$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://corretto.aws/downloads/resources/8.402.08.1/amazon-corretto-8.402.08.1-windows-x64-jdk.msi'
  Checksum64 = '490227fc995a0f6af6dcdda6bff2c8aa'
  ChecksumType64 = 'md5'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
