$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/SAP/SapMachine/releases/download/sapmachine-11.0.23/sapmachine-jre-11.0.23_windows-x64_bin.msi'
  Checksum64 = '15f02c0e0a28a3152213e9b3043c43dd298baf81a5e09d515a4738b7b5284d26'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
