# The form sends to the site's admin email (WPForms' default notification), which is still the old provider's
# address. Pointing the admin email at the office fixes it. (WPForms' own notification settings aren't reachable
# through the API; its abilities only edit a form's title, description and button.)

def solve():
    call('POST', '/wp/v2/settings', {'email': 'office@harbourplumbing.test'})
