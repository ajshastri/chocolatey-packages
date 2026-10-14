$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/21.0.12.1+1/bellsoft-jre21.0.12.1+1-windows-amd64-full.msi'
  Checksum64 = 'ac8dc5d244d869eb971f78fb97b48553a68e10af52280e916d7fe3e98575387a'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
