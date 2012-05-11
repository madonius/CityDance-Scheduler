#!/usr/bin/python3
# -*- coding: utf-8 -*-

#    Citydance Scheduler, converts the citydance.de program to an ics File
#    Copyright (C) 2011 Emmanouil Kampitakis <emmanouil@kampitakis.de>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import re
import shutil
import getopt
import os
import datetime
import time
import random
import urllib.request
import codecs
from optparse import OptionParser

#parse for option given to filter for Teacher
parser = OptionParser()
parser.add_option("-t", "--teacher", dest = "teacher_filt", help="Filter the ICS File for a specific teacher")

(opt, args) = parser.parse_args()

#returns the Date in a ics compatible format
def returndate():
    return time.strftime("%Y%m%d") + "T" + time.strftime("%H%M%S") +"Z"

#check for existing files and directories, if they don't exists create them
#folder to store futurerelevant files
if not os.path.exists('./files/'):
    os.makedirs('./files')
#folder to store the output
if not os.path.exists('./output/'):
    os.makedirs('./output/')

if(isinstance(opt.teacher_filt,str)):
       datespath='./files/'+opt.teacher_filt+'_dates.log'
else:
       datespath='./files/dates.log'

if not os.path.isfile(datespath):
    isdate = 0
else:
    isdate = 1

#define regex for different components in text
sched_date = re.compile("([0-9]+)\.([0-9]+)\.([0-9]{4})")
sched_time = re.compile("([0-9]{2}):([0-9]{2}).+([0-9]{2}):([0-9]{2})")
sched_text = re.compile("([\w|(|)|\s|,]*)")

today = datetime.date.today()

#download the relevant page
indexhtml = urllib.request.urlopen('http://www.citydance.de/component/option,com_danceschedule/date,'+today.strftime("%Y-%m-%d")+'/view,danceschedule/')
indexlines_withumlaute = indexhtml.readlines()
indexhtml.close()

#download the schedule for the three weeks after the current one
for i in range(1 , 4):
	extendweek = today + datetime.timedelta(days=7*i)
	indexhtml = urllib.request.urlopen('http://www.citydance.de/component/option,com_danceschedule/date,'+extendweek.strftime("%Y-%m-%d")+'/view,danceschedule/')
	print('http://www.citydance.de/component/option,com_danceschedule/date,'+extendweek.strftime("%Y-%m-%d")+'/view,danceschedule/')
	indexlines2_withumlaute = indexhtml.readlines()
	indexhtml.close()

	indexlines_withumlaute.extend(indexlines2_withumlaute) 
	del indexlines2_withumlaute

indexlines = [l.decode('utf-8') for l in indexlines_withumlaute]

#generate the relevant .ics header
outputheader=['BEGIN:VCALENDAR','PRODID:Citydance','VERSION:2.0','CALSCALE:GREGORIAN','METHOD:PUBLISH','X-WR-CALNAME:Tanzen '+ time.strftime("%W") + ' Woche','X-WR-TIMEZONE:Europe/Berlin','X-WR-CALDESC:Tanzveranstaltungen ' + time.strftime("%W") + ' Woche']

output=[]

output.extend(outputheader)

for linenumber in range(0, len(indexlines)-1):
    if('<tr class="weekday">' in indexlines[linenumber]):
        datum = sched_date.search(indexlines[linenumber+2])
        
	#check if number is single digits if not make it so 
        if len(datum.groups()[0]) == 2:
            day=datum.groups()[0]
        else:
            day="0"+datum.groups()[0]
             
            
        if len(datum.groups()[1]) == 2:
            month=datum.groups()[1]
        else:
            month="0"+datum.groups()[1]
 
        year=datum.groups()[2]  
         
        #check and open the dates.log file
        if isdate == 1:
            log = open(datespath,"r+")
            log_mem = log.read()
        else:
            log = open(datespath,"a+")

        #where the actual foo happens
        if((isdate==0) or (log_mem.find(str(year) + str(month) + str(day)) == -1)):
            for sublinenumber in range(linenumber+2, len(indexlines)-1):
                if('<tr class="weekday">' in indexlines[sublinenumber]):
                    break
                elif('<tr class="overview">' in indexlines[sublinenumber]):
                    #get the information out of the text
                    uhrzeiten = sched_time.search(indexlines[sublinenumber+2].strip())
                    stufe = sched_text.search(indexlines[sublinenumber+4].strip()).groups(1)[0]
                    tanz = sched_text.search(indexlines[sublinenumber+6].strip()).groups(1)[0]
                    kursinhalt = sched_text.search(indexlines[sublinenumber+8].strip()).groups(1)[0]
                    tanzlehrer = sched_text.search(indexlines[sublinenumber+10].strip()).groups(1)[0]

                    print(tanzlehrer,opt.teacher_filt)
                    if((isinstance(opt.teacher_filt,str) and (opt.teacher_filt in tanzlehrer)) or not (isinstance(opt.teacher_filt,str))):                
		    #write the Details of the calendar event
                        output.append('BEGIN:VEVENT')
                        output.append('DTSTART;TZID=Europe/Berlin:'+year+month+day+'T'+str(int(uhrzeiten.groups()[0]))+str(int(uhrzeiten.groups()[1]))+"00Z")
                        output.append('DTEND;TZID=Europe/Berlin:'+str(year)+str(month)+str(day)+'T'+str(int(uhrzeiten.groups()[2]))+str(int(uhrzeiten.groups()[3]))+"00Z")
                        output.append('DTSTAMP:'+returndate())
                        output.append('UID:citydance'+str(random.random()+random.random())+time.strftime("%W",time.gmtime())+"week@wochentage.de")
                        output.append('CREATED:'+returndate())
                        output.append('DESCRIPTION:'+kursinhalt.replace(',','\,').strip().replace("<strong>",""))
                        output.append('LAST-MODIFIED:'+returndate())
                        output.append('LOCATION:Citydance Muenchen')
                        output.append('SEQUENCE:0')
                        output.append('STATUS:TENTATIVE')
                        output.append('SUMMARY:'+stufe.strip()+": "+tanz.strip()+" mit "+tanzlehrer.strip())
                        output.append('TRANSP:TRANSPARENT')
                        output.append('END:VEVENT')	                    
            #define log file to write out the dates of the days already parsed and written
            log.write(str(year) + str(month) + str(day) +"\n")
            log.close()
        else: 
            log.close()

#end the Calendar                
output.append('END:VCALENDAR')

#output of the File
print("output created", file=sys.stderr)

if(isinstance(opt.teacher_filt, str)):
       outputpath = "./output/output"+time.strftime("%Y%m%d")+"_"+opt.teacher_filt+".ics"
else:
       outputpath = "./output/output"+time.strftime("%Y%m%d")+".ics"

if not os.path.isfile(outputpath):
   print("writing file", file=sys.stderr)
   output_file = open(outputpath,"w", encoding="utf-8")
   output_file.write('\r\n'.join(output))
   output_file.close()
