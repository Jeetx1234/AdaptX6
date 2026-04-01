"""
Temperature Alarm System - FIXED VERSION
==========================================
No pygame dependency - uses system beep as fallback.
"""

import threading
import time
import os
from typing import List
import logging
import subprocess
import sys


class AlarmSystem:
    """Non-blocking alarm system with adjustable thresholds."""
    
    def __init__(self, 
                 default_threshold: float = 42.0,
                 alarm_sound_path: str = "assets/alarm.mp3",
                 alarm_duration: float = 3.0):
        
        self._threshold = default_threshold
        self.alarm_sound_path = alarm_sound_path
        self.alarm_duration = alarm_duration
        
        self.is_alarm_active = False
        self.last_alarm_time = 0
        self.alarm_cooldown = 8  # Seconds between alarms
        
        self._alarm_thread = None
        self._stop_alarm = threading.Event()
        
        self.alarm_history: List[dict] = []
        self.max_history = 50
        
        # Check for sound capability
        self.sound_method = self._detect_sound_method()
    
    def _detect_sound_method(self) -> str:
        """Detect available sound playback method."""
        # Try pygame first
        try:
            import pygame
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            return "pygame"
        except:
            pass
        
        # Try playsound
        try:
            from playsound import playsound
            return "playsound"
        except:
            pass
        
        # Try system command (macOS)
        if sys.platform == "darwin":
            return "afplay"
        
        # Try system command (Linux)
        if sys.platform.startswith("linux"):
            return "aplay"
        
        # Try system command (Windows)
        if sys.platform == "win32":
            return "winsound"
        
        # Fallback to beep
        return "beep"
    
    def get_threshold(self) -> float:
        """Get current threshold."""
        return self._threshold
    
    def set_threshold(self, threshold: float) -> bool:
        """Set new temperature threshold."""
        if 25 <= threshold <= 80:
            old = self._threshold
            self._threshold = threshold
            return True
        return False
    
    def check_temperature(self, temperature: float) -> dict:
        """Check temperature against current threshold."""
        result = {
            'exceeded': False,
            'alarm_triggered': False,
            'temperature': temperature,
            'threshold': self._threshold,
            'message': ''
        }
        
        # Check against CURRENT threshold
        if temperature > self._threshold:
            result['exceeded'] = True
            
            current_time = time.time()
            time_since_last = current_time - self.last_alarm_time
            
            if time_since_last >= self.alarm_cooldown and not self.is_alarm_active:
                result['alarm_triggered'] = True
                result['message'] = f"🚨 ALARM: {temperature:.1f}°C exceeds {self._threshold}°C threshold!"
                
                self.alarm_history.append({
                    'time': current_time,
                    'temperature': temperature,
                    'threshold': self._threshold
                })
                
                if len(self.alarm_history) > self.max_history:
                    self.alarm_history.pop(0)
                
                self._trigger_alarm()
            else:
                if self.is_alarm_active:
                    result['message'] = f"⚠️ Temperature {temperature:.1f}°C > {self._threshold}°C (alarm active)"
                else:
                    cooldown_left = self.alarm_cooldown - time_since_last
                    result['message'] = f"⚠️ Temperature {temperature:.1f}°C > {self._threshold}°C (cooldown: {cooldown_left:.0f}s)"
        else:
            margin = self._threshold - temperature
            if margin < 3:
                result['message'] = f"⚠️ Temperature {temperature:.1f}°C approaching threshold ({self._threshold}°C)"
            else:
                result['message'] = f"✅ Temperature {temperature:.1f}°C is safe (threshold: {self._threshold}°C)"
        
        return result
    
    def _trigger_alarm(self):
        """Trigger alarm in background."""
        self.last_alarm_time = time.time()
        self.is_alarm_active = True
        
        self._stop_alarm.clear()
        self._alarm_thread = threading.Thread(
            target=self._play_alarm,
            daemon=True
        )
        self._alarm_thread.start()
    
    def _play_alarm(self):
        """Play alarm sound using detected method."""
        try:
            if self.sound_method == "pygame":
                self._play_pygame()
            elif self.sound_method == "playsound":
                self._play_playsound()
            elif self.sound_method == "afplay":
                self._play_afplay()
            elif self.sound_method == "aplay":
                self._play_aplay()
            elif self.sound_method == "winsound":
                self._play_winsound()
            else:
                self._play_beep()
        except Exception as e:
            logging.warning(f"Alarm sound failed: {e}")
            self._play_beep()
        finally:
            self.is_alarm_active = False
    
    def _play_pygame(self):
        """Play using pygame."""
        import pygame
        if os.path.exists(self.alarm_sound_path):
            pygame.mixer.music.load(self.alarm_sound_path)
            pygame.mixer.music.play()
            start = time.time()
            while time.time() - start < self.alarm_duration:
                if self._stop_alarm.is_set():
                    break
                time.sleep(0.1)
            pygame.mixer.music.stop()
        else:
            self._play_beep()
    
    def _play_playsound(self):
        """Play using playsound module."""
        from playsound import playsound
        if os.path.exists(self.alarm_sound_path):
            playsound(self.alarm_sound_path, block=False)
            time.sleep(self.alarm_duration)
        else:
            self._play_beep()
    
    def _play_afplay(self):
        """Play using macOS afplay."""
        if os.path.exists(self.alarm_sound_path):
            subprocess.run(
                ["afplay", "-t", str(self.alarm_duration), self.alarm_sound_path],
                capture_output=True
            )
        else:
            self._play_beep()
    
    def _play_aplay(self):
        """Play using Linux aplay."""
        if os.path.exists(self.alarm_sound_path):
            subprocess.run(
                ["aplay", self.alarm_sound_path],
                capture_output=True,
                timeout=self.alarm_duration
            )
        else:
            self._play_beep()
    
    def _play_winsound(self):
        """Play using Windows winsound."""
        import winsound
        for _ in range(3):
            if self._stop_alarm.is_set():
                break
            winsound.Beep(1000, 500)
            time.sleep(0.3)
    
    def _play_beep(self):
        """Fallback beep using terminal bell."""
        for _ in range(5):
            if self._stop_alarm.is_set():
                break
            print("\a", end="", flush=True)
            time.sleep(0.4)
    
    def stop_alarm(self):
        """Stop current alarm."""
        self._stop_alarm.set()
        self.is_alarm_active = False
    
    def get_alarm_history(self) -> List[dict]:
        """Get alarm history."""
        return self.alarm_history.copy()