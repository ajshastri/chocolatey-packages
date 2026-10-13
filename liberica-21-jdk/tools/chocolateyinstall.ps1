$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/21.0.12.1+1/bellsoft-jdk21.0.12.1+1-windows-amd64.msi'
  Checksum64 = 'f61e915b873d6d6f56996446f67d4266f715e4491650775059ac977bc557d606'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
