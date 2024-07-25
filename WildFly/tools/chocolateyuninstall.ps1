$programFiles = (${env:ProgramFiles}, ${env:ProgramFiles(x86)} -ne $null)[0]
$version = "33.0.0"

$WildFlyDirectory = "$programFiles\WildFly"

rm -r "$WildFlyDirectory\wildfly-$version"

If ((Get-ChildItem -Force $WildFlyDirectory) -eq $Null) {
    rmdir $WildFlyDirectory 
}

