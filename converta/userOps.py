from pyramid.events import NewRequest
from converta.hardHash import HardHashFactory
from converta.userDb import UserDb, UserDbFactory

import logging
log = logging.getLogger(__name__)

def includeme(config):

	try:
		# userDb is created at installation
		userDb = UserDbFactory.make('noSqlDb/users')
		HardHashFactory.hashFile = 'convertaDb'
		config.registry.settings['userDb'] = userDb
		config.registry.settings['sessionDb'] = HardHashFactory
	except Exception as exc:
		exc.message = 'failed to create or open database'
		raise
			
	def _getUserDb(request):
		
		return request.registry.settings['userDb']

	def _getSessionDb(request):
		
		return request.registry.settings['sessionDb']
		
	def _getUsersInGroup(request, groupName):
		
		return request.userDb.getUsersInGroup(groupName)

	def _getUserAccount(request, userKey, byXRef=False):

		return request.userDb.getUserAccount(userKey, byXRef)

	def _getMemberAccount(request, userKey, memberType):
		
		return request.userDb.getMemberAccount(userKey, memberType)

	def _hasPkAccessToken(request, userKey, pkToken):
		
		return request.userDb.hasPkAccessToken(userKey, pkToken)

	def _adminInRoot(request, userKey, byXRef=False):
		
		return request.userDb.adminInRoot(userKey, byXRef)

	def _userInGroup(request, userKey, groupName):
		
		return request.userDb.userInGroup(userKey, groupName)

	def _accessTokenIsValid(request, memberType, accessToken):
		
		return request.userDb.accessTokenIsValid(memberType, accessToken)

	def _hasAdminRole(request, userKey, byXRef=False):
		
		return request.userDb.hasAdminRole(userKey, byXRef)

	def _validateNewUser(request, userData):

		request.userDb.validateNewUser(userData)
		
	def _addUser(request, userData):
		
		request.syncEnd = True
		return request.userDb.addUser(userData)

	def _addMember(request, memberData):
		
		request.syncEnd = True
		return request.userDb.addMember(memberData)

	def _deleteUser(request, userKey, memberType):
		
		request.syncEnd = True
		return request.userDb.deleteUser(userKey, memberType)

	def _deleteMember(request, userEmail, memberType):
		
		request.syncEnd = True
		return request.userDb.deleteMember(userEmail, memberType)

	def _resetAccessToken(request, userEmail, memberType):
		
		request.syncEnd = True
		return request.userDb.resetAccessToken(userEmail, memberType)

	def _addGroup(request, groupName):
		
		request.syncEnd = True
		return request.userDb.addGroup(groupName)		

	def _deleteGroup(request, groupName, groupKey=None):
		
		request.syncEnd = True
		return request.userDb.deleteGroup(groupName, groupKey)

	def _updateUser(request, userData):
		
		request.syncEnd = True
		return request.userDb.updateUserAccount(userData)

	def _updateMember(request, memberData):
		
		request.syncEnd = True
		return request.userDb.updateMemberAccount(memberData)

	config.add_request_method(_getUserDb, 'userDb', property=True, reify=True)
	config.add_request_method(_getSessionDb, 'sessionDb', property=True, reify=True)
	config.add_request_method(_getUsersInGroup,'getUsersInGroup')
	config.add_request_method(_getUserAccount,'getUserAccount')
	config.add_request_method(_getMemberAccount,'getMemberAccount')
	config.add_request_method(_hasPkAccessToken,'hasPkAccessToken')
	config.add_request_method(_userInGroup,'userInGroup')
	config.add_request_method(_accessTokenIsValid,'accessTokenIsValid')
	config.add_request_method(_adminInRoot,'adminInRoot')
	config.add_request_method(_hasAdminRole,'hasAdminRole')
	config.add_request_method(_validateNewUser,'validateNewUser')
	config.add_request_method(_addUser,'addUser')	
	config.add_request_method(_addMember,'addMember')	
	config.add_request_method(_deleteUser,'deleteUser')
	config.add_request_method(_deleteMember,'deleteMember')
	config.add_request_method(_resetAccessToken,'resetAccessToken')
	config.add_request_method(_addGroup,'addGroup')
	config.add_request_method(_deleteGroup,'deleteGroup')
	config.add_request_method(_updateUser,'updateUser')
	config.add_request_method(_updateMember,'updateMember')

	# commit db changes, deleting redo space
	def _commit_user_db(request):

		try:
			if not hasattr(request,'syncEnd'):
				return
			request.userDb.sync()
			log.error('sync userDb done')
		except Exception as exc:
			log.error('failed to sync userDb : ' + str(exc))

	def _post_request(event):
			event.request.add_finished_callback(_commit_user_db)

	config.add_subscriber(_post_request, NewRequest)
    
