$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/8u513+9/bellsoft-jre8u513+9-windows-amd64.msi'
  Checksum64 = '14a4b4981fe5bd6459e27f79b24e791fcaf6630c69629a39b57830453e37adb7'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
