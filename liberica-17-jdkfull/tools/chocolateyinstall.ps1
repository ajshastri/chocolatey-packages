$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/17.0.21.0.3+5/bellsoft-jdk17.0.21.0.3+5-windows-amd64-full.msi'
  Checksum64 = 'bd6f283e16f837cf0488867f7f400d59301f6a46f9e9e55bad93f427bf03ad3f'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
