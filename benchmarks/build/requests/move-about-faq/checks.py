# The About and FAQ pages, moved from the old site (www.polveanvets.test) onto WordPress: with all their text, as
# content that can be edited, and their photos in the site's own media library.

OLD = 'www.polveanvets.test'
ABOUT = ['since 1987', 'independent practice', 'hannah rowse', 'tom bevan', 'sue pascoe', 'purpose-built surgery', 'rcvs accredited']
# Each question, and something from its answer.
FAQ = ['need an appointment', 'except emergencies', 'out of hours', 'vets now', 'exotic pets', 'not reptiles or birds',
       'much is a consultation', '£48', 'pay monthly', '£14.50', 'home visits', 'within 5 miles', 'where can i park',
       'free car park', 'repeat prescriptions', "48 hours"]


@cache
def about():
    return best_match(ABOUT)


@cache
def faq():
    return best_match(FAQ)


def check_about():
    p, _, missing = about()
    if not p:
        return False, 'No published page with the About page’s text.'
    return (not missing), ('The About page is missing: ' + ', '.join(missing) + '.' if missing else '')


def check_faq():
    p, _, missing = faq()
    if not p:
        return False, 'No published page with the FAQ.'
    return (not missing), ('The FAQ is missing: ' + ', '.join(missing) + '.' if missing else '')


def check_photos():
    p, body, missing = about()
    if not p or len(missing) > len(ABOUT) // 2:
        return False, 'No About page to look at.'
    shown = images(main_content(body))
    ours = [u for u in shown if in_uploads(u)]
    old = [u for u in shown + images(main_content(faq()[1])) if urllib.parse.urlparse(u).netloc == OLD]
    if old:
        return False, f'{len(old)} photo(s) are still loaded from the old site.'
    return len(ours) >= 2, ('' if len(ours) >= 2 else f'The About page has {len(ours)} of its 2 photos, from the site’s media library.')


def check_editable():
    pasted = [p['title'] for p in (about()[0], faq()[0]) if p and pasted_whole(raw_content(p))]
    if not about()[0] or not faq()[0]:
        return False, 'No About and FAQ pages to look at.'
    return (not pasted), ('Pasted in as a whole old web page: ' + ', '.join(pasted) + '.' if pasted else '')


ALLOW = {}
CHECKS = [('about', 'The About page is there, with its text', check_about),
          ('faq', 'The FAQ page is there, with every question and answer', check_faq),
          ('photos', 'The About page’s photos are in the site’s media library', check_photos),
          ('editable', 'They’re pages that can be edited, not copies of the old web pages', check_editable)]
