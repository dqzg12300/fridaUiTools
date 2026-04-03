Java.perform(function () {
    function klog(data) {
        var message = {};
        message["jsname"] = "okhttp_logger";
        message["data"] = data;
        send(message);
    }

    klog('[okhttp_logger] init');
    try {
        var RequestBuilder = Java.use('okhttp3.Request$Builder');
        var buildOverload = RequestBuilder.build.overload();
        buildOverload.implementation = function () {
            var request = buildOverload.call(this);
            try {
                klog('[okhttp_logger] request => ' + request.method() + ' ' + request.url().toString());
                klog('[okhttp_logger] headers =>\n' + request.headers().toString());
            } catch (innerError) {
                klog('[okhttp_logger] request parse failed: ' + innerError);
            }
            return request;
        };
    } catch (e) {
        klog('[okhttp_logger] Request$Builder hook failed: ' + e);
    }

    try {
        var Response = Java.use('okhttp3.Response');
        var codeMethod = Response.code.overload();
        codeMethod.implementation = function () {
            var code = codeMethod.call(this);
            try {
                var request = this.request();
                klog('[okhttp_logger] response => ' + code + ' ' + request.method() + ' ' + request.url().toString());
            } catch (innerError) {
                klog('[okhttp_logger] response parse failed: ' + innerError);
            }
            return code;
        };
    } catch (e) {
        klog('[okhttp_logger] Response hook failed: ' + e);
    }
});
