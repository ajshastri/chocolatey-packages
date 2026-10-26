$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/21.0.13.0.2+5/bellsoft-jdk21.0.13.0.2+5-windows-amd64.msi'
  Checksum64 = 'fdb39cba7893731513b80bb508c7675cf25d02adf2b0f92125604f3a16e984c4'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
