from qicode import QiType


def test_array_type_stringification():
    qi_array = QiType.ARRAY(QiType.NORMAL)
    assert str(qi_array) == "Array[NORMAL, ?]"

    qi_array = QiType.ARRAY(QiType.NORMAL, 10)
    assert str(qi_array) == "Array[NORMAL, 10]"


def type_should_hash():
    hash(QiType.AMPLITUDE)
    hash(QiType.UNKNOWN)
    hash(QiType.ARRAY(QiType.UNKNOWN))
    hash(QiType.ARRAY(QiType.PHASE))
    hash(QiType.ARRAY(QiType.PHASE, 10))


def test_scalar_type_is_hashable_and_usable_as_dict_key():
    d = {}
    d[QiType.NORMAL] = "normal"
    d[QiType.TIME] = "time"
    assert d[QiType.NORMAL] == "normal"
    assert d[QiType.TIME] == "time"
    assert len(d) == 2


def test_unknown_type_is_hashable():
    s = set()
    s.add(QiType.UNKNOWN)
    s.add(QiType.UNKNOWN)
    assert len(s) == 1


def test_array_type_is_hashable():
    arr = QiType.ARRAY(QiType.NORMAL, length=4)
    d = {arr: "array_val"}
    assert d[arr] == "array_val"


def test_equal_scalars_have_same_hash():
    a = QiType(QiType.NORMAL._proto())
    b = QiType(QiType.NORMAL._proto())
    assert a == b
    assert hash(a) == hash(b)


def test_different_scalars_have_different_hash():
    assert hash(QiType.NORMAL) != hash(QiType.TIME)


def test_scalar_unknown_array_in_same_set():
    arr = QiType.ARRAY(QiType.NORMAL, length=2)
    s = {QiType.NORMAL, QiType.UNKNOWN, arr}
    assert len(s) == 3
    assert QiType.NORMAL in s
    assert QiType.UNKNOWN in s
    assert arr in s
