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
//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJzb3VyY2VzIjpbIm5vZGVfbW9kdWxlcy9icm93c2VyLXBhY2svX3ByZWx1ZGUuanMiLCJub2RlX21vZHVsZXMvQGJhYmVsL3J1bnRpbWUtY29yZWpzMi9jb3JlLWpzL2pzb24vc3RyaW5naWZ5LmpzIiwibm9kZV9tb2R1bGVzL0BiYWJlbC9ydW50aW1lLWNvcmVqczIvY29yZS1qcy9vYmplY3QvZGVmaW5lLXByb3BlcnR5LmpzIiwibm9kZV9tb2R1bGVzL0BiYWJlbC9ydW50aW1lLWNvcmVqczIvaGVscGVycy9jbGFzc0NhbGxDaGVjay5qcyIsIm5vZGVfbW9kdWxlcy9AYmFiZWwvcnVudGltZS1jb3JlanMyL2hlbHBlcnMvY3JlYXRlQ2xhc3MuanMiLCJub2RlX21vZHVsZXMvQGJhYmVsL3J1bnRpbWUtY29yZWpzMi9oZWxwZXJzL2ludGVyb3BSZXF1aXJlRGVmYXVsdC5qcyIsIm5vZGVfbW9kdWxlcy9jb3JlLWpzL2xpYnJhcnkvZm4vanNvbi9zdHJpbmdpZnkuanMiLCJub2RlX21vZHVsZXMvY29yZS1qcy9saWJyYXJ5L2ZuL29iamVjdC9kZWZpbmUtcHJvcGVydHkuanMiLCJub2RlX21vZHVsZXMvY29yZS1qcy9saWJyYXJ5L21vZHVsZXMvX2EtZnVuY3Rpb24uanMiLCJub2RlX21vZHVsZXMvY29yZS1qcy9saWJyYXJ5L21vZHVsZXMvX2FuLW9iamVjdC5qcyIsIm5vZGVfbW9kdWxlcy9jb3JlLWpzL2xpYnJhcnkvbW9kdWxlcy9fY29yZS5qcyIsIm5vZGVfbW9kdWxlcy9jb3JlLWpzL2xpYnJhcnkvbW9kdWxlcy9fY3R4LmpzIiwibm9kZV9tb2R1bGVzL2NvcmUtanMvbGlicmFyeS9tb2R1bGVzL19kZXNjcmlwdG9ycy5qcyIsIm5vZGVfbW9kdWxlcy9jb3JlLWpzL2xpYnJhcnkvbW9kdWxlcy9fZG9tLWNyZWF0ZS5qcyIsIm5vZGVfbW9kdWxlcy9jb3JlLWpzL2xpYnJhcnkvbW9kdWxlcy9fZXhwb3J0LmpzIiwibm9kZV9tb2R1bGVzL2NvcmUtanMvbGlicmFyeS9tb2R1bGVzL19mYWlscy5qcyIsIm5vZGVfbW9kdWxlcy9jb3JlLWpzL2xpYnJhcnkvbW9kdWxlcy9fZ2xvYmFsLmpzIiwibm9kZV9tb2R1bGVzL2NvcmUtanMvbGlicmFyeS9tb2R1bGVzL19oYXMuanMiLCJub2RlX21vZHVsZXMvY29yZS1qcy9saWJyYXJ5L21vZHVsZXMvX2hpZGUuanMiLCJub2RlX21vZHVsZXMvY29yZS1qcy9saWJyYXJ5L21vZHVsZXMvX2llOC1kb20tZGVmaW5lLmpzIiwibm9kZV9tb2R1bGVzL2NvcmUtanMvbGlicmFyeS9tb2R1bGVzL19pcy1vYmplY3QuanMiLCJub2RlX21vZHVsZXMvY29yZS1qcy9saWJyYXJ5L21vZHVsZXMvX29iamVjdC1kcC5qcyIsIm5vZGVfbW9kdWxlcy9jb3JlLWpzL2xpYnJhcnkvbW9kdWxlcy9fcHJvcGVydHktZGVzYy5qcyIsIm5vZGVfbW9kdWxlcy9jb3JlLWpzL2xpYnJhcnkvbW9kdWxlcy9fdG8tcHJpbWl0aXZlLmpzIiwibm9kZV9tb2R1bGVzL2NvcmUtanMvbGlicmFyeS9tb2R1bGVzL2VzNi5vYmplY3QuZGVmaW5lLXByb3BlcnR5LmpzIiwic3JjL2NsYXNza2l0LnRzIiwic3JjL2luZGV4LnRzIiwic3JjL29iamVjdGtpdC50cyIsInNyYy9zdHJ1Y3QudHMiLCJzcmMvdXRpbHMudHMiXSwibmFtZXMiOltdLCJtYXBwaW5ncyI6IkFBQUE7QUNBQTs7QUNBQTs7QUNBQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTs7QUNOQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBOztBQ25CQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTs7QUNOQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7O0FDTEE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBOztBQ0xBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7O0FDSkE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBOztBQ0xBO0FBQ0E7QUFDQTs7QUNGQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7O0FDcEJBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7O0FDSkE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTs7QUNQQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7O0FDOURBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7O0FDUEE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7O0FDTkE7QUFDQTtBQUNBO0FBQ0E7QUFDQTs7QUNKQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7O0FDUkE7QUFDQTtBQUNBO0FBQ0E7O0FDSEE7QUFDQTtBQUNBO0FBQ0E7O0FDSEE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTs7QUNoQkE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBOztBQ1JBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFD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


})();
