# -*- coding: utf-8 -*-
from django.conf import settings
from django.test import client
from lettuce import before, after, world, step
from lettuce.django import django_url
import os
import selenium.webdriver.support.ui as ui


try:
    from lxml import html
    from selenium import webdriver
    from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
except:
    pass


@before.harvest
def setup_database(_foo):
    # make sure we have a fresh test database
    os.system("rm -f selenium.db")
    os.system("pwd")
    os.system("cp mvsim/main/fixtures/selenum_base.db selenium.db")


@before.all
def setup_browser():
    world.browser = None
    browser = getattr(settings, 'BROWSER', None)
    if browser is None:
        raise Exception('Please configure a browser in settings_test.py')
    elif browser == 'Firefox':
        ff_profile = FirefoxProfile()
        ff_profile.set_preference("webdriver_enable_native_events", False)
        world.browser = webdriver.Firefox(ff_profile)
    elif browser == 'Chrome':
        world.browser = webdriver.Chrome()
    elif browser == "Headless":
        world.browser = webdriver.PhantomJS()

    world.client = client.Client()
    world.using_selenium = False

    # Make the browser size at least 1024x768
    world.browser.execute_script("window.moveTo(0, 1); "
                                 "window.resizeTo(1024, 768);")

    # Wait implicitly for 2 seconds
    world.browser.implicitly_wait(5)

    # stash
    world.memory = {}


@after.all
def teardown_browser(total):
    world.browser.quit()


@step(u'Using selenium')
def using_selenium(step):
    world.using_selenium = True


@step(u'Finished using selenium')
def finished_selenium(step):
    world.using_selenium = False


@step(r'I access the url "(.*)"')
def access_url(step, url):
    if world.using_selenium:
        world.browser.get(django_url(url))
    else:
        response = world.client.get(django_url(url))
        world.dom = html.fromstring(response.content)


@step(u'I am not logged in')
def i_am_not_logged_in(step):
    if world.using_selenium:
        world.browser.get(django_url("/accounts/logout/"))
    else:
        world.client.logout()


@step(u'I log out')
def i_log_out(step):
    if world.using_selenium:
        world.browser.get(django_url("/accounts/logout/"))
    else:
        response = world.client.get(django_url("/accounts/logout/"),
                                    follow=True)
        world.response = response
        world.dom = html.fromstring(response.content)


@step(u'I log in')
def i_log_in(step):
    if not world.using_selenium:
        assert False, "click is not implemented in the django test client"
    else:
        elt = world.browser.find_element_by_id("local_login")
        elt.click()


@step(u'I am at the ([^"]*) page')
def i_am_at_the_name_page(step, name):
    if world.using_selenium:
        wait = ui.WebDriverWait(world.browser, 5)
        wait.until(lambda driver: world.browser.title.find(name) > -1)


@step(u'I type "([^"]*)" for ([^"]*)')
def i_type_value_for_field(step, value, field):
    if not world.using_selenium:
        assert False, "not implemented in the django test client"
    else:
        selector = "input[name=%s]" % field
        elt = world.browser.find_element_by_css_selector(selector)
        assert elt is not None, "Cannot locate input field named %s" % field
        elt.send_keys(value)


@step(u'I click the ([^"]*) button')
def i_click_the_value_button(step, value):
    if not world.using_selenium:
        assert False, "not implemented in the django test client"
    else:
        elt = find_button_by_value(value)
        assert elt, "Cannot locate button named %s" % value
        elt.click()


def find_button_by_value(value, parent=None):

    if not parent:
        parent = world.browser

    elts = parent.find_elements_by_css_selector("input[type=submit]")
    for e in elts:
        if e.get_attribute("value") == value:
            return e

    elts = parent.find_elements_by_css_selector("input[type=button]")
    for e in elts:
        if e.get_attribute("value") == value:
            return e

    elts = world.browser.find_elements_by_tag_name("button")
    for e in elts:
        if e.get_attribute("type") == "button" and e.text == value:
            return e

    # try the links too
    elts = parent.find_elements_by_tag_name("a")
    for e in elts:
        if e.text and e.text.strip() == value:
            return e

    return None

world.find_button_by_value = find_button_by_value
