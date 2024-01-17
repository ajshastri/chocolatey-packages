$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/11.0.22+12/bellsoft-jre11.0.22+12-windows-amd64.msi'
  Checksum64 = '373bb6c10a05a75e2145f4f3c38eb698b089f82f'
  ChecksumType64 = 'sha1'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
