import os
import urllib2
import ftplib
import urlparse
import urllib
import sys
import socket
import time


class DownloadFile(object):
       
    
    def __init__(self, url,start=0,stop=0,localFileName=None, auth=None, timeout=120.0, autoretry=False, retries=5):
        """Note that auth argument expects a tuple, ('username','password')"""
        self.start_bit=start
        self.stop_bit=stop
        self.url = url
        self.urlFileName = None
        self.progress = 0
        self.fileSize = (self.stop_bit-self.start_bit)
        self.localFileName = localFileName
        self.type = self.getType()
        self.auth = auth
        self.timeout = timeout
        self.retries = retries
        self.curretry = 0
        self.cur = 0
        self.urlFilesize = self.getUrlFileSize()
        if not self.localFileName: #if no filename given pulls filename from the url
            self.localFileName = self.getUrlFilename(self.url)
        
    def __downloadFile__(self, urlObj, fileObj,size_, callBack=None):
        """starts the download loop"""
        f_size=0.1
        prevsize =0
        #self.fileSize =int(size_)
        while 1:
            try:
                data = urlObj.read(8192)
            except (socket.timeout, socket.error) as t:
                print "caught ", t
                self.__retry__()
                break
            if not data:
                fileObj.close()
                break
            fileObj.write(data)
            local_fsize=self.getLocalFileSize()
            size =(local_fsize/100000)
            if size !=prevsize:
                f_size = float(size)/10
                per_size = (float(local_fsize)/self.fileSize)*100
                print str(per_size)+"% ---"+str(f_size)
                prevsize=size
            self.cur += 8192
            if callBack:
                callBack(cursize=self.cur)
    def _downloadbar_(self,filesize,webfilesize):
        pass
        
            
            
    def __retry__(self):
        """auto-resumes up to self.retries"""
        if self.retries > self.curretry:
                self.curretry += 1
                if self.getLocalFileSize() != self.urlFilesize:
                    self.resume()
        else:
            print 'retries all used up'
            return False, "Retries Exhausted"
                    
    def __authHttp__(self):
        """handles http basic authentication"""
        passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
        # this creates a password manager
        passman.add_password(None, self.url, self.auth[0], self.auth[1])
        # because we have put None at the start it will always
        # use this username/password combination for  urls
        authhandler = urllib2.HTTPBasicAuthHandler(passman)
        # create the AuthHandler
        opener = urllib2.build_opener(authhandler)
        urllib2.install_opener(opener)
        
    def __authFtp__(self):
        """handles ftp authentication"""
        ftped = urllib2.FTPHandler()
        ftpUrl = self.url.replace('ftp://', '')
        req = urllib2.Request("ftp://%s:%s@%s"%(self.auth[0], self.auth[1], ftpUrl))
        req.timeout = self.timeout
        ftpObj = ftped.ftp_open(req)
        return ftpObj
        
    def __startHttpResume__(self,curSize,url_fsize, restart=None, callBack=None):
        """starts to resume HTTP"""
        
        self.cur = curSize
        if restart:
            print "write"
            f = open(self.localFileName , "wb")
        else:
            print "appen"
            f = open(self.localFileName , "ab")
        if self.auth:
            self.__authHttp__()
        
        
        print url_fsize
        print "check 2"
        print 'bytes=%s-%s' % (curSize, str(url_fsize))
        print "check 3"
        req = urllib2.Request(self.url)
        #req.headers['Range'] = 'bytes=%s-%s' % (curSize, self.getUrlFileSize())
        req.headers['Range'] = 'bytes=%s-%s' % (curSize, str(url_fsize))
        req.headers['User-Agent']='Mozilla/5.0'
        urllib2Obj = urllib2.urlopen(req, timeout=self.timeout)
        self.__downloadFile__(urllib2Obj, f, callBack=callBack,size_=url_fsize)
    def __startFtpResume__(self, restart=None):
        """starts to resume FTP"""
        if restart:
            f = open(self.localFileName , "wb")
        else:
            f = open(self.localFileName , "ab")
        ftper = ftplib.FTP(timeout=60)
        parseObj = urlparse.urlparse(self.url)
        baseUrl= parseObj.hostname
        urlPort = parseObj.port
        bPath = os.path.basename(parseObj.path)
        gPath = parseObj.path.replace(bPath, "")
        unEncgPath = urllib.unquote(gPath)
        fileName = urllib.unquote(os.path.basename(self.url))
        ftper.connect(baseUrl, urlPort)
        ftper.login(self.auth[0], self.auth[1])
        if len(gPath) > 1:
            ftper.cwd(unEncgPath)
        ftper.sendcmd("TYPE I")
        ftper.sendcmd("REST " + str(self.getLocalFileSize()))
        downCmd = "RETR "+ fileName
        ftper.retrbinary(downCmd, f.write)
        
    def getUrlFilename(self, url):
        """returns filename from url"""
        return urllib.unquote(os.path.basename(url))
        #return "www.TamilRockers.lv - Sathya (2016) Malayalam DVDScr x264 700MB.mkv.zip"
        
    def getUrlFileSize(self):
        """gets filesize of remote file from ftp or http server"""
        print "getting size "
        if self.type == 'https' or self.type == "http":
            if self.auth:
                authObj = self.__authHttp__()
            urllib2Obj = urllib2.urlopen(self.url, timeout=self.timeout)
            size = urllib2Obj.headers.get('content-length')
            return size
        
    def getLocalFileSize(self):
        """gets filesize of local file"""
        size = os.stat(self.localFileName).st_size
        return size
        
    def getType(self):
        """returns protocol of url (ftp or http)"""
        type_ = urlparse.urlparse(self.url).scheme
        return type_    
        
    def checkExists(self):
        """Checks to see if the file in the url in self.url exists"""
        if self.auth:
            if self.type == 'http':
                authObj = self.__authHttp__()
                try:
                    urllib2.urlopen(self.url, timeout=self.timeout)
                except urllib2.HTTPError:
                    return False
                return True
            elif self.type == 'ftp':
                return "not yet supported"
        else:
            urllib2Obj = urllib2.urlopen(self.url, timeout=self.timeout)
            try:
                urllib2.urlopen(self.url, timeout=self.timeout)
            except urllib2.HTTPError:
                return False
            return True

    def download(self, callBack=None):
        """starts the file download"""
        self.curretry = 0
        self.cur = 0
        f = open(self.localFileName , "wb")
        if self.auth:
            if self.type == 'http':
                self.__authHttp__()
                urllib2Obj = urllib2.urlopen(self.url, timeout=self.timeout)
                self.__downloadFile__(urllib2Obj, f, callBack=callBack)
            elif self.type == 'ftp':
                self.url = self.url.replace('ftp://', '')
                authObj = self.__authFtp__()
                self.__downloadFile__(authObj, f, callBack=callBack)
        else:
            #headers = { 'User-Agent' : ' Mozilla/5.0 (Windows NT 6.1; WOW64; rv:12.0) Gecko/20100101 Firefox/12.0' }
            req = urllib2.Request(self.url,headers = { 'User-Agent' : ' Mozilla/5.0 (Windows NT 6.1; WOW64; rv:12.0) Gecko/20100101 Firefox/12.0' })
            urllib2Obj = urllib2.urlopen(req, timeout=self.timeout)
            size = urllib2Obj.headers.get('content-length')
            print size
            self.__downloadFile__(urllib2Obj, f, callBack=callBack,size_=size)
        return True

    def resume(self, callBack=None):
        """attempts to resume file download"""
        self.type = self.getType()
        print self.type
        if self.type == 'https'or "http":
            curSize_ = self.start_bit+self.getLocalFileSize()
            url_fsize_ = self.stop_bit
            if curSize_:
                pass
            else:
                curSize_ = self.getLocalFileSize()
            if url_fsize_:
                pass
            else:
                url_fsize_=int(self.getUrlFileSize())
            self.__startHttpResume__(curSize=curSize_,url_fsize=url_fsize_,callBack=callBack)
        elif self.type == 'ftp':
            self.__startFtpResume__()
        
def get_url():
    d_url="https://pastebin.com/iJNxNf7i"
    urlobj = urllib2.urlopen("https://pastebin.com/iJNxNf7i")
    raw_data = urlobj.read()
    down_url = raw_data.split("@@@@")
    return down_url[1]

def main():
        try:
            can_resume=0
            #url = get_url()
            #print url
            #url ="https://d39.usercdn.com/d/z4lvrgcptwsdzrijshcmrvsudqwk4w773khrg3a664jmpd5rjfnbw6cuz6ab63xdd2zn45ce/army%20of%20one"
            url ="http://87.120.36.18/Oceanofgames.com/Act_Of_Aggression_Reboot_Edition.iso?md5=9qq1ZBwFflBnlSpvx1LKQA&expires=1501905627"
            downloader = DownloadFile(url)
            #downloader.localFileName="addict.zip"
            print downloader.localFileName
            file_size_web = downloader.getUrlFileSize()
            print file_size_web
            try:
                file_size_local=downloader.getLocalFileSize()
                can_resume=1
            except:
                can_resume=0
            print can_resume
            #print str(file_size_web)+" "+str(file_size_local)
            if can_resume==0:
                print "downloading 1"
                downloader.download()
                print "downloading"
            else:
                
                if int(file_size_local) < int(file_size_web):
                    print "4"
                    print "resume"
                    downloader.resume()
                else:
                    time.sleep(100)
        except:
            print "error"
def splitbyte(part,url_):
    parts = []
    url = url_.strip()
    test = DownloadFile(url)
    fullsize = int(test.getUrlFileSize())
    partsize = (fullsize/part)
    prevstop=0
    for i in range(part):
        if i ==0:
            start = int(i*partsize)
        else:
            start = prevstop+1
        stop = int((i+1)*partsize)
        if i == (part-1):
            stop = fullsize
        prevstop = stop
        range_=[start,stop]
        parts.append(range_)
    return parts
def userinput():
    start = 0
    stop = 0
    print("do you want the last session y or n : ")
    _a_ = raw_input("")
    if _a_ == "n":
        url = raw_input("enter the url: ")
        choice = raw_input("byte select automatic y or n : ")
        if choice == 'y':
            no_parts = raw_input("how many parts do you want to divide : ")
            part_data =splitbyte(url_=url,part=int(no_parts))
            part_no = raw_input("select your part: ")
            start,stop =(part_data[int(part_no)-1])
            
            start = str(start)
            stop= str(stop)
            print "range = "+start +"----"+stop
        else:
            start = raw_input("enter starting byte if necessary: ")
            stop = raw_input("enter ending byte if necessary: ")
        if not start:
                    start='0'
        if not stop:
                    stop='0'
        _file_ = open('data.txt','w')
        _file_.write(url+'\n')
        _file_.write(start+'\n')
        _file_.write(stop+'\n')
        _file_.close()
        
    else:
        _file_ = open('data.txt','r')
        data = _file_.readlines()
        _file_.close()
        return data
    return url,start,stop
def maind():
    data= userinput()
    downloader = DownloadFile(url = data[0].strip(),start=int(data[1].strip()),stop=int(data[2].strip()))
    print downloader.getUrlFileSize()
    print downloader.localFileName
    try:
        downloader.resume()
        end = raw_input("download completed enter to continue")
    except WindowsError:
        file_ = open(downloader.localFileName,'wb')
        file_.close()
        downloader.resume()
        end = raw_input("download completed enter to continue")
        
        
maind()
#print splitbyte(part = 5,url ="https://d38.usercdn.com/d/zyl6l7vdtwsdzrij23dmxdkqaf5kjwmowus2tunkfj5eoqnys6inc2gn6awod35ghplooi3a/Cars%202017%20HD-rip.zip")
