$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/8u402+7/bellsoft-jdk8u402+7-windows-amd64.msi'
  Checksum64 = '461df49997221cd133e56db1169f78ef0d517fd8'
  ChecksumType64 = 'sha1'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
