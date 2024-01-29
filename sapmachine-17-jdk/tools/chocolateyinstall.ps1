$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/SAP/SapMachine/releases/download/sapmachine-17.0.10/sapmachine-jdk-17.0.10_windows-x64_bin.msi'
  Checksum64 = 'c363035e8bd0d031cd1cadb4d5094c88bcaa5956d021ff89d7389baca0208ebb'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
