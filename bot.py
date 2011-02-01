# http://sourceforge.net/projects/python-irclib/
import irclib, logging, sys, types
from datetime import datetime

l = logging.getLogger('awesome')
l.setLevel(logging.DEBUG)
l.addHandler(logging.StreamHandler())

class PlaybackBot(object):
	
	_CHANNELS = []
	_CHANNEL_MSGS = {} # Stores channel messages
	_MSG_LIMIT = 100
	
	_DEFINED_EVENTS = ('welcome', 'pubmsg', 'privmsg') # on_<event_type> should be defined for each one
	
	class IRCMessage(object):
		'''IRC message'''
		target, source, text = (None, None, None) 
		
		def __init__(self, source, target, text):
			self.source = source
			self.target = target
			self.text	= text
			self.when	= datetime.now()
			
		def __repr__(self):
			return '<%s:%s>> %s' % (self.source, str(self.when), self.text)
		
	def __init__(self, *args,  **kwargs):
		'''Expects channel list. args and kwargs are passed to the IRC lib for connection'''
		
		self._CHANNELS = kwargs.pop('channels')
		assert isinstance(self._CHANNELS, types.ListType) or isinstance(self._CHANNELS, types.TupleType)
		assert all(isinstance(channel, types.StringType) for channel in self._CHANNELS)
		
		self.irc = irclib.IRC()
		
		try:
			self.server = self.irc.server().connect(*args, **kwargs)
		except:
			l.debug('Unable to connect to IRC server')
			raise
		else:
			
			for event_type in self._DEFINED_EVENTS:
				self.server.add_global_handler(event_type, getattr(self, 'on_%s' % event_type))
			self.irc.process_forever()
			
	def on_welcome(self, connection, event):
		'''Logic execute when a WELCOME event is received'''
		
		# Join defined channels
		for channel in self._CHANNELS:
			l.debug('Joining channel %s' % channel)
			connection.join(channel)
			
	def on_pubmsg(self, connection, event):
		'''Logic executed when a PUBMSG event is received'''
		
		event_type, source, target, args = (event.eventtype(), event.source(), event.target(), event.arguments())
		
		# Might be first message from channel
		try:
			assert isinstance(target, types.StringType)
			self._CHANNEL_MSGS[target]
		except KeyError:
			self._CHANNEL_MSGS[target] = []
		else:
			if len(self._CHANNEL_MSGS[target]) > self._MSG_LIMIT:
				del self._CHANNEL_MSGS[target][0]
		
		self._CHANNEL_MSGS[target].append(self.IRCMessage(irclib.nm_to_n(source),target, args[0]))
		
		l.debug(self._CHANNEL_MSGS)
		
	def on_privmsg(self, connection, event):
		'''Logic executed when a PRIVMSG event is received'''
		
		event_type, source, target, args = (event.eventtype(), event.source(), event.target(), event.arguments())
		
		source_nick = irclib.nm_to_n(source)
		
		channel_name = None
		try:
			channel_name = args[0]
		except IndexError:
			connection.privmsg(source_nick, 'Not enough arguements')
		else:
			if not isinstance(channel_name, types.StringType):
				connection.privmsg(source_nick, 'Channel name is not a string')
			else:
				try:
					self._CHANNEL_MSGS[channel_name]
				except KeyError:
					connection.privmsg(source_nick, 'Channel specified does not exist or has no messages')
				else:
					for message in self._CHANNEL_MSGS[channel_name]:
						connection.privmsg(source_nick, str(message))
						
HOST,PORT,NICK, PASS, CHANNELS = ('', 2502, '', '', ('#bot_test','#awesome'))
bot = PlaybackBot(HOST, PORT, NICK, password = PASS, ssl = True, channels = CHANNELS)