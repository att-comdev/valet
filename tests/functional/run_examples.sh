 #run specific tests:
 sudo tox -epy27 --  '(TestAffinity|TestDiversity)'
 
 # isolate
 sudo tox -- --isolated
 
 
 
 
 
 # use  commands = ostestr --slowest '{posargs}' in file tox.ini
 # http://docs.openstack.org/developer/os-testr/ostestr.html#running-tests
 
 # run all tests until failure
 sudo tox -- --until-failure
 
 # unparallel running (serial)
 sudo tox -- --concurrency=1
 
 