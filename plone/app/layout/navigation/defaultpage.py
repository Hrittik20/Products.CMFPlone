# -*- coding: utf-8 -*-
from Acquisition import aq_inner, aq_base
from plone.app.layout.navigation.interfaces import IDefaultPage
from Products.BTreeFolder2.BTreeFolder2 import BTreeFolder2Base
from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFDynamicViewFTI.interfaces import IBrowserDefault
from Products.CMFDynamicViewFTI.interfaces import IDynamicViewTypeInformation
from Products.Five.browser import BrowserView
from zope.component import queryAdapter
from zope.component import queryUtility
from zope.interface import implementer


@implementer(IDefaultPage)
class DefaultPage(BrowserView):

    def isDefaultPage(self, obj):
        return isDefaultPage(aq_inner(self.context), obj)

    def getDefaultPage(self):
        return getDefaultPage(aq_inner(self.context))


def isDefaultPage(container, obj):
    """Finds out if the given obj is the default page in its parent folder.

    Only considers explicitly contained objects, either set as index_html,
    with the default_page property, or using IBrowserDefault.
    """
    parentDefaultPage = getDefaultPage(container)
    precondition = (
        parentDefaultPage is not None
        and '/' not in parentDefaultPage
        and hasattr(obj, 'getId')
    )
    return precondition and (parentDefaultPage == obj.getId())


def getDefaultPage(context):
    """Given a folderish item, find out if it has a default-page using
    the following lookup rules:

        1. A content object called 'index_html' wins
        2. Else check for IBrowserDefault, either if the container implements
           it or if an adapter exists. In both cases fetch its FTI and either
           take it if it implements IDynamicViewTypeInformation or adapt it to
           IDynamicViewTypeInformation. call getDefaultPage on the implementer
           and take value if given.
        3. Else, look up the attribute default_page on the object, without
           acquisition in place
        3.1 look for a content in the container with the id, no acquisition!
        3.2 look for a content at portal, with acquisition
        4. Else, look up the property default_page in site_properties for
           magic ids and test these

    The id of the first matching item is then used to lookup a translation
    and if found, its id is returned. If no default page is set, None is
    returned. If a non-folderish item is passed in, return None always.
    """
    # The ids where we look for default - must support __contains__
    ids = set()

    # For BTreeFolders we just use the __contains__ otherwise build a set
    if isinstance(aq_base(context), BTreeFolder2Base):
        ids = context
    elif hasattr(aq_base(context), 'objectIds'):
        ids = set(context.objectIds())

    # 1. test for contentish index_html
    if 'index_html' in ids:
        return 'index_html'

    # 2. Test for IBrowserDefault
    if IBrowserDefault.providedBy(context):
        browserDefault = context
    else:
        browserDefault = queryAdapter(context, IBrowserDefault)

    if browserDefault is not None:
        fti = context.getTypeInfo()
        if fti is not None:
            if IDynamicViewTypeInformation.providedBy(fti):
                dynamicFTI = fti
            else:
                dynamicFTI = queryAdapter(fti, IDynamicViewTypeInformation)
            if dynamicFTI is not None:
                page = dynamicFTI.getDefaultPage(context, check_exists=True)
                if page is not None:
                    return page

    # 3.1 Test for default_page attribute in folder, no acquisition
    pages = getattr(aq_base(context), 'default_page', [])
    if isinstance(pages, basestring):
        pages = [pages]
    for page in pages:
        if page and page in ids:
            return page

    portal = queryUtility(ISiteRoot)
    # Might happen during portal creation
    if portal is None:
        return

    # 3.2 Test for default page in portal, acquire
    for page in pages:
        if portal.unrestrictedTraverse(page, None):
            return page

    # 4. Test for default sitewide default_page setting
    pp = getattr(portal, 'portal_properties', None)
    if pp is not None:
        site_properties = getattr(pp, 'site_properties', None)
        if site_properties is not None:
            for page in site_properties.getProperty('default_page', []):
                if page in ids:
                    return page

    return
