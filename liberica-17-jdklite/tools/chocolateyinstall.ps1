$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/17.0.21.0.2+5/bellsoft-jdk17.0.21.0.2+5-windows-amd64-lite.msi'
  Checksum64 = '7104f5344a3da87df0d40c6457919f4ee939d73bd63134fe8f63558f5a0c8079'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
