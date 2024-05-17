$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/11.0.23+12/bellsoft-jdk11.0.23+12-windows-amd64-full.msi'
  Checksum64 = 'e2706cb08a0a910e45f96e95c68e4647f9eca1ad'
  ChecksumType64 = 'sha1'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
