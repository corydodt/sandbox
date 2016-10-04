from __future__ import unicode_literals, print_function

import re

import attr

from pypeg2 import K, maybe_some as pp_maybe_some


def preparse(text):
    """
    Get the field separator
    """
    prefix = text[:4]
    assert prefix[:3] == 'MSH'
    return Symbol(prefix[3]), Symbol(prefix[4])


fieldSep, compSep = preparse(text)
lineSep = re.compile(b'\r')
lineSepLax = re.compile(b'\n')
startBlock = b'\x0b'
endBlock = b'\x1c\r'
segmentName = re.compile('[a-zA-Z0-9_]+')


# Component           = [Subcomponent*]
# SubSeparator        = K("~")
Component           = re.compile('.*?(?=[' + fieldSep + '])') # lookahead whee
Field               = [Component, pp_maybe_some(compSep, Component)]
Segment             = [segmentName, pp_maybe_some(fieldSep, Field), lineSep] # fixme use omit() on separators
InterfaceMessage    = [startBlock, MSH, lineSep, pp_maybe_some(Segment), endBlock]

InterfaceMessageLax = [MSH, lineSep, pp_maybe_some(Segment)]


def parseInterfaceMessage(text):
    fieldSep, compSep = preparse(text)
    
    

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
    im = InterfaceMessage()
    im.load(adtText)
    pt = Patient.fromMessage(im)
    assert pt.givenName == 'GMH'
    assert p.familyName == 'IPCT'
    assert pt.birthdate == parseDate('1981-03-11')
    assert pt.mrn == '200001337'
    assert pt.insuranceCode == '3306'
    assert pt.insuranceStartDate is None
