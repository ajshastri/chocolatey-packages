$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/SAP/SapMachine/releases/download/sapmachine-17.0.13/sapmachine-jdk-17.0.13_windows-x64_bin.msi'
  Checksum64 = '11182205e2fc42a1c0480d2833d5f3f3b5b5508e041929371f4b8b4a254643be'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
