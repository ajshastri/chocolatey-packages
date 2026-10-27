$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/21.0.13.0.3+5/bellsoft-jre21.0.13.0.3+5-windows-amd64.msi'
  Checksum64 = 'e5f31ff2bcfa7b15df775ca5a2a546861d081425ca5eea267634fbc76da11fd1'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
