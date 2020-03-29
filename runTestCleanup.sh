#!/bin/bash -x
set -e

kill -9 $(cat pidfile1)
kill $(cat pidfile2)
service elasticsearch stop
kill $(cat pidfile4)
kill $(cat pidfile5)
kill $(cat pidfile6)
kill $(cat pidfile7)

rm pidfile1
rm pidfile2
rm pidfile3
rm pidfile4
rm pidfile5
rm pidfile6
rm pidfile7
