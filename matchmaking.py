#File containing the architecture needed for the MatchTree algorithm.

from __future__ import annotations

from utility import LinkedList

# Ruleset: a class with by default two functions: IsValid and IsMatch.
# Extend in a subclass for additional rulesets, such as to implement skill based algorithms.
class Ruleset:
	# minPlayers and maxPlayers define limits (inclusive) on what constitutes a valid match.
	# Set to -1 to ignore in the default implementation.
	minPlayers = 10
	maxPlayers = 10

	# if positive, the timer gives players a period before another ruleset is applied.
	# if zero, the next ruleset is applied immediately after this one fails to make a match.
	timer = -1

	# IsValid returns false if any player in playerList cannot produce
	# a valid match with this ruleset. By default, returns true for any
	# list at most the size of maxPlayers.
	# For any subset of playerList, if IsValid(playerList), then any subset must
	# also be IsValid (the opposite does not have to be true).
	# It is expected that if playerList is two players or less, it performs a constant-time check.
	def IsValid(self, playerList) -> bool:
		return len(playerList) <= self.maxPlayers
	
	# IsMatch returns true if the playerList forms a valid match for this ruleset.
	# By default, returns true as long as if the min player count is reached.
	def IsMatch(self, playerList) -> bool:
		return self.IsValid(playerList) and len(playerList) >= self.minPlayers
	
	# Given an IsMatch player list, returns a priority value indicating preference
	# of this ruleset and player list. Larger values are better. If -1 player list is invalid.
	# By default, returns 0- baseline
	def Priority(self, playerList) -> float:
		if(not self.IsMatch(playerList)):
			return -1
		return 0
	
	# Note about IsValid vs. IsMatch: if any player list IsMatch, then it is also IsValid;
	# if any player list is not IsValid, then it is also not IsMatch;
	# It is valid for a player list to be IsValid and not IsMatch. To avoid infinite recursion,
	# IsMatch should call IsValid.

	# IsValid and IsMatch and Priority are all playerList order-independent. In fact, it's suggested
	# to use a Set of players instead of an array.

# Player: stores references to any MatchTree for the player, and references to the next and previous
# player in the current queue.
class Player:
	# references to MatchTrees with this player as the player value
	trees = []

	# keep track of how long the player has been waiting in queue for the most recent ruleset.
	# Resets if that ruleset's timer has been reached, and is not negative.
	timer = 0

	# keep track of which ruleset the player is bound by, starting at highest priority 0 and down to the
	# length of tree
	rulesetNum = 0

	# indicates the next and previous player in the queue.
	newerPlayer: Player = None
	olderPlayer: Player = None

	# cleans up its MatchTrees
	def clearTrees(self):
		for t in self.trees:
			t.removeOwnLinks()

	def __del__(self):
		self.clearTrees()

	# updates all links for all this player's trees, with the given starting player and count
	def updateTrees(self, count, startingPlayer):
		for t in range(0, self.rulesetNum+1):
			self.trees[t].searchForNewLinks(count, startingPlayer)

	# gets the tree for the player at rulesetNum
	def getCurrentTree(self) -> MatchTree:
		return self.trees[self.rulesetNum]

	def getTotalTimeWaiting(self) -> int:
		val = self.timer
		for t in range(0, self.rulesetNum+1):
			time = self.trees[t].getRuleset().timer
			if time >= 0:
				val += time
		return val

	#Add additional attribute information below.

# MatchTree: a class containing a player, a reference to a ruleset,
# and references to MatchTrees within a certain range older than the current player who can match with
# the ruleset. MatchTree is currently not thread-safe.

class MatchTree:
	# reference to the array of all rulesets
	rules = []

	# the index of the rule which this matchtree is using
	ruleIndex = 0

	player : Player

	# references to other MatchTrees for which, if a link exists between players A and B, then rules.IsValid([A, B]) is true
	# all links must be older players to this tree's player
	links = LinkedList()

	# contents of links but mapped by player to the corresponding index
	linkMap = dict()

	# set of a given older player link which IsValid is false. Used for caching when checking a matchup.
	# Only cache invalid links dependent on static attributes, as there's no mechanisms for removing from the cache-
	# it's assumed any player that's not valid with another player, remains invalid for the ruleset.
	invalidParentsMap = set()

	# When an invalid link is cached, the child being cached is added here so when the child removes all its links,
	# it can clear its own cached references
	invalidParentsMapRefs = set()

	# similar to the invalidParentsMap, the validMatchups stores sets of players which IsValid is true. The validity expected
	# not to change like invalidParentsMap.

	validMatchups = set()

	# contains any player which has a validMatchup set containing this player
	validMatchupsRefs = set()

	# for each item in parents, a link exists to this tree's player with the same ruleset. Used to clean up references
	# if the player leaves the queue. All parents must be newer players to this tree's player
	parents = []

	# contents of parents but mapped by player to corresponding index
	parentMap = dict()

	# retrieves the corresponding ruleset that this matchtree will use
	def getRuleset(self) -> Ruleset:
		return self.rules[self.ruleIndex]

	# removes otherPlayer from own links or parents
	def removeLink(self, otherPlayer: Player):
		if(otherPlayer in self.linkMap):
			self.links.remove_data(self.linkMap.get(otherPlayer))
			self.linkMap.pop(otherPlayer)
		if(otherPlayer in self.parentMap):
			self.parents.pop(self.parentMap.get(otherPlayer))
			self.parentMap.pop(otherPlayer)

	# removes self from all parents and all children
	def removeOwnLinks(self):
		while self.links:
			v = self.links.pop_front()
			v.removeLink(self)
			self.linkMap.pop(v)
		
		while self.parents:
			v = self.parents.pop()
			v.removeLink(self)
			self.parentMap.pop(v)

		while self.invalidParentsMapRefs:
			v = self.invalidParentsMapRefs.pop()
			v.invalidParentsMap.remove(self)

		while self.invalidParentsMap:
			v = self.invalidParentsMap.pop()
			v.invalidParentsMapRefs.remove(self)

		while self.validMatchupsRefs:
			v = self.validMatchupsRefs.pop()
			for s in v.validMatchups:
				if self in s:
					v.validMatchups.remove(s)

		while self.validMatchups:
			v = self.validMatchups.pop()
			v.validMatchupsRefs.remove(self)


	# adds a parent to this tree (does not check ruleset, assumed to be called in addLinkIfValid)
	def addParent(self, otherParent: MatchTree):
		self.parents.append(otherParent)
		self.parentMap[otherParent] = len(self.parents)-1

	# adds a link to this tree if it passes the ruleset, returning true if added new
	def addLinkIfValid(self, otherPlayer: MatchTree) -> bool:
		if((otherPlayer not in self.linkMap) and self.getRuleset().IsValid({self.player, otherPlayer.player})):
			self.links.push_back(otherPlayer)
			self.linkMap[otherPlayer] = len(self.links)-1
			return True
		return False
	
	# starting from the next newer and older player, attempts to establish links up to maxLinks
	def searchForLinks(self, maxLinks):
		self.searchForNewLinks(maxLinks, self.player.olderPlayer)
		self.searchForNewLinks(-maxLinks, self.player.newerPlayer)

	# starting from the specified player, find up to count links (if negative, search previous players)
	# returns a list of players which it has made new links with
	def searchForNewLinks(self, count, startingPlayer):
		tmpPlayer = startingPlayer
		newLinks = []
		while(count != 0 and tmpPlayer != None):
			if(self.addLinkIfValid(tmpPlayer)):
				newLinks.append(tmpPlayer)
			tmpPlayer = tmpPlayer.olderPlayer if count > 0 else tmpPlayer.newerPlayer
			count -= 1 if count > 0 else -1
		return newLinks

	# applies the ruleset's timer to the player's timer
	def setPlayerTimer(self):
		self.player.timer = self.getRuleset().timer

	# starting at this MatchTree, attempts to make a match of at most depth players.
	# Returns a list of all valid matchups such that IsMatch is true.
	# otherPlayers is a list of players up the tree (parent + parents of parents) which
	# IsValid(otherPlayers) is true.
	def findMatchups(self, depth = 10, otherPlayers = {}) -> set:
		newSet = otherPlayers.copy()
		newSet.add(self.player)
		failedMatchup = False

		# if we've already encountered this set of otherPlayers, skip checks
		if otherPlayers not in self.validMatchups:
			# check if this player is incompatible with any players specified in otherPlayers
			for p in otherPlayers:
				if(p in self.invalidParentsMap):
					failedMatchup = True
				if(not self.getRuleset().IsValid({p, self.player})):
					self.invalidParentsMap.add(p.trees[self.ruleIndex])
					p.trees[self.ruleIndex].invalidParentsMapRef.add(self)
					failedMatchup = True
			if failedMatchup:
				return set()
		
		ret = set()
		if self.getRuleset().IsValid(newSet):
			self.validMatchups.add(newSet)
			for p in otherPlayers:
				p.trees[self.ruleIndex].validMatchupsRefs.add(self)
			
			
			if(self.getRuleset().IsMatch(newSet)):
				ret.add(newSet)
			if(depth > 0):
				for l in self.links:
					tmp = l.findMatchups(depth-1, newSet)
					ret.union(tmp)
		return ret	

	# initializes this matchtree
	def __init__(self, player: Player, rules, rulesetIndex: int):
		self.player = player
		self.rules = rules
		self.ruleIndex = rulesetIndex

	def __del__(self):
		self.removeOwnLinks()



# The master class which keeps track of players within itself, as well as establishing matches.
class Queue:
	# players in queue, with the last player being the newest
	players = []
	playerMap = dict()

	# rulesets which to apply to the players. All rulesets are applied in this order to each player.
	rulesets = [Ruleset()]

	#when performing a link search, sets the max amount of links which to create on either side of a player
	maxLinksToCheck = 100

	# adds a player into the queue at the end
	def addPlayer(self, player: Player):
		if(player not in self.playerMap):
			if(len(self.players) > 0):
				self.players[-1].newerPlayer = player
				player.olderPlayer = self.players[-1]
			self.players.append(player)
			self.playerMap[player] = len(self.players)-1
			for m in range(0, len(self.rulesets)):
				player.trees.append(MatchTree(player, self.rulesets, m))
			player.getCurrentTree().searchForLinks(self.maxLinksToCheck)
		

	# removes a player from the queue and cleans up and re-searches as necessary
	def removePlayer(self, player: Player):
		removedIndex = self.playerMap[player]
		player.clearTrees()
		if(player.olderPlayer is not None):
			player.olderPlayer.newerPlayer = player.newerPlayer
			#older players don't have to update any of their links

		if(player.newerPlayer is not None):
			player.newerPlayer.olderPlayer = player.olderPlayer
			playerCheckIndex = removedIndex - self.maxLinksToCheck
			playerUpdate = player.newerPlayer
			count = 0
			# update links
			while(playerUpdate is not None and count < self.maxLinksToCheck):
				if(playerCheckIndex < len(self.players)):
					playerUpdate.searchForNewLinks(1, self.players[playerCheckIndex])
				playerCheckIndex -= 1
				count += 1
				playerUpdate = playerUpdate.newerPlayer

		self.players.remove(player)

	# performs one search for matches, returning a dict of players to potential matchups, sorted by ruleset.
	# Use the player queue order additionally to matchmake players waiting longer.
	def searchForMatches(self, depth=10) -> dict:
		#maps player to all available matchups
		ret = dict()
		for p in self.players:

			#maps ruleset to matchups
			matches = []
			for i in range(0, p.ruleIndex+1):
				tmp = p.trees[i].findMatchups(depth, set())
				matches.append(tmp)
			ret[p] = matches
		return ret
	
	#decrements all player timers and updates their ruleset num as needed
	def doTick(self, delta=1):
		for p in self.players:
			if p.timer >= 0:
				if p.timer > 0:
					p.timer -= delta
				else:
					p.rulesetNum += 1
					p.timer = p.trees.getRuleset().timer
					p.getCurrentTree().searchForLinks(self.maxLinksToCheck)

