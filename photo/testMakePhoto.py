#!/usr/bin/python

import sys
import os
import csv

dir = os.getcwd()
sys.path.append(dir)
stimPath = dir + "/stim"

import V4Cycles_latest

stims = [1]

for stimNum in stims:
    inFile = stimPath + "/" + str(stimNum)
    try:
        with open(inFile+'_face.txt', newline='') as inputfile:
            faceSpec = list(csv.reader(inputfile))
        inputfile.close()

        with open(inFile+'_vert.txt', newline='') as inputfile:
            vertSpec = list(csv.reader(inputfile))
        inputfile.close()

    except:
        print("Error: unable to fetch data")

    envts = range(12)
    for ed in range(len(envts)):
        V4Cycles_latest.main(vertSpec,faceSpec,envts[ed],inFile+'_photo_'+str(envts[ed]))
