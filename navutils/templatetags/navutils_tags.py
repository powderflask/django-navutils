from django import template
from navutils import settings

register = template.Library()

def get_user(context, **kwargs):
    """ Return the user object from the context or kwargs, or raise a ValueError if not found """
    user = kwargs.get('user', context.get('user', getattr(context.get('request', object()), 'user', None)))
    if not user:
        raise ValueError('missing user parameter')
    return user

@register.simple_tag(takes_context=True)
def render_menu(context, menu, **kwargs):

    # menu = kwargs.get('menu', context.get('menu'))
    # if not menu:
    #     raise ValueError('Missing menu argument')

    user = get_user(context, **kwargs)

    max_depth = kwargs.get('max_depth', context.get('max_depth', 999))
    viewable_nodes = [node for node in menu.values() if node.is_viewable_by(user, context)]
    if not viewable_nodes and not menu.dynamic_nodes:   # purely dynamic menu may have not have static nodes
        return ''

    current_menu_item = kwargs.get('current_menu_item', context.get('current_menu_item'))
    current_node = menu.get_node(current_menu_item)
    t = template.loader.get_template(menu.template)
    c = {
        'menu': menu,
        'viewable_nodes': viewable_nodes,
        'user': user,
        'max_depth': max_depth,
        'current_menu_item': current_menu_item,
        'current_menu_node': current_node,
        'menu_config': settings.NAVUTILS_MENU_CONFIG,
    }
    try:
        final_context = menu.get_context({**context, **c})
    except TypeError:
        # Django 2.0+
        final_context = menu.get_context({**context.flatten(), **c})
    return t.render(final_context)


@register.simple_tag(takes_context=True)
def render_node(context, node, **kwargs):
    # node = kwargs.get('node', context.get('node'))
    # if not node:
    #     raise ValueError('Missing node argument')

    user = get_user(context, **kwargs)

    if not node.is_viewable_by(user, context):
        return ''

    current = kwargs.get('current_menu_item', context.get('current_menu_item'))
    max_depth = kwargs.get('max_depth', context.get('max_depth', 999))
    start_depth = kwargs.get('start_depth', context.get('start_depth', node.depth))
    current_depth = kwargs.get('current_depth', context.get('current_depth', node.depth - start_depth))

    viewable_children = []
    if current_depth + 1 <= max_depth:
        for child in node.children:
            if child.is_viewable_by(user, context):
                viewable_children.append(child)

    t = template.loader.get_template(node.template)

    c = {
        'is_current': node.is_current(current),
        'has_current': node.has_current(current, viewable_children),
        'current_menu_item': current,
        'node': node,
        'viewable_children': viewable_children,
        'user': user,
        'max_depth': max_depth,
        'current_depth': current_depth,
        'start_depth': start_depth,
        'menu_config': settings.NAVUTILS_MENU_CONFIG
    }
    try:
        final_context = node.get_context({**context, **c})
    except TypeError:
        # Django 2.0+
        final_context = node.get_context({**context.flatten(), **c})
    return t.render(final_context)


@register.simple_tag(takes_context=True)
def render_crumb(context, crumb, **kwargs):

    t = template.loader.get_template('navutils/crumb.html')

    return t.render({
        'crumb': crumb,
        'last': kwargs.get('last', False),
    })

@register.simple_tag(takes_context=True)
def render_breadcrumbs(context, crumbs, **kwargs):

    t = template.loader.get_template('navutils/breadcrumbs.html')

    return t.render({
        'crumbs': crumbs,
    })

@register.simple_tag(takes_context=True)
def render_nested(context, template_text):
    # create template from text
    tpl = template.Template(template_text)
    return tpl.render(context)


@register.simple_tag(takes_context=True)
def render_node_url(context, node, **kwargs):
    """ renders just the url for a node so it's link can be rendered in context from outside a menu """
    user = get_user(context, **kwargs)

    if not node.is_viewable_by(user, context):
        return ''

    c = {
        'node': node,
    }
    try:
        final_context = node.get_context({**context, **c})
    except TypeError:
        # Django 2.0+
        final_context = node.get_context({**context.flatten(), **c})
    return final_context['node'].get_url()

