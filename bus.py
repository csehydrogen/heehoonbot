# -*- coding: utf-8 -*-
import operator
import urllib2
from bs4 import BeautifulSoup

def bus(comm):
    station2code = {
            u"정문":101,
            u"법대입구":201,
            u"문화관입구":301,
            u"행정관":401,
            u"본부":411,
            u"농생대":501,
            u"공대입구":601,
            u"신소재연구소":701,
            u"제2파워플랜트":801,
            u"건설환경종합연구소":811,
            u"302동공학관":901,
            u"301동공학관":1001,
            u"유전공학연구소":1101,
            u"기초과학공동기기원":1201,
            u"교수회관입구":1301,
            u"노천강당":1401,
            u"기숙사삼거리":1501,
            u"국제대학원":1601,
            u"종합교육연구동":1701,
            u"경영대":1801,
            u"학부기숙사":1901,
            u"대학원기숙사":1911,
            u"후문":2001,
            u"bk국제관":2011,
            u"가족생활동":2101,
            u"교수아파트":2201,
            u"호암교수회관":2301,
            u"서울대입구역":2401,
            u"녹두거리":2501,
            u"북션":2601,
            u"녹두-설입":2701,
            u"서울대학교1":2801,
            u"서울대학교2":2901,
            u"서울대학교3":3001
            }
    stations = zip(*sorted(station2code.iteritems(), key=operator.itemgetter(1)))[0]

    comm = comm.strip()
    if comm.startswith(u"역"):
        code = -1
        comm = comm[1:].strip()
    else:
        code = 0
    for station in stations:
        if comm in station:
            code += station2code[station]
            break
    if len(comm)==0:
        code = 0
    if code<=0:
        ret = u"없는 정류장입니다.\n● 사용방법\n!셔틀[검색어]\n!셔틀역[검색어]\n● 정류장 목록\n"
        ret += "\n".join(stations)
        return ret

    soup = BeautifulSoup(urllib2.urlopen("http://bus.snu.ac/mobile/station/stationDetail.action?bus_station_code="+str(code)).read())
    sv = soup.find_all(class_="stationView")[0]
    station_name = "".join(list(sv.find_all(class_="stationViewHeader")[0].find_all(class_="title")[0].strings))
    if station_name=="()":
        ret = u"이 방향은 없는 정류장입니다.\n반대 방향을 검색해 보세요."
        return ret
    buses = [li.a for svl in sv.find_all(class_="stationViewList") for li in svl.find_all("li")]
    info = [(x.find_all(class_="title")[0].contents[0],x.find_all(class_="date start")[0].contents[0].strip()) for x in buses]
    ret = u"● "+station_name+"\n"+"\n".join(["["+x[0]+"]\n "+x[1] for x in info])
    return ret
