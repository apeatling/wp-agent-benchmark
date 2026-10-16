# Dave has left the committee: he can't get into the site any more, his news posts stay, and he's off the
# Who's who page.
ALLOW = {'removed_users': ['dave'], 'changed': ['whos-who']}


def dave_before():
    return user(baseline(), login='dave')


# The owner asked to take Dave off the website, not to remove his login: a careful agent spots that his editor
# account still works, so it's recorded, but not required.
OPTIONAL = {'access'}


def check_access():
    u = next((u for u in state()['users'] if u['id'] == dave_before()['id']), None)
    if not u:
        return True, ''
    if 'edit_posts' in u['caps'] or set(u['roles']) - {'subscriber'}:
        return False, f"Dave's account is still there and can still edit the site (role: {', '.join(u['roles']) or 'none'})."
    return True, ''


def check_posts():
    now = {p['id']: p for p in state()['posts']}
    his = [p for p in baseline()['posts'] if p['type'] == 'post' and p['status'] == 'publish' and p['author'] == dave_before()['id']]
    gone = [p['title'] for p in his if now.get(p['id'], {}).get('status') != 'publish']
    if gone:
        return False, f"{len(gone)} of the {len(his)} posts Dave wrote aren't published any more (e.g. “{gone[0]}”)."
    return True, ''


def check_page():
    page = find(state(), 'page', slug='whos-who')
    if not page:
        return False, 'The Who’s who page isn’t published any more.'
    s, t = visit(page[0])
    if s != 200:
        return False, f'The Who’s who page doesn’t load ({s}).'
    if 'pengelly' in t or 'dave' in t:
        return False, 'Dave is still on the Who’s who page.'
    if 'helen treloar' not in t or 'sue hocking' not in t:
        return False, 'The rest of the committee isn’t on the Who’s who page any more.'
    return True, ''


CHECKS = [('access', 'Dave can no longer get into the site', check_access),
          ('posts', 'Every news post Dave wrote is still up', check_posts),
          ('page', 'Dave is off the Who’s who page', check_page)]
