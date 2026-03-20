Java.perform(function () {
    console.log('[okhttp_logger] init');
    try {
        var RequestBuilder = Java.use('okhttp3.Request$Builder');
        var buildOverload = RequestBuilder.build.overload();
        buildOverload.implementation = function () {
            var request = buildOverload.call(this);
            try {
                console.log('[okhttp_logger] request => ' + request.method() + ' ' + request.url().toString());
                console.log('[okhttp_logger] headers =>\n' + request.headers().toString());
            } catch (innerError) {
                console.log('[okhttp_logger] request parse failed: ' + innerError);
            }
            return request;
        };
    } catch (e) {
        console.log('[okhttp_logger] Request$Builder hook failed: ' + e);
    }

    try {
        var Response = Java.use('okhttp3.Response');
        var codeMethod = Response.code.overload();
        codeMethod.implementation = function () {
            var code = codeMethod.call(this);
            try {
                var request = this.request();
                console.log('[okhttp_logger] response => ' + code + ' ' + request.method() + ' ' + request.url().toString());
            } catch (innerError) {
                console.log('[okhttp_logger] response parse failed: ' + innerError);
            }
            return code;
        };
    } catch (e) {
        console.log('[okhttp_logger] Response hook failed: ' + e);
    }
});
