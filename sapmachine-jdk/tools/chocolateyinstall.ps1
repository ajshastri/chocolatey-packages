$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit       = 'https://github.com/SAP/SapMachine/releases/download/sapmachine-21.0.12.1/sapmachine-jdk-21.0.12.1_windows-x64_bin.msi'
  Checksum64     = 'ecea698796b4605de6a467f0a330c98b58681e0df7d8a11b750d1f5389130862'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
