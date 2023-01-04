(function(){
  (function(){function r(e,n,t){function o(i,f){if(!n[i]){if(!e[i]){var c="function"==typeof require&&require;if(!f&&c)return c(i,!0);if(u)return u(i,!0);var a=new Error("Cannot find module '"+i+"'");throw a.code="MODULE_NOT_FOUND",a}var p=n[i]={exports:{}};e[i][0].call(p.exports,function(r){var n=e[i][1][r];return o(n||r)},p,p.exports,r,e,n,t)}return n[i].exports}for(var u="function"==typeof require&&require,i=0;i<t.length;i++)o(t[i]);return o}return r})()({1:[function(require,module,exports){
module.exports = require("core-js/library/fn/json/stringify");
},{"core-js/library/fn/json/stringify":6}],2:[function(require,module,exports){
module.exports = require("core-js/library/fn/object/define-property");
},{"core-js/library/fn/object/define-property":7}],3:[function(require,module,exports){
function _classCallCheck(instance, Constructor) {
  if (!(instance instanceof Constructor)) {
    throw new TypeError("Cannot call a class as a function");
  }
}

module.exports = _classCallCheck;
},{}],4:[function(require,module,exports){
var _Object$defineProperty = require("../core-js/object/define-property");

function _defineProperties(target, props) {
  for (var i = 0; i < props.length; i++) {
    var descriptor = props[i];
    descriptor.enumerable = descriptor.enumerable || false;
    descriptor.configurable = true;
    if ("value" in descriptor) descriptor.writable = true;

    _Object$defineProperty(target, descriptor.key, descriptor);
  }
}

function _createClass(Constructor, protoProps, staticProps) {
  if (protoProps) _defineProperties(Constructor.prototype, protoProps);
  if (staticProps) _defineProperties(Constructor, staticProps);
  return Constructor;
}

module.exports = _createClass;
},{"../core-js/object/define-property":2}],5:[function(require,module,exports){
function _interopRequireDefault(obj) {
  return obj && obj.__esModule ? obj : {
    "default": obj
  };
}

module.exports = _interopRequireDefault;
},{}],6:[function(require,module,exports){
var core = require('../../modules/_core');
var $JSON = core.JSON || (core.JSON = { stringify: JSON.stringify });
module.exports = function stringify(it) { // eslint-disable-line no-unused-vars
  return $JSON.stringify.apply($JSON, arguments);
};

},{"../../modules/_core":10}],7:[function(require,module,exports){
require('../../modules/es6.object.define-property');
var $Object = require('../../modules/_core').Object;
module.exports = function defineProperty(it, key, desc) {
  return $Object.defineProperty(it, key, desc);
};

},{"../../modules/_core":10,"../../modules/es6.object.define-property":24}],8:[function(require,module,exports){
module.exports = function (it) {
  if (typeof it != 'function') throw TypeError(it + ' is not a function!');
  return it;
};

},{}],9:[function(require,module,exports){
var isObject = require('./_is-object');
module.exports = function (it) {
  if (!isObject(it)) throw TypeError(it + ' is not an object!');
  return it;
};

},{"./_is-object":20}],10:[function(require,module,exports){
var core = module.exports = { version: '2.6.11' };
if (typeof __e == 'number') __e = core; // eslint-disable-line no-undef

},{}],11:[function(require,module,exports){
// optional / simple context binding
var aFunction = require('./_a-function');
module.exports = function (fn, that, length) {
  aFunction(fn);
  if (that === undefined) return fn;
  switch (length) {
    case 1: return function (a) {
      return fn.call(that, a);
    };
    case 2: return function (a, b) {
      return fn.call(that, a, b);
    };
    case 3: return function (a, b, c) {
      return fn.call(that, a, b, c);
    };
  }
  return function (/* ...args */) {
    return fn.apply(that, arguments);
  };
};

},{"./_a-function":8}],12:[function(require,module,exports){
// Thank's IE8 for his funny defineProperty
module.exports = !require('./_fails')(function () {
  return Object.defineProperty({}, 'a', { get: function () { return 7; } }).a != 7;
});

},{"./_fails":15}],13:[function(require,module,exports){
var isObject = require('./_is-object');
var document = require('./_global').document;
// typeof document.createElement is 'object' in old IE
var is = isObject(document) && isObject(document.createElement);
module.exports = function (it) {
  return is ? document.createElement(it) : {};
};

},{"./_global":16,"./_is-object":20}],14:[function(require,module,exports){
var global = require('./_global');
var core = require('./_core');
var ctx = require('./_ctx');
var hide = require('./_hide');
var has = require('./_has');
var PROTOTYPE = 'prototype';

var $export = function (type, name, source) {
  var IS_FORCED = type & $export.F;
  var IS_GLOBAL = type & $export.G;
  var IS_STATIC = type & $export.S;
  var IS_PROTO = type & $export.P;
  var IS_BIND = type & $export.B;
  var IS_WRAP = type & $export.W;
  var exports = IS_GLOBAL ? core : core[name] || (core[name] = {});
  var expProto = exports[PROTOTYPE];
  var target = IS_GLOBAL ? global : IS_STATIC ? global[name] : (global[name] || {})[PROTOTYPE];
  var key, own, out;
  if (IS_GLOBAL) source = name;
  for (key in source) {
    // contains in native
    own = !IS_FORCED && target && target[key] !== undefined;
    if (own && has(exports, key)) continue;
    // export native or passed
    out = own ? target[key] : source[key];
    // prevent global pollution for namespaces
    exports[key] = IS_GLOBAL && typeof target[key] != 'function' ? source[key]
    // bind timers to global for call from export context
    : IS_BIND && own ? ctx(out, global)
    // wrap global constructors for prevent change them in library
    : IS_WRAP && target[key] == out ? (function (C) {
      var F = function (a, b, c) {
        if (this instanceof C) {
          switch (arguments.length) {
            case 0: return new C();
            case 1: return new C(a);
            case 2: return new C(a, b);
          } return new C(a, b, c);
        } return C.apply(this, arguments);
      };
      F[PROTOTYPE] = C[PROTOTYPE];
      return F;
    // make static versions for prototype methods
    })(out) : IS_PROTO && typeof out == 'function' ? ctx(Function.call, out) : out;
    // export proto methods to core.%CONSTRUCTOR%.methods.%NAME%
    if (IS_PROTO) {
      (exports.virtual || (exports.virtual = {}))[key] = out;
      // export proto methods to core.%CONSTRUCTOR%.prototype.%NAME%
      if (type & $export.R && expProto && !expProto[key]) hide(expProto, key, out);
    }
  }
};
// type bitmap
$export.F = 1;   // forced
$export.G = 2;   // global
$export.S = 4;   // static
$export.P = 8;   // proto
$export.B = 16;  // bind
$export.W = 32;  // wrap
$export.U = 64;  // safe
$export.R = 128; // real proto method for `library`
module.exports = $export;

},{"./_core":10,"./_ctx":11,"./_global":16,"./_has":17,"./_hide":18}],15:[function(require,module,exports){
module.exports = function (exec) {
  try {
    return !!exec();
  } catch (e) {
    return true;
  }
};

},{}],16:[function(require,module,exports){
// https://github.com/zloirock/core-js/issues/86#issuecomment-115759028
var global = module.exports = typeof window != 'undefined' && window.Math == Math
  ? window : typeof self != 'undefined' && self.Math == Math ? self
  // eslint-disable-next-line no-new-func
  : Function('return this')();
if (typeof __g == 'number') __g = global; // eslint-disable-line no-undef

},{}],17:[function(require,module,exports){
var hasOwnProperty = {}.hasOwnProperty;
module.exports = function (it, key) {
  return hasOwnProperty.call(it, key);
};

},{}],18:[function(require,module,exports){
var dP = require('./_object-dp');
var createDesc = require('./_property-desc');
module.exports = require('./_descriptors') ? function (object, key, value) {
  return dP.f(object, key, createDesc(1, value));
} : function (object, key, value) {
  object[key] = value;
  return object;
};

},{"./_descriptors":12,"./_object-dp":21,"./_property-desc":22}],19:[function(require,module,exports){
module.exports = !require('./_descriptors') && !require('./_fails')(function () {
  return Object.defineProperty(require('./_dom-create')('div'), 'a', { get: function () { return 7; } }).a != 7;
});

},{"./_descriptors":12,"./_dom-create":13,"./_fails":15}],20:[function(require,module,exports){
module.exports = function (it) {
  return typeof it === 'object' ? it !== null : typeof it === 'function';
};

},{}],21:[function(require,module,exports){
var anObject = require('./_an-object');
var IE8_DOM_DEFINE = require('./_ie8-dom-define');
var toPrimitive = require('./_to-primitive');
var dP = Object.defineProperty;

exports.f = require('./_descriptors') ? Object.defineProperty : function defineProperty(O, P, Attributes) {
  anObject(O);
  P = toPrimitive(P, true);
  anObject(Attributes);
  if (IE8_DOM_DEFINE) try {
    return dP(O, P, Attributes);
  } catch (e) { /* empty */ }
  if ('get' in Attributes || 'set' in Attributes) throw TypeError('Accessors not supported!');
  if ('value' in Attributes) O[P] = Attributes.value;
  return O;
};

},{"./_an-object":9,"./_descriptors":12,"./_ie8-dom-define":19,"./_to-primitive":23}],22:[function(require,module,exports){
module.exports = function (bitmap, value) {
  return {
    enumerable: !(bitmap & 1),
    configurable: !(bitmap & 2),
    writable: !(bitmap & 4),
    value: value
  };
};

},{}],23:[function(require,module,exports){
// 7.1.1 ToPrimitive(input [, PreferredType])
var isObject = require('./_is-object');
// instead of the ES6 spec version, we didn't implement @@toPrimitive case
// and the second argument - flag - preferred type is a string
module.exports = function (it, S) {
  if (!isObject(it)) return it;
  var fn, val;
  if (S && typeof (fn = it.toString) == 'function' && !isObject(val = fn.call(it))) return val;
  if (typeof (fn = it.valueOf) == 'function' && !isObject(val = fn.call(it))) return val;
  if (!S && typeof (fn = it.toString) == 'function' && !isObject(val = fn.call(it))) return val;
  throw TypeError("Can't convert object to primitive value");
};

},{"./_is-object":20}],24:[function(require,module,exports){
var $export = require('./_export');
// 19.1.2.4 / 15.2.3.6 Object.defineProperty(O, P, Attributes)
$export($export.S + $export.F * !require('./_descriptors'), 'Object', { defineProperty: require('./_object-dp').f });

},{"./_descriptors":12,"./_export":14,"./_object-dp":21}],25:[function(require,module,exports){
"use strict";
/*
* Author: hluwa <hluwa888@gmail.com>
* HomePage: https://github.com/hluwa
* CreateTime: 2019/12/4
* */

var _interopRequireDefault = require("@babel/runtime-corejs2/helpers/interopRequireDefault");

var _defineProperty = _interopRequireDefault(require("@babel/runtime-corejs2/core-js/object/define-property"));

(0, _defineProperty["default"])(exports, "__esModule", {
  value: true
});

var struct_1 = require("./struct");

exports.match = function (name) {
  var result = [];

  try {
    Java.perform(function () {
      Java.enumerateLoadedClassesSync().forEach(function (p1) {
        if (p1.startsWith("[")) {
          return;
        }

        if (p1.match(name)) {
          result.push(p1);
        }
      });
    });
  } catch (e) {}

  return result;
};

exports.use = function (name) {
  var result = struct_1.ClassWrapper.NONE;
  Java.perform(function () {
    result = struct_1.ClassWrapper.byWrapper(Java.use(name));
  });
  return result;
};

},{"./struct":28,"@babel/runtime-corejs2/core-js/object/define-property":2,"@babel/runtime-corejs2/helpers/interopRequireDefault":5}],26:[function(require,module,exports){
"use strict";

var _interopRequireDefault = require("@babel/runtime-corejs2/helpers/interopRequireDefault");

var _stringify = _interopRequireDefault(require("@babel/runtime-corejs2/core-js/json/stringify"));

var _defineProperty = _interopRequireDefault(require("@babel/runtime-corejs2/core-js/object/define-property"));

(0, _defineProperty["default"])(exports, "__esModule", {
  value: true
});
/*
* Author: hluwa <hluwa888@gmail.com>
* HomePage: https://github.com/hluwa
* CreateTime: 2019/12/4
* */

var classkit_1 = require("./classkit");

var objectkit_1 = require("./objectkit");

rpc.exports.classMatch=function classMatch(name) {
    return classkit_1.match(name);
  };

rpc.exports.classUse=function classUse(name) {
    var clazz = classkit_1.use(name);
    return (0, _stringify["default"])(clazz);
  }

rpc.exports.objectSearch=function objectSearch(clazz, stop) {
    return objectkit_1.searchHandles(clazz, stop);
  }

rpc.exports.objectGetClass=function objectGetClass(handle) {
    return objectkit_1.getRealClassNameByHandle(handle);
  }

rpc.exports.objectGetField=function objectGetField(handle, field, clazz) {
    return objectkit_1.getObjectFieldValue(handle, field, clazz);
  }

rpc.exports.instanceOf=function instanceOf(handle, className) {
    return objectkit_1.instanceOf(handle, className);
  }

rpc.exports.mapDump=function mapDump(handle) {
    return objectkit_1.mapDump(handle);
  }

rpc.exports.collectionDump=function collectionDump(handle) {
    return objectkit_1.collectionDump(handle);
  }

// rpc.exports = {
//   classMatch: function classMatch(name) {
//     return classkit_1.match(name);
//   },
//   classUse: function classUse(name) {
//     var clazz = classkit_1.use(name);
//     return (0, _stringify["default"])(clazz);
//   },
//   objectSearch: function objectSearch(clazz, stop) {
//     return objectkit_1.searchHandles(clazz, stop);
//   },
//   objectGetClass: function objectGetClass(handle) {
//     return objectkit_1.getRealClassNameByHandle(handle);
//   },
//   objectGetField: function objectGetField(handle, field, clazz) {
//     return objectkit_1.getObjectFieldValue(handle, field, clazz);
//   },
//   instanceOf: function instanceOf(handle, className) {
//     return objectkit_1.instanceOf(handle, className);
//   },
//   mapDump: function mapDump(handle) {
//     return objectkit_1.mapDump(handle);
//   },
//   collectionDump: function collectionDump(handle) {
//     return objectkit_1.collectionDump(handle);
//   }
// };

},{"./classkit":25,"./objectkit":27,"@babel/runtime-corejs2/core-js/json/stringify":1,"@babel/runtime-corejs2/core-js/object/define-property":2,"@babel/runtime-corejs2/helpers/interopRequireDefault":5}],27:[function(require,module,exports){
"use strict";
/*
* Author: hluwa <hluwa888@gmail.com>
* HomePage: https://github.com/hluwa
* CreatedTime: 2020/6/12 22:09
* */

var _interopRequireDefault = require("@babel/runtime-corejs2/helpers/interopRequireDefault");

var _defineProperty = _interopRequireDefault(require("@babel/runtime-corejs2/core-js/object/define-property"));

(0, _defineProperty["default"])(exports, "__esModule", {
  value: true
});

var utils_1 = require("./utils");

exports.handleCache = {};

function getRealClassName(object) {
  var objClass = Java.use("java.lang.Object").getClass.apply(object);
  return Java.use("java.lang.Class").getName.apply(objClass);
}

function objectToStr(object) {
  try {
    return Java.use("java.lang.Object").toString.apply(object);
  } catch (e) {
    return "" + object;
  }
}

exports.searchHandles = function (clazz) {
  var stop = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : false;
  var result = {};

  var f = function f() {
    Java.choose(clazz, {
      onComplete: function onComplete() {},
      onMatch: function onMatch(instance) {
        var handle = utils_1.getHandle(instance);

        if (handle != null) {
          result[handle] = objectToStr(instance);
        }

        if (stop) {
          return "stop";
        }
      }
    });
  };

  Java.perform(f);
  return result;
};

exports.getRealClassNameByHandle = function (handle) {
  var result = null;
  Java.perform(function () {
    try {
      var obj = Java.use("java.lang.Object");
      var jObject = Java.cast(ptr(handle), obj);
      result = getRealClassName(jObject);
    } catch (e) {}
  });
  return result;
};

var getObjectByHandle = function getObjectByHandle(handle) {
  if (!utils_1.hasOwnProperty(exports.handleCache, handle)) {
    if (handle.startsWith("0x")) {
      var origClassName = exports.getRealClassNameByHandle(handle);

      if (!origClassName) {
        return;
      }

      exports.handleCache[handle] = Java.cast(ptr(handle), Java.use(origClassName));
    } else {
      exports.handleCache[handle] = Java.use(handle);
    }
  }

  return exports.handleCache[handle];
};

exports.getObjectFieldValue = function (handle, field, clazz) {
  var result = "null";
  Java.perform(function () {
    var origObject = getObjectByHandle(handle);

    if (clazz) {
      origObject = Java.cast(origObject, Java.use(clazz));
    }

    var value = utils_1.getOwnProperty(origObject, "_" + field);

    if (value == null) {
      value = utils_1.getOwnProperty(origObject, field);
    }

    if (value == null || value.value == null) {
      value = "null";
    } else {
      value = value.value;

      if (value == null) {
        value = "null";
      } else {
        var _handle = utils_1.getHandle(value);

        if (_handle != null) {
          console.log(field + " => " + value);
          value = "[" + _handle + "]: " + objectToStr(value).split("\n").join(" \\n ");
        }
      }
    }

    result = value.toString();
  });
  return result;
};

exports.instanceOf = function (handle, className) {
  var result = false;
  Java.perform(function () {
    try {
      var targetClass = Java.use(className);
      var newObject = Java.cast(getObjectByHandle(handle), targetClass);
      result = !!newObject;
    } catch (e) {
      result = false;
    }
  });
  return result;
};

exports.mapDump = function (handle) {
  var result = {};
  Java.perform(function () {
    try {
      var mapClass = Java.use("java.util.Map");
      var entryClass = Java.use("java.util.Map$Entry");
      var mapObject = getObjectByHandle(handle);
      var entrySet = mapClass.entrySet.apply(mapObject).iterator();

      while (entrySet.hasNext()) {
        var entry = Java.cast(entrySet.next(), entryClass);
        var key = entry.getKey();
        var keyHandle = utils_1.getHandle(key);

        if (key == null || keyHandle == null) {
          continue;
        }

        var value = entry.getValue();
        var valueHandle = utils_1.getHandle(value);

        if (value == null || valueHandle == null) {
          continue;
        }

        result["[" + keyHandle + "]: " + objectToStr(key)] = "[" + valueHandle + "]: " + objectToStr(value);
      }
    } catch (e) {
      console.error(e);
    }
  });
  return result;
};

exports.collectionDump = function (handle) {
  var result = [];
  Java.perform(function () {
    try {
      var collectionClass = Java.use("java.util.Collection");
      var collectionObject = getObjectByHandle(handle);
      var objectArray = collectionClass.toArray.apply(collectionObject);
      objectArray.forEach(function (element) {
        var eleHandle = utils_1.getHandle(element);
        result.push('[' + eleHandle + ']: ' + objectToStr(element));
      });
    } catch (e) {
      console.error(e);
    }
  });
  return result;
};

},{"./utils":29,"@babel/runtime-corejs2/core-js/object/define-property":2,"@babel/runtime-corejs2/helpers/interopRequireDefault":5}],28:[function(require,module,exports){
"use strict";
/*
* Author: hluwa <hluwa888@gmail.com>
* HomePage: https://github.com/hluwa
* CreatedTime: 2019/12/4 01:35
* */

var _interopRequireDefault = require("@babel/runtime-corejs2/helpers/interopRequireDefault");

var _classCallCheck2 = _interopRequireDefault(require("@babel/runtime-corejs2/helpers/classCallCheck"));

var _createClass2 = _interopRequireDefault(require("@babel/runtime-corejs2/helpers/createClass"));

var _defineProperty = _interopRequireDefault(require("@babel/runtime-corejs2/core-js/object/define-property"));

(0, _defineProperty["default"])(exports, "__esModule", {
  value: true
});

var utils_1 = require("./utils");

var ClassWrapper = /*#__PURE__*/function () {
  function ClassWrapper(handle) {
    (0, _classCallCheck2["default"])(this, ClassWrapper);
    this.constructors = [];
    this.staticMethods = {};
    this.instanceMethods = {};
    this.staticFields = {};
    this.instanceFields = {};
    this["implements"] = []; // console.log('come into consturtor')

    if (!handle) {
      this.name = "NONE";
      this["super"] = "NONE";
      return;
    }

    this.name = handle.$className;
    this["super"] = handle["class"].getSuperclass().getName(); // extract methods and fields

    var __this = this;

    var methods = handle["class"].getDeclaredMethods();
    methods.forEach(function (method) {
      var wrapper = new MethodWrapper(__this, method, false);

      if (wrapper.isStatic) {
        if (!__this.staticMethods.hasOwnProperty(wrapper.name)) {
          __this.staticMethods[wrapper.name] = [];
        }

        __this.staticMethods[wrapper.name].push(wrapper);
      } else {
        if (!__this.instanceMethods.hasOwnProperty(wrapper.name)) {
          __this.instanceMethods[wrapper.name] = [];
        }

        __this.instanceMethods[wrapper.name].push(wrapper);
      }
    });
    var jConstructors = handle["class"].getDeclaredConstructors();
    jConstructors.forEach(function (jConstructor) {
      var wrapper = new MethodWrapper(__this, jConstructor, true);

      __this.constructors.push(wrapper);
    });
    var fields = handle["class"].getDeclaredFields();
    fields.forEach(function (field) {
      var wrapper = new FieldWrapper(field);

      if (wrapper.isStatic) {
        if (!__this.staticFields.hasOwnProperty(wrapper.name)) {
          __this.staticFields[wrapper.name] = [];
        }

        __this.staticFields[wrapper.name].push(wrapper);
      } else {
        if (!__this.instanceFields.hasOwnProperty(wrapper.name)) {
          __this.instanceFields[wrapper.name] = [];
        }

        __this.instanceFields[wrapper.name].push(wrapper);
      }
    }); // get implemented interfaces

    var _this = this;

    handle["class"].getInterfaces().forEach(function (interfaceClass) {
      _this["implements"].push(interfaceClass.getName());
    });
  }

  (0, _createClass2["default"])(ClassWrapper, null, [{
    key: "byWrapper",
    value: function byWrapper(handle) {
      var name = handle["class"].getName();

      if (!(name in ClassWrapper.cache)) {
        ClassWrapper.cache[name] = new ClassWrapper(handle);
      }

      return ClassWrapper.cache[name];
    }
  }]);
  return ClassWrapper;
}();

exports.ClassWrapper = ClassWrapper;
ClassWrapper.cache = {};
ClassWrapper.NONE = new ClassWrapper(null);

var MethodWrapper = function MethodWrapper(own, handle, isConstructor) {
  (0, _classCallCheck2["default"])(this, MethodWrapper);
  this.arguments = [];

  var _this = this;

  this.ownClass = own.name;
  this.name = handle.getName();
  handle.getParameterTypes().forEach(function (t) {
    _this.arguments.push(t.getName());
  });
  this.isConstructor = isConstructor;

  if (!this.isConstructor) {
    this.retType = handle.getReturnType().getName();
  } else {
    this.retType = '';
  }

  this.isStatic = utils_1.isStatic(handle);
};

exports.MethodWrapper = MethodWrapper;

var FieldWrapper = function FieldWrapper(handle) {
  (0, _classCallCheck2["default"])(this, FieldWrapper);
  this.isStatic = utils_1.isStatic(handle);
  this.name = handle.getName();
  this.type = handle.getType().getName();
};

exports.FieldWrapper = FieldWrapper;

},{"./utils":29,"@babel/runtime-corejs2/core-js/object/define-property":2,"@babel/runtime-corejs2/helpers/classCallCheck":3,"@babel/runtime-corejs2/helpers/createClass":4,"@babel/runtime-corejs2/helpers/interopRequireDefault":5}],29:[function(require,module,exports){
"use strict";
/*
* Author: hluwa <hluwa888@gmail.com>
* HomePage: https://github.com/hluwa
* CreatedTime: 2020/6/13 00:30
* */

var _interopRequireDefault = require("@babel/runtime-corejs2/helpers/interopRequireDefault");

var _defineProperty = _interopRequireDefault(require("@babel/runtime-corejs2/core-js/object/define-property"));

(0, _defineProperty["default"])(exports, "__esModule", {
  value: true
});

var objectkit_1 = require("./objectkit");

function hasOwnProperty(obj, name) {
  try {
    return obj.hasOwnProperty(name) || name in obj;
  } catch (e) {
    return false;
  }
}

exports.hasOwnProperty = hasOwnProperty;

function getOwnProperty(obj, name) {
  if (!hasOwnProperty(obj, name)) {
    return null;
  }

  var result = null;

  try {
    result = obj[name];

    if (result) {
      return result;
    }
  } catch (e) {}

  try {
    result = obj.getOwnProperty(name);

    if (result) {
      return result;
    }
  } catch (e) {}

  return result;
}

exports.getOwnProperty = getOwnProperty;

function getHandle(object) {
  try {
    object = Java.retain(object);

    if (hasOwnProperty(object, '$handle') && object.$handle != undefined) {
      objectkit_1.handleCache[object.$handle] = object;
      return object.$handle;
    } else if (hasOwnProperty(object, '$h') && object.$h != undefined) {
      objectkit_1.handleCache[object.$h] = object;
      return object.$h;
    } else {
      var hashcode = Java.use("java.lang.Object").hashCode.apply(object);
      objectkit_1.handleCache[hashcode] = object;
      return hashcode;
    }
  } catch (e) {
    return null;
  }
}

exports.getHandle = getHandle;

exports.isStatic = function (obj) {
  return (obj.getModifiers() & 0x8) != 0;
};

},{"./objectkit":27,"@babel/runtime-corejs2/core-js/object/define-property":2,"@babel/runtime-corejs2/helpers/interopRequireDefault":5}]},{},[26])


})();
