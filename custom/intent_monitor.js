Java.perform(function () {
    function klog(data) {
        var message = {};
        message["jsname"] = "intent_monitor";
        message["data"] = data;
        send(message);
    }

    klog('[intent_monitor] init');

    function describeBundle(bundle) {
        if (!bundle) {
            return '{}';
        }
        try {
            var result = [];
            var iterator = bundle.keySet().iterator();
            while (iterator.hasNext()) {
                var key = iterator.next();
                result.push(key + '=' + bundle.get(key));
            }
            return '{' + result.join(', ') + '}';
        } catch (e) {
            return '{bundle parse failed: ' + e + '}';
        }
    }

    function describeIntent(intent) {
        if (!intent) {
            return 'null';
        }
        try {
            var component = intent.getComponent();
            return 'action=' + intent.getAction() +
                ', data=' + intent.getDataString() +
                ', type=' + intent.getType() +
                ', flags=' + intent.getFlags() +
                ', component=' + (component ? component.flattenToShortString() : '') +
                ', extras=' + describeBundle(intent.getExtras());
        } catch (e) {
            return 'intent parse failed: ' + e;
        }
    }

    try {
        var Activity = Java.use('android.app.Activity');
        var startActivity = Activity.startActivity.overload('android.content.Intent');
        startActivity.implementation = function (intent) {
            klog('[intent_monitor] Activity.startActivity => ' + describeIntent(intent));
            return startActivity.call(this, intent);
        };

        var startActivityBundle = Activity.startActivity.overload('android.content.Intent', 'android.os.Bundle');
        startActivityBundle.implementation = function (intent, options) {
            klog('[intent_monitor] Activity.startActivity(bundle) => ' + describeIntent(intent));
            return startActivityBundle.call(this, intent, options);
        };

        var startActivityForResult = Activity.startActivityForResult.overload('android.content.Intent', 'int');
        startActivityForResult.implementation = function (intent, requestCode) {
            klog('[intent_monitor] Activity.startActivityForResult => requestCode=' + requestCode + ', ' + describeIntent(intent));
            return startActivityForResult.call(this, intent, requestCode);
        };
    } catch (e) {
        klog('[intent_monitor] Activity hook failed: ' + e);
    }

    try {
        var ContextWrapper = Java.use('android.content.ContextWrapper');

        var startService = ContextWrapper.startService.overload('android.content.Intent');
        startService.implementation = function (intent) {
            klog('[intent_monitor] startService => ' + describeIntent(intent));
            return startService.call(this, intent);
        };

        if (ContextWrapper.startForegroundService) {
            var startForegroundService = ContextWrapper.startForegroundService.overload('android.content.Intent');
            startForegroundService.implementation = function (intent) {
                klog('[intent_monitor] startForegroundService => ' + describeIntent(intent));
                return startForegroundService.call(this, intent);
            };
        }

        var sendBroadcast = ContextWrapper.sendBroadcast.overload('android.content.Intent');
        sendBroadcast.implementation = function (intent) {
            klog('[intent_monitor] sendBroadcast => ' + describeIntent(intent));
            return sendBroadcast.call(this, intent);
        };
    } catch (e) {
        klog('[intent_monitor] ContextWrapper hook failed: ' + e);
    }
});
