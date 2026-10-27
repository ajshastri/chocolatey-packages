$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/25.0.5.0.3+5/bellsoft-jdk25.0.5.0.3+5-windows-amd64-full.msi'
  Checksum64 = '62b32135dfeaa3c6d3c2a91d7ed4c786e57d396a04c0c4eea41c69236022d40b'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
