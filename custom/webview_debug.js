Java.perform(function () {
    function klog(data) {
        var message = {};
        message["jsname"] = "webview_debug";
        message["data"] = data;
        send(message);
    }

    klog('[webview_debug] init');
    try {
        var WebView = Java.use('android.webkit.WebView');
        try {
            WebView.setWebContentsDebuggingEnabled(true);
            klog('[webview_debug] Web contents debugging enabled');
        } catch (e) {
            klog('[webview_debug] enable debug failed: ' + e);
        }

        var loadUrlMethod = WebView.loadUrl.overload('java.lang.String');
        loadUrlMethod.implementation = function (url) {
            klog('[webview_debug] loadUrl => ' + url);
            return loadUrlMethod.call(this, url);
        };

        var addJavascriptInterfaceMethod = WebView.addJavascriptInterface.overload('java.lang.Object', 'java.lang.String');
        addJavascriptInterfaceMethod.implementation = function (obj, name) {
            klog('[webview_debug] addJavascriptInterface => ' + name);
            return addJavascriptInterfaceMethod.call(this, obj, name);
        };
    } catch (e) {
        klog('[webview_debug] WebView hook failed: ' + e);
    }
});
