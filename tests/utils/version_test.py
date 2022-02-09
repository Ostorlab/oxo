from ostorlab.utils import version


def testVersionComparison_always_returnsCorrectValue():
    assert version.Version("100.9900.0") > version.Version("19.0.0")

def testVersionComparison2_always_returnsCorrectValue():
    assert version.Version("100.9900.0") > version.Version("1.0.0")

def testVersionComparison_whenEqual_returnsTrue():
    assert version.Version("100.9900.0") == version.Version("100.9900.0")

def testVersionMax_always_returnsCorrectValue():
    assert max([version.Version("100.9900.0"), version.Version("19.0.0"), version.Version("1.0.0")]) == version.Version("100.9900.0")
