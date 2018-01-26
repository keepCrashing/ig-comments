# -*- coding: utf-8 -*- 
import requests
import cookielib
import json
import time
import os
import sys
from bs4 import BeautifulSoup
import shutil
cookie = cookielib.CookieJar()
#https://www.instagram.com/accounts/login/ajax/
#{"id":"13460080","first":12,"after":"AQDrx48eXGhqQbdRsUo2FaB4q0zQoOonK0AiQZUhwiZBOgXM_A7tSxmpxKquCtSBwGX5wpuew4uTlkNunkAza2s3e4XDxHJ4JkyKj_oMXRcqsA"}
#https://www.instagram.com/graphql/query/?query_id=17888483320059182&variables=%7B"id"%3A"528817151"%2C"first"%3A12%2C"after"%3A"AQCvKwdRyT5_d28lcIGdnnC-1X16fj_rrum07L-74u9IEeVWK0XPtRiAq5vRHFhP_pp39gCkxYsnbwndkmHgSNMF27q_f3SFKX4OOxXYNhZvjw"%7D
#https://www.instagram.com/graphql/query/?query_id=17852405266163336&variables={%22shortcode%22:%22BeHYw0vnd63%22,%22first%22:20}
#https://www.instagram.com/graphql/query/?query_id=17852405266163336&variables={%22shortcode%22:%22BeIDXDth5l2fBG-NfOeomXfvgid3zmCi87IOR00%22,%22first%22:150}
class User():
    def __init__(self,username,password):
        self.username = username
        self.password = password
    def getCSRF_TOKEN(self):
        global cookie
        res = requests.get('https://www.instagram.com/')
        cookie = res.cookies
        #print res.cookies['csrftoken']
    def login(self):
        global cookie 
        self.getCSRF_TOKEN()
        data = "username=%s&password=%s"%(self.username, self.password)
        headers = {'content-type':'application/x-www-form-urlencoded','referer':'https://www.instagram.com/','x-csrftoken':cookie['csrftoken']}
        res = requests.post('https://www.instagram.com/accounts/login/ajax/',headers=headers, data=data, cookies = cookie)
        cookie = res.cookies
    def logout(self):
        global cookie
        data = "csrfmiddlewaretoken=%s"%(cookie['csrftoken'])
        headers = {'content-type':'application/x-www-form-urlencoded','referer':'https://www.instagram.com/','x-csrftoken':cookie['csrftoken']}
        res = requests.post('https://www.instagram.com/accounts/logout/',headers=headers, data=data, cookies = cookie)
        cookie = res.cookies
        print res
class Target():
    def __init__(self,account):
        self.account = account
        f = File()
        f.creatFolder(account)
    def getData(self):
        global cookie
        res = requests.get('https://www.instagram.com/%s/?__a=1'%(self.account), cookies = cookie)
        ret = json.loads(res.text)
        return ret
    def getID(self):
        return self.getData()['user']['id']
    def getList(self,num=1):
        global cookie
        uid = self.getID()
        res = requests.get('https://www.instagram.com/graphql/query/?query_id=17888483320059182&variables={"id":"%s","first":%s}'%(uid,num), cookies = cookie)
        ret = json.loads(res.text)
        return ret
    def getTypeName(self,shortCode):
        f = File()
        textList = []
        ret = ""
        res = requests.get('https://www.instagram.com/p/%s/?__a=1'%(shortCode), cookies = cookie)
        data = json.loads(res.text)
        typeName = data['graphql']['shortcode_media']['__typename']
        if typeName == "GraphSidecar":
            for d in data['graphql']['shortcode_media'].get('edge_sidecar_to_children').get('edges'):
                if d.get('node').get('is_video') == True:
                    ret = 'GraphSidecarVedio'
                    return ret
            ret = 'GraphSidecarImage'
                
        else:
            ret = typeName
        return ret
    def getShortCode(self):
        data = self.getList(100)['data']['user']['edge_owner_to_timeline_media']['edges']
        shortCodeList = []
        for i in range(0,len(data),1):
            #print data[i]['node']['shortcode']
            shortCodeList.append(data[i]['node']['shortcode'])
            f = File()
            f.creatFolder(self.account+'/'+data[i]['node']['shortcode'])
            f.download(data[i]['node']['display_url'],self.account+'/'+data[i]['node']['shortcode']+'/'+ data[i]['node']['shortcode'] +'.jpg')
            lt = []
            f.writeText(lt,self.account+'/'+data[i]['node']['shortcode']+'/'+self.getTypeName(data[i]['node']['shortcode']) + '.txt')
        return shortCodeList

            
    def getCommentCount(self,shortCode):
        while True:    
            res = requests.get('https://www.instagram.com/graphql/query/?query_id=17852405266163336&variables={"shortcode":"%s","first":0}'%(shortCode),cookies = cookie)
            jsonData = json.loads(res.text)
            print jsonData
            if jsonData.get('status') == 'fail':
                time.sleep(60)
            if jsonData.get('status') == 'ok':
                break
        ret = int(jsonData['data']['shortcode_media']['edge_media_to_comment']['count'])
        return ret
    def getComments(self):
        data = self.getShortCode()
        for shortCode in data:
            count = self.getCommentCount(shortCode)
            f = open(self.account+'/'+shortCode+'/'+'text.txt', 'w')
            if count != 0:
                res = requests.get('https://www.instagram.com/graphql/query/?query_id=17852405266163336&variables={"shortcode":"%s","first":%d}'%(shortCode,count), cookies = cookie)
                jsonData = json.loads(res.text)
                node = jsonData['data']['shortcode_media']['edge_media_to_comment']['edges']
                for i in range(0,len(node),1):
                    print node[i]['node']['text'].encode(sys.stdin.encoding, "replace").decode(sys.stdin.encoding)
                    f.write(node[i]['node']['text'].encode('utf-8') + '\n')
            f.close()
    def getComments2(self):
        data = self.getShortCode()
        for shortCode in data:
            after = ""
            textList = []
            while True:
                res = requests.get('https://www.instagram.com/graphql/query/?query_id=17852405266163336&variables={"shortcode":"%s","first":5000,"after":"%s"}'%(shortCode,after), cookies = cookie)
                jsonData = json.loads(res.text)
                if jsonData.get('status') == 'fail':
                    print jsonData
                    time.sleep(60)
                else:
                    has_next_page = jsonData['data']['shortcode_media']['edge_media_to_comment']['page_info']['has_next_page']
                    node = jsonData['data']['shortcode_media']['edge_media_to_comment']['edges']

                    for i in range(0,len(node),1):
                        print node[i]['node']['text'].encode(sys.stdin.encoding, "replace").decode(sys.stdin.encoding)
                        textList.append(node[i]['node']['text'])
                    if  has_next_page == False:
                        f = File()
                        f.writeText(textList,self.account+'/'+shortCode+'/'+'text.txt')
                        break
                    else:
                        after = jsonData['data']['shortcode_media']['edge_media_to_comment']['page_info']['end_cursor']

class File():
    def __init__(self):
        pass
    def creatFolder(self,name):
        if not os.path.exists(name):
            os.makedirs(name)
    def download(self,url,path):
        res = requests.get(url,stream=True)
        f = open(path,'wb')
        shutil.copyfileobj(res.raw,f)
        print 'download' + url
        f.close()
    def writeText(self,textList,path):
        f = open(path,'w')
        for text in textList:
            f.write(text.encode('utf-8') + '\n')
        f.close()

        
def main():
    ht = User('','')
    ht.login()
    t = raw_input()
    target = Target(t)
    target.getComments2()
    ht.logout()
    #target = Target("ann20023300")
    #print target.getTypeName('BXfclpaBO2m')
main()
