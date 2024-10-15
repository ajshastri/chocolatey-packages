$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/SAP/SapMachine/releases/download/sapmachine-21.0.5/sapmachine-jre-21.0.5_windows-x64_bin.msi'
  Checksum64 = '872275b908e33e97049113e711de0f4d132cc1c34d2e05d8a2eb34241d910acf'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
