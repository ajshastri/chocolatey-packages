$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://corretto.aws/downloads/resources/21.0.1.12.1/amazon-corretto-21.0.1.12.1-windows-x64.msi'
  Checksum64 = '58899be77c0992cce9317389de1cbeb8'
  ChecksumType64 = 'md5'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
