$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/11.0.32.1+1/bellsoft-jre11.0.32.1+1-windows-amd64.msi'
  Checksum64 = 'e8e638d9a92bee253c7a87289c2d10aeb76541f718efd3511c4a2f24cc16b1c5'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
