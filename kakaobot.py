# -*- coding: utf-8 -*-

import os
import urllib2
import socket
import struct
import rsa # pip install rsa
from Crypto.Cipher import AES # pip install pycrypto
from bson import BSON # pip install pymongo

app_ver = u'4.4.2'
os_type = u'android'
aes_key = struct.pack('B',0)*16;
aes_iv = 'locoforever'+struct.pack('B',0)*5;
rsa_n = 0xaf0dddb4de63c066808f08b441349ac0d34c57c499b89b2640fd357e5f4783bfa7b808af199d48a37c67155d77f063ddc356ebf15157d97f5eb601edc5a104fffcc8895cf9e46a40304ae1c6e44d0bcc2359221d28f757f859feccf07c13377eec2bf6ac2cdd3d13078ab6da289a236342599f07ffc1d3ef377d3181ce24c719
rsa_e = 3
loc_host = 'loco.kakao.com'
loc_port = 8080

def dic_to_loc(method_name,body,packet_id=0,status_code=0,body_type=0):
    ret=str()
    ret+='\xFF\xFF\xFF\xFF' # 4B
    ret+=struct.pack('H',status_code) # 2B
    ret+=method_name+struct.pack('B',0)*(11-len(method_name)) # 11B
    ret+=struct.pack('B',body_type) # 1B
    body=BSON.encode(body)
    ret+=body[:4] # 4B
    ret+=body
    return ret

def loc_to_sec(loc):
    ret = str()

    while len(loc)!=0:
        sec_body = enc_aes(loc[:2047])
        sec_head = struct.pack('I',len(sec_body))
        ret += sec_head+sec_body
        loc = loc[2047:]

    return ret

def sec_to_loc(sec):
    return dec_aes(sec[4:])

def loc_to_dic(res):
    ret = dict()
    ret['packetId'] = struct.unpack('I',res[0:4])[0]
    ret['statusCode'] = struct.unpack('H',res[4:6])[0]
    ret['methodName'] = res[6:17].rstrip('\0')
    ret['bodyType'] = struct.unpack('B',res[17:18])[0]
    ret['bodyLength'] = struct.unpack('I',res[18:22])[0]
    ret['body'] = BSON(res[22:]).decode()
    return ret

def enc_aes(plain):
    padded_plain = pad_PKCS7(plain)
    cipher = AES.new(key=aes_key,mode=AES.MODE_CBC,IV=aes_iv).encrypt(padded_plain)
    return cipher

def dec_aes(cipher):
    padded_plain = AES.new(key=aes_key,mode=AES.MODE_CBC,IV=aes_iv).decrypt(cipher)
    plain = unpad_PKCS7(padded_plain)
    return plain

def pad_PKCS7(unpadded):
    val = 16-len(unpadded)%16
    padded = unpadded + struct.pack('B',val)*val
    return padded

def unpad_PKCS7(padded):
    val = struct.unpack('B',padded[-1])[0]
    unpadded = padded[:-val]
    return unpadded

def enc_rsa(plain):
    pub_key = rsa.PublicKey(rsa_n,rsa_e)
    cipher = rsa.encrypt(plain, pub_key)
    return cipher

def get_handshake():
    ret=str()
    ret+=struct.pack('I',128);
    ret+=struct.pack('I',1);
    ret+=struct.pack('I',1);
    ret+=enc_rsa(aes_key)
    return ret

class Client():

    def __init__(self,sKey,duuid,debug=False,bot_id=None,bot_nick=''):
        self.sKey = sKey
        self.duuid = duuid
        self.debug = debug
        self.bot_id=bot_id
        self.bot_nick=bot_nick

    def recv(self):
        loc = str()
        sec = self.s.recv(4)
        sec += self.s.recv(struct.unpack('I',sec)[0])
        loc += sec_to_loc(sec)
        while len(loc[22:])<struct.unpack('I',loc[18:22])[0]:
            sec = self.s.recv(4)
            sec += self.s.recv(struct.unpack('I',sec)[0])
            loc += sec_to_loc(sec)
        dic = loc_to_dic(loc)

        if self.debug:
            print '[M]','RECV'
            print '[R]',dic

        method_name = dic['methodName']
        if method_name=='MSG':
            body = dic['body']
            chat_id = body['chatId']
            nick = body['authorNickname']
            chat_log = body['chatLog']
            author_id = chat_log['authorId']
            msg = chat_log['message']
            print '[R]',nick,'(',author_id,')','in',chat_id,':',msg,'(',len(msg),')'

        return dic

    def checkin(self):
        s_loc = dic_to_loc('CHECKIN',{u'os': os_type})

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((loc_host,loc_port))
        s.sendall(s_loc)
        r_loc = s.recv(22)
        r_loc += s.recv(struct.unpack('I',r_loc[18:22])[0])
        s.close()

        r_dic = loc_to_dic(r_loc)

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((r_dic['body']['host'],r_dic['body']['port']))

        h = get_handshake()
        self.s.sendall(h)

        if self.debug:
            print '[M]','CHECKIN'
            print '[S]',loc_to_dic(s_loc)
            print '[R]',r_dic

    def login(self):
        self.checkin()

        s_loc = dic_to_loc('LOGIN',{u'appVer':app_ver,u'os':os_type,u'sKey':self.sKey,u'duuid':self.duuid})
        s_sec = loc_to_sec(s_loc)
        self.s.sendall(s_sec)

        if self.debug:
            print '[M]','LOGIN'
            print '[S]',loc_to_dic(s_loc)

    def write(self,chat_id,msg):
        unit=1000
        while len(msg)!=0:
            cur_msg = msg[:unit]
            msg = msg[unit:]

            s_loc = dic_to_loc('WRITE',{u'chatId': chat_id, u'msg': cur_msg, u'type': 1})
            s_sec = loc_to_sec(s_loc)
            self.s.sendall(s_sec)

            if self.debug:
                print '[M]','WRITE'
                print '[S]',loc_to_dic(s_loc)

            print '[W]',self.bot_nick,'(',self.bot_id,')','in',chat_id,':',cur_msg,'(',len(cur_msg),')'

    def leave(self,chat_id):
        s_loc = dic_to_loc('LEAVE',{u'chatId':chat_id})
        s_sec = loc_to_sec(s_loc)
        self.s.sendall(s_sec)

        if self.debug:
            print '[M]','LEAVE'
            print '[S]',loc_to_dic(s_loc)

    def write_image(self,chat_id,image_url,width=0,height=0):
        extra = []
        extra.append("'path':'%s'" % (image_url))
        extra.append("'width':%d" % (width))
        extra.append("'height':%d" % (height))
        extra = "{%s}" % (",".join(extra))

        s_loc = dic_to_loc('WRITE',{u'chatId':chat_id, u'extra':extra, u'type':2})
        s_sec = loc_to_sec(s_loc)
        self.s.sendall(s_sec)

        if self.debug:
            print '[M]','WRITE'
            print '[S]',loc_to_dic(s_loc)

        print '[W]',self.bot_nick,'(',self.bot_id,')','in',chat_id,':',image_url

    def upload_image(self,image_url):
        image_url = str(image_url)
        image = urllib2.urlopen(image_url).read()

        boundary = "pykakao--multipart--formdata--boundary"

        body = []

        body.append("--%s" % (boundary))
        body.append("Content-Disposition: form-data; name='user_id'")
        body.append("\r\n")
        body.append(str(self.bot_id))

        body.append("--%s" % (boundary))
        body.append("Content-Disposition: form-data; name='attachment_type'")
        body.append("")
        body.append("image")

        body.append("--%s" % (boundary))
        body.append("Content-Disposition: form-data; name='attachment'; filename='%s'" % (os.path.basename(image_url)))
        body.append("Content-Transfer-Encoding: binary")
        body.append("Content-Length: %d" % len(image))
        body.append("")
        body.append(image)

        body.append("--%s--" % (boundary))
        body.append("")

        body = "\r\n".join(body)

        upload_url = "http://up-m.talk.kakao.com/upload"

        headers = {}
        headers["User-Agent"] = "KakaoTalk Win32 1.1.4"
        headers["Content-Type"] = "multipart/form-data; boundary=%s" % (boundary)
        headers["Content-Length"] = len(body)

        response = urllib2.urlopen(urllib2.Request(upload_url, data=body, headers=headers))

        return response.read() # url returned. pass it to write_image
