$ErrorActionPreference = 'Stop'
$programFiles = (${env:ProgramFiles}, ${env:ProgramFiles(x86)} -ne $null)[0]
$installDir = "$programFiles\WildFly"

$packageArgs = @{
    PackageName = $env:ChocolateyPackageName
    UnzipLocation = $targetDir = $installDir
    Url = 'https://github.com/wildfly/wildfly/releases/download/41.0.0.Final/wildfly-41.0.0.Final.zip'
    Checksum = '85768d52743935dba403b03170a00434f8e145bc9920c8fb7b441ea726d30147'
    ChecksumType = 'sha256'
}

Install-ChocolateyZipPackage @packageArgs
