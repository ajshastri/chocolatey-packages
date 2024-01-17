$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/17.0.10+13/bellsoft-jre17.0.10+13-windows-amd64-full.msi'
  Checksum64 = '513613f6b00e906bd305f2ffbe0af1a47207e320'
  ChecksumType64 = 'sha1'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
