from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Static
import random
import asyncio

class Card(Static):
    def __init__(self, rank: str, suit: str, suit_id: str) -> None:
        self.rank = rank
        self.suit = suit
        self.suit_id = suit_id
        label = f"{rank}\n{suit}"
        super().__init__(label, id=f"card-{rank}{suit_id}")

    def __repr__(self):
        return f"{self.rank}{self.suit}"

class Hand:
    def __init__(self, owner: str):
        self.owner = owner  # player or dealer
        self.cards: list[Card] = []

    def add(self, card: Card):
        self.cards.append(card)

    def clear(self):
        self.cards.clear()

    def values(self) -> tuple[int, int]:
        """Returns (low_value, high_value) where high_value uses aces as 11 when beneficial"""
        total = 0
        aces = 0
        for card in self.cards:
            if card.rank in ["J", "Q", "K"]:
                total += 10
            elif card.rank == "A":
                aces += 1
                total += 1
            else:
                total += int(card.rank)

        high = total + (10 if aces and total + 10 <= 21 else 0)
        return total, high

    def best_value(self) -> int:
        """Returns the best valid hand value"""
        low, high = self.values()
        return high if high <= 21 else low

    def is_blackjack(self) -> bool:
        return len(self.cards) == 2 and max(self.values()) == 21

    def is_bust(self) -> bool:
        return min(self.values()) > 21

    def __repr__(self):
        cards = " ".join(repr(c) for c in self.cards)
        return f"{self.owner} Hand: {cards} (best={self.best_value()})"

def generate_shoe(num_decks=6):
    """Generate a shuffled shoe of cards with a break card near the end"""
    ranks = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    suits = ["♠", "♥", "♦", "♣"]
    suit_ids = ["S", "H", "D", "C"]

    shoe = []
    card_id = 0
    for _ in range(num_decks):
        for rank in ranks:
            for suit, suit_id in zip(suits, suit_ids):
                card_id += 1
                shoe.append(Card(rank, suit, f"{suit_id}-{card_id}"))

    random.shuffle(shoe)

    # Insert break card near the end
    cut_position = random.randint(60, 75)
    break_card_index = len(shoe) - cut_position
    shoe.insert(break_card_index, "BREAK")

    return shoe

class BlackjackApp(App[str]):
    """A Textual blackjack game application"""
    CSS_PATH = "button.tcss"

    def __init__(self):
        super().__init__()
        self.shoe = generate_shoe()
        self.player_hand = Hand("Player")
        self.dealer_hand = Hand("Dealer")
        self.console_log = None

    def on_mount(self):
        self.console_log = self.query_one("#log", Static)

    def deal_new_hand(self):
        """Deal a new hand to both player and dealer"""
        # Clear containers
        self.query_one("#player-hand", Horizontal).remove_children()
        self.query_one("#dealer-hand", Horizontal).remove_children()
        
        # Clear hands
        self.player_hand.clear()
        self.dealer_hand.clear()

        # Deal two cards each
        self.player_hand.add(self.shoe.pop(0))
        self.dealer_hand.add(self.shoe.pop(0))
        self.player_hand.add(self.shoe.pop(0))
        self.dealer_hand.add(self.shoe.pop(0))

        # Render dealer hand (1 shown, 1 hidden)
        dealer_container = self.query_one("#dealer-hand", Horizontal)
        dealer_container.mount(self.dealer_hand.cards[0])
        dealer_container.mount(Card("O", "?", "hidden"))  # Hidden card

        # Render player hand
        player_container = self.query_one("#player-hand", Horizontal)
        for card in self.player_hand.cards:
            player_container.mount(card)

    def update_totals(self, reveal_dealer: bool = False):
        """Update the total displays for both hands"""
        player_total = self.player_hand.values()
        dealer_total = self.dealer_hand.values()

        self.query_one("#player-total", Static).update(
            f"Player Total: {player_total[0]} (Best: {player_total[1]})"
        )
        
        if reveal_dealer:
            self.query_one("#dealer-total", Static).update(
                f"Dealer Total: {dealer_total[0]} (Best: {dealer_total[1]})"
            )
        else:
            self.query_one("#dealer-total", Static).update("Dealer Total: ???")

    def reveal_dealer_cards(self):
        """Remove hidden card and show all dealer cards"""
        hidden_card = self.query_one("#card-Ohidden", Card)
        hidden_card.remove()

        dealer_container = self.query_one("#dealer-hand", Horizontal)
        for card in self.dealer_hand.cards[1:]:
            dealer_container.mount(card)

    def set_button_visibility(self, deal: bool = False, hit: bool = False, stand: bool = False):
        """Set visibility of game buttons"""
        self.query_one("#deal-button", Button).visible = deal
        self.query_one("#hit-button", Button).visible = hit
        self.query_one("#stand-button", Button).visible = stand

    async def handle_dealer_turn(self):
        """Handle the dealer's turn following blackjack rules"""
        dealer_container = self.query_one("#dealer-hand", Horizontal)
        
        while self.dealer_hand.values()[1] < 17:
            card = self.shoe.pop(0)
            self.dealer_hand.add(card)
            dealer_container.mount(card)
            self.console_log.update(f"Dealer drew: {card}")
            self.update_totals(reveal_dealer=True)
            await asyncio.sleep(1)

    def determine_winner(self) -> str:
        """Determine the winner and return result message"""
        player_best = self.player_hand.values()[1]
        dealer_best = self.dealer_hand.values()[1]

        if player_best > 21:
            return "Player busts! Dealer wins."
        elif dealer_best > 21:
            return "Dealer busts! Player wins!"
        elif player_best > dealer_best:
            return "Player wins!"
        elif player_best < dealer_best:
            return "Dealer wins!"
        else:
            return "It's a tie!"

    def compose(self) -> ComposeResult:
        """Compose the initial UI layout"""
        with Vertical(id="screen"):
            yield Static("Dealer Total: ???", id="dealer-total")
            with Horizontal(id="dealer-hand"):
                pass
            yield Static("Player Total: 0 (Best: 0)", id="player-total")
            with Horizontal(id="player-hand"):
                pass

            with Horizontal(id="button-row"):
                yield Button("Deal", id="deal-button")
                
                hit_button = Button("Hit", id="hit-button")
                hit_button.visible = False
                yield hit_button
                
                stand_button = Button("Stand", id="stand-button")
                stand_button.visible = False
                yield stand_button
                
            yield Static("Welcome to Blackjack! Press Deal to start.", id="log")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events"""
        if event.button.id == "deal-button":
            await self.handle_deal()
        elif event.button.id == "hit-button":
            await self.handle_hit()
        elif event.button.id == "stand-button":
            await self.handle_stand()
        else:
            self.console_log.update(f"Unknown button pressed: {event.button.id}")

    async def handle_deal(self):
        """Handle the deal button press"""
        self.console_log.update("Dealing new hand...")
        self.deal_new_hand()
        self.update_totals(reveal_dealer=False)
        
        if self.player_hand.is_blackjack():
            self.console_log.update("Blackjack! Player wins immediately.")
            self.reveal_dealer_cards()
            self.update_totals(reveal_dealer=True)
            self.set_button_visibility(deal=True)
        else:
            self.set_button_visibility(hit=True, stand=True)

    async def handle_hit(self):
        """Handle the hit button press"""
        card = self.shoe.pop(0)
        self.player_hand.add(card)
        self.console_log.update(f"Player drew: {card}")
        self.query_one("#player-hand", Horizontal).mount(card)
        self.update_totals(reveal_dealer=False)

        if self.player_hand.values()[1] > 21:
            self.console_log.update("Player busts!")
            self.reveal_dealer_cards()
            self.update_totals(reveal_dealer=True)
            self.set_button_visibility(deal=True)

    async def handle_stand(self):
        """Handle the stand button press"""
        self.console_log.update("Player stands")
        self.reveal_dealer_cards()
        self.update_totals(reveal_dealer=True)
        await asyncio.sleep(1)

        await self.handle_dealer_turn()
        
        result = self.determine_winner()
        self.console_log.update(result)
        self.set_button_visibility(deal=True)

if __name__ == "__main__":
    app = BlackjackApp()
    app.run()