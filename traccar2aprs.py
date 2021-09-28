#!/usr/bin/env python3

from time import time, sleep
from datetime import datetime, timezone
import os
import sys
import json
import requests 
from geopy import distance
import aprslib

#read config
with open(os.path.join(sys.path[0],"config.json")) as json_data_file:
    conf = json.load(json_data_file)

    TRACCAR_URL = conf.get('TRACCAR_URL')
    TRACCAR_USER = conf.get('TRACCAR_USER')
    TRACCAR_PASSWORD = conf.get('TRACCAR_PASSWORD')
    TRACCAR_DEVICEID = conf.get('TRACCAR_DEVICEID')

    APRS_CALLSIGN = conf.get('APRS_CALLSIGN') or "NOCALL"
    APRS_SSID = conf.get('APRS_SSID') or "12"
    APRS_SYMBOL = conf.get('APRS_SYMBOL') or "/>"
    APRS_COMMENT = conf.get('APRS_COMMENT') or "Traccar2APRS https://traccar2aprs.vado.li/"

    LOOPTIME = conf.get('LOOPTIME') or 60
    EXPIRETIME = conf.get('EXPIRETIME') or 180
    MINUPDATETIME = conf.get('MINUPDATETIME') or 60
    MINDISTANCE = conf.get('MINDISTANCE') or 100
    DEBUG = conf.get('DEBUG') or False




def main():

    # a valid passcode for the callsign is required in order to send
    APSRIS = aprslib.IS(APRS_CALLSIGN, passwd=aprslib.passcode(APRS_CALLSIGN), port=14580)
    APSRIS.connect()

    lastpos = None
    lastupdate = None

    if DEBUG:
        print("DEBUG")
    while True:
    
        payload = {'deviceId': TRACCAR_DEVICEID}
        response = requests.get(TRACCAR_URL + '/api/positions', auth=(TRACCAR_USER, TRACCAR_PASSWORD), params=payload, timeout=1.000)
        data = json.loads(response.content)[0]  
        #print(data['attributes'])

        stime = data['serverTime']
        lat = data['latitude']
        lon = data['longitude']
        alt = data['altitude']

        print(stime, lat, lon, alt)
        
        pos = (lat, lon)
        tim = datetime.strptime(stime, "%Y-%m-%dT%H:%M:%S.%f%z")
        timediff = (datetime.now(timezone.utc) - tim).total_seconds()
        if DEBUG:
            print("TimeDiff" ,timediff)

        if timediff <= EXPIRETIME: #skip if data is too old
            if lastpos == None: lastpos = pos
            if lastupdate == None: lastupdate = tim
        
            if DEBUG:
                print("Distance ", distance.distance(pos, lastpos).m)
                print("LastUpdate ", (datetime.now(timezone.utc) - lastupdate).total_seconds())

            if (distance.distance(pos, lastpos).m >= MINDISTANCE and (datetime.now(timezone.utc) - lastupdate).total_seconds() >= MINUPDATETIME - 2):
                
                pr = aprslib.packets.PositionReport()
                pr.fromcall = APRS_CALLSIGN +'-'+ APRS_SSID
                pr.tocall = 'TRCCAR'
                pr.symbol_table =APRS_SYMBOL[0]
                pr.symbol = APRS_SYMBOL[1]
                pr.comment = APRS_COMMENT
                pr.latitude = lat
                pr.longitude = lon
                pr.altitude = alt if alt != 0 else None #if tracker doesn't send altitude

                print(str(pr))

                #send position to APRS-IS
                APSRIS.sendall(str(pr))


                lastpos = pos
                lastupdate = datetime.now(timezone.utc)

        nextloop = (LOOPTIME - timediff) % LOOPTIME + 2
        if DEBUG:
            print("NextLoop ", nextloop)
        sleep(nextloop)
        


if __name__ == "__main__":
    main()


