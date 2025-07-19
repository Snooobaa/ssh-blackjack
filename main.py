from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, Container
from textual.widgets import Button, Static, Input
from textual.binding import Binding
import random
import asyncio
import json
import os
import sys
import threading
import re
import time

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
    """A Textual blackjack game application with chat"""
    CSS_PATH = "button.tcss"
    
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("enter", "send_chat", "Send chat message", show=False),
    ]

    def __init__(self):
        super().__init__()
        self.shoe = generate_shoe()
        self.player_hand = Hand("Player")
        self.dealer_hand = Hand("Dealer")
        self.console_log = None
        self.chat_log = None
        self.chat_input = None
        
        # Get session info from environment
        self.session_id = os.getenv("SSH_SESSION_ID", "local")
        self.username = os.getenv("SSH_USERNAME", "Player")
        
        # Track last chat message count
        self.last_chat_line = 0

    def display_chat_message(self, msg):
        """Display a chat message in the chat log"""
        if self.chat_log:
            username = msg.get("username", "Unknown")
            message = msg.get("message", "")
            timestamp = msg.get("timestamp", "")
            
            # Format timestamp
            if timestamp:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    time_str = dt.strftime("%H:%M:%S")
                except:
                    time_str = ""
            else:
                from datetime import datetime
                time_str = datetime.now().strftime("%H:%M:%S")
            
            formatted_msg = f"[{time_str}] {username}: {message}"
            
            # Get current chat log content
            current_content = str(self.chat_log.renderable) if self.chat_log.renderable else ""
            if current_content:
                new_content = current_content + "\n" + formatted_msg
            else:
                new_content = formatted_msg
            
            self.chat_log.update(new_content)

    def send_chat_message(self, message: str):
        """Send a chat message to all connected users"""
        if message.strip():
            # Always show the message immediately to the sender for better UX
            from datetime import datetime
            msg = {
                "username": self.username,
                "message": message.strip(),
                "timestamp": datetime.now().isoformat()
            }
            self.display_chat_message(msg)
            
            if self.session_id != "local":
                # Send via file-based communication to Go server
                chat_msg = {
                    "message": message.strip(),
                    "username": self.username,
                    "session_id": self.session_id,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                }
                chat_json = json.dumps(chat_msg)
                
                # Write to a dedicated chat file that the Go server monitors
                try:
                    with open('/tmp/ssh-chat-messages.log', 'a') as f:
                        f.write(f"{chat_json}\n")
                        f.flush()
                    
                    # Also write to debug file
                    with open('/tmp/python-chat-debug.log', 'a') as f:
                        f.write(f"[{self.session_id}] Sent to file: {chat_json}\n")
                        f.flush()
                        
                except Exception as e:
                    # Fallback: write to debug log
                    try:
                        with open('/tmp/python-chat-debug.log', 'a') as f:
                            f.write(f"[{self.session_id}] ERROR writing chat: {e}\n")
                            f.flush()
                    except:
                        pass

    def check_for_chat_messages(self):
        """Check for incoming chat messages from file"""
        try:
            chat_file = "/tmp/ssh-chat.log"
            if os.path.exists(chat_file):
                with open(chat_file, 'r') as f:
                    lines = f.readlines()
                
                # Process new lines since last check
                new_lines = lines[self.last_chat_line:]
                for line in new_lines:
                    line = line.strip()
                    if line:
                        try:
                            msg = json.loads(line)
                            # Don't display our own messages that come back from server
                            # (we already displayed them immediately when sending)
                            if msg.get("username") != self.username:
                                self.display_chat_message(msg)
                        except json.JSONDecodeError:
                            # Silently ignore malformed JSON lines
                            pass
                
                self.last_chat_line = len(lines)
        except Exception:
            # Silently ignore file reading errors
            pass
        
        # Schedule next check
        self.set_timer(1.0, self.check_for_chat_messages)

    def send_test_message(self):
        """Send a test message to verify chat functionality"""
        test_msg = f"Auto-test message from {self.username}"
        sys.stderr.write(f"DEBUG: Sending auto-test message: {test_msg}\n")
        sys.stderr.flush()
        self.send_chat_message(test_msg)

    def action_send_chat(self):
        """Action to send chat message when Enter is pressed"""
        if self.chat_input and self.chat_input.has_focus:
            message = self.chat_input.value
            if message.strip():
                self.send_chat_message(message)
                self.chat_input.value = ""
                sys.stderr.write(f"DEBUG: Chat message sent via action: '{message}'\n")
                sys.stderr.flush()

    def on_mount(self):
        self.console_log = self.query_one("#log", Static)
        self.chat_log = self.query_one("#chat-log", Static)
        self.chat_input = self.query_one("#chat-input", Input)
        
        # Debug: write session info to file
        try:
            with open('/tmp/python-startup-debug.log', 'a') as f:
                f.write(f"Session ID: {self.session_id}\n")
                f.write(f"Username: {self.username}\n")
                f.write(f"Is local: {self.session_id == 'local'}\n")
                f.flush()
        except:
            pass
        
        # Welcome message
        welcome_msg = f"Welcome {self.username}! You can chat with other players here."
        self.chat_log.update(welcome_msg)
        
        # Start chat message monitoring
        self.set_timer(1.0, self.check_for_chat_messages)
        
        # Send a test message after 3 seconds if not in local mode
        if self.session_id != "local":
            self.set_timer(3.0, self.send_test_message)

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
        with Horizontal(id="main-layout"):
            # Left side - Game
            with Vertical(id="game-area"):
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
            
            # Right side - Chat
            with Vertical(id="chat-area"):
                yield Static("💬 Chat", id="chat-title")
                yield Static("", id="chat-log", classes="chat-log")
                yield Input(placeholder="Type a message and press Enter...", id="chat-input")

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

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle chat input submission"""
        sys.stderr.write(f"DEBUG: Input submitted event triggered for {event.input.id}\n")
        sys.stderr.flush()
        
        if event.input.id == "chat-input":
            message = event.input.value
            sys.stderr.write(f"DEBUG: Chat input received: '{message}'\n")
            sys.stderr.flush()
            
            if message.strip():
                self.send_chat_message(message)
                event.input.value = ""
                sys.stderr.write(f"DEBUG: Chat message sent and input cleared\n")
                sys.stderr.flush()
            else:
                sys.stderr.write(f"DEBUG: Empty message, not sending\n")
                sys.stderr.flush()
        
        # Prevent the key binding from also triggering
        event.stop()

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