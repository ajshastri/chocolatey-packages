$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/11.0.23+10/bellsoft-jre11.0.23+10-windows-amd64-full.msi'
  Checksum64 = '1dec8ef529eaf366fe9175586a2d7dfd165d3a4d'
  ChecksumType64 = 'sha1'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
