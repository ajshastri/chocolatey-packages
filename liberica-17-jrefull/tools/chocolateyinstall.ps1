$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/17.0.21.0.2+5/bellsoft-jre17.0.21.0.2+5-windows-amd64-full.msi'
  Checksum64 = '963ccb75c39330358ea0074a69414e10c7e59db4f52f936a4c5dd4ae15daa00a'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
