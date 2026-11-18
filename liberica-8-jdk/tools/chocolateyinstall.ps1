$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/8u514+5/bellsoft-jdk8u514+5-windows-amd64.msi'
  Checksum64 = '3ed06a0875c3bb8b1c069ebebd905ae3195843187ccfd7d629f2970607aeebd8'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
