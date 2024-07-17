$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/21.0.4+9/bellsoft-jdk21.0.4+9-windows-amd64-lite.msi'
  Checksum64 = 'bf532ea55f5bb3e77a8e5fc8b116819acd05f494'
  ChecksumType64 = 'sha1'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
