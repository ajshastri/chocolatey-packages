$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/SAP/SapMachine/releases/download/sapmachine-17.0.11/sapmachine-jdk-17.0.11_windows-x64_bin.msi'
  Checksum64 = '0da034677b398e226a27a0c06d36ab4cae6eb6fdc89891a775822d3c32d111e1'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
