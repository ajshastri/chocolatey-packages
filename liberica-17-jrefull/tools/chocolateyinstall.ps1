$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/17.0.12+10/bellsoft-jre17.0.12+10-windows-amd64-full.msi'
  Checksum64 = 'efcdaf1b874a4085a11eb23a39973c3d9014e5c4'
  ChecksumType64 = 'sha1'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
