Java.perform(function() {

/*
hook list:
1.SSLcontext
2.okhttp
3.webview
4.XUtils
5.httpclientandroidlib
6.JSSE
7.network\_security\_config (android 7.0+)
8.Apache Http client (support partly)
9.OpenSSLSocketImpl
10.TrustKit
11.Cronet
*/

	// Attempts to bypass SSL pinning implementations in a number of
	// ways. These include implementing a new TrustManager that will
	// accept any SSL certificate, overriding OkHTTP v3 check()
	// method etc.
	var X509TrustManager = Java.use('javax.net.ssl.X509TrustManager');
	var HostnameVerifier = Java.use('javax.net.ssl.HostnameVerifier');
	var SSLContext = Java.use('javax.net.ssl.SSLContext');
	var quiet_output = false;

	// Helper method to honor the quiet flag.

	function quiet_send(data) {

		if (quiet_output) {

			return;
		}

		send(data)
	}


	// Implement a new TrustManager
	// ref: https://gist.github.com/oleavr/3ca67a173ff7d207c6b8c3b0ca65a9d8
	// Java.registerClass() is only supported on ART for now(201803). 所以android 4.4以下不兼容,4.4要切换成ART使用.
	/*
06-07 16:15:38.541 27021-27073/mi.sslpinningdemo W/System.err: java.lang.IllegalArgumentException: Required method checkServerTrusted(X509Certificate[], String, String, String) missing
06-07 16:15:38.542 27021-27073/mi.sslpinningdemo W/System.err:     at android.net.http.X509TrustManagerExtensions.<init>(X509TrustManagerExtensions.java:73)
        at mi.ssl.MiPinningTrustManger.<init>(MiPinningTrustManger.java:61)
06-07 16:15:38.543 27021-27073/mi.sslpinningdemo W/System.err:     at mi.sslpinningdemo.OkHttpUtil.getSecPinningClient(OkHttpUtil.java:112)
        at mi.sslpinningdemo.OkHttpUtil.get(OkHttpUtil.java:62)
        at mi.sslpinningdemo.MainActivity$1$1.run(MainActivity.java:36)
*/
	var X509Certificate = Java.use("java.security.cert.X509Certificate");
	var TrustManager;
	try {
		TrustManager = Java.registerClass({
			name: 'org.wooyun.TrustManager',
			implements: [X509TrustManager],
			methods: {
				checkClientTrusted: function(chain, authType) {},
				checkServerTrusted: function(chain, authType) {},
				getAcceptedIssuers: function() {
					// var certs = [X509Certificate.$new()];
					// return certs;
					return [];
				}
			}
		});
	} catch (e) {
		quiet_send("registerClass from X509TrustManager >>>>>>>> " + e.message);
	}





	// Prepare the TrustManagers array to pass to SSLContext.init()
	var TrustManagers = [TrustManager.$new()];

	try {
		// Prepare a Empty SSLFactory
		var TLS_SSLContext = SSLContext.getInstance("TLS");
		TLS_SSLContext.init(null, TrustManagers, null);
		var EmptySSLFactory = TLS_SSLContext.getSocketFactory();
	} catch (e) {
		quiet_send(e.message);
	}

	send('Custom, Empty TrustManager ready');

	// Get a handle on the init() on the SSLContext class
	var SSLContext_init = SSLContext.init.overload(
		'[Ljavax.net.ssl.KeyManager;', '[Ljavax.net.ssl.TrustManager;', 'java.security.SecureRandom');

	// Override the init method, specifying our new TrustManager
	SSLContext_init.implementation = function(keyManager, trustManager, secureRandom) {

		quiet_send('Overriding SSLContext.init() with the custom TrustManager');

		SSLContext_init.call(this, null, TrustManagers, null);
	};

	/*** okhttp3.x unpinning ***/


	// Wrap the logic in a try/catch as not all applications will have
	// okhttp as part of the app.
	try {

		var CertificatePinner = Java.use('okhttp3.CertificatePinner');

		quiet_send('OkHTTP 3.x Found');

		CertificatePinner.check.overload('java.lang.String', 'java.util.List').implementation = function() {

			quiet_send('OkHTTP 3.x check() called. Not throwing an exception.');
		}

	} catch (err) {

		// If we dont have a ClassNotFoundException exception, raise the
		// problem encountered.
		if (err.message.indexOf('ClassNotFoundException') === 0) {

			throw new Error(err);
		}
	}

	// Appcelerator Titanium PinningTrustManager

	// Wrap the logic in a try/catch as not all applications will have
	// appcelerator as part of the app.
	try {

		var PinningTrustManager = Java.use('appcelerator.https.PinningTrustManager');

		send('Appcelerator Titanium Found');

		PinningTrustManager.checkServerTrusted.implementation = function() {

			quiet_send('Appcelerator checkServerTrusted() called. Not throwing an exception.');
		}

	} catch (err) {

		// If we dont have a ClassNotFoundException exception, raise the
		// problem encountered.
		if (err.message.indexOf('ClassNotFoundException') === 0) {

			throw new Error(err);
		}
	}

	/*** okhttp unpinning ***/


	try {
		var OkHttpClient = Java.use("com.squareup.okhttp.OkHttpClient");
		OkHttpClient.setCertificatePinner.implementation = function(certificatePinner) {
			// do nothing
			quiet_send("OkHttpClient.setCertificatePinner Called!");
			return this;
		};

		// Invalidate the certificate pinnet checks (if "setCertificatePinner" was called before the previous invalidation)
		var CertificatePinner = Java.use("com.squareup.okhttp.CertificatePinner");
		CertificatePinner.check.overload('java.lang.String', '[Ljava.security.cert.Certificate;').implementation = function(p0, p1) {
			// do nothing
			quiet_send("okhttp Called! [Certificate]");
			return;
		};
		CertificatePinner.check.overload('java.lang.String', 'java.util.List').implementation = function(p0, p1) {
			// do nothing
			quiet_send("okhttp Called! [List]");
			return;
		};
	} catch (e) {
		quiet_send("com.squareup.okhttp not found");
	}

	/*** WebView Hooks ***/

	/* frameworks/base/core/java/android/webkit/WebViewClient.java */
	/* public void onReceivedSslError(Webview, SslErrorHandler, SslError) */
	var WebViewClient = Java.use("android.webkit.WebViewClient");

	WebViewClient.onReceivedSslError.implementation = function(webView, sslErrorHandler, sslError) {
		quiet_send("WebViewClient onReceivedSslError invoke");
		//执行proceed方法
		sslErrorHandler.proceed();
		return;
	};

	WebViewClient.onReceivedError.overload('android.webkit.WebView', 'int', 'java.lang.String', 'java.lang.String').implementation = function(a, b, c, d) {
		quiet_send("WebViewClient onReceivedError invoked");
		return;
	};

	WebViewClient.onReceivedError.overload('android.webkit.WebView', 'android.webkit.WebResourceRequest', 'android.webkit.WebResourceError').implementation = function() {
		quiet_send("WebViewClient onReceivedError invoked");
		return;
	};

	/*** JSSE Hooks ***/

	/* libcore/luni/src/main/java/javax/net/ssl/TrustManagerFactory.java */
	/* public final TrustManager[] getTrustManager() */
	/* TrustManagerFactory.getTrustManagers maybe cause X509TrustManagerExtensions error  */
	// var TrustManagerFactory = Java.use("javax.net.ssl.TrustManagerFactory");
	// TrustManagerFactory.getTrustManagers.implementation = function(){
	//     quiet_send("TrustManagerFactory getTrustManagers invoked");
	//     return TrustManagers;
	// }

	var HttpsURLConnection = Java.use("javax.net.ssl.HttpsURLConnection");
	/* libcore/luni/src/main/java/javax/net/ssl/HttpsURLConnection.java */
	/* public void setDefaultHostnameVerifier(HostnameVerifier) */
	HttpsURLConnection.setDefaultHostnameVerifier.implementation = function(hostnameVerifier) {
		quiet_send("HttpsURLConnection.setDefaultHostnameVerifier invoked");
		return null;
	};
	/* libcore/luni/src/main/java/javax/net/ssl/HttpsURLConnection.java */
	/* public void setSSLSocketFactory(SSLSocketFactory) */
	HttpsURLConnection.setSSLSocketFactory.implementation = function(SSLSocketFactory) {
		quiet_send("HttpsURLConnection.setSSLSocketFactory invoked");
		return null;
	};
	/* libcore/luni/src/main/java/javax/net/ssl/HttpsURLConnection.java */
	/* public void setHostnameVerifier(HostnameVerifier) */
	HttpsURLConnection.setHostnameVerifier.implementation = function(hostnameVerifier) {
		quiet_send("HttpsURLConnection.setHostnameVerifier invoked");
		return null;
	};

	/*** Xutils3.x hooks ***/
	//Implement a new HostnameVerifier
	var TrustHostnameVerifier;
	try {
		TrustHostnameVerifier = Java.registerClass({
			name: 'org.wooyun.TrustHostnameVerifier',
			implements: [HostnameVerifier],
			method: {
				verify: function(hostname, session) {
					return true;
				}
			}
		});

	} catch (e) {
		//java.lang.ClassNotFoundException: Didn't find class "org.wooyun.TrustHostnameVerifier"
		quiet_send("registerClass from hostnameVerifier >>>>>>>> " + e.message);
	}

	try {
		var RequestParams = Java.use('org.xutils.http.RequestParams');
		RequestParams.setSslSocketFactory.implementation = function(sslSocketFactory) {
			sslSocketFactory = EmptySSLFactory;
			return null;
		}

		RequestParams.setHostnameVerifier.implementation = function(hostnameVerifier) {
			hostnameVerifier = TrustHostnameVerifier.$new();
			return null;
		}

	} catch (e) {
		quiet_send("Xutils hooks not Found");
	}

	/*** httpclientandroidlib Hooks ***/
	try {
		var AbstractVerifier = Java.use("ch.boye.httpclientandroidlib.conn.ssl.AbstractVerifier");
		AbstractVerifier.verify.overload('java.lang.String', '[Ljava.lang.String', '[Ljava.lang.String', 'boolean').implementation = function() {
			quiet_send("httpclientandroidlib Hooks");
			return null;
		}
	} catch (e) {
		quiet_send("httpclientandroidlib Hooks not found");
	}

	/***
android 7.0+ network_security_config TrustManagerImpl hook
apache httpclient partly
***/
	var TrustManagerImpl = Java.use("com.android.org.conscrypt.TrustManagerImpl");
	// try {
	//     var Arrays = Java.use("java.util.Arrays");
	//     //apache http client pinning maybe baypass
	//     //https://github.com/google/conscrypt/blob/c88f9f55a523f128f0e4dace76a34724bfa1e88c/platform/src/main/java/org/conscrypt/TrustManagerImpl.java#471
	//     TrustManagerImpl.checkTrusted.implementation = function (chain, authType, session, parameters, authType) {
	//         quiet_send("TrustManagerImpl checkTrusted called");
	//         //Generics currently result in java.lang.Object
	//         return Arrays.asList(chain);
	//     }
	//
	// } catch (e) {
	//     quiet_send("TrustManagerImpl checkTrusted nout found");
	// }

	try {
		// Android 7+ TrustManagerImpl
		TrustManagerImpl.verifyChain.implementation = function(untrustedChain, trustAnchorChain, host, clientAuth, ocspData, tlsSctData) {
			quiet_send("TrustManagerImpl verifyChain called");
			// Skip all the logic and just return the chain again :P
			//https://www.nccgroup.trust/uk/about-us/newsroom-and-events/blogs/2017/november/bypassing-androids-network-security-configuration/
			// https://github.com/google/conscrypt/blob/c88f9f55a523f128f0e4dace76a34724bfa1e88c/platform/src/main/java/org/conscrypt/TrustManagerImpl.java#L650
			return untrustedChain;
		}
	} catch (e) {
		quiet_send("TrustManagerImpl verifyChain nout found below 7.0");
	}
	// OpenSSLSocketImpl
	try {
		var OpenSSLSocketImpl = Java.use('com.android.org.conscrypt.OpenSSLSocketImpl');
		OpenSSLSocketImpl.verifyCertificateChain.implementation = function(certRefs, authMethod) {
			quiet_send('OpenSSLSocketImpl.verifyCertificateChain');
		}

		quiet_send('OpenSSLSocketImpl pinning')
	} catch (err) {
		quiet_send('OpenSSLSocketImpl pinner not found');
	}
	// Trustkit
	try {
		var Activity = Java.use("com.datatheorem.android.trustkit.pinning.OkHostnameVerifier");
		Activity.verify.overload('java.lang.String', 'javax.net.ssl.SSLSession').implementation = function(str) {
			quiet_send('Trustkit.verify1: ' + str);
			return true;
		};
		Activity.verify.overload('java.lang.String', 'java.security.cert.X509Certificate').implementation = function(str) {
			quiet_send('Trustkit.verify2: ' + str);
			return true;
		};

		quiet_send('Trustkit pinning')
	} catch (err) {
		quiet_send('Trustkit pinner not found')
	}

	try {
		//cronet pinner hook
		//weibo don't invoke

		var netBuilder = Java.use("org.chromium.net.CronetEngine$Builder");

		//https://developer.android.com/guide/topics/connectivity/cronet/reference/org/chromium/net/CronetEngine.Builder.html#enablePublicKeyPinningBypassForLocalTrustAnchors(boolean)
		netBuilder.enablePublicKeyPinningBypassForLocalTrustAnchors.implementation = function(arg) {

			//weibo not invoke
			console.log("Enables or disables public key pinning bypass for local trust anchors = " + arg);

			//true to enable the bypass, false to disable.
			var ret = netBuilder.enablePublicKeyPinningBypassForLocalTrustAnchors.call(this, true);
			return ret;
		};

		netBuilder.addPublicKeyPins.implementation = function(hostName, pinsSha256, includeSubdomains, expirationDate) {
			console.log("cronet addPublicKeyPins hostName = " + hostName);

			//var ret = netBuilder.addPublicKeyPins.call(this,hostName, pinsSha256,includeSubdomains, expirationDate);
			//this 是调用 addPublicKeyPins 前的对象吗? Yes,CronetEngine.Builder
			return this;
		};

	} catch (err) {
		console.log('[-] Cronet pinner not found')
	}
});
