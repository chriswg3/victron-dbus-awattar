import QtQuick 1.0
import com.victron.velib 1.0
import "utils.js" as Utils

MbPage {
	id: pageAwattarSettings
	title: qsTr("Awattar")
	property string bindPrefix: "com.victronenergy.awattar.P-1"
	property VBusItem stateItem: VBusItem { bind: "com.victronenergy.awattar.P-1/State" }
        property VBusItem slotItem: VBusItem { bind: "com.victronenergy.awattar.P-1/Slots" }
	function randomScalingFactor() {
		return Math.random().toFixed(1);
	}

	model: VisualItemModel {


		MbSwitch {
			id: awattarSwitch
			name: qsTr("Use Awattar Service")
			bind: "com.victronenergy.awattar.P-1/State" 
			invertSense: false
		}
                
                MbItemOptions {
                        description: qsTr("Country")
                        bind: "com.victronenergy.awattar.P-1/Country"
                        possibleValues: [
                                MbOption { description: qsTr("Austria"); value: 0 },
                                MbOption { description: qsTr("Germany"); value: 1 }
                        ]
                        show: awattarSwitch.checked
                }
                
                MbEditBoxTime {
                                id: startTime
                                description: qsTr("Start time")
                                item.bind: Utils.path(bindPrefix, "/Start")
                                show: awattarSwitch.checked
                        }
                MbEditBoxTime {
                                id: endTime
                                description: qsTr("End time")
                                item.bind: Utils.path(bindPrefix, "/End")
                                show: awattarSwitch.checked
                        }
                
		MbEditBoxTime {
                                id: duration
                                description: qsTr("Duration (hh:mm)")
                                item.bind: Utils.path(bindPrefix, "/Duration")
                                show: awattarSwitch.checked
                        }

                MbSwitch {
                                id: socLimitEnabled
                                name: qsTr("Stop on SOC")
                                enabled: true
                                show: awattarSwitch.checked
                                checked: socLimit.item.value < 100
                                onCheckedChanged: {
                                        if (checked && socLimit.item.value >= 100)
                                                socLimit.item.setValue(95)
                                        else if (!checked && socLimit.item.value < 100)
                                                socLimit.item.setValue(100)
                                }
                        }

                MbSpinBox {
                                id: socLimit
                                description: qsTr("SOC Limit")
                                show: awattarSwitch.checked && socLimitEnabled.checked
                                item {
                                        bind: Utils.path(bindPrefix, "/Soc")
                                        decimals: 0
                                        unit: "%"
                                        min: 5
                                        max: 95
                                        step: 5
                                }
                        }
 
                MbSpinBox {
           			id: priceLimit
				description: qsTr("Price Limit")
				show: awattarSwitch.checked
				item {
					bind: Utils.path(bindPrefix,"/PriceLimit")
					decimals:1
					unit:" Cent"
					min: -100.0
					max: 100
					step: 0.5
				}
		}

		MbSpinBox {
				id: schedulePlanId
				description: qsTr("Use Scheduled Charging Slot")
				show: awattarSwitch.checked
				item {
					bind: Utils.path(bindPrefix,"/SPSlotId")
					decimals: 0
					min: 1
					max: 5
					step: 1
				     }
		}


	        MbSubMenu {
            		id: awattarStatusPage
			description: qsTr("Schedule Plan")
			show: awattarSwitch.checked

			subpage:  MbPage {
                                
				property variant myItem: slotItem.value	
                                onMyItemChanged: doReloadSp();
				
				function doReloadSp() {                                                      
                                        spModel.clear();             
                                        var t = 0;                                
                                        while (t < slotItem.value.length)           
                                        {                                              
                                                const item = Qt.createQmlObject('import QtQuick 1.0\nMbSubMenu { description: "'+slotItem.value[t]+'" }',awattarStatusPage,'myDynamicSnippet');
                                                spModel.append(item);       
                                                t++;                                  
                                        }                                         
                                }
                                Component.onCompleted: {
					doReloadSp();
				}
				
                                id: spOverview
                		title: awattarStatusPage.description
				clip: true
				
				model: VisualItemModel {
					
					id: spModel
				}
			}
		}
	
	}
}

