import os
import binascii
import json
from json import JSONDecodeError
from converta.hardHash import HardHash
from converta.userDb import UserDb

from pyramid.httpexceptions import \
 HTTPUnauthorized, HTTPBadRequest, HTTPNotFound, HTTPServiceUnavailable

import logging
log = logging.getLogger(__name__)
	
# validToken
def validParms1(request, **kwargs):
	header = 'X-Api-Token'
	accessToken = request.headers.get(header)
	
	if accessToken is None:
		raise HTTPUnauthorized("Unauthorized")

	try:
		memberType = request.matchdict['memberType']
	except KeyError:
		raise HTTPNotFound("Not Found")
	else:
		if memberType not in ('member','admin'):
			raise HTTPNotFound("Not Found")
		
	if not request.accessTokenIsValid(memberType, accessToken):
		raise HTTPUnauthorized("Unauthorized")
	
# in this case, user has forgot their access token and
# validates by an encoded personal information question:answer key
def validUserPkToken(request, userEmail, **kwargs):
	header = 'X-Api-PK-Token'
	pkToken = request.headers.get(header)
	
	if pkToken is None:
		return False

	if not request.hasUserPkToken(userEmail, pkToken):
		raise HTTPUnauthorized("Unauthorized")

# get userDict by converting json post data
def getUserParms(request, keepL=None, **kwargs):

	try:
		userDict = json.loads(request.body.decode('utf-8'))
	except JSONDecodeError as exc:
		raise HTTPBadRequest('json decode error : ' + str(exc))
	
	if not keepL:
		return userDict
	
	return HardHash.parse(userDict,keepL,pmode=[])
		
# getAdminAccessToken
def getAdminAccessToken(request, **kwargs):

	header = 'X-Api-Token'
	accessToken = request.headers.get(header)
	
	if accessToken is None:
		return False

	userKey = 'admin:' + accessToken
	
	if not request.hasAdminRole(userKey,True):
		raise HTTPUnauthorized("Unauthorized")
		
	return accessToken

# validAdminParams1
# route:/api/v1/users/get
def validAdminParms1(request, **kwargs):

	getAdminAccessToken(request)

# validAdminParams2
# route:/api/v1/user/get|delete|patch
def validAdminParms2(request, **kwargs):

	adminKey = 'admin:' + getAdminAccessToken(request)

	userKey = 'user:' + getUserParms(request,'email')

	# only root user can peek at other administrator accounts	
	if not request.adminInRoot(adminKey,True) and \
																				request.hasAdminRole(userKey):
		raise HTTPUnauthorized("Unauthorized")
		
# validAdminParams3 - NEW requests	only
# route:/api/v1/user/new
def validAdminParms3(request, **kwargs):

	getAdminAccessToken(request)

	userDict = getUserParms(request)
	request.validateNewUser(userDict)
