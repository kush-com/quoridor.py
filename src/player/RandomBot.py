#
# RandomBot.py
#
# @author    Alain Rinder
# @date      2017.06.02
# @version   0.1
#

import random

from src.player.IBot    import *
from src.action.IAction import *



class RandomBot(IBot):
    def moveRandomly(self, board) -> IAction:
        validPawnMoves = board.storedValidPawnMoves[self.pawn.coord] #board.validPawnMoves(self.pawn.coord)
        return random.choice(validPawnMoves)

    def placeFenceRandomly(self, board) -> IAction:
        # Prefer fence placings that increase opponents' path length while not blocking any player
        fencePlacingImpacts = {}
        for fencePlacing in board.storedValidFencePlacings:
            try:
                impact = board.getFencePlacingImpactOnPaths(fencePlacing)
            except Exception:
                # If the fence would block a player or an error occurs, skip it
                continue
            # Compute global impact: positive if it hurts opponents more than self
            globalImpact = 0
            for playerName, delta in impact.items():
                globalImpact += (-1 if playerName == self.name else 1) * delta
            fencePlacingImpacts[fencePlacing] = globalImpact

        if fencePlacingImpacts:
            # Adversarial (1-ply) selection: choose fence f that maximizes
            # minimax_score = impact(f) - min_{g != f} impact(g)
            # This approximates choosing a fence that gives good immediate impact
            # while considering the opponent's best immediate counter-fence.
            minimax_scores = {}
            impacts_values = list(fencePlacingImpacts.values())
            for f, impact_f in fencePlacingImpacts.items():
                # minimal opponent impact among other fences (worst-case for us)
                other_impacts = [v for k, v in fencePlacingImpacts.items() if k != f]
                min_other = min(other_impacts) if other_impacts else 0
                minimax_scores[f] = impact_f - min_other
            bestFence = max(minimax_scores, key=minimax_scores.get)
            # If the best minimax doesn't improve the situation, fall back to random choice
            if minimax_scores[bestFence] > 0:
                return bestFence

        # Fallback: pick a random non-blocking fence (up to N attempts)
        if not board.storedValidFencePlacings:
            return self.moveRandomly(board)
        attempts = 10
        randomFencePlacing = random.choice(board.storedValidFencePlacings)
        while board.isFencePlacingBlocking(randomFencePlacing) and attempts > 0:
            randomFencePlacing = random.choice(board.storedValidFencePlacings)
            attempts -= 1
        if attempts == 0:
            return self.moveRandomly(board)
        return randomFencePlacing

    def play(self, board) -> IAction:
        # 1 chance over 3 to place a fence
        #validFencePlacings = board.validFencePlacings()
        if random.randint(0, 2) == 0 and self.remainingFences() > 0 and len(board.storedValidFencePlacings) > 0:
            return self.placeFenceRandomly(board)
        else:
            return self.moveRandomly(board)
