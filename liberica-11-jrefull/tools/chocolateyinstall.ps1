$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/11.0.33.1+5/bellsoft-jre11.0.33.1+5-windows-amd64-full.msi'
  Checksum64 = '3f9ffe071d0f1918a784ff7f205bcfff6aec541d765170eaf780f848223bb853'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
