$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit       = 'https://github.com/SAP/SapMachine/releases/download/sapmachine-21.0.13.0.3/sapmachine-jre-21.0.13.0.3_windows-x64_bin.msi'
  Checksum64     = 'b1a107c494ad743aae61559b371c6fa2fb420cd6695c3b663ef15877fe680b64'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
