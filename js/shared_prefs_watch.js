Java.perform(function () {
    function klog(data) {
        var message = {};
        message["jsname"] = "shared_prefs_watch";
        message["data"] = data;
        send(message);
    }

    klog('[shared_prefs_watch] init');

    function stringify(value) {
        if (value === null || value === undefined) {
            return 'null';
        }
        try {
            return value.toString();
        } catch (e) {
            return '' + value;
        }
    }

    try {
        var SharedPreferencesImpl = Java.use('android.app.SharedPreferencesImpl');
        var getString = SharedPreferencesImpl.getString.overload('java.lang.String', 'java.lang.String');
        getString.implementation = function (key, defValue) {
            var result = getString.call(this, key, defValue);
            klog('[shared_prefs_watch] getString => key=' + key + ', value=' + stringify(result));
            return result;
        };

        var getInt = SharedPreferencesImpl.getInt.overload('java.lang.String', 'int');
        getInt.implementation = function (key, defValue) {
            var result = getInt.call(this, key, defValue);
            klog('[shared_prefs_watch] getInt => key=' + key + ', value=' + result);
            return result;
        };

        var getLong = SharedPreferencesImpl.getLong.overload('java.lang.String', 'long');
        getLong.implementation = function (key, defValue) {
            var result = getLong.call(this, key, defValue);
            klog('[shared_prefs_watch] getLong => key=' + key + ', value=' + result);
            return result;
        };

        var getBoolean = SharedPreferencesImpl.getBoolean.overload('java.lang.String', 'boolean');
        getBoolean.implementation = function (key, defValue) {
            var result = getBoolean.call(this, key, defValue);
            klog('[shared_prefs_watch] getBoolean => key=' + key + ', value=' + result);
            return result;
        };

        var getFloat = SharedPreferencesImpl.getFloat.overload('java.lang.String', 'float');
        getFloat.implementation = function (key, defValue) {
            var result = getFloat.call(this, key, defValue);
            klog('[shared_prefs_watch] getFloat => key=' + key + ', value=' + result);
            return result;
        };
    } catch (e) {
        klog('[shared_prefs_watch] SharedPreferencesImpl hook failed: ' + e);
    }

    try {
        var EditorImpl = Java.use('android.app.SharedPreferencesImpl$EditorImpl');

        var putString = EditorImpl.putString.overload('java.lang.String', 'java.lang.String');
        putString.implementation = function (key, value) {
            klog('[shared_prefs_watch] putString => key=' + key + ', value=' + stringify(value));
            return putString.call(this, key, value);
        };

        var putInt = EditorImpl.putInt.overload('java.lang.String', 'int');
        putInt.implementation = function (key, value) {
            klog('[shared_prefs_watch] putInt => key=' + key + ', value=' + value);
            return putInt.call(this, key, value);
        };

        var putLong = EditorImpl.putLong.overload('java.lang.String', 'long');
        putLong.implementation = function (key, value) {
            klog('[shared_prefs_watch] putLong => key=' + key + ', value=' + value);
            return putLong.call(this, key, value);
        };

        var putBoolean = EditorImpl.putBoolean.overload('java.lang.String', 'boolean');
        putBoolean.implementation = function (key, value) {
            klog('[shared_prefs_watch] putBoolean => key=' + key + ', value=' + value);
            return putBoolean.call(this, key, value);
        };

        var putFloat = EditorImpl.putFloat.overload('java.lang.String', 'float');
        putFloat.implementation = function (key, value) {
            klog('[shared_prefs_watch] putFloat => key=' + key + ', value=' + value);
            return putFloat.call(this, key, value);
        };

        var removeMethod = EditorImpl.remove.overload('java.lang.String');
        removeMethod.implementation = function (key) {
            klog('[shared_prefs_watch] remove => key=' + key);
            return removeMethod.call(this, key);
        };

        var clearMethod = EditorImpl.clear.overload();
        clearMethod.implementation = function () {
            klog('[shared_prefs_watch] clear all');
            return clearMethod.call(this);
        };

        var applyMethod = EditorImpl.apply.overload();
        applyMethod.implementation = function () {
            klog('[shared_prefs_watch] apply');
            return applyMethod.call(this);
        };

        var commitMethod = EditorImpl.commit.overload();
        commitMethod.implementation = function () {
            klog('[shared_prefs_watch] commit');
            return commitMethod.call(this);
        };
    } catch (e) {
        klog('[shared_prefs_watch] EditorImpl hook failed: ' + e);
    }
});
