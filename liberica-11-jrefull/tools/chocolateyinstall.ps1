$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/11.0.33.0.3+7/bellsoft-jre11.0.33.0.3+7-windows-amd64-full.msi'
  Checksum64 = 'e9a10caa33c9bba8ae257ede75b94142ddc8bc78061b6cf52333249f6cf6f54f'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
