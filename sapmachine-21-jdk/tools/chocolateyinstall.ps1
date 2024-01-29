$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/SAP/SapMachine/releases/download/sapmachine-21.0.2/sapmachine-jdk-21.0.2_windows-x64_bin.msi'
  Checksum64 = 'f3f77b87051e7b42768ab4c3fd8b0f2e5adbd63dbab8cee67e2bec4c43960d50'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
