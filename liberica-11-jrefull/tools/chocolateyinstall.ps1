$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/11.0.33.0.2+5/bellsoft-jre11.0.33.0.2+5-windows-amd64-full.msi'
  Checksum64 = 'e819b4705c6d11d41cd11abcef1b591ff7e53809f94efce38e033e415586b022'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
