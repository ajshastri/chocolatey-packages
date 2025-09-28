$ErrorActionPreference = 'Stop'
$toolsDir   = "$(Split-Path -parent $MyInvocation.MyCommand.Definition)"

$url64      = 'https://cdn.azul.com/zulu/bin/zulu25.28.85-ca-jdk25.0.0-win_x64.msi'

$packageArgs = @{
  packageName   = $env:ChocolateyPackageName
  unzipLocation = $toolsDir
  fileType      = 'msi'
  url           = $url
  url64bit      = $url64

  softwareName  = 'Zulu 25'
  checksum64    = '6537c4a256130c1fed66e874cc467098e3cf61e0fd0d8953634ab0643291558c'
  checksumType64= 'sha256'

  silentArgs    = "ADDLOCAL=ZuluInstallation,FeatureEnvironment /qn /norestart"
  validExitCodes= @(0)
}

Install-ChocolateyPackage @packageArgs
