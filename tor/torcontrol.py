import requests,time
from stem import Signal
from stem.control import Controller
  
def switchIP():
    with Controller.from_port(port=19151) as controller:
        controller.authenticate()
        controller.signal(Signal.NEWNYM)

  
    
def getIP(proxy=None):
    headers = {'Connection':'close'}
    proxies = {}
    if proxy != None:
        proxies["http"] = proxy
        proxies["https"] = proxy
    response = requests.get("http://ip-api.com/json", headers=headers,proxies=proxies)
    data=json.loads(response.content.decode('utf-8'))
    if data["status"] == "success":
        print(data["query"], data["city"])
        
        
def main():
    getIP("socks5h://127.0.0.1:19151")
    time.sleep(7)
    switchIP()
    getIP("socks5h://127.0.0.1:19151")
    
if __name__ == '__main__':
    main()
