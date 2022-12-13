#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DBUS SERVICE RESTART
"""

from gi.repository import GLib
import time
import subprocess
import logging
import sys
import os
import datetime
from awattar.client import AwattarClient
sys.path.insert(1, os.path.join(os.path.dirname(__file__), '/opt/victronenergy/dbus-systemcalc-py/ext/velib_python'))

# ************************ToDo

from dbus.mainloop.glib import DBusGMainLoop
from functools import partial
import dbus
from vedbus import VeDbusService
from ve_utils import exit_on_error
from settingsdevice import SettingsDevice
import traceback
from vedbus import VeDbusItemImport

VERSION = '0.1'


class SystemBus(dbus.bus.BusConnection):
        def __new__(cls):
                return dbus.bus.BusConnection.__new__(cls, dbus.bus.BusConnection.TYPE_SYSTEM)

class SessionBus(dbus.bus.BusConnection):
        def __new__(cls):
                return dbus.bus.BusConnection.__new__(cls, dbus.bus.BusConnection.TYPE_SESSION)


class Awattar():
    def __init__(self):
        logging.debug('Initialize Service...')
        self.dbus = self.dbusconnection()
        self.slots = ["No Data."]
        self.slotdata = []
        self.doupdate = True
        self.lastupdate = None
        timezone = VeDbusItemImport(
				self.dbus,
				'com.victronenergy.settings',
				'/Settings/System/TimeZone',
				eventCallback=None,
				createsignal=False)


        os.environ['TZ'] = timezone.get_value()
        time.tzset()
        self.tz = datetime.datetime.now(datetime.timezone(datetime.timedelta(0))).astimezone().tzinfo
        self.settings = SettingsDevice(bus=self.dbus,supportedSettings={'state' : ['/Settings/Awattar/State',0,0,1],
                              'country' : ['/Settings/Awattar/Country',0,0,1],
                              'start' : ['/Settings/Awattar/Start',0,0,86340],
                              'end' : ['/Settings/Awattar/End',0,0,86340],
                              'duration' : ['/Settings/Awattar/Duration',0,0,86340],
                              'soc' : ['/Settings/Awattar/Soc',80,0,100],
                              'pricelimit' : ['/Settings/Awattar/PriceLimit',10.0,-100.0,100.0],
                              'spslotid' : ['/Settings/Awattar/SPSlotId',1,1,5]
                              },eventCallback=self.handle_changed_setting)    
 
        self.service = VeDbusService('com.victronenergy.awattar.P-1', bus = self.dbus)
        self.service.add_path('/State',int(self.settings['state']),writeable=True,onchangecallback=self._change_state)
        self.service.add_path('/Country',int(self.settings['country']),writeable=True,onchangecallback=self._change_country)
        self.service.add_path('/Start',int(self.settings['start']),writeable=True,onchangecallback=self._change_start)
        self.service.add_path('/End',int(self.settings['end']),writeable=True,onchangecallback=self._change_end)
        self.service.add_path('/Duration',int(self.settings['duration']),writeable=True,onchangecallback=self._change_duration)
        self.service.add_path('/Soc',int(self.settings['soc']),writeable=True,onchangecallback=self._change_soc)
        self.service.add_path('/PriceLimit',float(self.settings['pricelimit']),writeable=True,onchangecallback=self._change_pricelimit)
        self.service.add_path('/Slots',self.slots,writeable=False)
        self.service.add_path('/SPSlotId',int(self.settings['spslotid']),writeable=True,onchangecallback=self._change_spslotid)
        self._loadSlotSettings();

    def _loadSlotSettings(self):

        self.scDay = VeDbusItemImport(                                                                                                     
                                      self.dbus,                                                                                       
                                      'com.victronenergy.settings',                                                                    
                                      '/Settings/CGwacs/BatteryLife/Schedule/Charge/'+str(self.settings['spslotid']-1)+'/Day',         
                                      eventCallback=None,                                                                                                        
                                      createsignal=False)                                                                                                        
        self.scSoc = VeDbusItemImport(                                                                                                                               
                                      self.dbus,                                                                                                                 
                                      'com.victronenergy.settings',                                                                                              
                                      '/Settings/CGwacs/BatteryLife/Schedule/Charge/'+str(self.settings['spslotid']-1)+'/Soc',                                   
                                      eventCallback=None,                                                                                                        
                                      createsignal=False)                                                                              
                                                                                                                                       
                                                                                                                                       
        self.scDuration = VeDbusItemImport(                                                                                                
                                      self.dbus,                                                                                       
                                      'com.victronenergy.settings',                                                                    
                                      '/Settings/CGwacs/BatteryLife/Schedule/Charge/'+str(self.settings['spslotid']-1)+'/Duration',    
                                      eventCallback=None,                                                                              
                                      createsignal=False)                                                                              
                                                                                                                                       
        self.scStart = VeDbusItemImport(                                                                                                   
                                      self.dbus,                                                                                       
                                      'com.victronenergy.settings',                                                                    
                                      '/Settings/CGwacs/BatteryLife/Schedule/Charge/'+str(self.settings['spslotid']-1)+'/Start',       
                                      eventCallback=None,                                                                              
                                      createsignal=False)                                                                              
                                                                                                                                       
    def _checkChargingSlot(self):
        

         if (self.settings['state']==0 or len(self.slotdata)<=0):
             self.scDay.set_value(-7)
         else:
             s = 0
             while(s<len(self.slotdata)):
                  if (self.slotdata[s].start_datetime>=datetime.datetime.now(self.tz).replace(second=0,minute=0,microsecond=0)):
                     break
                  else:
                     s = s + 1

             if (s>=len(self.slotdata)):
                 return True

             sstart = self.slotdata[s].start_datetime.hour*3600+self.slotdata[s].start_datetime.minute*60
             if (self.scStart.get_value()!=sstart):
                  self.scStart.set_value(sstart)

             i = s + 1 
             duration = 1
             while(i<len(self.slotdata)):
                 if (self.slotdata[i-1].start_datetime.hour+1==self.slotdata[i].start_datetime.hour):
                    duration = duration + 1
                 else:
                    break
                 i = i + 1
             if (self.scDuration.get_value()!=duration*3600):
                  self.scDuration.set_value(duration*3600)
             if (self.scSoc.get_value()!=self.settings['soc']):
                  self.scSoc.set_value(self.settings['soc'])
           
             wday = (self.slotdata[0].start_datetime.weekday() + 1) % 7
             if (self.scDay.get_value()!=wday):
                  self.scDay.set_value(wday)

         return True


    def dbusconnection(self):
        return SessionBus() if 'DBUS_SESSION_BUS_ADDRESS' in os.environ else SystemBus()    

    def _change_spslotid(self, p, v):
        if (self.scDay):
           self.scDay.set_value(-7);

        self.settings['spslotid']=int(v)
        self.service['/SPSlotId']=int(v)
        self._loadSlotSettings();
        return True    

    def _change_pricelimit(self, p, v):
        self.settings['pricelimit']=float(v)
        self.service['/PriceLimit']=float(v)
        return True
    def _change_soc(self, p, v):
        self.settings['soc']=int(v)
        self.service['/Soc']=int(v)        
        return True

    def _change_duration(self, p, v):
        self.settings['duration']=int(v)
        self.service['/Duration']=int(v)
        return True


    def _change_end(self, p, v):
         self.settings['end']=int(v)
         self.service['/End']=int(v)
         return True

    def _change_start(self, p, v):
         self.settings['start']=int(v)
         self.service['/Start']=int(v)
         return True

    def _change_state(self, p, v):
         self.settings['state']=int(v)
         self.service['/State']=int(v)
         return True

    def _change_country(self, p, v):
         self.settings['country']=int(v)
         self.service['/Country']=int(v)
         return True

    def handle_changed_setting(self, setting, oldvalue, newvalue):
        logging.debug('setting changed, setting: %s, old: %s, new: %s' % (setting, oldvalue, newvalue))
        self.doupdate = True
        return True

    def getCountry(self):
        if self.settings['country'] == 0:
             return "AT"
        else:
             return "DE"

    def update(self):

        diff = 0
	
        if (self.settings['state']==0):
            self._checkChargingSlot()
            return True
 
        if self.lastupdate is not None:
           diff = (datetime.datetime.now(self.tz) - self.lastupdate).total_seconds()
        
        if not self.doupdate and diff <= 60*60:
            return True

        logging.info('Refresh prices...')
        self.lastupdate = datetime.datetime.now(self.tz)
        self.doupdate=False
      
        client = AwattarClient(self.getCountry())

        starttime = datetime.timedelta(seconds=self.settings['start'])
        endtime = datetime.timedelta(seconds=self.settings['end'])
        now = datetime.datetime.now(self.tz).replace(second=0,minute=0,microsecond=0)
        duration = datetime.timedelta(seconds=self.settings['duration'])
        pricelimit = self.settings['pricelimit']
        starthour=starttime.seconds//3600
        endhour=endtime.seconds//3600
        durationCount = duration.seconds//3600
        
        if duration.seconds % 3600 > 0:
           durationCount = durationCount + 1

        endnextday = False
        if starthour>endhour:
            endnextday = True
        
        
        startdate = now
        if (now.hour<starthour):
            startdate = startdate - datetime.timedelta(days=1)

        startdate = startdate.replace(hour=starthour)

        
        enddate = startdate
        if endnextday: 
              enddate = startdate + datetime.timedelta(days=1)
        

        enddate = enddate.replace(hour=endhour)

        if startdate<=now and enddate<=now:
           startdate = startdate + datetime.timedelta(days=1)
           enddate = enddate + datetime.timedelta(days=1)

        if startdate == enddate:
           enddate = enddate + datetime.timedelta(days=1)

        data = client.request(startdate.astimezone(datetime.timezone.utc), enddate.astimezone(datetime.timezone.utc))
        
        if client.best_slot(1,enddate.astimezone(datetime.timezone.utc)-datetime.timedelta(hours=1),enddate.astimezone(datetime.timezone.utc)) is not None:
           logging.debug("All data fetched.")
 
        x = 0
        self.slots = []
        self.slotdata = []
        while x < durationCount:
            best_slot = client.best_slot(1)
            if best_slot is None:
               break
            else:
               client.removeMin()
               if best_slot.marketprice/10.0<=pricelimit:        
                   self.slotdata.append(best_slot);
                   self.slots.append(f'{best_slot.start_datetime:%Y-%m-%d %H:%M} - {best_slot.end_datetime:%H:%M} - {(best_slot.marketprice / 10):.2f} Cent/kWh')
                   x = x + 1
               else:
                   logging.info(f'Pricelimit does not match')
 
        self.slotdata.sort()
        self.slots.sort()
        if (len(self.slots)==0):
            self.slots.append('No charging slots for given conditions.')
        self.service['/Slots']=self.slots
        logging.info(self.slots)
        self._checkChargingSlot()
        logging.debug('Update finished.')
        return True

def main():
        print (" ********************************************* ")
        print ("    A W A T T A R   M A I N   S T A R T E D   ")
        print (" ********************************************* ")
        print (" ")

        logging.basicConfig( format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                             datefmt='%Y-%m-%d %H:%M:%S',
                             level=logging.INFO,
                             handlers=[
                                logging.FileHandler("%s/current.log" % (os.path.dirname(os.path.realpath(__file__)))),
                                logging.StreamHandler()
                             ])


        DBusGMainLoop(set_as_default=True)

        mainloop = GLib.MainLoop()
        awattar = Awattar()
        GLib.timeout_add(5000, awattar.update)
        mainloop.run()

if __name__ == "__main__":
        main()
