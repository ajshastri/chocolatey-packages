$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/SAP/SapMachine/releases/download/sapmachine-11.0.22/sapmachine-jdk-11.0.22_windows-x64_bin.msi'
  Checksum64 = 'f4677de9161ccf48254fc245a41b4987af7df19946f51e4782b650dfd56cd788'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
