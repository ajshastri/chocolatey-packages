$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/11.0.32.1+1/bellsoft-jre11.0.32.1+1-windows-amd64-full.msi'
  Checksum64 = '4822fde7a1d578d0313a42d7471871bc1639922f63029399c37eb456b7631308'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
