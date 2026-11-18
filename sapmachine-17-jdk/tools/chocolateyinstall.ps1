$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit       = 'https://github.com/SAP/SapMachine/releases/download/sapmachine-17.0.21.1/sapmachine-jdk-17.0.21.1_windows-x64_bin.msi'
  Checksum64     = 'b5d9a30a5105a4b051bdb98e50ad7b5a6eb5c2811f9024d04346bf98e0c2fc10'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
