from zope.component import getMultiAdapter
from zope.interface import implements

from Acquisition import aq_base, aq_inner, aq_parent

from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import utils
from Products.CMFPlone.browser.interfaces import INavigationPortlet

from Products.CMFPlone.browser.navtree import getNavigationRoot

class NavigationPortlet(utils.BrowserView):
    implements(INavigationPortlet)

    def title(self):
        context = utils.context(self)
        portal_properties = getToolByName(context, 'portal_properties')
        return portal_properties.navtree_properties.name

    def display(self):
        tree = self.getNavTree()
        root = self.getNavRoot()
        return (root is not None and len(tree['children']) > 0)

    def includeTop(self):
        context = utils.context(self)
        portal_properties = getToolByName(context, 'portal_properties')
        return portal_properties.navtree_properties.includeTop

    def navigationRoot(self):
        return self.getNavRoot()

    def rootTypeName(self):
        context = utils.context(self)
        root = self.getNavRoot()
        return utils.normalizeString(root.portal_type, context=context)

    def createNavTree(self):
        context = utils.context(self)
        data = self.getNavTree()
        properties = getToolByName(context, 'portal_properties')
        navtree_properties = getattr(properties, 'navtree_properties')
        bottomLevel = navtree_properties.getProperty('bottomLevel', 0)
        # XXX: The recursion should probably be done in python code
        return context.portlet_navtree_macro(
            children=data.get('children', []),
            level=1, show_children=True, isNaviTree=True, bottomLevel=bottomLevel)

    def isPortalOrDefaultChild(self):
        context = utils.context(self)
        root = self.getNavRoot()
        return (aq_base(root) == aq_base(context) or
                (aq_base(root) == aq_base(aq_parent(aq_inner(context))) and
                utils.isDefaultPage(context, self.request, context)))

    # Cached lookups

    def getNavRoot(self):
        """Get and cache the navigation root"""
        if not utils.base_hasattr(self, '_root'):
            context = utils.context(self)
            portal_url = getToolByName(context, 'portal_url')
            portal = portal_url.getPortalObject()

            view = getMultiAdapter((context, self.request),
                                   name='navtree_builder_view')
            rootPath = view.navigationTreeRootPath()

            if rootPath == portal_url.getPortalPath():
                root = portal
            else:
                try:
                    root = portal.unrestrictedTraverse(rootPath)
                except (AttributeError, KeyError,):
                    root = portal

            self._root = [root]

        return self._root[0]

    def getNavTree(self):
        """Calculate the navtree"""
        tree = getattr(self, '_navtree', None)
        if tree is not None:
            return tree
        else:
            context = utils.context(self)
            view = getMultiAdapter((context, self.request),
                                   name='navtree_builder_view')
            self._navtree = view.navigationTree()
            return self._navtree