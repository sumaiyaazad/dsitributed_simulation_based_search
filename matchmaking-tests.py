import random
import pytest
from matchmaking import Queue, Player

#test that a link exists for all players after the current player in the queue
def _testAllLinks(p, q, removedPlayers, treeInd = 0):
	for i in range(len(q.players)):
		player = p[i]
		testSet = p[i:].copy()
		resultingPlayers = []
		assert player not in removedPlayers
		for tree in player.trees[treeInd].links:
			assert tree.player not in removedPlayers
			assert tree.player not in resultingPlayers
			resultingPlayers.append(tree.player)
			if tree.player in testSet:
				testSet.remove(tree.player)
		assert player in testSet
		assert len(resultingPlayers) < q.maxLinksToCheck

def test_default():
	q = Queue()
	q.rulesets[0].minPlayers = 8
	q.maxLinksToCheck = 20
	players = 100
	# first, add maxLink players. We do not care about the attributes here.
	p = [Player("Player"+str(i)) for i in range(0, players)]

	# add the players into the queue
	for player in p:
		q.addPlayer(player)

	_testAllLinks(p, q, {})

	# remove a random player and check the last player again to make sure the
	# link was removed
	removed = random.choice(p)
	p.remove(removed)
	q.removePlayer(removed)

	_testAllLinks(p, q, {removed})
	
	minPlayers = 8

	x = 0
	while len(p) > minPlayers:
		x += 1
		totalMatches = 0
		print("Search", x)
		# obtain potential matchups and print them
		matches = q.searchForMatches()
		for k in matches:
			v = matches[k]
			
			print("Player " + k.name + ": ")
			for t in range(len(v)):
				print("Tree", t, ": ", len(v[t]), "matches")
				totalMatches += len(v[t])
				'''for m in v[t]:
					print("{")
					for l in m:
						print(l.name, end=" ")
					print("},", end=" ")
				print("],")'''
			print()

		if(totalMatches == 0 and len(p) >= minPlayers):
			print("No matches found! Re-searching all players")
			for pl in p:
				pl.updateTrees(q.maxLinksToCheck, pl.olderPlayer)

		print("Getting best matches... (and removing)")

		best = q.getBestMatches(matches)

		for k in best:
			print("Player " + k.name + ": ", end="")
			rule, prio, pll = best[k]
			for pl in pll:
				print(pl.name, end=" ")
				if pl in p:
					p.remove(pl)
					q.removePlayer(pl)
			print()

		print("\n************\nticking and re-searching\n************\n")

		q.doTick()

	print("Printing remaining players")
	for pl in p:
		print(pl.name)

	# test cleanup
	del q

if __name__ == "__main__":
	test_default()