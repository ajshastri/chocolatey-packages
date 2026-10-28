$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/17.0.21.0.3+5/bellsoft-jre17.0.21.0.3+5-windows-amd64.msi'
  Checksum64 = 'ddb12d0bb8805ade1876878e0d6f380b56f2814ff40911abc57aadd0ec30e06b'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
