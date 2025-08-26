$ErrorActionPreference = 'Stop'
$toolsDir   = "$(Split-Path -parent $MyInvocation.MyCommand.Definition)"
               
$url64      = 'https://cdn.azul.com/zulu/bin/zulu17.60.17-ca-fx-jdk17.0.16-win_x64.msi'

$packageArgs = @{
  packageName   = $env:ChocolateyPackageName
  unzipLocation = $toolsDir
  fileType      = 'msi'
  url           = $url
  url64bit      = $url64

  softwareName  = 'Zulu 17*'
  checksum64    = '706437034c74398f2b623ff8a52576864684f7f837121a5ad7de1371c5737847'
  checksumType64= 'sha256'

  silentArgs    = "ADDLOCAL=ZuluInstallation,FeatureEnvironment /qn /norestart"
  validExitCodes= @(0)
}

Install-ChocolateyPackage @packageArgs

