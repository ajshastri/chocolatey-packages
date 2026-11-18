$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/21.0.13.1+5/bellsoft-jre21.0.13.1+5-windows-amd64.msi'
  Checksum64 = '0fd283768c05d97751de65b7e89c50a5159f6d3e456bccb4dc3ac3affdd7332d'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
