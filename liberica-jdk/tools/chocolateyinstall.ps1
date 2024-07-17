$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/21.0.4+9/bellsoft-jdk21.0.4+9-windows-amd64.msi'
  Checksum64 = '6e6d97bf8c742e78240a7dad8cac9ff0aea3a5ea'
  ChecksumType64 = 'sha1'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
