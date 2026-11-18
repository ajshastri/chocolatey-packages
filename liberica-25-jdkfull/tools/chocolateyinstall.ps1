$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/25.0.5.1+5/bellsoft-jdk25.0.5.1+5-windows-amd64-full.msi'
  Checksum64 = 'eb73ca40cd76a03a37401dcfacf2d041eff26f21be5cbdd4b4c4f2c5c15b00e4'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
