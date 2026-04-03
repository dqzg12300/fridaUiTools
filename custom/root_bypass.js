Java.perform(function () {
    console.log('[root_bypass] init');
    var rootPackages = [
        'com.noshufou.android.su',
        'com.noshufou.android.su.elite',
        'eu.chainfire.supersu',
        'com.koushikdutta.superuser',
        'com.thirdparty.superuser',
        'com.topjohnwu.magisk',
        'com.kingroot.kinguser'
    ];
    var rootBinaries = [
        'su', 'busybox', 'magisk', 'supersu'
    ];
    var rootPaths = [
        '/system/bin/su', '/system/xbin/su', '/sbin/su', '/vendor/bin/su',
        '/system/app/Superuser.apk', '/system/app/SuperSU.apk', '/system/bin/busybox',
        '/system/xbin/busybox', '/data/local/bin/su', '/data/local/xbin/su'
    ];

    function shouldBlockCommand(commandText) {
        if (!commandText) {
            return false;
        }
        commandText = commandText.toLowerCase();
        return commandText.indexOf('su') >= 0 ||
            commandText.indexOf('getprop') >= 0 ||
            commandText.indexOf('which') >= 0 ||
            commandText.indexOf('busybox') >= 0 ||
            commandText.indexOf('magisk') >= 0 ||
            commandText.indexOf('mount') >= 0;
    }

    try {
        var PackageManager = Java.use('android.app.ApplicationPackageManager');
        var getPackageInfo = PackageManager.getPackageInfo.overload('java.lang.String', 'int');
        getPackageInfo.implementation = function (packageName, flags) {
            if (rootPackages.indexOf(packageName) >= 0) {
                console.log('[root_bypass] hide package => ' + packageName);
                packageName = 'android.fake.package';
            }
            return getPackageInfo.call(this, packageName, flags);
        };
    } catch (e) {
        console.log('[root_bypass] package hook failed: ' + e);
    }

    try {
        var File = Java.use('java.io.File');
        var existsMethod = File.exists.overload();
        existsMethod.implementation = function () {
            var path = this.getAbsolutePath();
            if (rootPaths.indexOf(path) >= 0) {
                console.log('[root_bypass] hide file => ' + path);
                return false;
            }
            var name = this.getName();
            if (rootBinaries.indexOf(name) >= 0) {
                console.log('[root_bypass] hide binary => ' + name);
                return false;
            }
            return existsMethod.call(this);
        };
    } catch (e) {
        console.log('[root_bypass] file hook failed: ' + e);
    }

    try {
        var SystemProperties = Java.use('android.os.SystemProperties');
        var getProperty = SystemProperties.get.overload('java.lang.String');
        getProperty.implementation = function (key) {
            if (key === 'ro.build.tags') {
                return 'release-keys';
            }
            if (key === 'ro.debuggable' || key === 'ro.secure') {
                return '0';
            }
            return getProperty.call(this, key);
        };
    } catch (e) {
        console.log('[root_bypass] system property hook failed: ' + e);
    }

    try {
        var Runtime = Java.use('java.lang.Runtime');
        var exec1 = Runtime.exec.overload('java.lang.String');
        exec1.implementation = function (command) {
            if (shouldBlockCommand(command)) {
                console.log('[root_bypass] rewrite command => ' + command);
                command = 'grep';
            }
            return exec1.call(this, command);
        };
        var exec2 = Runtime.exec.overload('[Ljava.lang.String;');
        exec2.implementation = function (commands) {
            var commandText = commands ? commands.toString() : '';
            if (shouldBlockCommand(commandText)) {
                console.log('[root_bypass] rewrite command array => ' + commandText);
                commands = Java.array('java.lang.String', ['grep']);
            }
            return exec2.call(this, commands);
        };
    } catch (e) {
        console.log('[root_bypass] runtime hook failed: ' + e);
    }

    try {
        var ProcessBuilder = Java.use('java.lang.ProcessBuilder');
        var ArrayList = Java.use('java.util.ArrayList');
        var startMethod = ProcessBuilder.start.overload();
        startMethod.implementation = function () {
            try {
                var commandList = this.command();
                var commandText = commandList ? commandList.toString() : '';
                if (shouldBlockCommand(commandText)) {
                    console.log('[root_bypass] rewrite ProcessBuilder => ' + commandText);
                    var fakeList = ArrayList.$new();
                    fakeList.add('grep');
                    this.command(fakeList);
                }
            } catch (innerError) {
                console.log('[root_bypass] ProcessBuilder inner failed: ' + innerError);
            }
            return startMethod.call(this);
        };
    } catch (e) {
        console.log('[root_bypass] process builder hook failed: ' + e);
    }
});
