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
def validPkAccessToken(request, **kwargs):
	header = 'X-Api-PK-Token'
	pkToken = request.headers.get(header)
	
	if pkToken is None:
		return False

	userKey = 'user:' + getUserParms(request,'email')
	
	return request.hasPkAccessToken(userKey, pkToken)

# get userDict by converting json post data
def getUserParms(request, keepL=None, **kwargs):

	try:
		userDict = json.loads(request.body.decode('utf-8'))
	except JSONDecodeError as exc:
		raise HTTPBadRequest('json decode error : ' + str(exc))
	
	if not keepL:
		return userDict
	
	try:
		return HardHash.parse(userDict,keepL)
	except Exception as exc:
		raise HTTPBadRequest(str(exc))
		
# getAdminAccessToken
def getAdminAccessToken(request, **kwargs):

	header = 'X-Api-Token'
	accessToken = request.headers.get(header)
	
	if accessToken is None:
		raise HTTPUnauthorized("Unauthorized")

	userKey = 'admin:' + accessToken
	
	if not request.hasAdminRole(userKey,True):
		raise HTTPUnauthorized("Unauthorized")
		
	return accessToken

# validAdminParams1
# route:/api/v1/users/get
def validAdminParms1(request, **kwargs):

	getAdminAccessToken(request)

# validAdminParams2
# route:/api/v1/user/get
def validAdminParms2(request, **kwargs):

	try:
		adminKey = 'admin:' + getAdminAccessToken(request)
	except HTTPUnauthorized:
		if validPkAccessToken(request):
			return
		raise
		
	# only root user can peek at other administrator accounts	
	if not request.adminInRoot(adminKey,True) and \
																				request.hasAdminRole(userKey):
		raise HTTPUnauthorized("Unauthorized")

# validAdminParams3
# route:/api/v1/user/delete|patch
def validAdminParms3(request, **kwargs):

	adminKey = 'admin:' + getAdminAccessToken(request)

	userKey = 'user:' + getUserParms(request,'email')

	# only root user can peek at other administrator accounts	
	if not request.adminInRoot(adminKey,True) and \
																				request.hasAdminRole(userKey):
		raise HTTPUnauthorized("Unauthorized")
		
# validAdminParams4 - NEW requests	only
# route:/api/v1/user/new
def validAdminParms4(request, **kwargs):

	getAdminAccessToken(request)

	userDict = getUserParms(request)
	request.validateNewUser(userDict)
