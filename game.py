from pokerkit import KuhnPokerHand, Automation, State, Deck, Street, Opening, BettingStructure
from random import random

#Define the initial strategies of each player
p1strategy={
    "K":[2.0/3.0,1.0/3.0],
    "Q":[0.5,0.5],
    "J":[1,0],
    "Kpb":[1,0],
    "Qpb":[0.5,0.5],
    "Jpb":[0,1]
}

p2strategy={
    "Kb":[1,0],
    "Kp":[1,0],
    "Qb":[0.5,0.5],
    "Qp":[2.0/3.0,1.0/3.0],
    "Jb":[0,1],
    "Jp":[1.0/3.0,2.0/3.0]
}

#Class that takes in 2 players and lets them play games.
class Table:
    def __init__(self,p1,p2):
        self.player_1 = p1
        self.player_2 = p2
    
    def playTable(self,printAll=False):

        #Define state for Kuhn Poker
        state = State(
            (
                Automation.ANTE_POSTING,
                Automation.BET_COLLECTION,
                Automation.BLIND_OR_STRADDLE_POSTING,
                Automation.CARD_BURNING,
                Automation.HOLE_DEALING,
                Automation.BOARD_DEALING,
                Automation.HOLE_CARDS_SHOWING_OR_MUCKING,
                Automation.HAND_KILLING,
                Automation.CHIPS_PUSHING,
                Automation.CHIPS_PULLING,
            ),
            Deck.KUHN_POKER,
            (KuhnPokerHand,),
            (
                Street(
                    False,
                    (False,),
                    0,
                    False,
                    Opening.POSITION,
                    1,
                    None,
                ),
            ),
            BettingStructure.FIXED_LIMIT,
            True,
            (1,) * 2,
            (0,) * 2,
            0,
            (2,) * 2,
            2,
        )

        #Get each player's hand
        p1Pos = state.hole_cards[0][0].rank.__str__()
        p2Pos = state.hole_cards[1][0].rank.__str__()
        
        #If printAll is set to true, print as the game progresses
        if printAll:
            print(f"The hole cards are: {state.hole_cards}")

        #If roll under the chance for betting, then bet
        if random() < self.player_1[p1Pos][0]:
            state.complete_bet_or_raise_to()
            p1Pos += "b"
            p2Pos += "b"
            if printAll:
                print(f"Player one bets, making the table {state.bets}")
        else:
            state.check_or_call()
            p1Pos += "p"
            p2Pos += "p"
            if printAll:
                print(f"Player one passes, making the table {state.bets}")
        
        if random() < self.player_2[p2Pos][0]:
            p1Pos += "b"

            #If p1 didn't bet, then bet
            if state.bets[0] == 0:
                state.complete_bet_or_raise_to()
                if printAll:
                    print(f"Player two bets, making the table {state.bets}")
                if random() < self.player_1[p1Pos][0]:
                    state.check_or_call()
                    if printAll:
                        print(f"Player one calls, making the table {state.bets}")
                else:
                    state.fold()
                    if printAll:
                        print(f"Player one folds, making the table {state.bets}")
            #If p1 did bet, then call
            else:
                state.check_or_call()
                if printAll:
                    print(f"Player two calls, making the table {state.bets}")

        #If p1 did bet, then fold
        elif state.bets[0] > 0:
            state.fold()
            if printAll:
                print(f"Player two folds, making the table {state.bets}")
        
        #If p1 didn't bet, then just pass
        else:
            state.check_or_call()
            if printAll:
                print(f"Player two passes, making the table {state.bets}")

        return state.stacks
    
    #Run a given amount of games and return the average winnings for each player
    def runGames(self,amount=10):
        totalWinnings=[0,0]
        for i in range(0,amount):
            result = self.playTable()
            totalWinnings[0]+=result[0]-2
            totalWinnings[1]+=result[1]-2
        return totalWinnings[0]/amount,totalWinnings[1]/amount
    


        



table = Table(p1=p1strategy, p2=p2strategy)
print(table.runGames(50))