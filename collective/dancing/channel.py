from zope import component
from zope import interface
import zope.app.container.interfaces

import OFS.event
import OFS.Folder
import OFS.SimpleItem
import Products.CMFPlone.interfaces
import collective.singing.subscribe
import collective.singing.interfaces
import collective.singing.message

import collective.dancing.collector
import collective.dancing.composer

def channel_lookup():
    root = component.getUtility(Products.CMFPlone.interfaces.IPloneSiteRoot)
    return root['portal_newsletters']['channels'].objectValues()
interface.directlyProvides(channel_lookup,
                           collective.singing.interfaces.IChannelLookup)

class IPortalNewsletters(interface.Interface):
    pass

class PortalNewsletters(OFS.Folder.Folder):
    interface.implements(IPortalNewsletters)
    Title = u"Newsletters"

@component.adapter(IPortalNewsletters,
                   zope.app.container.interfaces.IObjectAddedEvent)
def tool_added(tool, event):
    factories = dict(channels=ChannelContainer,
                     collectors=collective.dancing.collector.CollectorContainer)
    existing = tool.objectIds()
    for name, factory in factories.items():
        if name not in existing:
            tool[name] = factory(name)

class IChannelContainer(interface.Interface):
    pass

class ChannelContainer(OFS.Folder.Folder):
    interface.implements(IChannelContainer)
    """
      >>> container = ChannelContainer('xs')
      >>> container['your-channel'] = Channel('wq')
      >>> container.objectIds()
      ['your-channel']
    """

    Title = u"Channels"

class Channel(OFS.SimpleItem.SimpleItem):
    """
      >>> channel = Channel('xs')
      >>> from zope.interface.verify import verifyObject
      >>> verifyObject(collective.singing.interfaces.IChannel, channel)
      True
      >>> channel.name
      'xs'
    """
    interface.implements(collective.singing.interfaces.IChannel)

    def __init__(self, name, title=None,
                 composers=None, collector=None, scheduler=None):
        self.name = name
        if title is None:
            title = name
        self.title = title
        self.subscriptions = collective.singing.subscribe.SimpleSubscriptions()
        if composers is None:
            composers = {'html': collective.dancing.composer.HTMLComposer()}
        self.composers = composers
        self.collector = collector
        self.scheduler = scheduler
        self.queue = collective.singing.message.MessageQueues()
        super(Channel, self).__init__(name)

    @property
    def id(self):
        return self.name

    def Title(self):
        return self.title

@component.adapter(Channel)
@interface.implementer(collective.singing.interfaces.ISubscriptions)
def channel_subscriptions(channel):
    return channel.subscriptions
