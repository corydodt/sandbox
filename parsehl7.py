from __future__ import unicode_literals, print_function

import re

import attr

from py.test import fixture

from pypeg2 import Symbol, maybe_some as pp_maybe_some, parse


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
        if startBlock.match(text[0]):
            assert endBlock.match(text[-2:]), "Found mllp start but no mllp end"
            text = text[1:-2]
        else:
            lax = True
        assert text[:3] == 'MSH'
        return text[3], text[4], lax 

    @property
    def grammar(self):
        lineSep             = re.compile(b'\r')
        lineSepLax          = re.compile(b'\n')
        startBlock          = b'\x0b'
        endBlock            = b'\x1c\r'
        segmentName         = re.compile('[a-zA-Z0-9_]+')
        Component           = re.compile('.*?(?=[' + self.fieldSep.pattern + '])')  # lookahead whee
        Field               = [Component, pp_maybe_some(self.compSep.pattern, Component)]
        Segment             = [segmentName, pp_maybe_some(self.fieldSep.pattern, Field), lineSep]  # fixme use ignore() on separators
        InterfaceMessage    = [startBlock, MSH, lineSep, pp_maybe_some(Segment), endBlock]
        InterfaceMessageLax = [MSH, lineSepLax, pp_maybe_some(Segment)]
        return attr.makeinstance(
            dict(
                InterfaceMessage=InterfaceMessage,
                InterfaceMessageLax=InterfaceMessageLax,
                ))
    
    @classmethod
    def load(cls, text):
        # choose a mode, lax (\n newlines, no MLLP block markers) or mllp
        fieldSep, compSep, lax = Root.preparse(text)
        self = cls(fieldSep=fs, componentSep=cs, lax=lax)
        language = self.grammar.InterfaceMessageLax if self.lax else self.grammar.InterfaceMessage
        obj = parse(language(), text)
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
        """).replace('\n', '\r')

def test_load(adtText):
    asdkjlfh_ast_idk = Root.load(adtText)
    pt = Patient.fromMessage(obj)
    assert pt.givenName == 'GMH'
    assert p.familyName == 'IPCT'
    assert pt.birthdate == parseDate('1981-03-11')
    assert pt.mrn == '200001337'
    assert pt.insuranceCode == '3306'
    assert pt.insuranceStartDate is None
