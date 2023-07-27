$ErrorActionPreference = 'Stop';
$toolsDir   = "$(Split-Path -parent $MyInvocation.MyCommand.Definition)"
$url        = 'https://dn3.freedownloadmanager.org/6/latest/fdm_x86_setup.exe'
$url64      = 'https://dn3.freedownloadmanager.org/6/latest/fdm_x64_setup.exe'

$packageArgs = @{
  packageName   = 'FreeDownloadManager'
  unzipLocation = $toolsDir
  fileType      = 'EXE'
  url           = $url
  url64bit      = $url64
  softwareName  = 'FreeDownloadManager*'
  checksum      = '6b81e9096e235e9ddb85ef4e252c3cdb1a7ba59222ec0ba20b36240462dbf82e'
  checksumType  = 'sha256'
  checksum64    = '30adf5e886ddba24057585e8324a2d6d7ef2dcb9205542fa73c9c5e6356484ce'
  checksumType64= 'sha256'
  
  validExitCodes= @(0, 3010, 1641)
  silentArgs   = '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-'
}

Install-ChocolateyPackage @packageArgs










    








