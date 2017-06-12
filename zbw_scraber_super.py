from abc import ABCMeta, abstractmethod
import datetime
import pytz
import re
import threading
import urllib.request
import logging
import requests
import time
import random
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
        self.is_busy = False
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
        while self.is_busy:
            time.sleep(.5)
        self.is_busy = True
        r=None
        try:
            time.sleep(self.busy_time)
            r = requests_obj.get(url)
        except Exception as e:
            self.write_log(str(e))
        finally:
            self.is_busy = False
            return r
    def page_post(self,requests_obj,url,data):
        while self.is_busy:
            time.sleep(.5)
        self.is_busy = True
        r=None
        try:
            time.sleep(self.busy_time)
            r = requests_obj.post(url, data=data, allow_redirects=True)
        except Exception as e:
            self.write_log(str(e))
        finally:
            self.is_busy = False
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
    def __init__(self,user,password,threads_num,other_logger=None,call_back=None):
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
        self.finished_working=True
        self.is_getting_item_from_list=False
        self.has_finieshed_nums=0
        self.working_list =  [{'name':item,'content':{'last_upload_time':0,'upload_list':[]}} \
                              for item in ['9gag','doounias','viraldiys']]
        self.url_media_detail='https://www.instagram.com/p/'
        self.max_threading=threads_num
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

    def download_files(self,total_nums,filename=None):
        # while True:
        #     self.check_alive()
        #     if not self.login_status:
        #         return
        # test_url='https://scontent.cdninstagram.com/t50.2886-16/19054712_1515312775198294_3211878201529729024_n.mp4'
        while True:
            self.check_alive()
            if not self.login_status:
                self.is_getting_item_from_list = False
                return
            while self.is_getting_item_from_list:
                time.sleep(.5)
            self.is_getting_item_from_list=True
            item=self.pop_from_working_list()
            if not bool(item):
                print('downloading threading finished!')
                self.is_getting_item_from_list = False
                return
            try:
                item = dict(item)
                url=self.url_media_detail+item['code']
                self.write_log('start downloading %s/%s update at%s'%(item['type'],item['code'],item['date']))
                time.sleep(self.busy_time)
                # local_file,headers=urllib.request.urlretrieve(url, filename=filename)
                self.is_getting_item_from_list = False
                self.has_finieshed_nums +=1
                self.write_log('%s has downloaded successfully finished:%d/total:%d'%\
                               ('file',self.has_finieshed_nums,total_nums))
                if hasattr(self.call_back,'__call__'):
                    self.call_back()
                    continue
            except Exception as e:
                self.is_getting_item_from_list = False
                self.write_log(str(e))


    def pop_from_working_list(self):
        try:
            for item in self.working_list:
                if len(item['content']['upload_list'])==0:
                    continue
                else:
                    return  item['content']['upload_list'].pop(0)
        except Exception as e:
            self.write_log(str(e))
            self.finished_working = True
        self.finished_working=True


    def create_working_list(self):
        total_nums=0
        for item in self.working_list:
            """       self.working_list =  [{'name':item,'content':{'last_upload_time':0,'upload_list':[]}} \
                              for item in ['9gag','doounias']]"""
            r = self.page_open(self.s, self.url+item['name'])
            find_list = re.findall\
                (r'"__typename":\s*?"(GraphVideo|GraphImage)".*?"id":\s*?"(\d*?)".*?"code":\s*?"(.*?)".*?"date":\s*?(\d*?),', r.text)
            if bool(find_list):
                for (_type,_id,_code,_date)in find_list[:-1]:
                    if int(_date) > item['content']['last_upload_time']:
                        item['content']['upload_list'].append({'type':_type,'id':_id,'code':_code,'date':_date})
                        total_nums+=1
                else:
                    if int(find_list[0][-1]) > item['content']['last_upload_time']:
                        item['content']['last_upload_time'] = int(find_list[0][-1])
                        self.write_log('follow:%s last_upload_time at %s'%\
                                       (item['name'],self.timestamp2day(item['content']['last_upload_time'])))
                    else:
                        continue
            time.sleep(2)
        self.write_log('get new item nums:%d'%total_nums)
        return total_nums

    def web_process(self):
        self.finished_working=False
        nums=self.create_working_list()
        self.has_finieshed_nums=0
        for i in range(0,self.max_threading):
            t=threading.Thread(target=lambda : self.download_files(nums),daemon=True)
            t.start()

    def run_flow(self):
        self.check_alive()
        while True:
            if not self.login_status:
                self.log_in()
                continue
            if  not self.finished_working:
                time.sleep(.5)
                continue
            self.web_process()
            time.sleep(10)