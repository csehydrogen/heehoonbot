# -*- coding: utf-8 -*-
import urllib2
from bs4 import BeautifulSoup

def mini(comm):
    cafes = [u"학생회관",
            u"전망대(농대)",
            u"두레미담",
            u"서당골(사범대)",
            u"감골식당",
            u"동원관",
            u"자하연",
            u"공깡",
            u"220동",
            u"301동",
            u"302동",
            u"기숙사(919동)",
            u"기숙사(901동)"]
    comm = comm.strip()
    if comm==u"":
        key=u""
    else:
        key=comm
    soup = BeautifulSoup(urllib2.urlopen("http://mini.snu.kr/cafe/").read())
    main = soup.find_all(id="main")[0]
    date = main.div.h3.contents[0]
    trs = main.table.find_all("tr")
    time = trs[0].td.contents[0]
    ret = date+" "+time
    cnt = 0
    for tr in trs[1:]:
        if len(tr.contents)<2:
            break
        td0, td1 = tr.find_all("td")
        cafe = "".join(td0.contents[0::2])
        if key!=u"" and not key in cafe:
            continue
        cnt += 1
        food = zip([x.contents[0] for x in td1.contents[0::3]],td1.contents[1::3])
        ret += "\n["+cafe+"]\n"+"\n".join([" "+x[0]+"00 "+x[1] for x in food])
    if cnt==0:
        ret += u"\n검색어에 해당하는 식당이 없습니다. '!밥'으로 모든 식당을 확인할 수 있습니다."

    return ret
