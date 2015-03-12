#!/usr/bin/python

import unittest
from gluon.globals import Request, Session, Storage, Response
from gluon.tools import Auth
from gluon.contrib.test_helpers import form_postvars
from gluon import current

class FileController(unittest.TestCase):
        
    def __init__(self, p):
        global auth, session, request
        unittest.TestCase.__init__(self, p)
        
    def setUp(self):
        # Load the to-be-tested file
        execfile("applications/vidjil/controllers/file.py", globals())
        # set up default session/request/auth/...
        global response, session, request, auth
        session = Session()
        request = Request({})
        auth = Auth(globals(), db)
        auth.login_bare("test@vidjil.org", "1234")
        
        # rewrite info / error functions 
        # for some reasons we lost them between the testRunner and the testCase but we need them to avoid error so ...
        def f(a):
            pass
        log.info = f
        log.error = f
        log.debug = f
        
        # for defs
        current.db = db
        current.auth = auth
        
        
    def testAdd(self):      
        request.vars['id'] = fake_patient_id
        
        resp = add()
        self.assertTrue(resp.has_key('message'), "add() has returned an incomplete response")
        
        
    def testAddForm(self):      
        class emptyClass( object ):
            pass
        
        plop = emptyClass()
        setattr(plop, 'file',  open("../../doc/analysis-example.vidjil", 'rb'))
        setattr(plop, 'filename', 'plopapou')

        request.vars['sampling_date'] = "1992-02-02"
        request.vars['file_info'] = "plop"
        request.vars['pcr'] = "plop"
        request.vars['sequencer'] = "plop"
        request.vars['producer'] = "plop"
        request.vars['patient_id'] = fake_patient_id
        request.vars['filename'] = "plopapi"
        
        resp = add_form()
        self.assertNotEqual(resp.find('"redirect":"patient/info","message"'), -1, "add_form() failed")
    
    
    def testEdit(self):
        request.vars['patient_id'] = fake_patient_id
        
        resp = edit()
        self.assertTrue(resp.has_key('message'), "edit() has returned an incomplete response")
        
        
    def testEditForm(self):
        request.vars['id'] = fake_file_id
        request.vars['filename'] = "plopapi"
        
        request.vars['sampling_date'] = "1992-02-02"
        request.vars['file_info'] = "plop"
        request.vars['pcr'] = "plop"
        request.vars['sequencer'] = "plop"
        request.vars['producer']="plop"
        
        
        resp = edit_form()
        self.assertNotEqual(resp.find('"message":"plopapi: metadata saved"'), -1, "edit_form() failed")
       
       
    def testUpload(self):
        class emptyClass( object ):
            pass
        
        plop = emptyClass()
        setattr(plop, 'file',  open("../../doc/analysis-example.vidjil", 'rb'))
        setattr(plop, 'filename', 'plopapi')
    
        request.vars['file'] = plop
        request.vars['id'] = fake_file_id
    
        resp = upload()
        self.assertNotEqual(resp.find('"message":"upload finished: plopapi"'), -1, "edit_form() failed")
        
    def testConfirm(self):
        resp = confirm()
        self.assertTrue(resp.has_key('message'), "confirm() has returned an incomplete response")
    
    
    def testDelete(self):
        test_file_id = db.sequence_file.insert(sampling_date="1903-02-02",
                                    info="plop",
                                    pcr="plop",
                                    sequencer="plop",
                                    producer="plop",
                                    patient_id=fake_patient_id,
                                    filename="babibou",
                                    provider=user_id)
        
        self.assertTrue(db.sequence_file[test_file_id].filename == "babibou" , "file have been added")
        
        request.vars['id'] = test_file_id
        
        resp = delete()
        self.assertTrue(db.sequence_file[test_file_id] == None , "file have been deleted")
        
        
    def testSequencerList(self):
        
        resp = sequencer_list()
        self.assertNotEqual(resp.find('"sequencer":['), -1, "sequencer_list() doesn't return a valid json")
        
            
    def testPcrList(self):
        
        resp = pcr_list()
        self.assertNotEqual(resp.find('"pcr":['), -1, "pcr_list() doesn't return a valid json")
        
            
    def testProducerList(self):
        
        resp = producer_list()
        self.assertNotEqual(resp.find('"producer":['), -1, "producer_list() doesn't return a valid json")
            
            
            
            
            
            
            