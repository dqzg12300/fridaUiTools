Java.perform(function () {
    function klog(data) {
        var message = {};
        message["jsname"] = "sqlite_logger";
        message["data"] = data;
        send(message);
    }

    klog('[sqlite_logger] init');

    function stringify(value) {
        if (value === null || value === undefined) {
            return 'null';
        }
        try {
            return value.toString();
        } catch (e) {
            return '' + value;
        }
    }

    function stringifyArray(values) {
        if (!values) {
            return '[]';
        }
        try {
            return JSON.stringify(values);
        } catch (e) {
            return values.toString();
        }
    }

    try {
        var SQLiteDatabase = Java.use('android.database.sqlite.SQLiteDatabase');

        var execSql = SQLiteDatabase.execSQL.overload('java.lang.String');
        execSql.implementation = function (sql) {
            klog('[sqlite_logger] execSQL => ' + sql);
            return execSql.call(this, sql);
        };

        var execSqlArgs = SQLiteDatabase.execSQL.overload('java.lang.String', '[Ljava.lang.Object;');
        execSqlArgs.implementation = function (sql, bindArgs) {
            klog('[sqlite_logger] execSQL => ' + sql + ' | args=' + stringifyArray(bindArgs));
            return execSqlArgs.call(this, sql, bindArgs);
        };

        var rawQuery = SQLiteDatabase.rawQuery.overload('java.lang.String', '[Ljava.lang.String;');
        rawQuery.implementation = function (sql, selectionArgs) {
            klog('[sqlite_logger] rawQuery => ' + sql + ' | args=' + stringifyArray(selectionArgs));
            return rawQuery.call(this, sql, selectionArgs);
        };

        var insertMethod = SQLiteDatabase.insert.overload('java.lang.String', 'java.lang.String', 'android.content.ContentValues');
        insertMethod.implementation = function (table, nullColumnHack, values) {
            klog('[sqlite_logger] insert => table=' + table + ', values=' + stringify(values));
            return insertMethod.call(this, table, nullColumnHack, values);
        };

        var updateMethod = SQLiteDatabase.update.overload('java.lang.String', 'android.content.ContentValues', 'java.lang.String', '[Ljava.lang.String;');
        updateMethod.implementation = function (table, values, whereClause, whereArgs) {
            klog('[sqlite_logger] update => table=' + table + ', where=' + stringify(whereClause) + ', whereArgs=' + stringifyArray(whereArgs) + ', values=' + stringify(values));
            return updateMethod.call(this, table, values, whereClause, whereArgs);
        };

        var deleteMethod = SQLiteDatabase.delete.overload('java.lang.String', 'java.lang.String', '[Ljava.lang.String;');
        deleteMethod.implementation = function (table, whereClause, whereArgs) {
            klog('[sqlite_logger] delete => table=' + table + ', where=' + stringify(whereClause) + ', whereArgs=' + stringifyArray(whereArgs));
            return deleteMethod.call(this, table, whereClause, whereArgs);
        };
    } catch (e) {
        klog('[sqlite_logger] hook failed: ' + e);
    }
});
