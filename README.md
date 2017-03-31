# baka-watcher  
Jakmile se zmeni suplovani (system Bakalari), aplikace posle email. Jak proste.

Tato aplikace je vazana na sluzby Googlu, tim padem ji lze spustit pouze na Google App Engine.
  
Vyzadovane knihovny:  
* [cherrypy](https://github.com/cherrypy/cherrypy)  
* [sendgrid](https://github.com/sendgrid/sendgrid-python)  
* [smtpapi](https://github.com/sendgrid/smtpapi-python)  

  
Example SendGrid template
-------------------------
Ahoj :name!  
Právě vyšlo nové suplování  

-------------------------------------------------------------

<%body%>

-------------------------------------------------------------
Pro ukončení odběru těchto emailů klikněte zde: https://myapp.appspot.com/_api/unsub?:unsub
