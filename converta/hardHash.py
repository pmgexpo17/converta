import os
import json
import math
from collections.abc import MutableMapping
from collections import OrderedDict

#------------------------------------------------------------------#
# HardHash
#
# - similar to python shelve without dbm dependency
# - author : Peter McGill - Oct 2017
#------------------------------------------------------------------#
class HardHash(MutableMapping):

	def __init__(self):

		#----------------------------------------------------------------#
		# constructor parms -
		#----------------------------------------------------------------#		
		self.keyz = OrderedDict()
		self.redo = {'all':[]}
		self.delitem = False
		self.valuez = None

	#----------------------------------------------------------------#
	# MutableMapping methods for emulating a dict
	#----------------------------------------------------------------#		
	
	# iterate
	def __iter__(self):
		for k in self.keyz.keys():
			yield (k, self.__getitem__(k))

	# length
	def __len__(self):
		return len(self.keyz)

	# contains
	def __contains__(self, key):
		return key in self.keyz

	# get with default
	def get(self, key, default=None):
		if key in self.keyz:
			return self.__getitem__(key)
		return default
	
	# get
	def __getitem__(self, key):
		index = self.keyz[key].offset
		self.valuez.seek(index)
		return json.loads(self.valuez.readline())

	# set
	def __setitem__(self, key, value):
		self.isExtType = isinstance(value, (list,dict))
		_value = json.dumps(value)
		try:
			self.keyz[key]
		except KeyError:
			self.put(key,_value)
		else:
			self.replace(key,_value)

	# delete
	def __delitem__(self, key):
		_index = self.keyz[key]
		self.keep(_index)
		del self.keyz[key]
		self.delitem = True

	# enter scope
	def __enter__(self):
		return self

	# exit scope
	def __exit__(self, type, value, traceback):
		self.sync()

	#----------------------------------------------------------------#
	# hash storage methods
	#----------------------------------------------------------------#		

	# descendent method for app specific hash variable setup
	def afterCreate(self):
		pass
	
	# append value to self[key] which must be a list
	def append(self, key, value):
		
		_list = self.get(key)
		try:
			_list.append(value)
		except AttributeError:
			errmsg = 'list append method failed, subject must be a list'
			raise Exception(errmsg)
		self.__setitem__(key, _list)

	# close with keep keys option, which is really a dev debug method
	def close(self, keep=False):
		if not keep or self.keyz is None:
			self.valuez.close()
			return
		self.dbFile = os.path.splitext(os.path.abspath(self.valuez.name))[0]
		self.dumpKeys()
		self.valuez.close()

	# dump the db keys to hard storage
	def dumpKeys(self, keyFile=None):

		if not keyFile:
			keyFile = self.dbFile
		keyFile = '%s.key' % keyFile
		with open(keyFile,'w') as fh:
			for key, indexr in self.keyz.items():
				fh.write(json.dumps([key, indexr.__dict__]) + '\n')

	# find a size in the redo register
	def find(self, size):
		
		try:
			self.redo[size]
		except:			
			if not self.redo['all'] or size > self.redo['all'][-1]:
				raise Exception
			for resize in self.redo['all']:
				if size < resize:
					return resize
		return size

	# keep an index, adding it to redo register
	def keep(self, _indexr):

		try:
			self.redo[_indexr.size].append(_indexr.offset)
		except:
			self.redo[_indexr.size] = [_indexr.offset]
		if _indexr.size not in self.redo['all']:
				self.redo['all'].append(_indexr.size)
				self.redo['all'] = sorted(self.redo['all'])

	# load the db keys from hard storage
	def loadKeys(self, keyFile=None):

		if not keyFile:
			keyFile = self.dbFile
		keyFile = '%s.key' % keyFile
		with open(keyFile,'r') as fh:
			_keyz = OrderedDict()
			for item in fh:				
				key, indexr = json.loads(item)
				_keyz[key] = self.indexR()
				_keyz[key].__dict__ = indexr
			self.keyz = _keyz
		
	# put the value in hard storage. first attempt to recycle a cached
	# file index if the size is available, else append the value
	def put(self, key, value):

		#print('put, %s : %s' % (key, value))
		upsize = size = math.ceil(len(value) / 16)
		# increase initial size for list/dict for extend capacity
		if self.isExtType:
			#print('upsizing list/dict to extend capacity')
			# decrease upsize factor for existing large size
			_upsize = size * 2 if size < 4 else math.ceil(size * 1.5)
			# ensure size at least = 4
			upsize = _upsize if _upsize >= 4 else 4
		try:
			# resize may be greater than required size
			resize = self.find(upsize)
		except:
			msg = 'no recycle option found for size : %d, so append to the file'
			#print(msg % upsize)
			self.valuez.seek(0, 2)
			self.keyz[key] = self.indexR()
			self.keyz[key].offset = self.valuez.tell()
			self.keyz[key].size = upsize
			# no recycle option found, so append to the file
			# use record len = 17 to handle newlines in potential redo action

		else:
			# recycle option found, check if this is a new record
			#print('recycle option found for size : %s, key : %s' % (upsize, key))
			try:
				self.keyz[key]
			except KeyError:
				self.keyz[key] = self.indexR()
								
			self.keyz[key].size = upsize
			_offset = self.recycle(upsize, resize)
			self.valuez.seek(_offset)
			self.keyz[key].offset = _offset
		finally:
			#print('finally put the record, %s : %s' % (key, value))
			record = value.ljust(upsize * 17,' ')
			record = record[:-1] + '\n'
			self.valuez.write(record)

	# exclusive sync operation that appends the next hash value to a
	# new temporary hard storage
	def putRaw(self, key, fh):

		offset = self.keyz[key].offset
		self.valuez.seek(offset)
		value = self.valuez.readline().rstrip()
		
		isExtType = isinstance(value, (list,dict))
		upsize = size = math.ceil(len(value) / 16)
		# increase initial size for list/dict for extend capacity
		if isExtType:
		# decrease upsize factor for existing large size
			_upsize = size * 2 if size < 4 else math.ceil(size * 1.5)
			# ensure size at least = 4
			upsize = _upsize if _upsize >= 4 else 4
		fh.seek(0, 2)
		# Its OK to update an existing key value while dict iterating
		self.keyz[key].offset = fh.tell()
		self.keyz[key].size = upsize
		record = value.ljust(upsize * 17,' ')
		record = record[:-1] + '\n'
		fh.write(record)
		
	# handle second hand record redemption, recaching a remainder segment
	# if the redo record is downsized
	def recycle(self, size, resize):

		try:
			# test if redo[size] exists 
			self.redo[size]
		except:
			# size must be reduced from existing resize
			msg = 'size[%d] must be reduced from existing resize[%d]'
			#print(msg % (size, resize))
			offset = self.redo[resize].pop(0)
			# remove the resize list if empty
			if not self.redo[resize]:
				del(self.redo[resize])
				if resize in self.redo['all']:
					self.redo['all'].remove(resize)
			# add the downsized slot to the related redo list
			downsize = resize - size
			#print('add the downsized[%d] slot to the redo list' % downsize)
			_offset = offset + (size * 17)
			try:
				self.redo[downsize].append(_offset)
			except:
				self.redo[downsize] = [_offset]
			# reset the all size list
			if downsize not in self.redo['all']:
				self.redo['all'].append(downsize)
				self.redo['all'] = sorted(self.redo['all'])
		else:
			# size exists in redo
			#print('recycled size[%d] is available in redo list' % size)
			offset = self.redo[size].pop(0)
			if not self.redo[size]:
				del(self.redo[size])
				if size in self.redo['all']:
					self.redo['all'].remove(size)
				
		return offset
			
	# replace an existing hash value. if the current size doesn't fit then
	# keep the current index for potential redo, and put the value in a
	# recycled or new index
	def replace(self, key, value):
		
		#print('replace, %s : %s' % (key, value))
		_index = self.keyz[key]
		self.valuez.seek(_index.offset)
		resize = math.ceil(len(value) / 16)
		#print('replace : %d, %d, %d' % (_index.offset, _index.size, resize))
		if resize <= _index.size:
			#print('replace fits in current record')
			# most convenient when resize fits inside current slot
			# msg = 'replacement length fits inside current slot : %s, for key : %s'
			record = value.ljust(_index.size * 17,' ')
			record = record[:-1] + '\n'
			self.valuez.write(record)
			return
		#print('replace needs new record')
		# clean the current record for potential recycling
		record = ' ' * (_index.size * 17)
		record = record[:-1] + '\n'
		self.valuez.write(record)
		# keep the record for recycling by adding to the redo register
		self.keep(_index)
		self.put(key, value)

	# remove value from self[key] which must be a list
	def remove(self, key, value):
		
		_list = self.get(key)
		try:
			_list.remove(value)
		except AttributeError:
			errmsg = 'list remove method failed, subject must be a list'
			raise Exception(errmsg)
		self.__setitem__(key, _list)

	# sync the hard hash, both key and value, purging the redo space
	def sync(self):
		
		filePath = os.path.abspath(self.valuez.name)
		basePath = os.path.dirname(filePath)
		baseName = os.path.splitext(os.path.basename(filePath))[0]
		
		os.chdir(basePath)
		# only rewrite the val file if redo register has items
		# TO DO: review persistance method, atm sync required after every
		#        write operation, needs to be transactional
		#if self.redo['all'] or self.delitem:
		valFile = '%s/.%s.val' % (basePath, baseName)
		# avoid keyz dict copy by generator
		getKey = (key for key in self.keyz)
		with open(valFile,'w') as fh:
			for key in getKey:
				value = self.putRaw(key, fh)
				
		self.valuez.close()
		os.system('mv .{0}.val {0}.val'.format(baseName))
		valFile = '%s/%s.val' % (basePath, baseName)
		self.valuez = open(valFile, 'r+')
		self.redo = {'all':[]}
		self.delitem = False
			
		keyFile = '%s/.%s' % (basePath, baseName)
		self.dumpKeys(keyFile)
		os.system('mv .{0}.key {0}.key'.format(baseName))

	
	# update self[key] by merging the value. both self[key] and value must 
	# be a dict
	def update(self, key, value):

		_dict = self.get(key)
		try:
			if isinstance(value, str):			
				# in this case, remove by key, where key = value
				del(_dict[value])
			else:
				_dict = dict(_dict, **value)
		except TypeError:
			errmsg = 'dict update failed, update item must be a dict'
			raise Exception(errmsg)
		except ValueError:
			errmsg = 'dict update failed, subject must be a dict'
			raise Exception(errmsg)
		self.__setitem__(key, _dict)
		
	# indexR - index record
	class indexR(object):
		
		def __init__(self):
			self.offset = 0
			self.size = 1
			
	# open a HardHash connection
	@classmethod
	def open(cls, dbFile, flag):
		
		db = cls()
		_flag = flag
		if flag == 'n':
			_flag = 'w+'
		elif flag in ['c','w']:
			_flag = 'r+'
		
		try:
			db.valuez = open(dbFile, _flag)
			db.dbFile = os.path.splitext(os.path.abspath(db.valuez.name))[0]
			# if not a new instance, then load the keys
			if _flag != 'w+':
				db.loadKeys()			
		except FileNotFoundError as exc:
			# when flag = r+ is wrong, create a new instance
			flag = 'n'
			db.valuez = open(dbFile, 'w+')
			
		# run app specific hash variable setup
		if flag == 'n':
			db.afterCreate()
		return db

	@staticmethod
	def parse(_dict, skeep, pmode=[]):
		
		if skeep:
			keep = skeep.split(':')
			try:
				if isinstance(pmode, dict):
					return dict((key,_dict[key]) for key in keep)
				if isinstance(pmode, list):
					if len(keep) == 1:
						return _dict[keep.pop()]
					return list(_dict[key] for key in keep)
			except KeyError:
				raise Exception('key not found in source dict')
			except ValueError:
				raise Exception('data type error')
				
		return None

#----------------------------------------------------------------#
# HardHashFactory
#
# - convenience HardHash instance factory
# - this is a demo class which recommends the factory style for
# - application specific instance creation
#
# - fileNameHH: class variable, HardHash instance filename 
#----------------------------------------------------------------#		
class HardHashFactory(object):
	hashFile = None
	
	#----------------------------------------------------------------#
	# make -
	# - repoPath: absolute filesystem location of HardHash filename
	# - makeFlag: same as python shelve
	# -- persistance depends on the application type. is your hash
	# -- just a throw away convenience resource or is it permanent
	#----------------------------------------------------------------#				
	@staticmethod
	def make(repoPath, hashFile=None, makeFlag='c'):
		
		fileName = hashFile if hashFile else HardHashFactory.hashFile
		filePath = '%s/%s.val' % (repoPath, fileName)
		return HardHash.open(filePath, makeFlag)
		
