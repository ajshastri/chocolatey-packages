$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/11.0.33.1+5/bellsoft-jre11.0.33.1+5-windows-amd64.msi'
  Checksum64 = '7ced23c3e3bafb73b783ef47c1d017f53dc20f2ac7742b17796ab6dedaddcf5a'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
