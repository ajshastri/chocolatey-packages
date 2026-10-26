$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/21.0.13.0.2+5/bellsoft-jre21.0.13.0.2+5-windows-amd64-full.msi'
  Checksum64 = '02b601d8d42ca239f34e1534f9ce27bcda79b8d21f03f0e82f822f16fcaf680b'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
