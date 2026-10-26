$ErrorActionPreference = 'Stop'
$programFiles = (${env:ProgramFiles}, ${env:ProgramFiles(x86)} -ne $null)[0]
$installDir = "$programFiles\WildFly"

$packageArgs = @{
    PackageName = $env:ChocolateyPackageName
    UnzipLocation = $targetDir = $installDir
    Url = 'https://github.com/wildfly/wildfly/releases/download/42.0.0.Final/wildfly-42.0.0.Final.zip'
    Checksum = '3162d4ce32d26cefdd814e6dfe53670645a78945cdd6a68b69e26bb127241fd6'
    ChecksumType = 'sha256'
}

Install-ChocolateyZipPackage @packageArgs
