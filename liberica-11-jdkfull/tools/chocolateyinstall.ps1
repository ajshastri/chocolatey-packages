$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/11.0.23+10/bellsoft-jdk11.0.23+10-windows-amd64-full.msi'
  Checksum64 = 'd907a26c2e45dad75bbc82dc1935e7aa72a78112'
  ChecksumType64 = 'sha1'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
