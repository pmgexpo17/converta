#----------------------------------------------------------------------#
# userDb
#
# - manages api user CRUD
#
# pmg - 30/09/2017:
#----------------------------------------------------------------------# 
from email.utils import parseaddr
from datetime import date
from pyramid.httpexceptions import HTTPBadRequest
import binascii
import json
import os
import re
from converta.hardHash import HardHash

import logging
log = logging.getLogger(__name__)

class UserDb(HardHash):
	
	def afterCreate(self):
		self['groups'] = []		
		self['user:root'] = []
		self['user:admin'] = []		
		self['user:all'] = []
		self['member:all'] = []
		self['system:group'] = ['admin']
		self.keyLabel = None
		
	# -------------------------------------------------------------- #
	# add a new user account
	# TO DO : transactional method with rollback
	# ---------------------------------------------------------------#
	def addUser(self, userData):

		try:
			groupName, userEmail = HardHash.parse(userData,'group:email')
		except Exception as exc:
			raise HTTPBadRequest(str(exc))

		userKey = 'user:' + userEmail
		if self.hasUserAccount(userKey):
			reason = '%s user account already exists' % userEmail
			raise HTTPBadRequest(reason)

		account = self.makeUserAccount(userData)

		# 1 of 5 - add user to all users
		userId = self.addGroupToken('user:all')
		log.info('new user id : %s' % userId)

		# 2 of 5 - add userId by email index
		self[userKey] = userId
		
		# 3 of 5 - add user account to HardHash
		accountKey = 'user:%s' % userId
		self[accountKey] = account		
		
		# 4 of 5 - add group
		self.addGroup(groupName)

		# 5 of 5 - add user in group
		groupKey = 'user:' + groupName
		self.addGroupToken(groupKey, token=userId)

		self.userId = userId		
		self.accountKey = accountKey

		return account

	# -------------------------------------------------------------- #
	# add user account, with unique user id
	# ---------------------------------------------------------------#
	def makeUserAccount(self, userData):

		# userData is approved by validateUserData
		try:
			account = HardHash.parse(userData,'name:group:email',pmode={})
			umixin = HardHash.parse(userData,'umixin')
		except Exception as exc:
			raise HTTPBadRequest(str(exc))
		
		account['accessToken'] = None
		account['startDate'] = '{:%d%m%Y}'.format(date.today())
		account['isAdmin'] = False
		account['pkToken'] = None
		account['endDate'] = None
		
		if umixin:
			account = dict(account, **umixin)

		return account
		
	# -------------------------------------------------------------- #
	# add a new Member
	# ---------------------------------------------------------------#
	def addMember(self, memberData):

		self.userId = None
		self.accountKey = None
		self.userKey = None
		
		try:
			userEmail, memberType, mmixin = \
											HardHash.parse(memberData,'email:mtype:mmixin')
		except Exception as exc:
			raise HTTPBadRequest(str(exc))

		# self.userId is set internally by getAccessToken
		userKey = 'user:' + userEmail
		accessToken = self.getAccessToken(userKey)

		memberKey = '%s:%s' % (memberType, accessToken)
		if self.hasMemberAccount(memberKey):
			reason = '%s is already a member' % userEmail
			raise HTTPBadRequest(reason)

		# 1 of 4, make member account
		account = self.makeMemberAccount(memberType, mmixin)

		# 2 of 4 - add member to all members
		accessToken = self.addGroupToken('member:all')

		# 3 of 4 - add member account to HardHash
		self.memberKey = '%s:%s' % (memberType, accessToken)
		self[self.memberKey] = account
					
		# 4 of 4 - update accessToken in user account
		self.update(self.accountKey,{'accessToken': accessToken})
		
		logMsg = 'member added, accessToken : %s, userId : %s'
		log.info(logMsg % (accessToken, self.userId))
		
		return account

	# -------------------------------------------------------------- #
	# make a new member account
	# ---------------------------------------------------------------#
	def makeMemberAccount(self, memberType, mmixin=None):
				
		account = {'userId': self.userId}
		account['startDate'] = '{:%d%m%Y}'.format(date.today())
		account['endDate'] = None
		account['mtype'] = memberType
		account['productName'] = None

		if mmixin:
			account = dict(account, **mmixin)
		
		return account

	# -------------------------------------------------------------- #
	# unique id provider
	# ---------------------------------------------------------------#
	def makeToken(self, groupKey, size=11, tries=3):

		for _try in range(tries):
			userId = UserDb.createToken(size)
			if userId not in self[groupKey]:
				break
			userId = None
		if not userId:
			reason = 'exhausted %d tries to make unique user id' % tries
			raise HTTPBadRequest(reason)
			
		return userId

	# -------------------------------------------------------------- #
	# get a hash key
	# ---------------------------------------------------------------#
	def getHashKey(self, suffix, keyLabel=None):
		
		if keyLabel:
			return '%s:%s' % (keyLabel, suffix)
		return '%s:%s' % (self.keyLabel, suffix)
		
	# -------------------------------------------------------------- #
	# add a new group
	# ---------------------------------------------------------------#
	def addGroup(self, groupName):

		if groupName not in self['groups']:
			self.append('groups', groupName)

	# -------------------------------------------------------------- #
	# add token to group
	# protocol : if groupName = None then groupKey must be provided
	# ---------------------------------------------------------------#
	def addGroupToken(self, groupKey, token=None):

		if not token:
			token = self.makeToken(groupKey)
			
		try:
			self[groupKey]
		except KeyError:
			self[groupKey] = [token]
		else:
			self.append(groupKey, token)
		
		return token

	# -------------------------------------------------------------- #
	# delete a user
	# ---------------------------------------------------------------#
	def deleteUser(self, userKey, memberType):

		self.accountKey = None
		self.userKey = None		
		
		# 1 of 5, delete member record, if it exists
		try:
			self.deleteMember(userKey, memberType)
		except:
			pass

		if not self.hasUserAccount(userKey):
			raise HTTPBadRequest('%s user account not found' % userKey)

		account = self[self.accountKey]
				
		# 2 of 5, delete user in group
		groupKey = 'user:' + account['group']
		self.removeGroupToken(groupKey, self.userId)
		try:
			self.deleteGroup(groupKey, account['group'])
		except HTTPBadRequest:
			pass

		# 3 of 5, delete userId in all users
		self.removeGroupToken('user:all', self.userId)
		
		# 4 of 5, delete user account
		del(self[self.accountKey])			
		
		# 5 of 5, delete userId by email
		del(self[self.userKey])			
			
		return account

	# -------------------------------------------------------------- #
	# delete a member
	# ---------------------------------------------------------------#
	def deleteMember(self, userKey, memberType):

		memberAccount = self.getMemberAccount(userKey, memberType)
		
		# 1 of 3, update accessKey in user account
		self.update(self.accountKey, {'accessToken': None})

		# 2 of 3, remove member in all members
		self.removeGroupToken('member:all', self.accessToken)

		# 3 of 3, delete member account
		del(self[self.memberKey])
			
		return memberAccount

	# -------------------------------------------------------------- #
	# remove token in group
	# ---------------------------------------------------------------#
	def removeGroupToken(self, groupKey, token):

		try:	
			self.remove(groupKey, token)
		except:
			reason = '%s not found in group %s' % (token, groupKey)
			raise HTTPBadRequest(reason)

	# -------------------------------------------------------------- #
	# delete a non-system group
	# ---------------------------------------------------------------#
	def deleteGroup(self, groupKey, groupName):

		try:
			if self[groupKey]:
				raise HTTPBadRequest('group still has members')
		except KeyError:
			raise HTTPBadRequest('%s group does not exist' % groupKey)			

		del(self[groupKey])
		
		if groupName not in self['system:group']:
			self.remove('groups', groupName)
			
	# -------------------------------------------------------------- #
	# reset an existing user authorization token
	# ---------------------------------------------------------------#
	def resetAccessToken(self, userEmail, memberType):

		userKey = 'user:' + userEmail
		memberAccount = self.getMemberAccount(userKey, memberType)
	
		accessToken = self.makeToken('member:all')
		memberKey = '%s:%s' % (memberType, accessToken)
		self[memberKey] = memberAccount
		
		# self.accountKey is set by getMemberAccount
		self.update(self.accountKey,{'accessToken': accessToken})

		# self.memberKey is set by getMemberAccount
		del(self[self.memberKey])
			
		return {'email': userEmail,'accessToken': accessToken}

	# -------------------------------------------------------------- #
	# get users in group
	# ---------------------------------------------------------------#
	def getUsersInGroup(self, groupName):

		groupKey = 'user:' + groupName
		try:
			self[groupKey]
		except KeyError:
			reason = '%s group not found' % groupName
			raise HTTPBadRequest(reason)
			
		return {'users': self[groupKey],'group': groupName}

	# -------------------------------------------------------------- #
	# get user id
	# ---------------------------------------------------------------#
	def getUserId(self, userKey, byXRef=False):

		self.userKey = userKey
		try:
			if not byXRef:
				return self[self.userKey]
			return self[self.userKey]['userId']
		except KeyError:
			raise

	# -------------------------------------------------------------- #
	# has user account
	# ---------------------------------------------------------------#
	def hasUserAccount(self, userKey=None, byXRef=False):
	
		if userKey:
			try:
				self.userId = self.getUserId(userKey, byXRef)
			except KeyError:
				return False
		
		self.accountKey = 'user:%s' % self.userId
		try:
			self[self.accountKey]
		except KeyError:
			return False
			
		return True
	
	# -------------------------------------------------------------- #
	# get user account
	# ---------------------------------------------------------------#
	def getUserAccount(self, userKey=None, byXRef=False):
	
		if not self.hasUserAccount(userKey, byXRef):
			raise HTTPBadRequest('account not found : %s' % userKey)
			
		return self[self.accountKey]

	# -------------------------------------------------------------- #
	# get user token
	# ---------------------------------------------------------------#
	def getAccessToken(self, userKey=None, byXRef=False):

		account = self.getUserAccount(userKey, byXRef)
			
		return account['accessToken']

	# -------------------------------------------------------------- #
	# return accessToken is valid status 
	# ---------------------------------------------------------------#
	def accessTokenIsValid(self, memberType, accessToken):

		memberKey = '%s:%s' % (memberType, accessToken)
		if not self.hasMemberAccount(memberKey):
			return False
			
		self.userId = self[self.memberKey]['userId']
		
		if not self.hasUserAccount():
			return False

		return True

	# -------------------------------------------------------------- #
	# has member account
	# ---------------------------------------------------------------#
	def hasMemberAccount(self, memberKey=None):

		if memberKey:
			self.memberKey = memberKey
			
		try:
			self[self.memberKey]
		except KeyError:
			return False
			
		return True
		
	# -------------------------------------------------------------- #
	# get member account
	# ---------------------------------------------------------------#
	def getMemberAccount(self, userKey, memberType):

		accessToken = self.getAccessToken(userKey)
		
		self.memberKey = '%s:%s' % (memberType, accessToken)
		
		if not self.hasMemberAccount():
			raise HTTPBadRequest('member account not found for %s' % userKey)
		
		self.accessToken = accessToken
		
		return self[self.memberKey]

	# -------------------------------------------------------------- #
	# return pkToken in account pkToken list
	# ---------------------------------------------------------------#
	def hasPkAccessToken(self, userKey, pkToken):

		account = self.getUserAccount(userKey)
		
		if not account['pkToken']:
			return False
			
		return pkToken in account['pkToken']

	# -------------------------------------------------------------- #
	# return user in group status
	# ---------------------------------------------------------------#
	def userInGroup(self, userKey, groupName):
		
		try:
			userId = self.getUserId(userKey)
		except KeyError:
			reason = '%s user not found' % userKey
			raise HTTPBadRequest(reason)

		groupKey = 'user:%s' % groupName
		
		try:
			self[groupKey]
		except KeyError:
			reason = '%s group not found' % groupName
			raise HTTPBadRequest(reason)
			
		return userId in self[groupKey]

	# -------------------------------------------------------------- #
	# return admin in root
	# ---------------------------------------------------------------#
	def adminInRoot(self, userKey, byXRef=False):
		
		try:
			adminId = self.getUserId(userKey, byXRef)
		except KeyError:
			return False
			
		return adminId in self['user:root']

	# -------------------------------------------------------------- #
	# return user in admin group status
	# ---------------------------------------------------------------#
	def hasAdminRole(self, userKey, byXRef=False):
		
		try:
			userId = self.getUserId(userKey, byXRef)
		except KeyError:
			return False

		return userId in self['user:admin']

	# -------------------------------------------------------------- #
	# update user account
	# ---------------------------------------------------------------#
	def updateUserAccount(self, userData):

		try:
			userEmail, umixin = HardHash.parse(userData,'email:umixin')
		except Exception as exc:
			raise HTTPBadRequest(str(exc))
		
		userKey = 'user:' + userEmail
		self.getUserAccount(userKey)
		
		self.update(self.accountKey, umixin)
		
		return self[self.accountKey]

	# -------------------------------------------------------------- #
	# update member account
	# ---------------------------------------------------------------#
	def updateMemberAccount(self, memberData):
		
		try:
			userEmail, memberType, mmixin = \
											HardHash.parse(memberData,'email:mtype:mmixin')
		except Exception as exc:
			raise HTTPBadRequest(str(exc))

		userKey = 'user:' + userEmail
		self.getMemberAccount(userKey, memberType)
		
		self.update(self.memberKey, mmixin)
		
		return self[self.memberKey]

	# -------------------------------------------------------------- #
	# test user data
	# note : KeyErrors are caught by the calling method
	# ---------------------------------------------------------------#
	def validateNewUser(self, userData):
		
		try:
			userName, groupName, userEmail = \
													HardHash.parse(userData,'name:group:email')
		except ValueError:
			raise HTTPBadRequest('invalid user data : %s' % str(userData))
		reason1 = '''%s must be lowercase alphanumeric, length between 
                 3 and 12 chars'''
		reason2 = 'email address format is invalid'
		reason3 = 'user already exists in group'
			
		regex = re.compile("^([a-z]|[0-9]){3,12}$")
		if not regex.match(userName):
			reason = re.sub('\s+',' ',reason1 % 'username')
			raise HTTPBadRequest(reason)

		if not regex.match(groupName):
			reason = re.sub('\s+',' ',reason1 % 'groupname')
			raise HTTPBadRequest(reason)
			
		validEmail = parseaddr(userEmail)[1]
		if userEmail != validEmail or '@' not in userEmail:
			raise HTTPBadRequest(reason2)
			
	# -------------------------------------------------------------- #
	# create a token
	# ---------------------------------------------------------------#
	@staticmethod
	def createToken(size):
		return binascii.b2a_hex(os.urandom(size)).decode('utf-8')

class UserDbFactory(object):
		
	@staticmethod
	def make(repoName):
			
		factory = UserDbFactory()
		factory.makeDbSpace(repoName)				
		userDb = factory.createUserDb()
		factory.putMakeStatus()
			
		return userDb
		
	def makeDbSpace(self, repoName):
		
		basePath = os.path.dirname(os.path.abspath(__file__))
		jsonFile = '%s/make/converta.json' % basePath
		# open r+ had issues with seek(0) and rewrite
		with open(jsonFile) as jsonFh:
			makeObj = json.loads(jsonFh.readline())
		dbSpace = '%s/%s' % (basePath, repoName)
		if not os.path.exists(dbSpace):
			os.makedirs(dbSpace)
		elif makeObj['install'] != 'done':
			#print('clearing repo : %s' % repoName)
			os.system('rm -rf %s/*' % dbSpace)
		
		self.jsonFile = jsonFile
		self.makeObj = makeObj
		self.dbSpace = dbSpace			
				
	def createUserDb(self):
			
		_convertaDb = '%s/convertaDb.val' % self.dbSpace
		if self.makeObj['install'] != 'done':
			log.info('[make] installing convertaDb ...')
			userDb = UserDb.open(_convertaDb,'n')
			#print('making a new userDb')
			userDb.addUser(self.makeObj)
			userDb.addGroupToken('user:root', token=userDb.userId)
			memberData = \
						HardHash.parse(self.makeObj,'email:mtype:mmixin',pmode={})
			userDb.addMember(memberData)
			userDb.sync()
		else:
			log.info('[make] opening convertaDb ...')
			userDb = UserDb.open(_convertaDb,'c')

		return userDb

	def putMakeStatus(self):
			
		if self.makeObj['install'] == 'done':
			return
		with open(self.jsonFile,'w') as jsonFh:
			self.makeObj['install'] = 'done'
			jsonFh.write(json.dumps(self.makeObj))
