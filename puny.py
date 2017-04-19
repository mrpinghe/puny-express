#!/usr/bin/env python

import base64
import urllib
import urllib2
import socket
import ssl
import json
import sys
import lxml.html
from lxml.cssselect import CSSSelector

# for i in $(seq 1 100); do echo -n companyname | mimic -m $i | base64 >> domain-list.txt; done
# cat domain-list.txt | sort | uniq > domain-list-uniq.txt
file_path = "./domain-list-uniq.txt"
# print socket.gethostbyname("google.com")
puny_domains = {}

with open(file_path) as file:
	for line in file:
		# change base64 to unicode and then add .com
		name = "%s.com" % base64.b64decode(line).strip()
		# change to punycode
		punycode = name.decode("utf-8").encode("idna")

		if punycode not in puny_domains:
			puny_domains[punycode] = []

		puny_domains[punycode].append({"b64": line.strip(), "unicode": name})


print "** Total distinct punycode domain: %d **" % len(puny_domains)

for punycode, name in puny_domains.iteritems():
	try:
		ctx = ssl.create_default_context()
		# not validating cert when using Burp to proxy request
#		ctx.check_hostname = False
#		ctx.verify_mode = ssl.CERT_NONE

		# Request 1. Get a valid csrf_token and cookie
		url = "https://www.name.com/domain/search/thankyou-name.com"
		headers = {
			"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"
		}

		req = urllib2.Request(url, None, headers)
		resp = urllib2.urlopen(req, context=ctx)

		resp_headers = str(resp.info()).split("\r\n")

		for header in resp_headers:
			if "REG_IDT" in header:
				cookie = header.split(" ")[1]

		if cookie is None:
			print "couldn't get valid cookie"
			sys.exit(2)

		tree = lxml.html.fromstring(resp.read())
		sel = CSSSelector("meta[name=\"csrf-token\"]")
		meta = sel(tree)
		csrf_token = meta[0].get("content")

		# Request 2. Use valid csrf token & cookie combo to get a search_tracking_id and search_id
		url = "https://www.name.com/api/search/start"
		headers.update({
			"x-csrf-token-auth": csrf_token,
			"Cookie": cookie,
			"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"
		})
		data = {
			"config": "new-dizzy-geo",
			"page": "0",
			"tracking_type": "dynamic-powerbar-search",
			"version": "5.2",
			"search_tracking_id": "0",
			"keyword": punycode
		}

		query = urllib.urlencode(data)

		req = urllib2.Request(url, query, headers)
		resp = urllib2.urlopen(req, context=ctx)

		if resp.getcode() != 200:
			print "Can't get valid tracking_id"
			sys.exit(2)

		jdata = json.loads(resp.read())
		search_id = jdata["search_id"]
		search_tracking_id = jdata["search_tracking_id"]

		# Request 3. Do the actual search
		url = "https://www.name.com/api/search/poll"
		data.update({
			"search_tracking_id": search_tracking_id,
			"search_id": search_id,
			"person_name": "0"
		})

		query = urllib.urlencode(data)
		req = urllib2.Request(url, query, headers)
		resp = urllib2.urlopen(req, context=ctx)
		if resp.getcode() != 200:
			print "Can't get valid availability data"
			sys.exit(2)

		jdata = json.loads(resp.read())
		avail = jdata["domains"][punycode]["avail"]
		print "punycode: %s; available: %s" % (punycode, avail)
		if avail == 0:
			print "!! Possible variations of this punycode !!"
			for val in name:
				print "[-] %s; base64: %s" % (val["unicode"], val["b64"])
	except:
		print "Encountered unknown problems when validating %s. Consider verify it manually" % punycode
		print "!! Possible variations of this punycode !!"
		for val in name:
			print "[-] %s; base64: %s" % (val["unicode"], val["b64"])
