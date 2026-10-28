$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/17.0.21.0.3+5/bellsoft-jre17.0.21.0.3+5-windows-amd64-full.msi'
  Checksum64 = '5ae48fe3d1ae86cad5ece8d2c70df1cb5f9d2fea55215311a3441f472c104c87'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
