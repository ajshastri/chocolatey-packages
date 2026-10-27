$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/25.0.5.0.3+5/bellsoft-jre25.0.5.0.3+5-windows-amd64.msi'
  Checksum64 = '3fa18afbe85827a4dd42304b6e7cf77bdad212aa65df83c9ad1b23cad7df35f5'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
