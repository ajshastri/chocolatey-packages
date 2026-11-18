$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit       = 'https://github.com/SAP/SapMachine/releases/download/sapmachine-21.0.13.1/sapmachine-jre-21.0.13.1_windows-x64_bin.msi'
  Checksum64     = '8f1f16fa95c5d2f5de0ea0ea85c8172e2cc2271e7fd5bd7b26012c0c328c7211'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
