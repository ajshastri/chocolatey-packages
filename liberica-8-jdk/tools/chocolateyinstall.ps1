$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/8u513+5/bellsoft-jdk8u513+5-windows-amd64.msi'
  Checksum64 = '0fd029de3947ca142abd92568b7c93428c654f0fa576ce2b4ebeabe07949cd4b'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
