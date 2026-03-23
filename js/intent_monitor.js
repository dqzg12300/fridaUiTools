Java.perform(function () {
    console.log('[intent_monitor] init');

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
            console.log('[intent_monitor] Activity.startActivity => ' + describeIntent(intent));
            return startActivity.call(this, intent);
        };

        var startActivityBundle = Activity.startActivity.overload('android.content.Intent', 'android.os.Bundle');
        startActivityBundle.implementation = function (intent, options) {
            console.log('[intent_monitor] Activity.startActivity(bundle) => ' + describeIntent(intent));
            return startActivityBundle.call(this, intent, options);
        };

        var startActivityForResult = Activity.startActivityForResult.overload('android.content.Intent', 'int');
        startActivityForResult.implementation = function (intent, requestCode) {
            console.log('[intent_monitor] Activity.startActivityForResult => requestCode=' + requestCode + ', ' + describeIntent(intent));
            return startActivityForResult.call(this, intent, requestCode);
        };
    } catch (e) {
        console.log('[intent_monitor] Activity hook failed: ' + e);
    }

    try {
        var ContextWrapper = Java.use('android.content.ContextWrapper');

        var startService = ContextWrapper.startService.overload('android.content.Intent');
        startService.implementation = function (intent) {
            console.log('[intent_monitor] startService => ' + describeIntent(intent));
            return startService.call(this, intent);
        };

        if (ContextWrapper.startForegroundService) {
            var startForegroundService = ContextWrapper.startForegroundService.overload('android.content.Intent');
            startForegroundService.implementation = function (intent) {
                console.log('[intent_monitor] startForegroundService => ' + describeIntent(intent));
                return startForegroundService.call(this, intent);
            };
        }

        var sendBroadcast = ContextWrapper.sendBroadcast.overload('android.content.Intent');
        sendBroadcast.implementation = function (intent) {
            console.log('[intent_monitor] sendBroadcast => ' + describeIntent(intent));
            return sendBroadcast.call(this, intent);
        };
    } catch (e) {
        console.log('[intent_monitor] ContextWrapper hook failed: ' + e);
    }
});
