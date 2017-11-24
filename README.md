Converta - part1 - cornice api for csv to json conversion and reverse

Design features :

- cornice python web service framework
- authorization by api token
- csv2json conversion by uploading csv zipfile and streaming json output
- json2csv conversion by uploading json record file and streaming csv zipfile output
- test option included to confirm parsing success
- admin functions for user CRUD
- see hardHash.py for a persistent hash design, similar to python shelve
- fulled tested and proven using curl web client
- deployed at Heroku for demo and future business options
- as at 25 Nov 2017, api is hosted at https://converta.herokuapp.com

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
