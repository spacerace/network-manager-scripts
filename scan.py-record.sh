#!/bin/bash

clear
./scan.py >> record.txt
tail -n 30 record.txt
sleep 1

./record.sh
