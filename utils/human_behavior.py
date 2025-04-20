"""
Human Behavior Simulation module for OwO-Dusk.
This module adds human-like behavior patterns to avoid detection.
"""

import random
import time
import asyncio
import math
from datetime import datetime, timedelta

# Typical human typing speed ranges (characters per minute)
TYPING_SPEED = {
    "slow": (150, 250),      # 25-42 WPM (avg word = 6 chars)
    "average": (250, 350),   # 42-58 WPM
    "fast": (350, 500)       # 58-83 WPM
}

# Activity patterns by time of day (24-hour format)
ACTIVITY_PATTERNS = {
    "morning": (6, 11),      # 6 AM - 11 AM
    "afternoon": (11, 17),   # 11 AM - 5 PM
    "evening": (17, 22),     # 5 PM - 10 PM
    "night": (22, 6)         # 10 PM - 6 AM
}

# Fatigue modeling - longer sessions cause more delays and mistakes
FATIGUE_MODEL = {
    "base_time": 0,          # Session start time
    "fatigue_onset": 3600,   # Time in seconds before fatigue starts (1 hour)
    "max_fatigue": 0.5,      # Maximum fatigue effect (0.5 = 50% slowdown)
    "recovery_rate": 0.2     # Recovery rate when taking breaks
}

class HumanBehaviorSimulator:
    def __init__(self, activity_pattern="auto"):
        """
        Initialize the human behavior simulator.
        
        Args:
            activity_pattern: The activity pattern to use ('morning', 'afternoon', 'evening', 'night', or 'auto')
        """
        self.session_start = time.time()
        self.last_action = time.time()
        self.active_hours = 0
        self.action_count = 0
        self.breaks_taken = 0
        self.typing_speed = "average"
        
        # Set activity pattern based on current time if auto
        if activity_pattern == "auto":
            current_hour = datetime.now().hour
            for pattern, (start, end) in ACTIVITY_PATTERNS.items():
                if start <= current_hour < end or (start > end and (current_hour >= start or current_hour < end)):
                    self.activity_pattern = pattern
                    break
        else:
            self.activity_pattern = activity_pattern
            
        # Initialize random seeds with some entropy
        random.seed(time.time() + hash(str(datetime.now().microsecond)))
        
    def get_current_fatigue(self):
        """Calculate current fatigue level based on session duration."""
        session_duration = time.time() - self.session_start
        
        # No fatigue before onset time
        if session_duration < FATIGUE_MODEL["fatigue_onset"]:
            return 0
            
        # Calculate fatigue based on session duration, with diminishing returns
        base_fatigue = min(1.0, (session_duration - FATIGUE_MODEL["fatigue_onset"]) / 
                          (3600 * 6))  # 6 hours to reach maximum fatigue
                          
        # Reduce fatigue based on breaks taken
        fatigue_reduction = min(0.8, self.breaks_taken * FATIGUE_MODEL["recovery_rate"])
        
        # Final fatigue is capped at max_fatigue
        return min(FATIGUE_MODEL["max_fatigue"], base_fatigue * (1 - fatigue_reduction))
        
    def simulate_typing_time(self, message_length):
        """
        Simulate realistic typing time for a message.
        
        Args:
            message_length: Length of the message in characters
            
        Returns:
            Simulated typing time in seconds
        """
        # Get base typing speed range based on profile
        min_cpm, max_cpm = TYPING_SPEED[self.typing_speed]
        
        # Add some randomness to typing speed
        typing_speed = random.uniform(min_cpm, max_cpm)
        
        # Apply fatigue effect (slows down typing)
        fatigue = self.get_current_fatigue()
        typing_speed = typing_speed * (1 - fatigue)
        
        # Calculate base typing time
        typing_time = (message_length / typing_speed) * 60
        
        # Add thinking time at the beginning (people don't start typing immediately)
        thinking_time = random.uniform(0.5, 2.0) * (1 + fatigue)
        
        # Add some randomness for pauses during typing
        pause_count = max(0, int(message_length / 20))  # One pause per ~20 chars
        pause_time = sum(random.uniform(0.1, 0.5) for _ in range(pause_count))
        
        # Calculate total time
        total_time = thinking_time + typing_time + pause_time
        
        # Add time of day variation
        if self.activity_pattern == "night":
            # People type slower at night
            total_time *= random.uniform(1.05, 1.2)
        elif self.activity_pattern == "morning":
            # People may be sluggish in the morning
            total_time *= random.uniform(1.0, 1.15)
            
        return total_time
        
    def should_take_break(self):
        """Determine if it's time to take a break based on human behavior."""
        session_duration = time.time() - self.session_start
        time_since_last_action = time.time() - self.last_action
        
        # Higher chance of break as session gets longer
        base_break_chance = min(0.15, session_duration / (3600 * 8))  # 15% max after 8 hours
        
        # Add fatigue factor
        fatigue_factor = self.get_current_fatigue() * 0.2
        
        # Increase chance if we've done many actions without a break
        action_factor = min(0.1, self.action_count / 100)
        
        # Time of day factor
        time_factor = 0
        if self.activity_pattern == "night":
            time_factor = 0.1  # Higher chance of breaks at night
        elif self.activity_pattern == "afternoon":
            time_factor = -0.05  # Lower chance during active hours
            
        # Calculate final break chance
        break_chance = base_break_chance + fatigue_factor + action_factor + time_factor
        
        # Always return False if we just took an action
        if time_since_last_action < 60:
            return False
            
        return random.random() < break_chance
    
    def get_break_duration(self):
        """Get a realistic break duration based on session length and time of day."""
        session_duration = time.time() - self.session_start
        
        # Base break time increases with session length
        base_break = min(10, session_duration / 3600)  # 1 minute per hour, up to 10 minutes
        
        # Add some randomness
        random_factor = random.uniform(0.5, 2.0)
        
        # Consider time of day
        time_factor = 1.0
        if self.activity_pattern == "night":
            time_factor = 2.0  # Longer breaks at night
        elif self.activity_pattern == "morning":
            time_factor = 1.2  # Slightly longer in morning
            
        break_duration = base_break * random_factor * time_factor
        
        # Convert to seconds, with a minimum of 30 seconds
        return max(30, break_duration * 60)
    
    def register_action(self):
        """Register that an action was taken."""
        self.last_action = time.time()
        self.action_count += 1
    
    def register_break(self):
        """Register that a break was taken."""
        self.breaks_taken += 1
        
    async def simulate_typing(self, channel, message_length):
        """
        Simulate human typing behavior in Discord.
        
        Args:
            channel: Discord channel to simulate typing in
            message_length: Length of the message
            
        Returns:
            The simulated typing time in seconds
        """
        typing_time = self.simulate_typing_time(message_length)
        
        # Register this as an action
        self.register_action()
        
        # Simulate typing indicator (typical Discord behavior)
        async with channel.typing():
            # Sleep for most of the typing time
            await asyncio.sleep(typing_time * 0.8)
        
        # Small delay before sending (people sometimes pause before hitting enter)
        await asyncio.sleep(random.uniform(0.2, 0.8))
        
        return typing_time
        
    def get_random_command_delay(self, command_type="normal"):
        """
        Get a randomized but human-like delay between commands.
        
        Args:
            command_type: Type of command ('normal', 'complex', 'simple')
            
        Returns:
            Delay time in seconds
        """
        # Base delay ranges by command type
        if command_type == "simple":
            base_min, base_max = 2, 5
        elif command_type == "complex":
            base_min, base_max = 5, 12
        else:  # normal
            base_min, base_max = 3, 8
            
        # Add fatigue effect
        fatigue = self.get_current_fatigue()
        fatigue_addon = fatigue * random.uniform(1, 5)
        
        # Time of day variations
        time_factor = 1.0
        if self.activity_pattern == "night":
            time_factor = 1.3  # Slower at night
        elif self.activity_pattern == "afternoon":
            time_factor = 0.9  # Faster during afternoon
            
        # Calculate delay with some randomness
        delay = random.uniform(base_min, base_max) * time_factor + fatigue_addon
        
        # Add some natural variation
        # Sometimes humans pause a bit longer between commands
        if random.random() < 0.15:  # 15% chance of a longer pause
            delay *= random.uniform(1.5, 2.5)
            
        return delay
        
    def get_active_hours_profile(self):
        """
        Generate a human-like active hours profile.
        
        Returns:
            Dictionary with active hours probability by hour (0-23)
        """
        # Base activity profile - probability of being active at each hour
        base_profile = {
            0: 0.2, 1: 0.1, 2: 0.05, 3: 0.03, 4: 0.02, 5: 0.05,
            6: 0.1, 7: 0.2, 8: 0.4, 9: 0.6, 10: 0.7, 11: 0.8, 
            12: 0.9, 13: 0.9, 14: 0.8, 15: 0.8, 16: 0.7, 17: 0.8,
            18: 0.9, 19: 0.9, 20: 0.8, 21: 0.7, 22: 0.5, 23: 0.3
        }
        
        # Add some randomness to create individual profile
        profile = {}
        for hour, prob in base_profile.items():
            # Add random variation (-20% to +20%)
            variation = random.uniform(-0.2, 0.2)
            profile[hour] = max(0.01, min(0.99, prob + variation))
            
        return profile
        
    def should_be_active_now(self):
        """
        Determine if a human user would likely be active at the current time.
        
        Returns:
            Boolean indicating if active, and confidence level (0-1)
        """
        profile = self.get_active_hours_profile()
        current_hour = datetime.now().hour
        
        # Get base probability for current hour
        base_probability = profile[current_hour]
        
        # Consider day of week (higher probability on weekends)
        day_of_week = datetime.now().weekday()
        is_weekend = day_of_week >= 5  # 5=Saturday, 6=Sunday
        
        if is_weekend:
            # Higher probability on weekends, especially during morning/day
            if 7 <= current_hour <= 17:  # 7 AM to 5 PM
                base_probability = min(0.95, base_probability * 1.3)
        else:
            # Lower probability on weekdays during working hours
            if 9 <= current_hour <= 17:  # 9 AM to 5 PM
                base_probability = base_probability * 0.8
        
        # Random chance to deviate from pattern (humans aren't perfectly predictable)
        random_factor = random.uniform(0.8, 1.2)
        final_probability = min(0.99, base_probability * random_factor)
        
        # Determine if active
        is_active = random.random() < final_probability
        
        return is_active, final_probability
        
    def generate_realistic_command_sequence(self, available_commands, session_duration_minutes=30):
        """
        Generate a realistic sequence of commands that a human might use.
        
        Args:
            available_commands: List of available command types
            session_duration_minutes: Duration of the session in minutes
            
        Returns:
            List of command types in a human-like sequence with timestamps
        """
        sequence = []
        commands_copy = available_commands.copy()
        
        # Calculate how many commands would be realistic in this time period
        # Humans typically use 1-4 commands per minute depending on complexity
        avg_commands_per_minute = random.uniform(1, 3)
        expected_command_count = int(session_duration_minutes * avg_commands_per_minute)
        
        # Add some variation
        command_count = int(expected_command_count * random.uniform(0.8, 1.2))
        
        # Generate timestamps (not evenly distributed)
        session_duration_seconds = session_duration_minutes * 60
        timestamps = []
        
        for _ in range(command_count):
            # More likely to cluster commands than spread them perfectly
            if not timestamps:
                # First command comes quickly
                timestamps.append(random.uniform(1, 10))
            else:
                last_time = timestamps[-1]
                
                # Small chance of a longer pause
                if random.random() < 0.1:
                    # Take a break (30-120 seconds)
                    delay = random.uniform(30, 120)
                else:
                    # Normal delay between commands (3-15 seconds)
                    delay = random.uniform(3, 15)
                    
                new_time = last_time + delay
                if new_time < session_duration_seconds:
                    timestamps.append(new_time)
                else:
                    break
        
        # Generate command sequence
        for timestamp in timestamps:
            # Humans tend to use the same command multiple times in a row
            if sequence and random.random() < 0.4:
                # 40% chance to repeat last command
                command = sequence[-1]["command"]
            else:
                # Otherwise pick a command with weighted probability
                # Certain commands are used more often
                command = self._weighted_command_choice(commands_copy)
                
            sequence.append({
                "timestamp": timestamp,
                "command": command
            })
            
        return sequence
    
    def _weighted_command_choice(self, commands):
        """
        Make a weighted random choice from available commands.
        Some commands are used more frequently by humans than others.
        """
        # Define weights for different command types (if available)
        weights = {
            "hunt": 10,
            "battle": 8, 
            "owo": 7,
            "pray": 3,
            "curse": 2,
            "sell": 3,
            "daily": 1,
            "lottery": 1,
            "shop": 1,
            "cookie": 2
        }
        
        # Filter to only available commands
        available_weighted_commands = []
        available_weights = []
        
        for cmd in commands:
            weight = weights.get(cmd, 1)  # Default weight 1 if not specified
            available_weighted_commands.append(cmd)
            available_weights.append(weight)
            
        # If weights are empty, use equal weights
        if not available_weights:
            return random.choice(commands)
            
        # Use weighted choice
        return random.choices(
            available_weighted_commands,
            weights=available_weights,
            k=1
        )[0]

# Helper functions that can be used directly

async def human_delay(behavior_simulator=None, command_type="normal"):
    """
    Create a human-like delay between actions.
    
    Args:
        behavior_simulator: HumanBehaviorSimulator instance or None
        command_type: Type of command for context
        
    Returns:
        Time delayed in seconds
    """
    if behavior_simulator is None:
        behavior_simulator = HumanBehaviorSimulator()
        
    delay = behavior_simulator.get_random_command_delay(command_type)
    
    # Add micro-variations to seem more human
    micro_variation = random.uniform(-0.1, 0.1) * delay
    final_delay = max(0.1, delay + micro_variation)
    
    await asyncio.sleep(final_delay)
    return final_delay

def vary_cooldown(base_cooldown, variation_percent=15, min_cooldown=None, max_cooldown=None):
    """
    Apply human-like variation to cooldown times.
    
    Args:
        base_cooldown: Base cooldown time in seconds
        variation_percent: Percent variation (default 15%)
        min_cooldown: Minimum allowed cooldown
        max_cooldown: Maximum allowed cooldown
        
    Returns:
        Varied cooldown value
    """
    # Calculate variation amount
    variation = (base_cooldown * variation_percent / 100) 
    
    # Sometimes add extra delay to seem more human
    if random.random() < 0.2:  # 20% chance
        extra = random.uniform(1, 5)
    else:
        extra = 0
        
    # Calculate final cooldown with random variation
    final_cooldown = base_cooldown + random.uniform(-variation, variation) + extra
    
    # Apply limits if specified
    if min_cooldown is not None:
        final_cooldown = max(min_cooldown, final_cooldown)
    if max_cooldown is not None:
        final_cooldown = min(max_cooldown, final_cooldown)
        
    return final_cooldown
    
def generate_active_times(days=7):
    """
    Generate a realistic schedule of active times for a human user.
    
    Args:
        days: Number of days to generate schedule for
        
    Returns:
        Dictionary with dates and active hour ranges
    """
    simulator = HumanBehaviorSimulator()
    
    schedule = {}
    today = datetime.now().date()
    
    for day_offset in range(days):
        target_date = today + timedelta(days=day_offset)
        day_of_week = target_date.weekday()
        
        # Determine how many active sessions on this day (1-3 typically)
        if day_of_week < 5:  # Weekday
            num_sessions = random.choices([1, 2, 3], weights=[0.3, 0.5, 0.2])[0]
        else:  # Weekend
            num_sessions = random.choices([1, 2, 3], weights=[0.2, 0.4, 0.4])[0]
            
        # Generate sessions
        day_sessions = []
        
        for _ in range(num_sessions):
            # Humans tend to have preferred times of day
            preferred_period = random.choice(["morning", "afternoon", "evening", "night"])
            period_start, period_end = ACTIVITY_PATTERNS[preferred_period]
            
            # Convert to 24-hour format (handle night crossing midnight)
            if preferred_period == "night" and period_start > period_end:
                if random.random() < 0.5:
                    # Evening to midnight session
                    start_hour = random.randint(period_start, 23)
                    end_hour = random.randint(start_hour + 1, min(start_hour + 4, 24))
                else:
                    # After midnight session
                    start_hour = random.randint(0, period_end - 1)
                    end_hour = random.randint(start_hour + 1, min(start_hour + 4, period_end))
            else:
                start_hour = random.randint(period_start, period_end - 1)
                end_hour = random.randint(start_hour + 1, min(start_hour + 4, period_end))
            
            # Add minutes for more realism
            start_minute = random.randint(0, 59)
            end_minute = random.randint(0, 59)
            
            session = {
                "start": f"{start_hour:02d}:{start_minute:02d}",
                "end": f"{end_hour:02d}:{end_minute:02d}",
                "duration_minutes": ((end_hour - start_hour) * 60 + (end_minute - start_minute))
            }
            
            day_sessions.append(session)
            
        schedule[target_date.strftime("%Y-%m-%d")] = day_sessions
    
    return schedule 