from CTFd import create_app
from CTFd.config import TestingConfig
from CTFd.models import *
from CTFd.cache import cache
from sqlalchemy_utils import database_exists, create_database, drop_database
from sqlalchemy.engine.url import make_url
from collections import namedtuple
import datetime
import six
import gc

if six.PY2:
    text_type = unicode
    binary_type = str
else:
    text_type = str
    binary_type = bytes


FakeRequest = namedtuple('FakeRequest', ['form'])


def create_ctfd(ctf_name="CTFd", name="admin", email="admin@ctfd.io", password="password", user_mode="users", setup=True, enable_plugins=False):
    if enable_plugins:
        TestingConfig.SAFE_MODE = False

    app = create_app(TestingConfig)

    if setup:
        app = setup_ctfd(app, ctf_name, name, email, password, user_mode)
    return app


def setup_ctfd(app, ctf_name="CTFd", name="admin", email="admin@ctfd.io", password="password", user_mode="users"):
    with app.app_context():
        with app.test_client() as client:
            r = client.get('/setup')  # Populate session with nonce
            with client.session_transaction() as sess:
                data = {
                    "ctf_name": ctf_name,
                    "name": name,
                    "email": email,
                    "password": password,
                    "user_mode": user_mode,
                    "nonce": sess.get('nonce')
                }
            client.post('/setup', data=data)
    return app


def destroy_ctfd(app):
    with app.app_context():
        gc.collect()  # Garbage collect (necessary in the case of dataset freezes to clean database connections)
        cache.clear()
        drop_database(app.config['SQLALCHEMY_DATABASE_URI'])


def register_user(app, name="user", email="user@ctfd.io", password="password", raise_for_error=True):
    with app.app_context():
        with app.test_client() as client:
            r = client.get('/register')
            with client.session_transaction() as sess:
                data = {
                    "name": name,
                    "email": email,
                    "password": password,
                    "nonce": sess.get('nonce')
                }
            client.post('/register', data=data)
            if raise_for_error:
                with client.session_transaction() as sess:
                    assert sess['id']
                    assert sess['name'] == name
                    assert sess['type']
                    assert sess['email']
                    assert sess['nonce']


def register_team(app, name="team", password="password"):
    with app.app_context():
        with app.test_client() as client:
            r = client.get('/team')
            with client.session_transaction() as sess:
                data = {
                    "name": name,
                    "password": password,
                    "nonce": sess.get('nonce')
                }
            client.post('/teams/new', data=data)


def login_as_user(app, name="user", password="password", raise_for_error=True):
    with app.app_context():
        with app.test_client() as client:
            r = client.get('/login')
            with client.session_transaction() as sess:
                data = {
                    "name": name,
                    "password": password,
                    "nonce": sess.get('nonce')
                }
            client.post('/login', data=data)
            if raise_for_error:
                with client.session_transaction() as sess:
                    assert sess['id']
                    assert sess['name']
                    assert sess['type']
                    assert sess['email']
                    assert sess['nonce']
            return client


def get_scores(user):
    r = user.get('/api/v1/scoreboard')
    scores = r.get_json()
    return scores['data']


def gen_challenge(db, name='chal_name', description='chal_description', value=100, category='chal_category', type='standard', state='visible', **kwargs):
    chal = Challenges(name=name, description=description, value=value, category=category, type=type, state=state, **kwargs)
    db.session.add(chal)
    db.session.commit()
    return chal


def gen_award(db, user_id, team_id=None, name="award_name", value=100):
    award = Awards(user_id=user_id, team_id=team_id, name=name, value=value)
    award.date = datetime.datetime.utcnow()
    db.session.add(award)
    db.session.commit()
    return award


def gen_tag(db, challenge_id, value='tag_tag', **kwargs):
    tag = Tags(challenge_id=challenge_id, value=value, **kwargs)
    db.session.add(tag)
    db.session.commit()
    return tag


def gen_file(db, location, challenge_id=None, page_id=None):
    if challenge_id:
        f = ChallengeFiles(challenge_id=challenge_id, location=location)
    elif page_id:
        f = PageFiles(page_id=page_id, location=location)
    else:
        f = Files(location=location)
    db.session.add(f)
    db.session.commit()
    return f


def gen_flag(db, challenge_id, content='flag', type='static', data=None, **kwargs):
    flag = Flags(challenge_id=challenge_id, content=content, type=type, **kwargs)
    if data:
        flag.data = data
    db.session.add(flag)
    db.session.commit()
    return flag


def gen_user(db, name='user_name', email='user@ctfd.io', password='password', **kwargs):
    user = Users(name=name, email=email, password=password, **kwargs)
    db.session.add(user)
    db.session.commit()
    return user


def gen_team(db, name='team_name', email='team@ctfd.io', password='password', **kwargs):
    team = Teams(name=name, email=email, password=password, **kwargs)
    db.session.add(team)
    db.session.commit()
    return team


def gen_hint(db, challenge_id, content="This is a hint", cost=0, type="standard", **kwargs):
    hint = Hints(challenge_id=challenge_id, content=content, cost=cost, type=type, **kwargs)
    db.session.add(hint)
    db.session.commit()
    return hint


def gen_unlock(db, user_id, team_id, target, type):
    unlock = Unlocks(
        user_id=user_id,
        team_id=team_id,
        target=target,
        type=type
    )
    db.session.add(unlock)
    db.session.commit()
    return unlock


def gen_solve(db, user_id, team_id=None, challenge_id=None, ip='127.0.0.1', provided='rightkey', **kwargs):
    solve = Solves(user_id=user_id, team_id=team_id, challenge_id=challenge_id, ip=ip, provided=provided, **kwargs)
    solve.date = datetime.datetime.utcnow()
    db.session.add(solve)
    db.session.commit()
    return solve


def gen_fail(db, user_id, team_id=None, challenge_id=None, ip='127.0.0.1', provided='wrongkey', **kwargs):
    fail = Fails(user_id=user_id, team_id=team_id, challenge_id=challenge_id, ip=ip, provided=provided, **kwargs)
    fail.date = datetime.datetime.utcnow()
    db.session.add(fail)
    db.session.commit()
    return fail


def gen_tracking(db, user_id=None, ip='127.0.0.1', **kwargs):
    tracking = Tracking(ip=ip, user_id=user_id, **kwargs)
    db.session.add(tracking)
    db.session.commit()
    return tracking


def gen_page(db, title, route, content, draft=False, auth_required=False, **kwargs):
    page = Pages(title=title, route=route, content=content, draft=draft, auth_required=auth_required, **kwargs)
    db.session.add(page)
    db.session.commit()
    return page


def gen_notification(db, title='title', content='content'):
    notif = Notifications(title=title, content=content)
    db.session.add(notif)
    db.session.commit()
