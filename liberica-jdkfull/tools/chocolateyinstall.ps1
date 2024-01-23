$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/21.0.2+14/bellsoft-jdk21.0.2+14-windows-amd64-full.msi'
  Checksum64 = '6ca389fd214000c3c64e8fe21beed780c9b9f1cc'
  ChecksumType64 = 'sha1'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
