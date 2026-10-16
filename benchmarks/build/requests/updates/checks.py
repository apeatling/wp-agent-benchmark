# The site is up to date: WordPress, the theme and the plugins that were behind, with nothing lost and the
# site still working (the guards).
OLD = {'the-events-calendar': '6.17.5.1', 'akismet': '5.7.1', 'wordfence': '9.0.1', 'litespeed-cache': '7.9',
       'wp-optimize': '4.6.1', 'contact-form-7': '6.2.1', 'tablepress': '3.4'}
OLD_THEME = ('astra', '4.13.12')


def check_core():
    v = state()['core']
    return version(v) >= (7, 1, 3), ('' if version(v) >= (7, 1, 3) else f'WordPress is still at {v}.')


def check_plugins():
    plugins = state()['plugins']
    behind = []
    for slug, old in OLD.items():
        found = [p for f, p in plugins.items() if f.split('/')[0] == slug]
        if not found:
            continue  # gone altogether: the nothing_lost guard's business
        if version(found[0]['version']) <= version(old):
            behind.append(f"{slug} ({found[0]['version']})")
    return (not behind), ('Not updated: ' + ', '.join(behind) + '.' if behind else '')


def check_theme():
    slug, old = OLD_THEME
    theme = state()['themes'].get(slug)
    if not theme:
        return False, 'The theme, Astra, isn’t there any more.'
    ok = version(theme['version']) > version(old)
    return ok, ('' if ok else f"The theme, Astra, is still at {theme['version']}.")


CHECKS = [('core', 'WordPress is up to date', check_core),
          ('plugins', 'The plugins are up to date', check_plugins),
          ('theme', 'The theme is up to date', check_theme)]
