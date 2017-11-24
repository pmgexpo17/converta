Converta - part1 - cornice api for csv to json conversion and reverse

Design features :

  Cornice python web service framework
  Authorization by api token
  Csv2json conversion by uploading csv zipfile and streaming json output
  Json2csv conversion by uploading json record file and streaming csv zipfile output
  Test option included to confirm parsing success
  Admin functions for user CRUD
  See hardHash.py for a persistent hash design, similar to python shelve
  Fulled tested and proven using curl web client
  Deployed at Heroku for demo and future business options
  As at 25 Nov 2017, this api is hosted at https://converta.herokuapp.com

To try a demo :

1. request the access token for demo user guest01@globalmedia.com
2. download the sample csv zipfile, unittest_csv02.zip in sample/
3. open a terminal
4. run csv2json test command : 
  curl -H X-Api-Token:<guest01-token> -F srcfile=@/local/path/to/sample/unittest_csv02.zip
	              https://converta.herokuapp.com/api/v1/member/test/csv2json
		api will confirm csv content is valid
5. run csv2json command, redirecting :
  curl -H X-Api-Token:<guest01-token> -F srcfile=@/local/path/to/sample/unittest_csv02.zip
    https://converta.herokuapp.com/api/v1/member/test/csv2json > unittest_json02.txt
6. run json2csv test command :
  curl -H X-Api-Token:<guest01-token> -F srcfile=@/local/path/to/sample/unittest_json02.txt
	              https://converta.herokuapp.com/api/v1/member/test/json2csv
		api will confirm json content is valid
7. run json2csv command :
  curl -H X-Api-Token:<guest01-token> -F srcfile=@/local/path/to/sample/unittest_json02.txt
	  https://converta.herokuapp.com/api/v1/member/json2csv > unittest_csv02a.zip

Note : the csv and json format are application specific. A future version will
  be generic by interpreting a user provided json schema to define the table model
