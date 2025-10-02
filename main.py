#!/usr/bin/env python3
"""
Claude Chat Terminal - Use Claude.ai from terminal with your subscription
Requires: 
    pip install undetected-chromedriver selenium
Usage: python claude_chat_terminal.py
"""

import time
import sys
import os
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class ClaudeChatTerminal:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.last_message_count = 0
        
    def init_browser(self):
        """Initialize undetected Chrome browser"""
        print("Initializing browser...")
        
        options = uc.ChromeOptions()
        # Don't use headless - it's more detectable
        # options.add_argument('--headless=new')
        
        # Use a persistent user data directory to save login
        user_data_dir = os.path.expanduser("~/.claude_terminal_chrome")
        options.add_argument(f'--user-data-dir={user_data_dir}')
        
        # Additional options for stability
        options.add_argument('--no-first-run')
        options.add_argument('--no-service-autorun')
        options.add_argument('--password-store=basic')
        
        # Initialize undetected Chrome with automatic driver download for version 137
        try:
            self.driver = uc.Chrome(options=options, version_main=137, use_subprocess=True)
        except Exception as e:
            print(f"Failed to initialize with version 137, trying auto-detect: {e}")
            # Fallback: let it auto-detect and download
            self.driver = uc.Chrome(options=options, use_subprocess=True)
        
        self.wait = WebDriverWait(self.driver, 20)
        
        print("✓ Browser initialized\n")
        
    def login_if_needed(self):
        """Navigate to Claude and check if login is needed"""
        print("Navigating to Claude.ai...")
        self.driver.get("https://claude.ai/new")
        
        # Wait a bit for page to load
        time.sleep(5)
        
        # Check if we need to login
        current_url = self.driver.current_url
        if "login" in current_url.lower() or "claude.ai/new" not in current_url:
            print("\n" + "="*60)
            print("  PLEASE LOG IN TO CLAUDE.AI IN THE BROWSER WINDOW")
            print("  After logging in, return here and press Enter")
            print("="*60 + "\n")
            
            input("Press Enter after you've logged in...")
            
            # Check if we're now at the right page
            time.sleep(2)
            if "claude.ai" not in self.driver.current_url:
                print("Login may have failed. Please check the browser.")
                return False
            
            print("✓ Login successful!\n")
        else:
            print("✓ Already logged in!\n")
        
        return True
    
    def get_all_messages(self):
        """Get all message elements on the page"""
        # Try multiple strategies to find messages
        selectors = [
            # Modern Claude UI selectors
            'div[data-test-render-count]',
            'div.font-user-message',
            'div.font-claude-message',
            # Generic message containers
            'div[class*="Message"]',
            'div[class*="message"]',
            # Content editable and text areas
            'div.prose',
            'div[class*="whitespace-pre-wrap"]',
        ]
        
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements and len(elements) > 0:
                    # Filter out empty elements
                    non_empty = [el for el in elements if el.text.strip()]
                    if non_empty:
                        return non_empty
            except Exception as e:
                continue
        
        return []
    
    def send_message(self, message):
        """Send a message to Claude and wait for response"""
        try:
            # Store current message count before sending
            initial_messages = self.get_all_messages()
            initial_count = len(initial_messages)
            
            # Find the input field - try multiple selectors
            input_selectors = [
                'div[contenteditable="true"]',
                'div.ProseMirror',
                'textarea',
                '[role="textbox"]',
                'div[data-placeholder]'
            ]
            
            input_field = None
            for selector in input_selectors:
                try:
                    input_field = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if input_field and input_field.is_displayed():
                        break
                except:
                    continue
            
            if not input_field:
                return "Error: Could not find input field. The page structure may have changed."
            
            # Clear and type message
            input_field.click()
            time.sleep(0.5)
            
            # Clear any existing content
            input_field.send_keys(Keys.CONTROL + "a")
            input_field.send_keys(Keys.BACKSPACE)
            time.sleep(0.3)
            
            # Type message
            input_field.send_keys(message)
            time.sleep(0.5)
            
            # Send the message (try Enter key)
            input_field.send_keys(Keys.RETURN)
            time.sleep(2)
            
            # Wait for response to start appearing
            print("Waiting for Claude's response", end="", flush=True)
            
            # Wait for new messages to appear
            max_wait = 15
            for i in range(max_wait):
                time.sleep(1)
                current_messages = self.get_all_messages()
                if len(current_messages) > initial_count:
                    print(" Message sent!", flush=True)
                    break
                if i % 3 == 0:
                    print(".", end="", flush=True)
            else:
                print(" Timeout waiting for response")
            
            # Now wait for the response to complete
            print("Generating", end="", flush=True)
            
            max_wait = 120
            last_length = 0
            stable_count = 0
            
            for waited in range(max_wait):
                time.sleep(1)
                
                if waited % 3 == 0:
                    print(".", end="", flush=True)
                
                # Get current messages
                current_messages = self.get_all_messages()
                
                if current_messages:
                    # Get the last message's length
                    current_length = len(current_messages[-1].text) if current_messages else 0
                    
                    # If length hasn't changed for 3 seconds, assume complete
                    if current_length == last_length and current_length > 0:
                        stable_count += 1
                        if stable_count >= 3:
                            break
                    else:
                        stable_count = 0
                        last_length = current_length
                
                # Also check for stop button
                try:
                    stop_buttons = self.driver.find_elements(By.CSS_SELECTOR, 
                        'button[aria-label*="stop" i], button[aria-label*="Stop"]')
                    if not any(btn.is_displayed() for btn in stop_buttons):
                        if waited > 5:  # Give it at least 5 seconds
                            break
                except:
                    pass
            
            print(" Done!\n")
            time.sleep(1)
            
            # Extract the response
            try:
                all_messages = self.get_all_messages()
                
                if not all_messages:
                    # Fallback: try to get all text from the page
                    body = self.driver.find_element(By.TAG_NAME, "body")
                    return f"Could not extract messages cleanly. Page content:\n{body.text[-2000:]}"
                
                # Get the last message (should be Claude's response)
                if len(all_messages) > initial_count:
                    # Get the new message(s)
                    new_messages = all_messages[initial_count:]
                    response_text = "\n\n".join([msg.text for msg in new_messages])
                    return response_text if response_text else "Response received but appears empty."
                else:
                    # Fallback to last message
                    last_message = all_messages[-1]
                    response_text = last_message.text
                    return response_text if response_text else "Response received but text extraction failed."
                    
            except Exception as e:
                return f"Error extracting response: {str(e)}"
                
        except Exception as e:
            return f"Error sending message: {str(e)}"
    
    def start_new_chat(self):
        """Start a new conversation"""
        try:
            self.driver.get("https://claude.ai/new")
            time.sleep(3)
            self.last_message_count = 0
            print("✓ Started new conversation\n")
        except Exception as e:
            print(f"Error starting new chat: {e}\n")
    
    def print_banner(self):
        print("\n" + "="*60)
        print("  Claude Chat Terminal")
        print("  Using your Claude.ai subscription")
        print("="*60)
        print("\nCommands:")
        print("  /exit or /quit - Exit the program")
        print("  /new - Start a new conversation")
        print("  /help - Show this help message")
        print("  /debug - Show page source for debugging")
        print("\n" + "="*60 + "\n")
    
    def handle_command(self, command):
        """Handle special commands"""
        cmd = command.lower().strip()
        
        if cmd in ["/exit", "/quit"]:
            print("\nClosing browser and exiting...")
            self.cleanup()
            sys.exit(0)
        
        elif cmd == "/new":
            self.start_new_chat()
            return True
        
        elif cmd == "/help":
            self.print_banner()
            return True
        
        elif cmd == "/debug":
            print("\n--- Debug Info ---")
            print(f"Current URL: {self.driver.current_url}")
            messages = self.get_all_messages()
            print(f"Found {len(messages)} message elements")
            for i, msg in enumerate(messages[-5:]):  # Show last 5
                print(f"\nMessage {i}:")
                print(f"  Text length: {len(msg.text)}")
                print(f"  Preview: {msg.text[:100]}...")
            print("\n--- End Debug ---\n")
            return True
        
        else:
            print(f"\n✗ Unknown command: {cmd}")
            print("Type /help for available commands\n")
            return True
    
    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
    
    def run(self):
        """Main loop"""
        try:
            self.init_browser()
            
            if not self.login_if_needed():
                self.cleanup()
                return
            
            self.print_banner()
            
            while True:
                try:
                    # Get user input
                    user_input = input("\033[1;36mYou:\033[0m ").strip()
                    
                    if not user_input:
                        continue
                    
                    # Handle commands
                    if user_input.startswith("/"):
                        self.handle_command(user_input)
                        continue
                    
                    # Send message and get response
                    print()
                    response = self.send_message(user_input)
                    print("\033[1;35mClaude:\033[0m")
                    print(response)
                    print()
                    
                except KeyboardInterrupt:
                    print("\n\nUse /exit or /quit to exit")
                    continue
                except EOFError:
                    print("\n\nGoodbye!")
                    break
                    
        finally:
            self.cleanup()

def main():
    terminal = ClaudeChatTerminal()
    terminal.run()

if __name__ == "__main__":
    main()