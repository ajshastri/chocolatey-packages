$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/11.0.33.0.2+5/bellsoft-jdk11.0.33.0.2+5-windows-amd64.msi'
  Checksum64 = 'efa4c0d1c532b7685958965fcfde081e9bf00a0688a6d104204eacb8c579ee19'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
