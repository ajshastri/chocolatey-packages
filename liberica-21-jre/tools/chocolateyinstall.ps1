$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/21.0.12.1+1/bellsoft-jre21.0.12.1+1-windows-amd64.msi'
  Checksum64 = 'a87d42f5fe1dcdd378fa08f94305023fa163e1bfbadc064827de1b0ca7bed5a3'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
