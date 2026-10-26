$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit       = 'https://github.com/SAP/SapMachine/releases/download/sapmachine-17.0.21.0.2/sapmachine-jdk-17.0.21.0.2_windows-x64_bin.msi'
  Checksum64     = 'd0edb9a32d2746b2b1892eec5d0e699e0e3fcbb86356fcc69435796c5d411877'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
