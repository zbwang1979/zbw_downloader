from abc import ABCMeta, abstractmethod
import datetime
import pytz
import re
import threading
import urllib.request
import os
import logging
import requests
import time
import weakref



class SUPER_ZBW_DOWNLAOD(metaclass=ABCMeta):
    start_time=''
    end_time=''
    num_files=0
    num_size=0
    log_file_path=''
    user_agent = ("Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/48.0.2564.103 Safari/537.36")
    accept_language = 'ru-RU,ru;q=0.8,en-US;q=0.6,en;q=0.4'
    instances = weakref.WeakSet()
    def __init__(self,user,log_mod=0):
        if len(SUPER_ZBW_DOWNLAOD.instances)==0:
            SUPER_ZBW_DOWNLAOD.start_time=time.time()

        SUPER_ZBW_DOWNLAOD.instances.add(self)
        self.log_mod=log_mod
        self.user_login=user
        self.login_status=False
        self.home_dir=''
        self.log_file=0
        self.busy_time = 2
        log_string = 'zbw scraber started at %s:\n' % \
                     (SUPER_ZBW_DOWNLAOD.timestamp2day(self.start_time))
        self.write_log(log_string)
        pass


    def get_instance_set(self):
        return [instant for instant in SUPER_ZBW_DOWNLAOD.instances\
                if instant.__class__.__name__==self.__class__.__name__]


    @staticmethod
    def timestamp2day(timestramp):
        tz = pytz.timezone(pytz.country_timezones('cn')[0])
        format_local_time= datetime.datetime.fromtimestamp(timestramp,tz).strftime('%Y-%m-%d %H:%M:%S\t')
        return format_local_time
        pass
    @staticmethod
    def remove_emoji(txt):
        emoji_pattern = re.compile(r'\\u([a-z]|[0-9]|[A-Z]){4}')
        e1=re.compile(r'\\n')
        txt2=re.sub(e1, '', re.sub(emoji_pattern, '', txt))
        e2 = re.compile(r'#\S*?\s')
        txt3=re.sub(e2,'',txt2)
        res_txt=(''.join([char for char in txt3 if char.isprintable()])).replace("\\", '')
        return res_txt

    def write_log(self, log_text):
        """ Write log by print() or logger """
        if self.log_mod == 0:
            try:
                print(log_text)
            except UnicodeEncodeError:
                print("Your text has unicode problem!")
        elif self.log_mod == 1:
            # Create log_file if not exist.
            if self.log_file == 0:
                self.log_file = 1
                tz = pytz.timezone(pytz.country_timezones('cn')[0])
                now_time = datetime.datetime.now(tz)
                log_full_path = '%s_%s_%s.log' % (self.log_file_path,self.user_login,now_time.strftime("%d.%m.%Y_%H:%M"))
                formatter = logging.Formatter('%(asctime)s - %(name)s '
                                              '- %(message)s')
                self.logger = logging.getLogger(self.user_login)
                hdrl = logging.FileHandler(log_full_path, mode='w')
                hdrl.setFormatter(formatter)
                self.logger.setLevel(level=logging.INFO)
                self.logger.addHandler(hdrl)
            # Log to log file.
            try:
                self.logger.info(log_text)
            except UnicodeEncodeError:
                print("Your text has unicode problem!")


    def page_open(self,requests_obj,url):
        r=None
        try:
            time.sleep(self.busy_time)
            r = requests_obj.get(url)
        except Exception as e:
            self.write_log(str(e))
        finally:
            return r
    def page_post(self,requests_obj,url,data):
        r=None
        try:
            time.sleep(self.busy_time)
            r = requests_obj.post(url, data=data, allow_redirects=True)
        except Exception as e:
            self.write_log(str(e))
        finally:
            return r

    @abstractmethod
    def log_in(self):
        pass

    @abstractmethod
    def check_alive(self):
        pass

    @abstractmethod
    def web_process(self):
        pass

    @abstractmethod
    def run_flow(self):
        pass

class zbw_scraber_instagram(SUPER_ZBW_DOWNLAOD):
    def __init__(self,user,password,receive_files_num=1,other_logger=None,call_back=None):
        super().__init__(user)
        self.user_login=user.lower()
        self.pass_word=password
        self.call_back=call_back
        self.other_logger=other_logger
        self.url_login='https://www.instagram.com/accounts/login/ajax/'
        self.s = requests.Session()
        self.url = 'https://www.instagram.com/'
        self.user_name='"username": "modswzb"'
        self.login_post={}
        self.log_nums_files=0
        self.log_size_receive=0
        self.finished_working=True
        self.has_finieshed_nums=0
        self.working_list =  [{'name':item,'content':{'last_upload_time':int(self.start_time),'upload_list':[]}} \
                              for item in ['laugh.r.us','doounias','viraldiys','todays.bucketlist']]
        self.url_media_detail='https://www.instagram.com/p/'
        self.max_receive_files=receive_files_num
        pass
    # def write_log(self, log_text):
    #     if not bool(self.other_logger) :
    #         try:
    #             print(log_text)
    #         except UnicodeEncodeError:
    #             print("Your text has unicode problem!")
    #     else:
    #         self.other_logger.info(log_text)


    def check_alive(self):
        r=self.page_open(self.s,self.url)
        if bool(r) and r.status_code==200:
            finder = r.text.find(self.user_name)
            if finder != -1:
                self.login_status = True
            else:
                self.login_status = False
        else:
            self.login_status = False

    def log_in(self):
        log_string = 'Trying to login as %s...\n' % self.user_login
        self.write_log(log_string)
        self.s.cookies.update({
            'sessionid': '',
            'mid': '',
            'ig_pr': '1',
            'ig_vw': '1366',
            'csrftoken': '',
            's_network': '',
            'ds_user_id': '',
            'rur':'ASH'
        })
        self.login_post = {
            'username': self.user_login,
            'password': self.pass_word
        }
        self.s.headers.update({
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': self.accept_language,
            'Connection': 'keep-alive',
            'Content-Length': '0',
            'Host': 'www.instagram.com',
            'Origin': 'https://www.instagram.com',
            'Referer': 'https://www.instagram.com/',
            'User-Agent': self.user_agent,
            'X-Instagram-AJAX': '1',
            'X-Requested-With': 'XMLHttpRequest'
        })

        r=self.page_open(self.s,self.url)
        if bool(r) and r.status_code==200:
            self.s.headers.update({'X-CSRFToken': r.cookies['csrftoken']})
            login=self.page_post(self.s,self.url_login,self.login_post)
            self.s.headers.update({'X-CSRFToken': login.cookies['csrftoken']})
        else:
            return

        if bool(login) and  login.status_code == 200:
            self.check_alive()
            if self.login_status:
                log_string = '%s login success!' % self.user_name
                self.write_log(log_string)
            else:
                self.write_log('Login error! Check your login data!')
        else:
            self.write_log('Login error! Connection error!'+str(login.status_code))

    def get_details(self,url,item):
        r=self.page_open(self.s,url)
        if bool(r):
            if 'image' in item['type'].lower():
                filename = 'zbw_%s.jpg' % item['id']
                '''"display_url": "https://scontent.cdninstagram.com/t51.2885-15/e35/19051844_1834502583534667\
                "text": "Out beyond the ideas of right and wrong there is a field.\nI will meet you there. \
                \ud83c\udf24\n.\n\ud83c\udde8\ud83c\udded@switzerland.vacations"_1764999162270580736_n.jpg"'''
                match_url = re.search(r'"display_url":\s*?"(.*?)"', r.text,re.DOTALL)
            else:
                filename = 'zbw_%s.mp4' % item['id']
                '''"video_url": "https://scontent.cdninstagram.com/t50.2886-16/19054712_1515312\
                775198294_3211878201529729024_n.mp4"'''
                match_url = re.search(r'"video_url":\s*?"(.*?)"', r.text,re.DOTALL)
            res_url = match_url.group(1)
            match_desc=None
            try:
                match_desc = re.search('"text":\s*?"(.*?)"', r.text, re.DOTALL)
                if bool(match_desc):
                    desc=match_desc.group(1)
                else:
                    desc=''
            except ValueError:
                if bool(match_desc.group(1)):
                    desc=match_desc.group(1)
                else:
                    desc =''
            try:
                time.sleep(self.busy_time)
                urllib.request.urlretrieve(res_url, filename=filename)
            except Exception as e:
                self.write_log(str(e))
            return filename,SUPER_ZBW_DOWNLAOD.remove_emoji(desc)

        pass

    def download_files(self,total_nums):

        while True:
            time.sleep(self.busy_time)
            self.check_alive()
            if not self.login_status:
                self.finished_working = True
                return
            owner_name,item=self.pop_from_working_list()
            if not bool(item):
                self.write_log('downloading finished\nstatus：today_files_nums:%d totalsize:%dKb'%(self.log_nums_files,
                                                                                     self.log_size_receive))
                return
            item = dict(item)
            url=self.url_media_detail+item['code']
            self.write_log('start downloading %s at %s'%(url,SUPER_ZBW_DOWNLAOD.timestamp2day(time.time())))

            filename,file_desc=self.get_details(url,item)
            if not bool(filename):
                return
            self.has_finieshed_nums +=1
            if time.time()-self.start_time > 24*60*60:
                self.log_nums_files =0
                self.log_size_receive=0
                self.write_log('log files nums reset!')
            self.log_nums_files+=1
            try:
                file_size=round(float(os.path.getsize(filename))/1024,3)
                self.log_size_receive+=file_size
                self.write_log('%s size:%dKb downloaded successfully\tfinished:%d/total:%d'%\
                               (filename,file_size,self.has_finieshed_nums,total_nums))
                if hasattr(self.call_back,'__call__'):
                    self.call_back(filename,file_desc,item['type'],owner_name)
            except Exception as e:
                self.write_log(str(e))


    def pop_from_working_list(self):
        try:
            for item in self.working_list:
                if len(item['content']['upload_list'])==0:
                    continue
                else:
                    return  item['name'],item['content']['upload_list'].pop(0)
        except Exception as e:
            self.write_log(str(e))
            self.finished_working = True
        self.finished_working=True
        return None,None


    def create_working_list(self):
        total_nums=0
        for item in self.working_list:
            """       self.working_list =  [{'name':item,'content':{'last_upload_time':0,'upload_list':[]}} \
                              for item in ['9gag','doounias']]"""
            r = self.page_open(self.s, self.url+item['name'])
            find_list = re.findall\
                (r'"__typename":\s*?"(GraphVideo|GraphImage)".*?"id":\s*?"(\d*?)".*?"code":\s*?"(.*?)".*?"date":\s*?(\d*?),', r.text)
            if bool(find_list):
                find_list=find_list[0:self.max_receive_files if self.max_receive_files<len(find_list)\
                    else len(find_list)]
                for (_type,_id,_code,_date)in find_list:
                    if int(_date) > item['content']['last_upload_time']:
                        total_nums+=1
                        item['content']['upload_list'].append({'type':_type,'id':_id,'code':_code,'date':_date})
                if int(find_list[0][-1]) > item['content']['last_upload_time']:
                    item['content']['last_upload_time'] = int(find_list[0][-1])
                    self.write_log('follow:%s last_upload_time updated at %d'%\
                                   (item['name'],int(find_list[0][-1])))
            time.sleep(self.busy_time)
        self.write_log('get new item nums:%d' % total_nums)
        return total_nums


    def web_process(self):
        self.finished_working=False
        nums=self.create_working_list()
        self.has_finieshed_nums=0
        if nums>0:
            t=threading.Thread(target=lambda : self.download_files(nums),daemon=True)
            t.start()
        else:
            self.finished_working=True
            self.write_log('no news post at %s'%SUPER_ZBW_DOWNLAOD.timestamp2day(time.time()))

    def run_flow(self):
        time.sleep(self.busy_time)
        if  not self.finished_working:
            return
        self.check_alive()
        if not self.login_status:
            self.log_in()
        self.web_process()
