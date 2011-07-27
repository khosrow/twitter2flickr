import cgi
import flickrUpload
import flickr
import logging
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext.webapp.util import run_wsgi_app


# extend db to store info relating to the photos 
class Photo(db.Model):
	message = db.StringProperty()
	tags = db.StringProperty()
	date = db.DateTimeProperty(auto_now_add=True)
	data = db.BlobProperty(required=True)
	mimetype = db.StringProperty(required=True)
	photo_id = db.StringProperty()
	shortURL = db.StringProperty()


class Tag(db.Model):
	tag_id = db.Key()
	post_id = int()
	name = db.StringProperty()
	url = db.Link()


class Auth(db.Model):
	api_key = db.StringProperty()
	api_secret = db.StringProperty()
	token = db.StringProperty()


# the main page of the webapp
class MainPage(webapp.RequestHandler):
    def get(self):
		#token = db.GqlQuery("SELECT token FROM Auth")
		photos = db.GqlQuery("SELECT * FROM Photo ORDER BY date DESC LIMIT 10")
TODO:
		for photo in photos:
			date_str = photo.date.isoformat(' ')[0:16]
			tags = photo.tags.split(' ')
			self.response.out.write("""
			<tr class="rowdiv" onMouseOver="this.className='highlight'" onMouseOut="this.className='rowdiv'">
			<td class="celldiv">%s</td>
			<td class="celldiv">%s</td>
			<td class="celldiv">
			""" % (date_str, photo.message) )
			for tag in tags:
				self.response.out.write('<a href="http://flickr.com/photos/xosrow/tags/' + tag + '">' + tag + '</a> ')
			self.response.out.write("</td></tr>")
		self.response.out.write("""</table>
		</body>
		</html>""") 


# PicPoster page presents a form to user to post pics. For debug only
class PicPoster(webapp.RequestHandler):
	def get(self):
		self.response.out.write("""
		<html>
			<head><title>Pic Poster test</title></head>
			<body>
			
			<h2 style="font-family: Sans-Serif;">Select your photo</h2>
			<div style="font-family: Sans-Serif; display:block; background:#eee; border:1px solid #ccc; width:80%; border-bottom-left-radius: 5px 5px; border-bottom-right-radius: 5px 5px; border-top-left-radius: 5px 5px; border-top-right-radius: 5px 5px;padding: 10px 20px; margin-left: auto; margin-right: auto;">
			
			<form action="/uploader" method="post" enctype="multipart/form-data">
			message: <input type="text" name="message"><br>
			File: <input type="file" name="media"><br>
			<input type="submit">
			</form>""")
		self.response.out.write('</body></html>')


# uploader page is what gets called by Twitter for iPhone			
class Uploader(webapp.RequestHandler):
    def post(self):
		tweet = self.request.get('message')
		words = tweet.split(' ')
		message = ''
		myTags = ''
		
		# setting API key and secret manually for now
		flickr.API_KEY = 'd6d991956d33e88d1114ac377f4b0467'
		flickr.API_SECRET = 'e227ded1f7148092'
		# break up the tweet. Remove hashtags and send them separately as tags.
		for word in words:
			if word.rfind('#') == 0:
				junk1, junk2, tag = word.partition('#')
				myTags += tag + ' ' 
				logging.debug("tag: %s" % word)
			else:
				message += word + ' '
		# add the twitter tag by default
		myTags += 'twitter'
		
		# get the uploaded file and it's mimetype
		file = self.request.POST['media']
		
		# record the info in the db table
		photo = Photo(data=file.value, mimetype=file.type)
		photo.message = message
		photo.tags = myTags
		photo.put()
		
		# some debug info to know where the post came from
		headers = self.request.headers
		logging.debug(headers)
		logging.debug(self.request.arguments())
		logging.debug("mitmetype: %s" % file.type)
				
		# upload the image - - debug mode for now
		photo = flickrUpload.upload(filedata=file.value, mimetype=file.type, title=photo.message, tags=myTags)
		photoid = photo.__getattr__('id')
		encodedid = encode58(photoid)
		
		# if we are here the flickrError exception hasn't been thrown 
		# and we can continue to send the reponse with stat=ok
		myResponse = """<?xml version="1.0" encoding="UTF-8"?>
		<rsp stat="ok">
		<mediaid>%s</mediaid>
		<mediaurl>http://flic.kr/p/%s</mediaurl>
		</rsp>""" % (photoid, encodedid)
		
		# test debug message
		#myResponse = """<?xml version="1.0" encoding="UTF-8"?>
		#<rsp stat="ok">
		#<mediaid>abc123</mediaid>
		#<mediaurl>http://yfrog.com/835fzcj</mediaurl>
		#</rsp>"""
		
		logging.debug("writing response %s" % myResponse)
		
		# send a the response back to caller 
		self.response.out.write(myResponse)
		
		# next line is useful for later
		# redirect back to main page	
		#self.redirect('/')
    

application = webapp.WSGIApplication([('/', MainPage),
                                      ('/picposter', PicPoster),
                                      ('/uploader', Uploader)
                                     ],
                                     debug=True)


def encode58(number):
	# define the alphabet
	# includes 1 to 9
	# includes 'a' to 'z' except for 'l'
	# includes 'A' to 'Z' except for 'O' and 'I'
	alphabet = range(1,10)
	alphabet.extend(map(chr,range(97,108)))
	alphabet.extend(map(chr,range(109,123)))
	alphabet.extend(map(chr,range(65, 73)))
	alphabet.extend(map(chr,range(74,79)))
	alphabet.extend(map(chr,range(80,91)))
		
	num = int(number)
	encoded = '' 
	while num >= 58:
		remainder = num % 58
		encoded = str(alphabet[remainder]) + encoded
		temp = int(num/58)
		num = temp
		
	encoded = str(alphabet[num]) + encoded	 
		
	return encoded


def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
