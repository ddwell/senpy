import os
import logging

from senpy.extensions import Senpy
from senpy import models
from flask import Flask
from unittest import TestCase
from itertools import product


def check_dict(indic, template):
    return all(item in indic.items() for item in template.items())


def parse_resp(resp):
    return models.from_json(resp.data.decode('utf-8'))


class BlueprintsTest(TestCase):
    def setUp(self):
        self.app = Flask("test_extensions")
        self.app.debug = False
        self.client = self.app.test_client()
        self.senpy = Senpy()
        self.senpy.init_app(self.app)
        self.dir = os.path.join(os.path.dirname(__file__), "..")
        self.senpy.add_folder(self.dir)
        self.senpy.activate_plugin("Dummy", sync=True)
        self.senpy.activate_plugin("DummyRequired", sync=True)
        self.senpy.default_plugin = 'Dummy'

    def assertCode(self, resp, code):
        self.assertEqual(resp.status_code, code)

    def test_home(self):
        """
        Calling with no arguments should ask the user for more arguments
        """
        resp = self.client.get("/api/")
        self.assertCode(resp, 400)
        js = parse_resp(resp)
        logging.debug(js)
        assert js["status"] == 400
        atleast = {
            "status": 400,
            "message": "Missing or invalid parameters",
        }
        assert check_dict(js, atleast)

    def test_analysis(self):
        """
        The dummy plugin returns an empty response,\
        it should contain the context
        """
        resp = self.client.get("/api/?i=My aloha mohame")
        self.assertCode(resp, 200)
        js = parse_resp(resp)
        logging.debug("Got response: %s", js)
        assert "@context" in js
        assert "entries" in js

    def test_analysis_extra(self):
        """
        Extra params that have a default should
        """
        resp = self.client.get("/api/?i=My aloha mohame&algo=Dummy")
        self.assertCode(resp, 200)
        js = parse_resp(resp)
        logging.debug("Got response: %s", js)
        assert "@context" in js
        assert "entries" in js

    def test_analysis_extra_required(self):
        """
        Extra params that have a required argument that does not
        have a default should raise an error.
        """
        resp = self.client.get("/api/?i=My aloha mohame&algo=DummyRequired")
        self.assertCode(resp, 400)
        js = parse_resp(resp)
        logging.debug("Got response: %s", js)
        assert isinstance(js, models.Error)

    def test_error(self):
        """
        The dummy plugin returns an empty response,\
        it should contain the context
        """
        resp = self.client.get("/api/?i=My aloha mohame&algo=DOESNOTEXIST")
        self.assertCode(resp, 404)
        js = parse_resp(resp)
        logging.debug("Got response: %s", js)
        assert isinstance(js, models.Error)

    def test_list(self):
        """ List the plugins """
        resp = self.client.get("/api/plugins/")
        self.assertCode(resp, 200)
        js = parse_resp(resp)
        logging.debug(js)
        assert 'plugins' in js
        plugins = js['plugins']
        assert len(plugins) > 1
        assert list(p for p in plugins if p['name'] == "Dummy")
        assert "@context" in js

    def test_headers(self):
        for i, j in product(["/api/plugins/?nothing=", "/api/?i=test&"],
                            ["inHeaders"]):
            resp = self.client.get("%s" % (i))
            js = parse_resp(resp)
            assert "@context" in js
            resp = self.client.get("%s&%s=0" % (i, j))
            js = parse_resp(resp)
            assert "@context" in js
            resp = self.client.get("%s&%s=1" % (i, j))
            js = parse_resp(resp)
            assert "@context" not in js
            resp = self.client.get("%s&%s=true" % (i, j))
            js = parse_resp(resp)
            assert "@context" not in js

    def test_detail(self):
        """ Show only one plugin"""
        resp = self.client.get("/api/plugins/Dummy/")
        self.assertCode(resp, 200)
        js = parse_resp(resp)
        logging.debug(js)
        assert "@id" in js
        assert js["@id"] == "plugins/Dummy_0.1"

    def test_default(self):
        """ Show only one plugin"""
        resp = self.client.get("/api/plugins/default/")
        self.assertCode(resp, 200)
        js = parse_resp(resp)
        logging.debug(js)
        assert "@id" in js
        assert js["@id"] == "plugins/Dummy_0.1"

    def test_context(self):
        resp = self.client.get("/api/contexts/context.jsonld")
        self.assertCode(resp, 200)
        js = parse_resp(resp)
        assert "@context" in js
        assert check_dict(
            js["@context"],
            {"marl": "http://www.gsi.dit.upm.es/ontologies/marl/ns#"})

    def test_schema(self):
        resp = self.client.get("/api/schemas/definitions.json")
        self.assertCode(resp, 200)
        js = parse_resp(resp)
        assert "$schema" in js
