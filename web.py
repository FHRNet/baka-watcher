#!/usr/bin/python
# -*- coding: utf8 -*-

import cherrypy
import os
import json
import sendgrid
import re
import urllib2
import hashlib
import binascii

from email.utils import parseaddr
from google.appengine.ext import ndb
from google.appengine.ext.webapp.util import run_wsgi_app


class SendMail:
    client = None
    
    def __init__(self):
        self.client = sendgrid.SendGridClient('sg_login', 'sg_pass')

    def send(self, email, name, html, unsub):
        s = self.client
        message = sendgrid.Mail()

        # From address
        message.set_from('skola@example.com')
        message.add_to(email)
        # Subject of sent emails
        message.set_subject('Nové suplování')
        message.add_filter('templates', 'enable', '1')
        # SendGrid template id
        message.add_filter('templates', 'template_id', 'xxxxx')
        # Pass variables to template
        message.add_substitution(':name', name)
        message.add_substitution(':unsub', unsub)
        message.set_html(html)
        status, msg = s.send(message)
        


# Database models
class Subscribers(ndb.Model):
    email = ndb.StringProperty()
    name = ndb.StringProperty()

class Misc(ndb.Model):
    k = ndb.StringProperty()
    v = ndb.StringProperty()


class Main(object):
    data = None
    sm = None
    
    @cherrypy.expose(['send'])
    def send(self, email, name):
        # Generate unsub key
        unsub = "email=" + email + "&key=" + self.unsubKey(email)
        self.sm.send(email, name, self.data, unsub)
        return("OK")

    @cherrypy.expose(['subscribe'])
    def subscribe(self, name, email):
        if name == "":
            # User has not filled in his name, fall back to this value
            name = "člověče"
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            # Wait a minute... this is not a valid email address
            return("Not Valid")
        if(Subscribers.query(Subscribers.email == email).count(10) > 0):
            # Already subscribed
            return("Already exists")
        else:
            # Yaay, everything is fine. Add them to Subscribers table.
            newsub = Subscribers(email=email, name=name)
            newsub_store = newsub.put()
            self.send(email, name)
            return("Stored")

    @cherrypy.expose(['unsub'])
    def unsub(self, email, key):
        # User wants to unsub :/
        # But is he real?
        if(key == self.unsubKey(email)):
            # He sure is. Delete them.
            ndb.delete_multi(Subscribers.query(Subscribers.email == email).fetch(keys_only=True))
            return("OK")
        else:
            # Bye mate.
            return("Access denied")

    def sendToSubs(self):
        # Get everyone from database
        qry = Subscribers.query().fetch()
        # Each user wants to get an email
        self.sm = SendMail()
        for sub in qry:
            self.send(sub.email, sub.name)
        return("OK")

    @cherrypy.expose
    def suplovani(self):
        # Download and filter the document
        www = urllib2.urlopen('http://example.com/bakalar/suplovani/suplobec.htm', timeout=2).read() # Get data
        style = urllib2.urlopen('http://example.com/bakalar/suplovani/styly_s.css', timeout=2).read() # Get stylesheet
        # Filter out the nasty stuff
        www = www.replace('<link rel="stylesheet" type="text/css" href="styly_s.css">', '').replace('<title>Bakaláři - Suplování</title>', '')
        # Return with our added stuff
        return(www+"<style>"+style+" tr.tr_suplucit_3, tr.tr_abtrid_3, tr.tr_supltrid_3 { background-color: transparent !important; }</style>")

    def updateSuplovani(self):
        print("Fetching a fresh copy of data")
        self.data = self.suplovani()

    def unsubKey(self, email):
        return(hashlib.sha1(email + b'MY_PRECIOUS').hexdigest()) # Unsubscribe key generator with salt

    @cherrypy.expose
    def hasChanged(self):
        # See if we need to update
        # Get a hash of current document
        self.updateSuplovani()
        cur = hashlib.md5(self.data).hexdigest()
        try:
            # No need to update
            if(Misc.query(Misc.k == "lastid").fetch().pop(0).v == cur):
                return("Latest version")
            # We do need to update
            else:
                ndb.delete_multi(Misc.query(Misc.k == "lastid").fetch(keys_only=True))
                m = Misc(k="lastid", v=cur)
                m.put()
                print("Sending emails")
                self.sendToSubs()
                return("Updated")
        except:
            # Nothing in database, this is first run
            m = Misc(k="lastid", v=cur)
            m.put()
            self.sendToSubs()
            return("Updated")


# CherryPy config
conf = {
    '/_api/': {
        'environment': 'embedded',
    }
}

# "Do the needful"
# /s
app = cherrypy.tree.mount(Main(), '/_api/', conf)
app.request_class.show_tracebacks = False
logger = cherrypy.log.access_log
logger.removeHandler(logger.handlers[0])
run_wsgi_app(app)
