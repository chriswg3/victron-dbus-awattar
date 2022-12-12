#!/bin/bash

mode=0

qmlDir=/opt/victronenergy/gui/qml

if [ $# -gt 0 ] && ([ $1 == 'INSTALL' ] || [ $1 == 'UNINSTALL' ]); then
    if [ $1 == 'INSTALL' ]; then
	mode=0
    else
	mode=1
    fi
else
    echo "Available actions:"
    echo "INSTALL -- Install Awattar Plugin"
    echo "UNINSTALL -- Uninstall Awattar Plugin"
    exit -1
fi


if [ $mode == 0 ]; then #Install
    echo "Do install"
    if grep -Fq "MbSubMenu { description: qsTr(\"Awattar\")" $qmlDir/PageSettings.qml
    then
	echo "Already in file"
    else
	echo "Not found, do install."
	cp $qmlDir/PageSettings.qml $qmlDir/PageSettings.qml.awattar.orig
	sed -i ':a;N;$!ba;s/PageSettingsIo { id: ioSettings }\n\t\t}/PageSettingsIo { id: ioSettings }\n\t\t}\n\n\t\tMbSubMenu { description: qsTr("Awattar"); subpage: Component { PageSettingsAwattar {} } }/g' $qmlDir/PageSettings.qml
	cp gui/PageSettingsAwattar.qml $qmlDir/
	ln -s /data/dbus-awattar/service /service/dbus-awattar
	svc -t /service/gui
   fi
   if grep -qxF "ln -s /data/dbus-awattar/service /service/dbus-awattar" /data/rc.local
   then
	echo "Service already installed."
   else
	echo "ln -s /data/dbus-awattar/service /service/dbus-awattar" >> /data/rc.local
   fi
else #Uninstall
    echo "Do uninstall"
    if [ -f $qmlDir/PageSettings.qml.awattar.orig ]; then
    	mv $qmlDir/PageSettings.qml.awattar.orig $qmlDir/PageSettings.qml
    fi
    if [ -d /service/dbus-awattar ]; then
	svc -d /service/dbus-awattar
	svc -x /service/dbus-awattar
	rm /service/dbus-awattar
    fi
    if [ -f $qmlDir/PageSettingsAwattar.qml ]; then
	rm $qmlDir/PageSettingsAwattar.qml
    fi
    sed -i "s/ln -s \/data\/dbus-awattar\/service \/service\/dbus-awattar//" /data/rc.local
    svc -t /service/gui
fi



