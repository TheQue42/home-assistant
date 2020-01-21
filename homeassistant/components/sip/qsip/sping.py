'''
Created on 21 jan. 2020

@author: taisto
'''
from qsip import *

if __name__ == '__main__':
    sipSender = qsip.qsip({"addr": "", "port": 0})

    # digestResponse = calc_digest_response("bob","bee.net", "bob", "REGISTER", "sip:bee.net",
    #                                       "49e4ab81fb07c2228367573b093ba96efd292066",
    #                                       "00000001", "8d82cf2d1e7ff78b28570c311d2e99bd", "HejsanSvejsan")
    # print("Challenge Response: ", digestResponse)

#    result = sipSender.sendMessage("10.9.24.132", 5060, "sip:taisto@trippelsteg.se", "HejsanSvejsan1")
    time.sleep(1)
    method = "InVite"
    #m = [mm for mm in if mm == method]
    print("M", m)

#     h = HeaderList()
#     na1 = NameAddress(HeaderEnum.FROM, uri="taisto@kenneth.qvist", display_name="Taisto k. Qvist", param1="p1", param2="p2")
#     na2 = NameAddress(HeaderEnum.FROM, uri="taisto@kenneth.qvist", param1="pelle")
#     na3 = NameAddress(HeaderEnum.FROM, uri="taisto@kenneth.qvist")
# 
#     Cseq = CseqHeader(MethodEnum.INVITE, 5, cseqParam="Nej")
# 
#     subject1 = SimpleHeader(HeaderEnum.SUBJECT, "Subject-1", SubjectParam1=11212)
#     subject2 = SimpleHeader(HeaderEnum.SUBJECT, "Subject-2", subjectParam2=222)
# 
#     custom1 = CustomHeader(hname="MyCustomHeader", value="MyCustomValue", customParam1="FortyTwo", X=0.1)
#     vvv = dict()
#     vvv["One"] = "realm=trippelsteg.se"
#     vvv["Two"] = "digest"
#     vvv["Three"] = "cnonce=9823139082013982"
# #    print("Types:", type(vvv), type(vvv.keys()))
# 
#     custom2 = CustomHeader(hname="Authorization", value=vvv, customParam2="FortyThree", X=0.2)
# 
#     hlist = HeaderList()
#     hlist.add(na1)
#     hlist.add(na2)
#     hlist.add(na3)
#     hlist.add(Cseq)
#     hlist.add(subject1)
#     hlist.add(custom1)
#     hlist.add(custom2)
#     hlist.add(subject2)

    #print("vars:", vars(hlist))
    print("------------------")
    test = str(hlist)
    print(test)
    print("HasHeader1", hlist.hasHeader(HeaderEnum.CALL_ID))
    print("HasHeader2", hlist.hasHeader(HeaderEnum.SUBJECT))
    print("IsEqual:", HeaderEnum.SUBJECT == "SubJect")
