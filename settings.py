# -*- coding: utf-8 -*-

import os.path

from tornado.options import define

define("port", default=8080, help="run on the given port", type=int)
define("config", default=None, help="tornado config file")
define("debug", default=False, help="debug mode")

settings = {}

settings["debug"] = True
settings["cookie_secret"] = "Q8Xev2uFQ3SEkoHCd+EV6HTCeTQZokGGgqxnORuUx/M="
settings["login_url"] = "/login"
settings["static_path"] = os.path.join(os.path.dirname(__file__), "static")
settings["template_path"] = os.path.join(os.path.dirname(__file__), "templates")
settings["xsrf_cookies"] = False
settings["facebook_api_key"] = "426446497428837"
settings["facebook_secret"] = "7a811496573b875c107d3bafc1828cc2"
settings["fitbit_consumer_key"] = "5ba9a84658214216809634f88dd3b9ec"
settings["fitbit_consumer_secret"] = "f6e3ddeeb88c42aabcdf0ebc60fdfb0c"
settings["flickr_consumer_key"] = "59f4b933dc69a3079b7b33a8a53b26bf"
settings["flickr_consumer_secret"] = "cfda19efd6679c0b"
settings["foursquare_api_key"] = "MSJXJGSMPMWVEEZKGCF1YEHUIAZG5YW3U4U0CNRZJYJ5TPPC"
settings["foursquare_client_id"] = "MSJXJGSMPMWVEEZKGCF1YEHUIAZG5YW3U4U0CNRZJYJ5TPPC"
settings["foursquare_client_secret"] = "2CU20YV4WTEYKVQNKCXM51IMFDALG2RSLAHI5LGGMW0FSGBL"
settings["google_consumer_key"] = "anonymous"
settings["google_consumer_secret"] = "anonymous"
settings["khanacademy_consumer_key"] = "ypzzb7hyX2Q9mVHR"
settings["khanacademy_consumer_secret"] = "pfGvSc5adwCRCyE3"
settings["twitter_consumer_key"] = "OaqpkBvltogUUjmeCqVhVw"
settings["twitter_consumer_secret"] = "0f88f60eae0142b586340594249e5f67"
settings["withings_consumer_key"] = "5d5db6b4b09ce845b17f315116dcd660080c9ce9cfc987e3e79e04017bdc"
settings["withings_consumer_secret"] = "b22913cf4013ed3266e551f71b73ce3451e3f8950d884348dffd3b338b5b4f"
settings["zeo_consumer_key"] = "peter.darche"
settings["zeo_consumer_secret"] = "Aiy0EeXeRae9AebilaiK1t"
