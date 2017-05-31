# -*- coding: utf-8 -*-
import unittest
import logging
import sys
import os  # noqa: F401
import time
import hashlib
from time import sleep

from os import environ
try:
    from ConfigParser import ConfigParser  # py2
except:
    from configparser import ConfigParser  # py3

from pprint import pprint  # noqa: F401

from biokbase.workspace.client import Workspace as workspaceService
from ReadsAlignmentUtils.ReadsAlignmentUtilsImpl import ReadsAlignmentUtils
from ReadsAlignmentUtils.ReadsAlignmentUtilsServer import MethodContext
from ReadsAlignmentUtils.authclient import KBaseAuth as _KBaseAuth
from ReadsAlignmentUtils.core.sam_tools import SamTools



class ScriptUtilsTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.__LOGGER = logging.getLogger('SamTools_test')
        cls.__LOGGER.setLevel(logging.INFO)
        streamHandler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(filename)s - %(lineno)d - %(levelname)s - %(message)s")
        formatter.converter = time.gmtime
        streamHandler.setFormatter(formatter)
        cls.__LOGGER.addHandler(streamHandler)
        cls.__LOGGER.info("Logger was set")

        token = environ.get('KB_AUTH_TOKEN', None)
        config_file = environ.get('KB_DEPLOYMENT_CONFIG', None)
        cls.cfg = {}
        config = ConfigParser()
        config.read(config_file)
        for nameval in config.items('ReadsAlignmentUtils'):
            cls.cfg[nameval[0]] = nameval[1]
        # Getting username from Auth profile for token
        authServiceUrl = cls.cfg['auth-service-url']
        auth_client = _KBaseAuth(authServiceUrl)
        user_id = auth_client.get_user(token)
        # WARNING: don't call any logging methods on the context object,
        # it'll result in a NoneType error
        cls.ctx = MethodContext(None)
        cls.ctx.update({'token': token,
                        'user_id': user_id,
                        'provenance': [
                            {'service': 'ReadsAlignmentUtils',
                             'method': 'please_never_use_it_in_production',
                             'method_params': []
                             }],
                        'authenticated': 1})
        cls.wsURL = cls.cfg['workspace-url']
        cls.wsClient = workspaceService(cls.wsURL)
        cls.serviceImpl = ReadsAlignmentUtils(cls.cfg)
        cls.scratch = cls.cfg['scratch']
        cls.callback_url = os.environ['SDK_CALLBACK_URL']


    def test_valid_convert_sam_to_bam(self):
        opath = '/kb/module/work/'
        ofile = 'accepted_hits_valid_test_output.bam'

        if os.path.exists(opath+ofile):
            os.remove(opath+ofile)

        samt = SamTools(self.__class__.cfg, self.__class__.__LOGGER)

        result = samt.convert_sam_to_sorted_bam(ifile='accepted_hits.sam',
                                       ipath='data/samtools',
                                       ofile=ofile,
                                       opath=opath )
        sleep(4)

        self.assertEquals(result, 0)
        self.assertTrue(os.path.exists(opath+ofile))
        self.assertEquals(hashlib.md5(open(opath+ofile,'rb').read()).hexdigest(),
                          '96c59589b0ed7338ff27de1881cf40b3')


    def test_invalid_convert_sam_to_bam(self):
        #TODO need to add validation before writing this method
        pass


    def test_valid_convert_bam_to_sam(self):
        opath = '/kb/module/work/'
        ofile = 'accepted_hits_valid_test_output.sam'

        if os.path.exists(opath+ofile):
            os.remove(opath+ofile)

        samt = SamTools(self.__class__.cfg, self.__class__.__LOGGER)

        result = samt.convert_bam_to_sam(ifile='accepted_hits_sorted.bam',
                                       ipath='data/samtools',
                                       ofile=ofile,
                                       opath=opath )
        sleep(4)

        self.assertEquals(result, 0)
        self.assertTrue(os.path.exists(opath+ofile))
        self.assertEquals(hashlib.md5(open(opath+ofile,'rb').read()).hexdigest(),
                          'e8fd0e3d115bef90a520c831a0fbf478')


    def test_invalid_convert_bam_to_sam(self):
        #TODO need to add validation before writing this method
        pass


    def test_valid_create_bai_to_bam(self):
        opath = '/kb/module/work/'
        ofile = 'accepted_hits_valid_test_output.bai'

        if os.path.exists(opath+ofile):
            os.remove(opath+ofile)

        samt = SamTools(self.__class__.cfg, self.__class__.__LOGGER)

        result = samt.create_bai_from_bam(ifile='accepted_hits_sorted.bam',
                                       ipath='data/samtools',
                                       ofile=ofile,
                                       opath=opath )
        sleep(4)

        self.assertEquals(result, 0)
        self.assertTrue(os.path.exists(opath+ofile))
        self.assertEquals(hashlib.md5(open(opath+ofile,'rb').read()).hexdigest(),
                          '479a05f10c62e47c68501b7551d44593')


    def test_invalid_create_bai_to_bam(self):
        #TODO need to add validation before writing this method
        pass



