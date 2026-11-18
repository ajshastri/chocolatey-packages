$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/21.0.13.1+5/bellsoft-jre21.0.13.1+5-windows-amd64-full.msi'
  Checksum64 = '4e1f334e0bb91eb63c720f0f747c6b3044cdc9c0109264388fd8de1af872081b'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
