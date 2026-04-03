#!/bin/bash
# 杀掉旧的 frida-server
adb -s 98.98.125.9:20018 shell "killall fservice fservice64 frida-server" 2>/dev/null
adb -s 98.98.125.9:20018 shell su -c "killall fservice fservice64 frida-server" 2>/dev/null
adb -s 98.98.125.9:20018 shell su 0 sh -c "killall fservice fservice64 frida-server" 2>/dev/null
adb -s 98.98.125.9:20018 forward --remove tcp:27042 2>/dev/null
adb -s 98.98.125.9:20018 forward --remove tcp:27043 2>/dev/null
adb -s 98.98.125.9:20018 forward --remove tcp:12345 2>/dev/null
sleep 1


adb -s 98.98.125.9:20018 forward tcp:12345 tcp:12345
adb -s 98.98.125.9:20018 shell sh -c 'chmod 0777 /data/local/tmp/fservice 2>/dev/null; chmod 0777 /data/local/tmp/fservice64 2>/dev/null' || adb -s 98.98.125.9:20018 shell su -c 'chmod 0777 /data/local/tmp/fservice 2>/dev/null; chmod 0777 /data/local/tmp/fservice64 2>/dev/null' || adb -s 98.98.125.9:20018 shell su 0 sh -c 'chmod 0777 /data/local/tmp/fservice 2>/dev/null; chmod 0777 /data/local/tmp/fservice64 2>/dev/null'
adb -s 98.98.125.9:20018 shell sh -c '/data/local/tmp/fservice64 -l 0.0.0.0:12345' || adb -s 98.98.125.9:20018 shell su -c '/data/local/tmp/fservice64 -l 0.0.0.0:12345' 2>/dev/null || adb -s 98.98.125.9:20018 shell su 0 sh -c '/data/local/tmp/fservice64 -l 0.0.0.0:12345' 2>/dev/null
