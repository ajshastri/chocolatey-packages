$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/SAP/SapMachine/releases/download/sapmachine-21.0.4/sapmachine-jdk-21.0.4_windows-x64_bin.msi'
  Checksum64 = 'baba51bf15a9c8aadeef8cf329401fdbfddb301ab5b05b4b1881a4c7d3f8decb'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
