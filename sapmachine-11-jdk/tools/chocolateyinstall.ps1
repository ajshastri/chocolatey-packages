$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/SAP/SapMachine/releases/download/sapmachine-11.0.23/sapmachine-jdk-11.0.23_windows-x64_bin.msi'
  Checksum64 = 'abaa676822e192ba458c27dca40f3d1122fe318387801a36081dbbecd2895ab6'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
