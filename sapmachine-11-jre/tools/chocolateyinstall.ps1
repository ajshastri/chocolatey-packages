$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/SAP/SapMachine/releases/download/sapmachine-11.0.24/sapmachine-jre-11.0.24_windows-x64_bin.msi'
  Checksum64 = '9ba1b89f3e5991eb3a11489580527c3f4dfe5ed35b2d4106abd94168fe2ca662'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
