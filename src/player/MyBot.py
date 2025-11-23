#
# MyBot.py
#
# Brief description
# 
# @author    My Name
# @date      2000.00.00
# @version   0.1
#

import random

from src.player.IBot    import *
from src.action.IAction import * 
from src.Path import Path



class MyBot(IBot):
    def play(self, board) -> IAction:
        # Try placing a fence sometimes (1/3 chance) if available
        if random.randint(0, 2) == 0 and self.remainingFences() > 0 and len(board.storedValidFencePlacings) > 0:
            randomFencePlacing = random.choice(board.storedValidFencePlacings)
            attempts = 5
            while board.isFencePlacingBlocking(randomFencePlacing) and attempts > 0:
                randomFencePlacing = random.choice(board.storedValidFencePlacings)
                attempts -= 1
            if attempts > 0:
                return randomFencePlacing

        # Otherwise compute best path using A*
        path = Path.AStar(board, self.pawn.coord, self.endPositions)
        if path is None:
            # Fallback to a random valid pawn move
            validPawnMoves = board.storedValidPawnMoves[self.pawn.coord]
            return random.choice(validPawnMoves)
        return path.firstMove()

