$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/25.0.5.0.3+5/bellsoft-jdk25.0.5.0.3+5-windows-amd64-lite.msi'
  Checksum64 = 'e72529b2868c944111b2ed965d66420b3a0f5f7dd637a087d616a689c2562996'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
