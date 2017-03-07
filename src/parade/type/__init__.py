from __future__ import unicode_literals
from collections import defaultdict

from .stdtypes import StringType, IntegerType, DecimalType, BoolType, DateType

_STRING_TYPE = StringType()
_INTEGER_TYPE = IntegerType()
_DECIMAL_TYPE = DecimalType()
_BOOLEAN_TYPE = BoolType()
_DATE_TYPE = DateType()


def str_to_stdtype(expr):
    norm_expr = expr.lower()
    if norm_expr.startswith('integer'):
        import re
        match_result = re.match(r'integer\((\d+)\)', norm_expr)
        if match_result is not None:
            return IntegerType(length=int(match_result.group(1)))
        return _INTEGER_TYPE
    if norm_expr == 'decimal':
        return _DECIMAL_TYPE
    if norm_expr == 'date':
        return _DATE_TYPE
    if norm_expr == 'bool' or norm_expr == 'boolean':
        return _BOOLEAN_TYPE
    if norm_expr.startswith('string'):
        match_result = re.match(r'string\((\d+)\)', norm_expr)
        if match_result is not None:
            return StringType(max_len=int(match_result.group(1)))
        return _STRING_TYPE
    raise RuntimeError("Unsupported data type [" + expr + "]")


def str_to_sqltype(expr):
    import re
    import sqlalchemy.types as sqltypes
    norm_expr = expr.lower()
    if norm_expr.startswith('integer'):
        match_result = re.match(r'integer\((\d+)\)', norm_expr)
        if match_result is not None:
            return sqltypes.BIGINT() if int(match_result.group(1)) > 11 else sqltypes.INTEGER()
        return sqltypes.BIGINT()
    if norm_expr == 'decimal':
        return sqltypes.DECIMAL()
    if norm_expr == 'date':
        return sqltypes.DATETIME()
    if norm_expr == 'bool' or norm_expr == 'boolean':
        return sqltypes.BOOLEAN()
    if norm_expr.startswith('string'):
        match_result = re.match(r'string\((\d+)\)', norm_expr)
        if match_result is not None:
            maxlen = int(match_result.group(1))
            return sqltypes.VARCHAR(maxlen) if maxlen < 65536 else sqltypes.TEXT
        return sqltypes.TEXT()
    raise RuntimeError("Unsupported data type [" + expr + "]")


def sqltype_to_stdtype(sqltype):
    import sqlalchemy.types as sqltypes
    if isinstance(sqltype, (sqltypes.VARCHAR, sqltypes.CHAR, sqltypes.TEXT, sqltypes.Enum, sqltypes.String)):
        return _STRING_TYPE
    if isinstance(sqltype, (sqltypes.DATETIME, sqltypes.DATE, sqltypes.TIME, sqltypes.TIMESTAMP)):
        return _DATE_TYPE
    if isinstance(sqltype, (sqltypes.INTEGER, sqltypes.BIGINT, sqltypes.SMALLINT, sqltypes.Integer)):
        return _INTEGER_TYPE
    if isinstance(sqltype, (sqltypes.REAL, sqltypes.DECIMAL, sqltypes.NUMERIC, sqltypes.FLOAT)):
        return _DECIMAL_TYPE
    if isinstance(sqltype, sqltypes.BOOLEAN):
        return _BOOLEAN_TYPE


def stdtype_to_sqltype(stdtype):
    import sqlalchemy.types as sqltypes
    if isinstance(stdtype, stdtypes.StringType):
        return sqltypes.VARCHAR(length=stdtype.max_len) if 0 < stdtype.max_len < 65536 else sqltypes.TEXT()
    if isinstance(stdtype, stdtypes.BoolType):
        return sqltypes.BOOLEAN()
    if isinstance(stdtype, stdtypes.DateType):
        return sqltypes.DATE() if stdtype.only_date else sqltypes.TIMESTAMP()
    if isinstance(stdtype, stdtypes.IntegerType):
        return sqltypes.BIGINT() if stdtype.length > 11 else sqltypes.INTEGER()
    if isinstance(stdtype, stdtypes.DecimalType):
        return sqltypes.DECIMAL()
    if isinstance(stdtype, stdtypes.ArrayType):
        return sqltypes.ARRAY(item_type=stdtype.item_type)


def type_guess(df, strict=False):
    """ The type guesser aggregates the number of successful
    conversions of each column to each type, weights them by a
    fixed type priority and select the most probable type for
    each column based on that figure. It returns a list of
    ``CellType``. Empty cells are ignored.
    Strict means that a type will not be guessed
    if parsing fails for a single cell in the column.
    :param df:
    :param strict: """
    guesses = []
    types = [_STRING_TYPE, _INTEGER_TYPE, _DECIMAL_TYPE, _BOOLEAN_TYPE, _DATE_TYPE]
    type_instances = [i for t in types for i in t.instances()]
    if strict:
        at_least_one_value = []
        for row in df.iterrows():
            # ri = row[0]
            cells = row[1]
            diff = len(cells) - len(guesses)
            for _ in range(diff):
                type_dict = {}
                for stdtype in type_instances:
                    type_dict[stdtype] = 0
                guesses.append(type_dict)
                at_least_one_value.append(False)
            for ci, cell in enumerate(cells.iteritems()):
                # key = cell[0]
                val = str(cell[1])
                if not val:
                    continue
                at_least_one_value[ci] = True
                for stdtype in list(guesses[ci].keys()):
                    if not stdtype.test(val):
                        guesses[ci].pop(stdtype)
        # no need to set guessing weights before this
        # because we only accept a type if it never fails
        for i, guess in enumerate(guesses):
            for stdtype in guess:
                guesses[i][stdtype] = stdtype.guessing_weight
        # in case there were no values at all in the column,
        # we just set the guessed type to string
        for i, v in enumerate(at_least_one_value):
            if not v:
                guesses[i] = {StringType(): 0}
    else:
        for row in df.iterrows():
            # i = row[0]
            cells = row[1]
            diff = len(cells) - len(guesses)
            for _ in range(diff):
                guesses.append(defaultdict(int))
            for i, cell in enumerate(cells.iteritems()):
                # add string guess so that we have at least one guess
                guesses[i][StringType()] = guesses[i].get(StringType(), 0)
                # key = cell[0]
                val = str(cell[1])
                if not val:
                    continue
                for stdtype in type_instances:
                    if stdtype.test(val):
                        guesses[i][stdtype] += stdtype.guessing_weight
    _columns = []
    for guess in guesses:
        # this first creates an array of tuples because we want the types to be
        # sorted. Even though it is not specified, python chooses the first
        # element in case of a tie
        # See: http://stackoverflow.com/a/6783101/214950
        guesses_tuples = [(t, guess[t]) for t in type_instances if t in guess]
        _columns.append(max(guesses_tuples, key=lambda t_n: t_n[1])[0])
    return dict(zip(df.columns, _columns))
