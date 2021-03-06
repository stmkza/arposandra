import os
import sys
import configparser
import gettext
import logging
import json
from collections import namedtuple

from tornado.web import Application
from tornado import locale

from . import database
from . import dispatch
from . import pages
from . import card_page
from . import pageutils
from . import tlinject
from . import news
from . import card_tracking
from . import event_tracker
from . import dict_aggregator
import libcard2


def readonly_app_path(*p):
    return os.path.join(os.path.dirname(__file__), *p)


def create_runtime_info():
    vi_class = namedtuple("runtime_info_t", ("app_revision", "host_id", "python_version"))
    return vi_class(os.environ.get("AS_GIT_REVISION"), os.environ.get("AS_HOST_ID"), sys.version)


class DictionaryAccessProtocolImp(gettext.GNUTranslations):
    class Fallback(object):
        @classmethod
        def gettext(cls, k):
            return None

    def __init__(self, fp):
        super().__init__(fp)
        self.add_fallback(self.Fallback)

    def lookup_single_string(self, key):
        return self.gettext(key)


def static_strings():
    sd = {}
    catalog = readonly_app_path("gettext")
    for langcode in os.listdir(catalog):
        sd[langcode] = gettext.translation(
            "static", catalog, [langcode], DictionaryAccessProtocolImp
        )

    return sd


def find_astool_master_version(in_base):
    with open(os.path.join(in_base, "astool_store.json"), "r") as jsf:
        return json.load(jsf)["master_version"]


def create_dict_aggregator(master, language):
    choices = {}
    extra = os.environ.get("AS_EXTRA_DICTIONARIES")
    if extra:
        for tag in extra.split(";"):
            rgn_tag, lang_code, name = tag.split(":")
            region_root = os.path.join(os.environ.get("AS_DATA_ROOT", "."), rgn_tag)
            base = os.path.join(region_root, "masters", find_astool_master_version(region_root))
            logging.debug("Loading dictionary: %s", base)

            choices[lang_code] = dict_aggregator.Alternative(
                name, lang_code, libcard2.string_mgr.DictionaryAccess(base, lang_code)
            )

    fallback = libcard2.string_mgr.DictionaryAccess(master, language)
    return dict_aggregator.DictionaryAggregator(fallback, choices)


def application(master, language, debug):
    if os.environ.get("AS_TLINJECT_SECRET", ""):
        print("TLInject is enabled for this server.")

    locale.set_default_locale("en")
    locale.load_gettext_translations(readonly_app_path("gettext"), "tornado")
    strings = static_strings()
    db_coordinator = database.DatabaseCoordinator()

    application = Application(
        dispatch.ROUTES,
        db_coordinator=db_coordinator,
        master=libcard2.master.MasterData(master),
        string_access=create_dict_aggregator(master, language),
        image_server=os.environ.get("AS_IMAGE_SERVER"),
        tlinject_context=tlinject.TLInjectContext(db_coordinator),
        news_context=news.NewsDatabase(db_coordinator),
        card_tracking=card_tracking.CardTrackingDatabase(db_coordinator),
        event_tracking=event_tracker.EventTrackingDatabase(db_coordinator),
        template_path=readonly_app_path("webui"),
        runtime_info=create_runtime_info(),
        tlinject_secret=os.environ.get("AS_TLINJECT_SECRET", "").encode("utf8"),
        ui_methods=pageutils.UI_METHODS,
        static_path=readonly_app_path("static"),
        static_strings=strings,
        debug=debug,
        autoreload=debug,
    )
    return application
