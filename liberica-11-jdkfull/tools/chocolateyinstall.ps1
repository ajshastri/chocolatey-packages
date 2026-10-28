$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/11.0.33.0.3+7/bellsoft-jdk11.0.33.0.3+7-windows-amd64-full.msi'
  Checksum64 = 'fa8465813c4b5bedf0db8da5881d76b44e0d89363076cbcde25d0f001589fea3'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
