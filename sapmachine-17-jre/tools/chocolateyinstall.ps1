$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit       = 'https://github.com/SAP/SapMachine/releases/download/sapmachine-17.0.20.1/sapmachine-jre-17.0.20.1_windows-x64_bin.msi'
  Checksum64     = '45e3de0063ce8a19392dfc090d043e475e9160750fc42027ac9431c1f60b7c94'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
