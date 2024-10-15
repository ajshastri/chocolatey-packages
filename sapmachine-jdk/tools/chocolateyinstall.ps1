$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/SAP/SapMachine/releases/download/sapmachine-21.0.5/sapmachine-jdk-21.0.5_windows-x64_bin.msi'
  Checksum64 = 'f47da522c038a335eba20e9a6f6c7a7788076adfad66778dbb460a92b8a08092'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
