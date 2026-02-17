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
