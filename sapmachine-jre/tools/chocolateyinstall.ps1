$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit       = 'https://github.com/SAP/SapMachine/releases/download/sapmachine-21.0.12.1/sapmachine-jre-21.0.12.1_windows-x64_bin.msi'
  Checksum64     = '1d03c2ca103c645a576f83662a46fa29a6bf7fcb616e1b6a11c38756a2f8921b'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
