$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit       = 'https://github.com/SAP/SapMachine/releases/download/sapmachine-25.0.5.1/sapmachine-jre-25.0.5.1_windows-x64_bin.msi'
  Checksum64     = '740d359ba1f870198d2a502c6d6a318b4280183b73d074fc30922eaaf7994e8f'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
