""" Cornice services.
"""
from cornice import Service
from pyramid.view import view_config, notfound_view_config
from pyramid.request import Request
from pyramid.httpexceptions import \
  HTTPNotFound, HTTPException, HTTPBadRequest, HTTPServiceUnavailable
from pyramid.response import FileResponse, FileIter
from converta.validators import validParms1, validAdminParms1, \
  validAdminParms2, validAdminParms3, validAdminParms4
from converta.csv2Json.csv2Json import Csv2Json
from converta.json2Csv.json2Csv import Json2Csv
from converta.hardHash import HardHash
from json import JSONDecodeError
import os
import json

import logging
log = logging.getLogger(__name__)

@notfound_view_config()
def notfound(request):
	request.response.status_int = 404
	return {'status': 'error', 'reason': 'Not Found'}

@view_config(context=HTTPException)
def exception_view(context, request):
	
	# set the response status code
	request.response.status_int = context.code
	log.info('request matched route : ' + request.matched_route.name)
	log.info('request method : ' + request.method)
	log.info('request current route path : ' + request.current_route_path())
	return {'status': 'error', 'route': request.matched_route.name, 
          'reason': context.detail}

# admin only service - get all users list
users = Service(name='users', 
                path='/api/v1/users/get/{groupName}', 
                description="All users view")

@users.get(validators=validAdminParms1)
def get_users(request):
	"""Returns a list of all users."""
	
	groupName = request.matchdict['groupName']
	return request.getUsersInGroup(groupName)

# admin only service - get user 
getUser = Service(name='getUser', 
               path='/api/v1/user/get',
               description="User maintenance")
	
@getUser.post(validators=validAdminParms2)
def get_user(request):
	"""Get the user token."""
	
	try:
		userDict = json.loads(request.body.decode('utf-8'))
	except JSONDecodeError as exc:
		raise HTTPBadRequest('json decode error : ' + str(exc))

	try:
		userKey = 'user:' + HardHash.parse(userDict,'email')
		response = request.getUserAccount(userKey)
	except Exception as exc:
		raise HTTPBadRequest(str(exc))

	return {'status': 'success','response': response}

# admin only service - delete user
deleteUser = Service(name='deleteUser', 
               path='/api/v1/user/delete',
               description="User maintenance")

@deleteUser.post(validators=validAdminParms3)
def delete_user(request):
	"""delete the user."""

	try:
		userDict = json.loads(request.body.decode('utf-8'))
	except JSONDecodeError as exc:
		raise HTTPBadRequest('json decode error : ' + str(exc))

	try:
		userEmail, memberType = HardHash.parse(userDict,'email:mtype')
		userKey = 'user:' + userEmail	
		response = request.deleteUser(userKey, memberType)
	except Exception as exc:
		raise HTTPBadRequest(str(exc))

	return {'status': 'success','response': response}

# admin only service - patch user
patchUser = Service(name='patchUser',
               path='/api/v1/user/patch',
               description="User maintenance")

@patchUser.post(validators=validAdminParms3)
def patch_user(request):
	"""reset the users access token"""
	
	try:
		userDict = json.loads(request.body.decode('utf-8'))
	except JSONDecodeError as exc:
		raise HTTPBadRequest('json decode error : ' + str(exc))

	try:
		response = request.updateUser(userDict)
	except Exception as exc:
		raise HTTPBadRequest(str(exc))

	return {'status': 'success','response': response}

# admin only service - add new user
newUser = Service(name='newUser', 
               path='/api/v1/user/new',
               description="User maintenance")

@newUser.post(validators=validAdminParms4)
def new_user(request):
	"""Add a new user."""
	
	try:
		userDict = json.loads(request.body.decode('utf-8'))
	except JSONDecodeError as exc:
		raise HTTPBadRequest('json decode error : ' + str(exc))

	try:
		response = request.addUser(userDict)
	except Exception as exc:
		raise HTTPBadRequest(str(exc))

	return {'status': 'success','response': response}

# admin only service - get member
getMember = Service(name='getMember', 
               path='/api/v1/member/get',
               description="Member maintenance")

@getMember.post(validators=validAdminParms3)
def get_member(request):
	"""get member account."""
	
	try:
		userDict = json.loads(request.body.decode('utf-8'))
	except JSONDecodeError as exc:
		raise HTTPBadRequest('json decode error : ' + str(exc))

	try:
		userEmail, memberType = HardHash.parse(userDict,'email:mtype')	
		userKey = 'user:' + userEmail
		response = request.getMemberAccount(userKey, memberType)
	except Exception as exc:
		raise HTTPBadRequest(str(exc))

	return {'status': 'success','response': response}
	
# admin only service - delete member
deleteMember = Service(name='deleteMember', 
                   path='/api/v1/member/delete',
                   description="Member maintenance")

@deleteMember.post(validators=validAdminParms3)
def delete_member(request):
	"""delete a member."""
	
	try:
		userDict = json.loads(request.body.decode('utf-8'))
	except JSONDecodeError as exc:
		raise HTTPBadRequest('json decode error : ' + str(exc))

	try:
		userEmail, memberType = HardHash.parse(userDict,'email:mtype')
		userKey = 'user:' + userEmail          
		response = request.deleteMember(userKey, memberType)
	except Exception as exc:
		raise HTTPBadRequest(str(exc))

	return {'status': 'success','response': response}

# admin only service - patch member
patchMember = Service(name='patchMember',
               path='/api/v1/member/patch',
               description="Member maintenance")

@patchMember.post(validators=validAdminParms3)
def patch_member(request):
	"""reset the users access token"""
	
	try:
		userDict = json.loads(request.body.decode('utf-8'))
	except JSONDecodeError as exc:
		raise HTTPBadRequest('json decode error : ' + str(exc))

	try:
		response = request.updateMember(userDict)
	except Exception as exc:
		raise HTTPBadRequest(str(exc))

	return {'status': 'success','response': response}

# admin only service - add new member
newMember = Service(name='newMember', 
               path='/api/v1/member/new',
               description="Member maintenance")
	
@newMember.post(validators=validAdminParms1)
def new_member(request):
	"""add a new member."""
	
	try:
		userDict = json.loads(request.body.decode('utf-8'))
	except JSONDecodeError as exc:
		raise HTTPBadRequest('json decode error : ' + str(exc))

	try:
		response = request.addMember(userDict)
	except Exception as exc:
		raise HTTPBadRequest(str(exc))

	return {'status': 'success','response': response}

# apiInfo for client users
apiInfoMember = Service(name='apiInfoMember', 
												path='/api/v1/{memberType}/list', 
												description="Api service listing")

@apiInfoMember.get(validators=validParms1)
def get_apiinfo_member(request):
	"""Get user api information"""

	memberType = request.matchdict['memberType']
	
	if memberType not in ('member','admin'):
		HTTPBadRequest('member type not recognised')
	
	basePath = os.path.dirname(__file__)

	return FileResponse('%s/static/%sApiList.json' % (basePath, memberType))

# csv2json
csv2json = Service(name='csv2json', 
										path='/api/v1/{memberType}/csv2json', 
										description="Transform format1 to format2")

@csv2json.post(validators=validParms1)
def run_csv2json(request):

	log.debug('service : csv2json')

	try:
		jsonWriter = Csv2Json(request)
		jsonWriter.parse(request)
		jsonFilePath = jsonWriter.convert(request)
	except Exception as exc:
		raise HTTPBadRequest({'status':'error','reason':'%s' % str(exc)})
	finally:
		jsonWriter.close()

	return FileResponse(jsonFilePath)

# csv2jsonTest
csv2jsonTest = Service(name='csv2jsonTest', 
											path='/api/v1/{memberType}/test/csv2json', 
											description="Test transform format1 to format2")

@csv2jsonTest.post(validators=validParms1)
def test_csv2json(request):

	log.debug('service : csv2jsonTest')

	try:
		jsonWriter = Csv2Json(request)
		jsonWriter.parse(request)
	except Exception as exc:
		raise HTTPBadRequest({'status':'error','reason':'%s' % str(exc)})
	finally:
		jsonWriter.close()

	return {'status':'success'}

# json2csv
json2csv = Service(name='json2csv', 
										path='/api/v1/{memberType}/json2csv', 
										description="Transform format1 to format2")

@json2csv.post(validators=validParms1)
def run_json2csv(request):

	log.debug('service : json2csv')
	response = request.response
	
	try:
		csvWriter = Json2Csv(request)
		csvWriter.parse(request)
		csvWriter.convert(request)
	except Exception as exc:
		try:
			log.error('@run_json2csv:1, ' + str(exc))
			# zipfile will contain only a json error report txt file
			response.status_int = 400
			zfh = csvWriter.get400ErrZipFile(request, str(exc))
		except Exception as exc:
			log.error('@run_json2csv:2\n')
			raise500Error(request, str(exc))
		finally:
			csvWriter.close()
	else:
		try:
			zfh = csvWriter.getCsvZipFile()
		except Exception as exc:
			raise500Error(request, str(exc))
		finally:
			csvWriter.close()
	finally:
		csvWriter.close()
		
	# rewind zipfile back to start of the file
	zfh.seek(0)

	# let the factory response set the content_length
	# because a length compare mismatch will cause an exception
	response.content_type = 'application/zip'
	response.app_iter = FileIter(zfh)
	return response

# json2csvTest
json2csvTest = Service(name='json2csvTest', 
											path='/api/v1/{memberType}/test/json2csv', 
											description="Test transform format1 to format2")

@json2csvTest.post(validators=validParms1)
def test_json2csv(request):

	log.debug('service : json2csvTest')

	try:
		csvWriter = Json2Csv(request)
		csvWriter.parse(request)
	except Exception as exc:
		raise HTTPBadRequest({'status':'error','reason':str(exc)})
	else:
		if csvWriter.hasJsonDecodeErrors(request=request):
			return csvWriter.get400ErrJsonFile()
	finally:
		csvWriter.close()	

	return {'status':'success'}

#def postLogMsg(place, errmsg, reason):
	
def raise500Error(request, reason):

	outputDir = request.getWorkSpace('outputCsv')
		
	zipFilePath = '%s/json2csv.zip' % outputDir
		
	errmsg = 'failed to create zipfile : %s\n reason : %s' 
	errmsg = errmsg %	(zipFilePath, reason)
	log.error(errmsg)
	raise HTTPServiceUnavailable({'status':'error', 
																'reason': 'failed to create zipfile'})

	
