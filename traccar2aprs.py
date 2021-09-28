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

    TRACCAR_URL = conf['TRACCAR_URL']
    TRACCAR_USER = conf['TRACCAR_USER']
    TRACCAR_PASSWORD = conf['TRACCAR_PASSWORD']
    TRACCAR_DEVICEID = conf['TRACCAR_DEVICEID']

    APRS_CALLSIGN = conf['APRS_CALLSIGN']
    APRS_SSID = conf['APRS_SSID']
    APRS_SYMBOL = conf['APRS_SYMBOL']
    APRS_COMMENT = conf['APRS_COMMENT']

    LOOPTIME = conf['LOOPTIME']
    MINUPDATETIME = conf['MINUPDATETIME']
    MINDISTANCE = conf['MINDISTANCE']




def main():

    # a valid passcode for the callsign is required in order to send
    APSRIS = aprslib.IS(APRS_CALLSIGN, passwd=aprslib.passcode(APRS_CALLSIGN), port=14580)
    APSRIS.connect()

    lastpos = None
    lastupdate = None
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

        if (datetime.now(timezone.utc) - tim).total_seconds() < 300: #skip if data is too old
            if lastpos == None: lastpos = pos
            if lastupdate == None: lastupdate = tim
        
            if (distance.distance(pos, lastpos).m >= MINDISTANCE and (datetime.now(timezone.utc) - lastupdate).total_seconds() >= MINUPDATETIME):
                #print("Distance ", distance.distance(pos, lastpos).m)
                #print("LastUpdate ", (datetime.now(timezone.utc) - lastupdate).total_seconds())

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

        sleep(LOOPTIME - time() % LOOPTIME)
        


if __name__ == "__main__":
    main()


