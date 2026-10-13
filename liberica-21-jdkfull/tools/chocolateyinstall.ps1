$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/21.0.12.1+1/bellsoft-jdk21.0.12.1+1-windows-amd64-full.msi'
  Checksum64 = '56a0fa617ea7806a0482593a8c7ac1d0d238519dc7887239b16adf8b32ca9dbe'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
