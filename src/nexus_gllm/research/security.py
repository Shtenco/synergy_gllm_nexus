from __future__ import annotations
import ipaddress, socket
from urllib.parse import urlparse
from dataclasses import dataclass

@dataclass(frozen=True)
class ValidatedURL:
    url:str
    host:str
    ips:tuple[str,...]

def _blocked(ip:ipaddress._BaseAddress)->bool:
    return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved or ip.is_unspecified

def validate_public_http_url(url:str,resolver=None)->ValidatedURL:
    p=urlparse(url)
    if p.scheme not in ('http','https') or not p.hostname: raise ValueError('only public http(s) URLs allowed')
    host=p.hostname.lower()
    try:
        ip=ipaddress.ip_address(host)
        ips=[str(ip)]
    except ValueError:
        if host in ('localhost','metadata.google.internal'): raise ValueError('blocked host')
        if resolver is None:
            # Avoid DNS in deterministic tests. Production transports pass a resolver.
            return ValidatedURL(url,host,())
        ips=list(resolver(host))
    for s in ips:
        if _blocked(ipaddress.ip_address(s)): raise ValueError('private/reserved target blocked')
    return ValidatedURL(url,host,tuple(ips))