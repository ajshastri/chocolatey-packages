$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/21.0.2+14/bellsoft-jre21.0.2+14-windows-amd64.msi'
  Checksum64 = 'be605ada5daadc44c4f59407e6d97e301dae955c'
  ChecksumType64 = 'sha1'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
