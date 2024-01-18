$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://corretto.aws/downloads/resources/17.0.10.7.1/amazon-corretto-17.0.10.7.1-windows-x64-jdk.msi'
  Checksum64 = '2bc47187eea0e84dae732013b762148d5'
  ChecksumType64 = 'md5'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
