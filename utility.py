# utilities

from __future__ import annotations

# doubly linked list, non circular, rudimentary.
# Simply add or remove by creating nodes (passing in prevN/nextN) or deleting
class _LinkedListNode:
	data: any
	nextN: _LinkedListNode
	prevN: _LinkedListNode

	# length of linked list of this node and all next nodes
	__len = 0

	def __init__(self, data, prevN = None, nextN = None):
		self.data = data
		self.nextN = nextN
		self.prevN = prevN

		if(self.nextN is not None):
			if(self.prevN is None):
				self.prevN = self.nextN.prevN
			self.nextN.prevN = self
			
		if(self.prevN is not None):
			if(self.nextN is None):
				self.nextN = self.prevN.nextN
			self.prevN.nextN = self
		
		self.__incrementLen()

	def __incrementLen(self):
		self.__len += 1
		if(self.prevN is not None):
			self.prevN.__incrementLen()

	def __decrementLen(self):
		self.__len -= 1
		if(self.prevN is not None):
			self.prevN.__decrementLen()

	def _removeSelf(self):
		self.__decrementLen()
		if(self.nextN is not None):
			self.nextN.prevN = self.prevN
		if(self.prevN is not None):
			self.prevN.nextN = self.nextN
		self.nextN = None
		self.prevN = None
		

	def __del__(self):
		self._removeSelf()

	def __len__(self):
		return self.__len

class _LLIter:
	current: _LinkedListNode
	def __init__(self, lst):
		self.current = lst.start

	def __iter__(self):
		return self
	
	def __next__(self):
		if self.current is None:
			raise StopIteration
		dat = self.current.data
		self.current = self.current.nextN
		return dat

class LinkedList:
	start: _LinkedListNode = None
	end: _LinkedListNode = None

	def __len__(self):
		if self.start is None:
			return 0
		return len(self.start)
	
	def __get(self, ind=0):
		ret = self.start
		for _ in range(0, ind):
			if(ret is not None):
				ret = ret.nextN
			else:
				break
		if(ret is None):
			raise IndexError()
		return ret
	
	def __setitem__(self, key, value):
		if type(key) is int:
			nex = self.__get(key)
			prev = nex.prevN
			_LinkedListNode(value, prev, nex)
		else:
			raise TypeError()
	
	def __getitem__(self, key):
		if type(key) is int:
			return self.__get(key).data
		else:
			raise TypeError()

	
	def __delitem__(self, key):
		ret = self.start
		if type(key) is int:
			for i in range(0, key):
				if(ret is not None):
					ret = ret.nextN
		end = ret
		if type(key) is tuple:
			end = key[1]
			ret = key[0]
		if(ret is not None):
			nex = ret.nextN
			del ret
			ret = nex
		while(ret != end and ret is not None):
			nex = ret.nextN
			del ret
			ret = nex
			
	def push_back(self, data):
		self.end = _LinkedListNode(data, self.end)
		if self.start is None:
			self.start = self.end

	def push_front(self, data):
		self.start = _LinkedListNode(data, None, self.start)
		if self.end is None:
			self.end = self.start

	def pop_back(self):
		tmp = None
		if(self.end is not None):
			tmp = self.end.data
			k = self.end
			self.end = self.end.prevN
			if self.start == k:
				self.start = None
			del k
		
		return tmp

	def pop_front(self):
		tmp = None
		if(self.start is not None):
			tmp = self.start.data
			k = self.start
			self.start = self.start.nextN
			if self.end == k:
				self.end = None
			del k
		
		return tmp
	
	#removes the first instance of data, returning true if removed
	def remove_data(self, data):
		k = self.start
		while k is not None:
			if k.data == data:
				if k == self.start:
					self.start = k.nextN
				k._removeSelf()
				del k
				return True
			k = k.nextN
		return False
				
	def __iter__(self):
		return _LLIter(self)