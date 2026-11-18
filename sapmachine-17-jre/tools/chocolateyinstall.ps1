$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit       = 'https://github.com/SAP/SapMachine/releases/download/sapmachine-17.0.21.1/sapmachine-jre-17.0.21.1_windows-x64_bin.msi'
  Checksum64     = '628a2e200e87345d261f430bc3033441b6364cc4a90ba7f84f8bfc0c9484264e'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
