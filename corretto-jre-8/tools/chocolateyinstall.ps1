$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://corretto.aws/downloads/resources/8.392.08.1/amazon-corretto-8.392.08.1-windows-x64-jre.msi'
  Checksum64 = 'b1b44d0389b328d787f4b2c1714b509d'
  ChecksumType64 = 'md5'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
