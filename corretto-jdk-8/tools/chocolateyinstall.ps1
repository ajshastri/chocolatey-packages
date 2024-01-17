$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://corretto.aws/downloads/resources/8.402.07.1/amazon-corretto-8.402.07.1-windows-x64-jdk.msi'
  Checksum64 = 'f41faf887847927565ce94c5f0159e87'
  ChecksumType64 = 'md5'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
