# utilities

from __future__ import annotations

class LinkedList:
	start: LinkedListNode
	end: LinkedListNode

	def __len__(self):
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
			LinkedListNode(value, prev, nex)
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
		self.end = LinkedListNode(data, self.end)

	def push_front(self, data):
		self.start = LinkedListNode(data, None, self.start)

	def pop_back(self):
		self.end = self.end.prevN
		tmp = None
		if(self.end is not None):
			tmp = self.end.data
			del self.end
		return tmp

	def pop_front(self):
		self.start = self.start.nextN
		tmp = None
		if(self.end is not None):
			tmp = self.start.data
			del self.start
		return tmp
	
	#removes the first instance of data, returning true if removed
	def remove_data(self, data):
		k = self.start
		while k is not None:
			if k.data == data:
				if k == self.start:
					self.start = k.nextN
				del k
				return True
			k = k.nextN
		return False
				
	def __iter__(self):
		return self.start



# doubly linked list, non circular, rudimentary.
# Simply add or remove by creating nodes (passing in prevN/nextN) or deleting
class LinkedListNode:
	data: any
	nextN: LinkedListNode
	prevN: LinkedListNode

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

	def __del__(self):
		if(self.nextN is not None):
			self.nextN.prevN = self.prevN
		if(self.prevN is not None):
			self.prevN.nextN = self.nextN
		self.__decrementLen()

	def __len__(self):
		return self.__len
	
	def __iter__(self):
		return self

	def __next__(self):
		if self.nextN is not None:
			return self.nextN
		else:
			raise StopIteration