$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit       = 'https://github.com/SAP/SapMachine/releases/download/sapmachine-25.0.5.1/sapmachine-jdk-25.0.5.1_windows-x64_bin.msi'
  Checksum64     = '5e60080d4fbcd093adf204d913f21e51d0ce0d2b72239b90bc99225f4d69e49d'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
