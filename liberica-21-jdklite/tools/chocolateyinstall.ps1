$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/21.0.13.0.3+5/bellsoft-jdk21.0.13.0.3+5-windows-amd64-lite.msi'
  Checksum64 = 'd336d0f2fd1b53ad1650aae83d41169dce78daab3f4ab749e1fb0313dc31d973'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
