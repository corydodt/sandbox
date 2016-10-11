from __future__ import unicode_literals, print_function

import re
from inspect import cleandoc

import attr

from py.test import fixture

from pypeg2 import maybe_some as pp_maybe_some, parse, attr as pp_attr


START_BLOCK = re.compile(b'\x0b')
END_BLOCK = re.compile(b'\x1c\r')
MSH_SEGMENT = 'MSH'


@attr.s
class Root(object):
    fieldSep = attr.ib()
    componentSep = attr.ib()
    lax = attr.ib(default=False)

    @staticmethod
    def preparse(text):
        """
        => field-separator, component-separator, lax-mode(bool)

        Get the field separators and parse mode
        """
        lax = False
        if START_BLOCK.match(text[0]):
            assert END_BLOCK.match(text[-2:]), "Found mllp start but no mllp end"
            text = text[1:-2]
        else:
            lax = True
        assert text[:3] == MSH_SEGMENT
        return text[3], text[4], lax

    @property
    def grammar(self):
        ret = dict()

        @attr.s
        class GrammarStub(object):
            name = attr.ib()
            grammar = attr.ib()

            @classmethod
            def make(cls, name, *a):
                if isinstance(a[0], str):
                    ret[name] = re.compile(a[0])
                    return ret[name]
                else:
                    self = cls(name, a)
                    ret[name] = self
                    return self

        make = GrammarStub.make

        lineSep = make("lineSep", b'\r')
        lineSepLax = make("lineSepLax", b'\n')
        segmentName = make("segmentName", '[a-zA-Z0-9_]+')
        component = make("component", '.*?(?=[' + self.fieldSep + '])')  # lookahead whee
        Field = make("Field", component, pp_maybe_some(self.componentSep, component))
        Segment = make("Segment", pp_attr('name', segmentName), pp_maybe_some(self.fieldSep, Field), lineSep)  # fixme use ignore() on separators
        MSH = make("MSH", pp_attr('name', MSH_SEGMENT), pp_maybe_some(self.fieldSep, Field), lineSep)
        ## InterfaceMessage = make("InterfaceMessage", START_BLOCK, MSH, lineSep, pp_maybe_some(Segment), END_BLOCK)
        ## InterfaceMessageLax = make("InterfaceMessageLax", MSH, lineSepLax, pp_maybe_some(Segment))

        return attr.make_class(b"Grammar", ret.keys())(**ret)

    @classmethod
    def load(cls, text):
        # choose a mode, lax (\n newlines, no MLLP block markers) or mllp
        fs, cs, lax = Root.preparse(text)
        self = cls(fieldSep=fs, componentSep=cs, lax=lax)
        language = self.grammar.InterfaceMessageLax if self.lax else self.grammar.InterfaceMessage
        obj = parse(text.splitlines()[0], language)
        return obj


@fixture
def adtText():
    return cleandoc(r"""
        MSH|^~\\&|EPIC|08|Bright.md||20160316144917|230|ADT^A31^ADT_A01|156445P.ADT|T|2.4||A08
        EVN|A31|20160316144917||REG_UPDATE|230^CARTER^STEVEN^^^^^^GHS^^^^^GMH
        PID|1||200001337^^^100000^MR||IPCT^GMH^ORI||19810311|M|IPCT^GMH^OR|NEW|13311 CEDAR CREEK COURT^^GREENVILLE^SC^29615^US^L^^SC023|SC023|(708)341-5614^P^PH^^^708^3415614~^NET^Internet^test@test.com||ENG|S|OTH||349299234|||NON|||||N|||N
        PD1|||GREENVILLE MEMORIAL HOSPITAL^^100000
        PV1|1|O|08OR^GMH POOL BED^7065^100000^^08^^^1^^DEPID|R|||26049^COBB IV^WILLIAM^SINTON^^^^^PROVID^^^^PROVID|||SUR||||RP|||26049^COBB IV^WILLIAM^SINTON^^^^^PROVID^^^^PROVID|||4||||||||||||||||||||||^^^100000||20150922081714|||73512.6
        PV2||Outpatient B||||||20150922070000||||HOSP ENC|||||||||n|N
        DG1|1||^chemical burn|chemical burn||Admission Text
        GT1|1|3306|IPCT^GMH^ORI||13311 CEDAR CREEK COURT^^GREENVILLE^SC^29615^US^^^SC023|(708)341-5614^^^^^708^3415614||19810311|M|P/F|SLF|349299234||||ADT SECURITY SYSTEM|10 CENTRAL AVE^^GREENVILLE^SC^29606^US|(864)271-0626^^^^^864^2710626||Full
        """)  # .replace('\n', '\r')


@fixture
def msh():
    return cleandoc(r"""MSH|^~\\&|EPIC""")


@fixture
def root():
    return Root(b'|', b'^')


def mkBasic(o):
    cls = attr.make_class(b'BasicGrammar', ['grammar'])
    return cls


def test_basics(root):

    @attr.s
    class X(object):
        grammar = attr.ib(default=(b'=',))

    print(X)
    print(parse(b'=', X))
    s = b'\r'
    assert 'xyz' == parse(s, mkBasic(root.grammar.lineSep.pattern))
    s = b'\n'
    assert b'abc' == parse(s, mkBasic(root.grammar.lineSepLax))


def test_segment(root, msh):
    assert parse(msh, root.grammar.Segment) == 'hello'
    assert parse(msh, root.grammar.MSH) == 'hello'


def test_load(adtText):
    assert 0
    asdkjlfh_ast_idk = Root.load(adtText)
    pt = Patient.fromMessage(obj)
    assert pt.givenName == 'GMH'
    assert p.familyName == 'IPCT'
    assert pt.birthdate == parseDate('1981-03-11')
    assert pt.mrn == '200001337'
    assert pt.insuranceCode == '3306'
    assert pt.insuranceStartDate is None
