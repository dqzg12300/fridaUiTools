Java.perform(function () {
    function klog(data) {
        var message = {};
        message["jsname"] = "clipboard_monitor";
        message["data"] = data;
        send(message);
    }

    klog('[clipboard_monitor] init');

    function describeClip(clip) {
        if (!clip) {
            return 'null';
        }
        try {
            var parts = [];
            var count = clip.getItemCount();
            for (var i = 0; i < count; i++) {
                var item = clip.getItemAt(i);
                var text = item.getText();
                var htmlText = item.getHtmlText();
                var uri = item.getUri();
                var intent = item.getIntent();
                parts.push('[item ' + i + '] text=' + (text ? text.toString() : '') + ', html=' + (htmlText ? htmlText.toString() : '') + ', uri=' + (uri ? uri.toString() : '') + ', intent=' + (intent ? intent.toUri(0) : ''));
            }
            return parts.join(' | ');
        } catch (e) {
            return 'clip parse failed: ' + e;
        }
    }

    try {
        var ClipboardManager = Java.use('android.content.ClipboardManager');

        var setPrimaryClip = ClipboardManager.setPrimaryClip.overload('android.content.ClipData');
        setPrimaryClip.implementation = function (clip) {
            klog('[clipboard_monitor] setPrimaryClip => ' + describeClip(clip));
            return setPrimaryClip.call(this, clip);
        };

        var getPrimaryClip = ClipboardManager.getPrimaryClip.overload();
        getPrimaryClip.implementation = function () {
            var result = getPrimaryClip.call(this);
            klog('[clipboard_monitor] getPrimaryClip => ' + describeClip(result));
            return result;
        };

        if (ClipboardManager.setText) {
            var setText = ClipboardManager.setText.overload('java.lang.CharSequence');
            setText.implementation = function (text) {
                klog('[clipboard_monitor] setText => ' + text);
                return setText.call(this, text);
            };
        }

        if (ClipboardManager.getText) {
            var getText = ClipboardManager.getText.overload();
            getText.implementation = function () {
                var result = getText.call(this);
                klog('[clipboard_monitor] getText => ' + result);
                return result;
            };
        }
    } catch (e) {
        klog('[clipboard_monitor] hook failed: ' + e);
    }
});
