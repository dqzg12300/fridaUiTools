
#!/bin/zsh

osascript <<END

tell application "Terminal"

    do script "adb shell su -c 'pkill -9 hluda-server '; adb forward tcp:27042 tcp:27042 ;adb forward tcp:27043 tcp:27043 ; adb shell su -c '/data/local/tmp/hluda-server-14.2.18-android-x86'"

end tell

END
