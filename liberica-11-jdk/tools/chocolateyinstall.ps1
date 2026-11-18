$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/11.0.33.1+5/bellsoft-jdk11.0.33.1+5-windows-amd64.msi'
  Checksum64 = '72dd31ba611e2e17939ce644eeb2944fd0cb57d7f3fc512b7ed448d2fbf352af'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
