# An ICAP service library for Python

## Introduction

The Internet Content Adaptation Protocol (ICAP) is defined in
[RFC 3507]([I'm an inline-style link](https://www.google.com).

It offers a mechanism for intercepting and modifying HTTP requests
and responses before they reach the HTTP client.

It can be a deceptively difficult protocol to use.  This library
aims to make it simple.


## Quick Start

For an ICAP service to be useful it needs to be connected to an
ICAP client.  The Squid HTTP Proxy offers
 [ICAP](http://wiki.squid-cache.org/Features/ICAP). That's what
we use here.

To get a suitably configured Squid Proxy running use the supplied
[Vagrantfile](https://www.vagrantup.com/).

