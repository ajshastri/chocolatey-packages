$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://corretto.aws/downloads/resources/11.0.22.7.1/amazon-corretto-11.0.22.7.1-windows-x64-jdk.msi'
  Checksum64 = '59c529c07d2a79896ab67bd04d1e8fef'
  ChecksumType64 = 'md5'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
