__all__ = ['get_arxiv_entries', 'get_kipac_members', 'calc_scores',
           'get_active_indices_and_clean_up', 'prepare_email_to_organizers',
           'iter_prepare_email_to_individuals', 'format_today']

import io
import time
import md5
import cgi
from collections import defaultdict
import numpy as np

from fetch_arxiv import fetch_arxiv, get_time_range, fetch_arxiv_rss
from topic_model import topic_model, collection_weight, similarity_threshold
from secrets import keypass, member_list_path, collection_weight_path
from Member import Member


def get_arxiv_entries():
    arxiv = fetch_arxiv_rss()
    if arxiv.date == time.strftime("%Y%m%d") and arxiv.entries:
        return arxiv.entries

    arxiv = fetch_arxiv(
        max_results=200,
        search_query='cat:astro-ph*+AND+submittedDate:[{0[0]}+TO+{0[1]}]'.format(get_time_range(time.time())),
    )
    return arxiv.entries

def get_kipac_members():
    people = []
    with io.open(member_list_path, 'r', encoding='utf-8') as f:
        header = f.next().strip().split(',')
        for line in f:
            row = dict(zip(header, line.strip().split(',')))
            m = Member(row['arxivname'])
            if row['email'] and (m.has_prefs() or int(row['is_kipac'] or 0)):
                row['model'] = m.get_model()
                row['prefs'] = m.get_prefs()
                if row['model'] is not None:
                    people.append(row)
    return people


def calc_scores(entries, people, return_keywords=0):
    with open(collection_weight_path, 'rb') as f:
        cw = collection_weight(f.read())
    scores = []
    return_keywords = int(return_keywords)
    if return_keywords:
        keywords = defaultdict(list)
    for entry in entries:
        model = topic_model()
        model.add_document(entry['title'] + '.' + entry['summary'])
        model.apply_weight(cw)
        if return_keywords:
            for i, person in enumerate(people):
                s, k = model.get_similarity(person['model'], return_keywords)
                scores.append(s)
                keywords[i].append(k)
        else:
            scores.extend(model.get_similarity(person['model']) for person in people)
    scores = np.array(scores).reshape(len(entries), len(people))
    if return_keywords:
        return scores, keywords
    else:
        return scores


def get_active_indices_and_clean_up(people):
    active_idx = []
    for i, person in enumerate(people):
        if int(person['active'] or 0):
            active_idx.append(i)
        del person['model']
        del person['active']
    return active_idx


def get_largest_indices(scores, limit, threshold=similarity_threshold, store_argsort=None):
    s = scores.argsort()
    if store_argsort is not None:
        store_argsort[:] = s[::-1]
    for c, i in enumerate(reversed(s)):
        if scores[i] < threshold or c >= limit:
            break
        yield i


def format_today():
    return time.strftime('%m/%d', time.localtime())


def format_authors(authors, max_authors=6):
    a = u', '.join(authors[:max_authors])
    if len(authors) > max_authors:
        a += u' et al.'
    return cgi.escape(a)


def format_keywords(keywords, max_keywords=3, bold=False):
    if not keywords:
        return u''
    keywords = list(keywords)
    final_keywords = []
    n = len(keywords)
    for _ in range(n):
        k = keywords.pop(0)
        if not any(k in kk for kk in keywords):
            final_keywords.append(k)
            if len(final_keywords) >= max_keywords:
                break
            keywords.append(k)
    return u'<i>Keywords: {1}{0}{2}</i> <br>'.format(cgi.escape(u', '.join(final_keywords)), '<b>' if bold else '', '</b>' if bold else '')


def format_entry(entry, arxivname, print_abstract=True, score=None, keywords=None, export=False):
    arxiv_id = entry['key']
    key = md5.md5(arxiv_id + arxivname + keypass).hexdigest()
    url = 'https://web.stanford.edu/group/kipac_teabot/cgi-bin/teabot/taste-tea.py?id={0}&name={1}&key={2}'.format(arxiv_id, arxivname, key)
    abstract = u'{0} [<a href="{1}">Read more</a>] <br><br><br>'.format(cgi.escape(entry['summary']), url) if print_abstract else u''
    score = u' (score = {:.3g})'.format(score) if score is not None else u''
    keywords = format_keywords(keywords, bold=print_abstract)
    export_links = u'[<a href="{0}&mendeley=on">Save to Mendeley</a>] <br>'.format(url) if export else ''
    return u'<li>[<a href="{0}&abs=on">{1}</a>] <b><a href="{0}">{2}</a></b>{5} <br>by {3} <br>{6}{7}<br>{4}</li>'.format(\
                url, arxiv_id, cgi.escape(entry['title']), format_authors(entry['authors']), abstract, score, keywords, export_links)


def prepare_email_to_organizers(entries, people, scores, active_idx, n_papers=8, n_people=4):
    msg = u'<h2>KIPAC people might find the following new papers on arXiv today interesting:</h2>'
    msg += u'<ul>'
    median_scores = np.median(scores[:,active_idx], axis=1)
    any_paper = False
    for i in get_largest_indices(median_scores, n_papers, 0):
        names = [people[active_idx[j]]['name'] \
                for j in get_largest_indices(scores[i,active_idx], n_people)]
        if names:
            any_paper = True
            entry = entries[i]
            msg += u'<li>[<a href="https://arxiv.org/abs/{0[key]}">{0[key]}</a>] <a href="https://arxiv.org/pdf/{0[key]}.pdf">{1}</a> <br>by {2} <br>Try asking: {3} <br><br></li>'.format(\
                    entry, cgi.escape(entry['title']), format_authors(entry['authors']), ', '.join(names))
    msg += u'</ul>'
    msg += u'<p>Also check <a href="http://stanford.edu/group/kipac_teabot/cgi-bin/teabot/arxiv-discovery">this page</a> for new arXiv papers authored by KIPAC members.</p>'
    return msg if any_paper else u''


def iter_prepare_email_to_individuals(entries, people, scores, keywords=None):
    for j, person in enumerate(people):
        if not person['prefs'] or not person['email']:
            continue
        greetings = u'Hi {0}, <br><br>'.format(person['nickname'])
        msg = u'TeaBot thinks you\'ll find the following paper(s) on arXiv today interesting: <br>'
        msg += u'<ul>'
        any_paper = 0
        ss = np.empty(len(scores), int) if person['prefs']['nl'] > person['prefs']['nr'] else None
        for i in get_largest_indices(scores[:, j], person['prefs']['nr'], store_argsort=ss):
            if not any_paper:
                best_title = entries[i]['title']
            msg += format_entry(entries[i], person['arxivname'], person['prefs']['pa'], keywords=keywords[j][i], export=person['prefs'].get('export', False))
            any_paper += 1
        msg += u'</ul>'
        if person['prefs']['nl'] > person['prefs']['nr']:
            if not any_paper:
                any_paper += 1
                best_title = '{0} new papers on arXiv'.format(time.strftime('%m/%d',time.localtime()))
                msg = u''
            msg += u'The following papers are sorted by relevance:'
            msg += u'<ul>'
            for i in ss[any_paper:person['prefs']['nl']]:
                msg += format_entry(entries[i], person['arxivname'], False, keywords=keywords[j][i], export=person['prefs'].get('export', False))
            msg += u'</ul>'
        if any_paper:
            yield '{0[name]} <{0[email]}>'.format(person), best_title, greetings + msg
