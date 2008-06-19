from zope import interface
from zope import component
from zope import schema

from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile 

from collective.dancing.composer import FullFormatWrapper
from collective.singing.channel import lookup
from collective.singing.interfaces import ISubscription
from collective.singing.interfaces import IChannel
from collective.singing.scheduler import render_message

class PreviewSubscription(object):
    interface.implements(ISubscription)

    secret = u""

    collector_data = {}
    format = 'html'
    
    metadata = {
        'format': format,
        }

    def __init__(self, channel):
        self.channel = channel

        composer = self.channel.composers[self.format]
        
        # set default composer data
        self.composer_data = dict(
            (name, field.default) \
            for name, field in schema.getFields(composer.schema).items())
        
class PreviewNewsletterView(BrowserView):
    template = ViewPageTemplateFile("preview.pt")
    
    def __call__(self, name=None, include_collector_items=False):
        if IChannel.providedBy(self.context):
            channel = self.context
            items = ()
        else:
            assert name is not None
            channel = lookup(name)
            items = (FullFormatWrapper(self.context),)
            
        sub = PreviewSubscription(channel)

        message = render_message(
            channel,
            self.request,
            sub,
            items,
            bool(include_collector_items))

        if message is not None:
            # pull message out of hat
            channel.queue[message.status].pull(-1)
        
            # walk message, decoding HTML payload
            for part in message.payload.walk():
                if part.get_content_type() == 'text/html':
                    html = part.get_payload(decode=True)
                    break
            else:
                raise ValueErrorr("Message does not contain a 'text/html' part.")
        else:
            html = u""
            
        return self.template(content=html, title=channel.title)
