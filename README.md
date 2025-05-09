# Kuhn Poker Solver using Counterfactual Regret Minimization (CFR)
## Authored by: Ivan Flores, John Pham, Caleb Cassin

## 1. Overview

This project implements the Counterfactual Regret Minimization (CFR) algorithm to find near-optimal game strategies for Kuhn Poker. Kuhn Poker is a simplified, three-card version of poker often used in game theory research as a manageable model for imperfect information games. The goal is to compute strategies that are close to a Nash Equilibrium, meaning they are difficult for an opponent to exploit.

## 2. File Structure

The core logic is contained in a single Python script `game.py`.

## 3. Core Concepts

* **Kuhn Poker:** A two-player game using a three-card deck (e.g., Jack, Queen, King). Each player antes 1 chip, gets one card, and there's one round of betting where players can check or bet 1 chip.
* **Counterfactual Regret Minimization (CFR):** An iterative algorithm where the system plays against itself many times. In each iteration, it calculates "regret" for not choosing different actions in the past. Actions with higher regret become more likely to be chosen in the future. Over many iterations, the average strategy converges towards a Nash Equilibrium.
* **Information Set (InfoSet):** Represents everything a player knows at a specific decision point – their private card and the sequence of public actions (bets, checks) so far. Strategies are defined for each information set.
* **Actions:** In this implementation:
    * `0`: Pass / Check / Fold
    * `1`: Bet / Call

## 4. Key Components and Functions

Here's a breakdown of the main parts of the Python script:

### Constants:
* `NUM_ACTIONS`: Defines the number of possible actions (2 in this case).
* `CARDS`: A list representing the deck (e.g., `['J', 'Q', 'K']`).

### `CFRNode` Class:
* **Purpose:** Represents a single information set in the game tree. It stores the learning state for that specific game situation.
* `__init__(self, num_actions)`:
    * Initializes a node.
    * `self.regret_sum`: A NumPy array storing the sum of counterfactual regrets for each action. If an action would have led to a better outcome in past iterations, its regret increases.
    * `self.strategy_sum`: A NumPy array storing the sum of strategy probabilities used so far. This is used to calculate the average strategy over all iterations.
    * `self.info_set_key`: A unique string identifying this information set (e.g., "Qpb" for Player 0 holding a Queen after "pass-bet" history).
* `get_strategy(self)`:
    * Calculates the current iteration's strategy (a probability distribution over actions).
    * It's based on "regret matching": actions with positive accumulated regret are chosen proportionally to their regret. If all regrets are zero or negative, a uniform random strategy is used.
* `get_average_strategy(self)`:
    * Calculates the average strategy across all iterations. This is the strategy that converges to the Nash Equilibrium.
    * It's derived from `self.strategy_sum`.
* `__str__(self)`:
    * Provides a string representation of the node, showing its average strategy and accumulated regrets (useful for debugging).

### Helper Functions & Data:
* `info_set_map` (Global Dictionary):
    * **Purpose:** Stores all `CFRNode` objects created during training.
    * **How it works:** Keys are the `info_set_key` strings, and values are the corresponding `CFRNode` objects. This allows quick retrieval of a node for any game state.
* `get_information_set_key(card, history)`:
    * **Purpose:** Creates a unique string key for an information set.
    * **How it works:** Concatenates the player's private card (e.g., 'J') and the public history of actions (e.g., "pb" for pass-bet).
* `get_node(info_set_key)`:
    * **Purpose:** Retrieves an existing `CFRNode` from `info_set_map` or creates a new one if this information set hasn't been encountered before.
* `get_kuhn_legal_actions(history)`:
    * **Purpose:** Determines the legal actions (0 or 1) available to the current player based on the game history.
    * **How it works:** Uses simple logic for Kuhn Poker (e.g., after a bet, actions are fold or call).

### Core CFR Algorithm:
* `cfr(cards, history, reach_probabilities, active_player)`:
    * **Purpose:** The heart of the CFR algorithm; a recursive function that traverses the game tree.
    * **Inputs:**
        * `cards`: A tuple of cards dealt to Player 0 and Player 1 (e.g., `('K', 'Q')`).
        * `history`: String representing the sequence of actions taken so far.
        * `reach_probabilities`: A NumPy array `[P0_reach_prob, P1_reach_prob]` representing the probability that Player 0 and Player 1, respectively, would play to reach the current `history` *if they were trying to reach it*.
        * `active_player`: An integer (0 or 1) indicating whose turn it is.
    * **Logic:**
        1.  **Terminal State Check:** If the `history` indicates the game has ended (e.g., a fold, or all betting rounds complete), it calculates and returns the payoffs for Player 0 and Player 1.
        2.  **Get Node:** Identifies the current information set for the `active_player` using `get_information_set_key()` and retrieves/creates the corresponding `CFRNode` using `get_node()`.
        3.  **Get Strategy:** Gets the current strategy for this node using `node.get_strategy()`.
        4.  **Recursive Calls:** For each legal action the `active_player` can take:
            * It recursively calls `cfr()` for the next game state (updated history, updated reach probabilities reflecting the chance of taking this action, and the other player now active).
            * The results of these recursive calls (utilities of child states) are stored.
        5.  **Calculate Utilities & Regrets:**
            * Calculates the expected utility of the current node based on the current strategy and the utilities of child states.
            * For each action, it calculates the "counterfactual regret": how much better the outcome would have been if that specific action had been taken, compared to the expected utility of playing according to the current strategy. This regret is weighted by the opponent's reach probability.
        6.  **Update Node:**
            * `node.regret_sum` is updated with the calculated regrets.
            * `node.strategy_sum` is updated with the current strategy, weighted by the current player's reach probability.
        7.  **Return Value:** Returns the expected utility vector `[P0_utility, P1_utility]` for the current node/history.

### Training Orchestration:
* `train(iterations)`:
    * **Purpose:** Manages the overall training process.
    * **Logic:**
        1.  Initializes an overall utility tracker `utils`.
        2.  Loops for the specified number of `iterations`:
            * Shuffles the `CARDS` deck and deals two cards.
            * Calls the main `cfr()` function for the start of a new game (empty history, initial reach probabilities of 1.0 for both players, Player 0 starts).
            * Adds the returned utilities from `cfr()` to the `utils` tracker.
            * Prints progress periodically.
        3.  After all iterations, calculates and prints the average game value for Player 0 (total utility for P0 / iterations). This value indicates how well Player 0 is expected to do if both players play according to the learned average strategies.
        4.  Prints the final average strategies for all visited information sets by iterating through `info_set_map`.
        5.  Returns the calculated `avg_game_value_p0`.

### Visualization:
* `plot_strategies(info_sets_to_plot, avg_game_value)`:
    * **Purpose:** Generates and displays a bar chart visualizing the average strategies for selected information sets.
    * **Inputs:**
        * `info_sets_to_plot`: A list of information set keys (strings) to include in the plot.
        * `avg_game_value`: The average game value for Player 0, to display on the plot.
    * **Logic:**
        1.  For each specified info set key, retrieves the `CFRNode` from `info_set_map`.
        2.  Gets the average strategy using `node.get_average_strategy()`.
        3.  Uses `matplotlib.pyplot` to create a grouped bar chart showing the probabilities of Action 0 (Pass/Check/Fold) and Action 1 (Bet/Call) for each info set.
        4.  Displays the average game value and the theoretical game value in the legend or title.

## 5. How They Work Together (Workflow)

1.  **Initialization:** The script starts by defining constants and the global `info_set_map` (which is initially empty).
2.  **Training Begins:** The `train(NUM_ITERATIONS)` function is called.
    * Inside `train()`, a loop runs for many iterations. In each iteration:
        * A new hand of Kuhn Poker begins (cards are shuffled and dealt).
        * `train()` calls `cfr()` with the initial game state (cards, empty history `""`, reach probabilities `[1.0, 1.0]`, Player 0 active).
3.  **CFR Recursion:**
    * The `cfr()` function is the engine. When called:
        * If it's a game-ending state, it returns the payoffs.
        * Otherwise, for the `active_player`, it forms an `info_set_key` (e.g., Player 0 has 'K', history is empty -> "K").
        * It calls `get_node("K")`. If "K" isn't in `info_set_map`, a new `CFRNode` is created and added.
        * The `CFRNode`'s `get_strategy()` method provides the action probabilities for this turn (based on past regrets).
        * `cfr()` then iterates through possible actions (e.g., Check or Bet). For each action:
            * It makes a recursive call to `cfr()` for the *next* state (e.g., if P0 bets with K, next history is "b", next active player is P1). The reach probabilities are updated to reflect the path taken.
        * Once the recursive calls return utilities from deeper in the game tree, the current `cfr()` call calculates regrets for the actions just explored at node "K".
        * These regrets update `info_set_map["K"].regret_sum`. The strategy used updates `info_set_map["K"].strategy_sum`.
        * This process unfolds recursively until the entire game tree for that hand is explored.
4.  **Accumulating Results:** The initial call to `cfr()` in `train()` eventually returns the expected value of that specific hand, which `train()` accumulates.
5.  **Training Ends:** After all iterations, `train()` computes `avg_game_value_p0`.
6.  **Visualization:**
    * `train()` calls `plot_strategies()`, passing it a list of important information set keys and the `avg_game_value_p0`.
    * `plot_strategies()` iterates through these keys, retrieves the corresponding `CFRNode` objects from the (now fully populated) `info_set_map`, and calls `get_average_strategy()` on each to get the final learned behaviors.
    * It then uses `matplotlib` to display these strategies and the game value.

Essentially, `train` drives the process over many games. `cfr` explores possibilities within each game, learning from regrets. `CFRNode` objects store this learning per game situation. `plot_strategies` shows the final learned behaviors.

## 6. How to Run

1.  Ensure you have Python installed.
2.  Install necessary libraries:
    ```bash
    pip install numpy matplotlib
    ```
3.  Save the code as a Python file (e.g., `kuhn_cfr.py`).
4.  Run the script from your terminal:
    ```bash
    python kuhn_cfr.py
    ```
    The script will print training progress, final average strategies for all info sets, the average game value, and then display a plot of key strategies.

## 7. Dependencies

* Python 3.x
* NumPy: For numerical operations, especially array manipulations for regrets and strategies.
* Matplotlib: For plotting the strategy visualizations.