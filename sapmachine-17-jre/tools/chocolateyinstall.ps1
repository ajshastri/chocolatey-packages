$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/SAP/SapMachine/releases/download/sapmachine-17.0.11/sapmachine-jre-17.0.11_windows-x64_bin.msi'
  Checksum64 = 'bd95a541232cc878f2f5a33aa860c27d3bdf78effbaacc940f88ada08e0f870d'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
