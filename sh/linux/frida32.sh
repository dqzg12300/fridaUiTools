adb shell "su -c 'pkill -9 frida-server '"
adb forward tcp:27042 tcp:27042
adb forward tcp:27043 tcp:27043
adb shell "su -c '/data/local/tmp/frida-server-14.2.18-android-arm'"