Java.perform(function () {
    console.log('[webview_debug] init');
    try {
        var WebView = Java.use('android.webkit.WebView');
        try {
            WebView.setWebContentsDebuggingEnabled(true);
            console.log('[webview_debug] Web contents debugging enabled');
        } catch (e) {
            console.log('[webview_debug] enable debug failed: ' + e);
        }

        var loadUrlMethod = WebView.loadUrl.overload('java.lang.String');
        loadUrlMethod.implementation = function (url) {
            console.log('[webview_debug] loadUrl => ' + url);
            return loadUrlMethod.call(this, url);
        };

        var addJavascriptInterfaceMethod = WebView.addJavascriptInterface.overload('java.lang.Object', 'java.lang.String');
        addJavascriptInterfaceMethod.implementation = function (obj, name) {
            console.log('[webview_debug] addJavascriptInterface => ' + name);
            return addJavascriptInterfaceMethod.call(this, obj, name);
        };
    } catch (e) {
        console.log('[webview_debug] WebView hook failed: ' + e);
    }
});
