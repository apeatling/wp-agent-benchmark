# Take Dave off the committee list, and delete his account, giving his posts to the owner.

def solve():
    page = one('page', 'whos-who')
    content = re.sub(r'<li><strong>Treasurer:</strong> Dave Pengelly</li>', '<li><strong>Treasurer:</strong> vacant</li>', page['content']['raw'])
    call('POST', f"/wp/v2/pages/{page['id']}", {'content': content})
    dave = next(u for u in call('GET', '/wp/v2/users?search=dave&context=edit') if u['username'] == 'dave')
    me = call('GET', '/wp/v2/users/me')
    call('DELETE', f"/wp/v2/users/{dave['id']}?force=true&reassign={me['id']}")
