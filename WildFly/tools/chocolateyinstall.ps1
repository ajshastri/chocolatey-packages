$programFiles = (${env:ProgramFiles}, ${env:ProgramFiles(x86)} -ne $null)[0]
$installDir = "$programFiles\WildFly"

$packageArgs = @{
    PackageName = $env:ChocolateyPackageName
    UnzipLocation = $targetDir = $installDir
    Url = 'https://github.com/wildfly/wildfly/releases/download/30.0.1.Final/wildfly-30.0.1.Final.zip'
    Checksum = 'cd9c13350d775abcc728259b24b8bfabdf2b90a3'
    ChecksumType = 'sha1'
}

Install-ChocolateyZipPackage @packageArgs
