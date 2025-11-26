import random
import pytest
from matchmaking import Queue, Player

#test that a link exists for all players after the current player in the queue
def testAllLinks(p, q, removedPlayers, treeInd = 0):
	for i in range(len(q.players)):
		player = p[i]
		testSet = p[i:].copy()
		resultingPlayers = []
		assert player not in removedPlayers
		for tree in player.trees[treeInd].links:
			assert tree.player not in removedPlayers
			assert tree.player in testSet
			resultingPlayers.append(tree.player)
			testSet.remove(tree.player)
		assert player in testSet
		assert len(resultingPlayers) < q.maxLinksToCheck

def test_default():
	q = Queue()
	# first, add maxLink players. We do not care about the attributes here.
	p = [Player("Player"+str(i)) for i in range(0, q.maxLinksToCheck*2)]

	# add the players into the queue
	for player in p:
		q.addPlayer(player)

	testAllLinks(p, q, {})

	# remove a random player and check the last player again to make sure the
	# link was removed
	removed = random.choice(p)
	p.remove(removed)
	q.removePlayer(removed)

	testAllLinks(p, q, {removed})
	
	# obtain potential matchups and print them
	matches = q.searchForMatches()
	for k in matches:
		v = matches[k]
		print("Player " + k.name + ": ")
		for m in v:
			print("{")
			for l in m:
				print(l.name)
			print("}, ")
		print("\n")

	# test cleanup
	del q

if __name__ == "__main__":
	test_default()