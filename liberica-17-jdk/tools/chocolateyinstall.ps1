$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/17.0.20.1+1/bellsoft-jdk17.0.20.1+1-windows-amd64.msi'
  Checksum64 = 'ecdf64ad3454fe774f8e9c59ffe89cb773ab822257e913bf978b2d8ba1aeef62'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
