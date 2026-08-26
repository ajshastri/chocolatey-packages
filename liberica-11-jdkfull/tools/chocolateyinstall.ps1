$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/11.0.32.1+1/bellsoft-jdk11.0.32.1+1-windows-amd64-full.msi'
  Checksum64 = 'f977b88932a7fad696e3c9d3f135c39e15aa064d'
  ChecksumType64 = 'sha1'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
