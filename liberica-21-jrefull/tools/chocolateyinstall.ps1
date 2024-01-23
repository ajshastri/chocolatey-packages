$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/21.0.2+14/bellsoft-jre21.0.2+14-windows-amd64-full.msi'
  Checksum64 = 'e3bdcb3fe931f2c2d05e3f3772bf63b1f52eef37'
  ChecksumType64 = 'sha1'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
