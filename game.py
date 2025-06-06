from pokerkit import KuhnPokerHand, Automation, State, Deck, Street, Opening, BettingStructure
from random import random
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# --- Constants ---
# Actions: 0 = Pass/Check/Fold, 1 = Bet/Call
NUM_ACTIONS = 2

CARDS = ['J', 'Q', 'K']
NUM_CARDS = len(CARDS)

# --- Information Set Node ---
class CFRNode:
    """ Represents a node in the game tree corresponding to an information set. """
    def __init__(self, num_actions=NUM_ACTIONS):
        self.num_actions = num_actions
        # Stores cumulative regret for NOT choosing action 'a'
        self.regret_sum = np.zeros(self.num_actions)
        # Stores cumulative strategy probabilities used so far
        self.strategy_sum = np.zeros(self.num_actions)
        # Unique key for this information set (e.g., "Kc", "Jcb")
        self.info_set_key = "" 

    def get_strategy(self):
        """ Calculate current strategy based on positive regrets """
        normalizing_sum = np.sum(np.maximum(self.regret_sum, 0))
        if normalizing_sum > 0:
            strategy = np.maximum(self.regret_sum, 0) / normalizing_sum
        else:
            # Default to uniform random strategy if no positive regrets
            strategy = np.full(self.num_actions, 1.0 / self.num_actions)
        return strategy

    def get_average_strategy(self):
        """ Calculate the average strategy over all iterations """
        normalizing_sum = np.sum(self.strategy_sum)
        if normalizing_sum > 0:
            avg_strategy = self.strategy_sum / normalizing_sum
        else:
            # Default to uniform if strategy_sum is all zeros
            avg_strategy = np.full(self.num_actions, 1.0 / self.num_actions)
        return avg_strategy

    def __str__(self):
        """ String representation for debugging """
        avg_strategy_str = np.array2string(self.get_average_strategy(), formatter={'float_kind':lambda x: "%.2f" % x})
        return f"{self.info_set_key}: Avg Strat={avg_strategy_str}, Regret={self.regret_sum}"

# --- Helper Function for Info Set Keys ---
def get_information_set_key(card, history):
    """ Creates a unique string key for an information set. """
    # Ensure card is a string if it isn't already
    return str(card) + history

# --- Main CFR Data Structure ---
# Maps information set keys (strings) to CFRNode objects
info_set_map = {}

# --- Function to Get/Create Nodes ---
def get_node(info_set_key):
    """ Retrieves or creates a CFRNode for a given information set key """
    if info_set_key not in info_set_map:
        # Create a new node if this info set hasn't been seen before
        node = CFRNode()
        node.info_set_key = info_set_key
        info_set_map[info_set_key] = node
    return info_set_map[info_set_key]


def get_kuhn_legal_actions(history):
    """ Returns the list of legal action indices for Kuhn Poker history """
    # Actions: 0 = Pass/Check/Fold, 1 = Bet/Call
    if history == "":   # Start of game
        return [0, 1] # Pass or Bet
    elif history == "p": # Player 1 passed
        return [0, 1] # Pass or Bet
    elif history == "b": # Player 1 bet
        return [0, 1] # Fold or Call
    elif history == "pb": # Player 1 passed, Player 2 bet
        return [0, 1] # Fold or Call
    else: # Should not happen in valid Kuhn history before terminal state
        return []


def cfr(cards, history, reach_probabilities, active_player):
    """
    Counterfactual Regret Minimization recursive function.
    """
    opponent = 1 - active_player

    # Check for folds first (these end the game immediately)
    if history.endswith('f'): # History is 'bf' or 'pbf'
        payoff_p0 = 1 if history == 'bf' else -1
        return np.array([payoff_p0, -payoff_p0])

    # Check for showdowns (all other paths of length 2 or 3 end in showdown)
    if history in ['pp', 'bk', 'pbk']:
        player0_card = cards[0]
        player1_card = cards[1]
        rank_map = {'J': 1, 'Q': 2, 'K': 3}
        player0_wins = rank_map[player0_card] > rank_map[player1_card]

        if history == 'pp': # Pass-Pass (like check-check), pot=2 (1 ante each)
            # Payoff FOR Player 0
            payoff_p0 = 1 if player0_wins else -1
        else: # Bet was called ('bk' or 'pbk'), pot=4 (1 ante + 1 bet each)
             # Payoff FOR Player 0
            payoff_p0 = 2 if player0_wins else -2

        # Return payoffs for (Player 0, Player 1)
        return np.array([payoff_p0, -payoff_p0])

    # --- Player Decision Node Logic ---
    info_set_key = get_information_set_key(cards[active_player], history)
    node = get_node(info_set_key)
    strategy = node.get_strategy() # Current strategy based on regrets

    legal_actions = get_kuhn_legal_actions(history)
    # Should always have 2 legal actions if not terminal
    assert len(legal_actions) == node.num_actions

    # Calculate expected value of this node using current strategy
    action_utility_vectors = np.zeros((node.num_actions, 2)) # Store payoff vectors [P0, P1] for each action
    node_utility_vector = np.zeros(2)        # Store overall expected payoff vector [P0, P1] for this node

    action_map = {0: 'p', 1: 'b'} # Map action index 0 to 'p' (pass/check/fold), 1 to 'b' (bet/call)
    if history == 'b' or history == 'pb': # If facing bet, action 0 is fold, action 1 is call
        action_map = {0: 'f', 1: 'k'}

    for action in legal_actions:
        action_char = action_map[action]
        next_history = history + action_char

        # Calculate next reach probabilities
        next_reach_probabilities = reach_probabilities.copy()
        next_reach_probabilities[active_player] *= strategy[action]

        # Recursive call - payoff vector from opponent's perspective after this action
        action_utility_vectors[action] = cfr(cards, next_history, next_reach_probabilities, opponent)

        # Accumulate node utility vector weighted by strategy probability
        node_utility_vector += strategy[action] * action_utility_vectors[action]

    # Calculate immediate counterfactual regrets and update node sums
    # Regret is calculated from the perspective of the active player
    utility_for_active_player = node_utility_vector[active_player]

    for action in legal_actions:
        # Utility for the active player if they had taken this specific action
        action_utility_for_player = action_utility_vectors[action][active_player]
        # Immediate counterfactual regret for this action
        regret = action_utility_for_player - utility_for_active_player
        # Accumulate regret, weighted by opponent's reach probability
        node.regret_sum[action] += reach_probabilities[opponent] * regret

    # Update strategy sum, weighted by current player's reach probability
    node.strategy_sum += reach_probabilities[active_player] * strategy

    return node_utility_vector 


# --- Training Loop ---
def train(iterations):
    utils = np.zeros(2) # Tracks sum of payoffs for P0, P1
    deck = list(CARDS) # J, Q, K
    print(f"Starting training for {iterations} iterations...")
    for i in range(iterations):
        # Shuffle deck randomly for each hand
        np.random.shuffle(deck)

        # Ensure cards are passed as strings ('J', 'Q', 'K')
        current_cards = tuple(map(str, deck[0:2]))

        # Start recursion: initial history "", initial reach probs [1.0, 1.0], P0 active (0)
        utils += cfr(current_cards, "", np.ones(2), 0)

        if (i + 1) % 10000 == 0: # Print progress every 10,000 iterations   
            print(f"  Iteration {i+1}/{iterations} completed.")

    print(f"\nTraining Complete over {iterations} iterations.")
    # Average game value is the sum of utilities divided by iterations
    avg_game_value_p0 = utils[0] / iterations
    avg_game_value_p1 = utils[1] / iterations 
    print(f"Average Game Value (P0 perspective): {avg_game_value_p0:.4f}")

    # Print final strategies
    print("\nFinal Average Strategies (Action 0: Pass/Check/Fold, Action 1: Bet/Call):")
    # Sort items for consistent output
    sorted_info_sets = sorted(info_set_map.items())
    if not sorted_info_sets:
        print("  No information sets were visited (check training loop/iterations).")
    else:
        for key, node in sorted_info_sets:
            print(node)
    
     # Calculate average game value
    avg_game_value_p0 = utils[0] / iterations
    avg_game_value_p1 = utils[1] / iterations
    print(f"Average Game Value (P0 perspective): {avg_game_value_p0:.4f}")

    return avg_game_value_p0

    

# --- Function to Plot Strategies ---
def plot_strategies(info_sets_to_plot, avg_game_value):
    """ Generates bar charts for the average strategy of specified info sets """
    print("\nGenerating strategy plots...")

    labels = []
    pass_probs = [] # Probability of Action 0 (Pass/Check/Fold)
    bet_probs = []  # Probability of Action 1 (Bet/Call)

    num_sets_found = 0
    for key in info_sets_to_plot:
        if key in info_set_map:
            num_sets_found += 1
            node = info_set_map[key] # Directly access since get_node creates if not found
            avg_strategy = node.get_average_strategy()
            labels.append(key)
            pass_probs.append(avg_strategy[0])
            bet_probs.append(avg_strategy[1])
        else:
            print(f"  Warning: Info set key '{key}' not found in map. Skipping.")

    if num_sets_found == 0:
        print("  No specified info sets were found to plot.")
        return

    x = np.arange(len(labels)) 
    width = 0.35  

    fig, ax = plt.subplots(figsize=(10, 6)) 
    rects1 = ax.bar(x - width/2, pass_probs, width, label='Action 0 (Pass/Check/Fold)', color='skyblue')
    rects2 = ax.bar(x + width/2, bet_probs, width, label='Action 1 (Bet/Call)', color='lightcoral')
    ax.bar_label(rects1, padding=3, fmt='%.2f')
    ax.bar_label(rects2, padding=3, fmt='%.2f')
    

    # Add some text for labels, title and axes ticks
    ax.set_ylabel('Probability of Action')
    ax.set_ylabel('Probability')
    ax.set_title('Average Strategy (GTO) for Key Kuhn Poker Information Sets')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 1.05) 
    # Prepare the text for the game value
    theoretical_value = -1/18
    game_value_text = f'Avg Game Value (P0): {avg_game_value:.4f} (Theoretical: {theoretical_value:.4f})'

    # Get existing handles and labels from the bars
    handles, existing_labels = ax.get_legend_handles_labels()

    # Create a dummy artist for our text (it won't be visible on the plot)
    game_value_patch = mpatches.Patch(color='none', label=game_value_text)

    # Append the dummy patch and its label to the existing ones
    handles.append(game_value_patch)
    existing_labels.append(game_value_text) 

    # Create the legend with the combined handles and labels
    ax.legend(handles=handles, labels=existing_labels, 
              loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3) # ncol=1 to stack them vertically
    fig.tight_layout()

    plt.show()



# --- Call Training ---
NUM_ITERATIONS = 100000 
final_avg_game_value = train(NUM_ITERATIONS) # Capture the returned value

# --- Plot Key Strategies After Training ---
keys_to_plot = ['J', 'K', 'Q', 'Jb', 'Qb', 'Kb', 'Jp', 'Qp', 'Kp', 'Jpb', 'Qpb', 'Kpb']
existing_keys_to_plot = [key for key in keys_to_plot if key in info_set_map]

if existing_keys_to_plot: 
    plot_strategies(existing_keys_to_plot, final_avg_game_value) 
else:
    print("\nNo strategies found in map to plot.")