$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/17.0.20.1+1/bellsoft-jre17.0.20.1+1-windows-amd64.msi'
  Checksum64 = 'f54c90a6c2f4da7fc072143d1feb0330def7b3757e74eda9986c54446b00d15e'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
