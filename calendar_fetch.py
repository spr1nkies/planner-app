"""Bounded HTTPS calendar fetches with pinned public DNS targets; no URL logging."""
import http.client, ipaddress, socket, ssl
from urllib.parse import urlsplit, urljoin
LIMIT=2*1024*1024

def normalise_url(value):
    if not isinstance(value,str) or len(value)>4096: raise ValueError('Invalid calendar link.')
    value=value.strip()
    if value.lower().startswith('webcal://'): value='https://'+value[9:]
    p=urlsplit(value)
    if p.scheme!='https' or not p.hostname or p.username or p.password or p.port not in (None,443) or p.fragment:
        raise ValueError('Use an HTTPS or webcal calendar subscription link without credentials in the address.')
    if not '.' in p.hostname or p.hostname.endswith(('.local','.localhost','.internal')): raise ValueError('Use a public calendar provider.')
    return value

class PinnedHTTPS(http.client.HTTPSConnection):
    def __init__(self,host,ip):
        super().__init__(host,timeout=15,context=ssl.create_default_context());self.target_ip=ip
    def connect(self):
        raw=socket.create_connection((self.target_ip,443),timeout=self.timeout)
        self.sock=self._context.wrap_socket(raw,server_hostname=self.host)

def fetch_calendar(value):
    url=normalise_url(value)
    for _ in range(4):
        p=urlsplit(url)
        targets=socket.getaddrinfo(p.hostname,443,type=socket.SOCK_STREAM)
        addresses=list(dict.fromkeys(x[4][0] for x in targets))
        if not addresses or any(not ipaddress.ip_address(ip).is_global or getattr(ipaddress.ip_address(ip),'ipv4_mapped',None) for ip in addresses):raise ValueError('Calendar links must resolve to public servers.')
        conn=PinnedHTTPS(p.hostname,addresses[0])
        try:
            conn.request('GET',(p.path or '/')+('?' + p.query if p.query else ''),headers={'Accept':'text/calendar','User-Agent':'Planner-Calendar/1.0','Accept-Encoding':'identity'})
            response=conn.getresponse()
            if response.status in (301,302,303,307,308):
                target=response.getheader('Location')
                if not target:raise ValueError('Invalid calendar redirect.')
                url=normalise_url(urljoin(url,target));continue
            if response.status!=200:raise ValueError('Calendar provider did not return a calendar. Check that the subscription link is accessible.')
            raw=response.read(LIMIT+1)
            if len(raw)>LIMIT:raise ValueError('Calendar exceeds the 2 MB limit.')
            text=raw.decode('utf-8-sig')
            if 'BEGIN:VCALENDAR' not in text[:1024]:raise ValueError('The link returned a web page rather than an .ics calendar. Use its subscription/export URL.')
            return text
        finally:conn.close()
    raise ValueError('Too many calendar redirects.')
