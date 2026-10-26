$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit       = 'https://github.com/SAP/SapMachine/releases/download/sapmachine-21.0.13.0.2/sapmachine-jdk-21.0.13.0.2_windows-x64_bin.msi'
  Checksum64     = '2f9dba1c88626f142cb5f11a70d09f63a9d00dab227b0217ef1e4f898f79b64c'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
