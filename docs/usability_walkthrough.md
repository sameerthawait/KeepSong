# Keepsong Patient Check-In Usability Walkthrough Script

**Target User Profile:** Individual with mild-to-moderate memory loss using the check-in screen unassisted.
**Usability Principle:** Radical simplicity — zero menus, zero settings, zero navigation, zero dead-end states.

---

## Zero-Context Usability Step-by-Step Script

### Step 1: Accessing the Device (PIN Entry)
1. Device displays a high-contrast screen titled **"Daily Check-In: Please enter your PIN"**.
2. Large $64\times64\text{px}$ numeric keys (`0-9`, `Clear`, `⌫`) are displayed with high contrast.
3. Patient enters 4-digit PIN (`1234`). Visual dots indicate progress.
4. Patient taps green **"Start Check-In"** button.

### Step 2: Orientation & Context Parsing
1. Screen opens to a single, focused page.
2. **Top Header:** Displays today's date (e.g. *"Wednesday, July 22, 2026"*) and current live weather (e.g. *"72°F Partly Cloudy"*).
3. **Relative Orientation Card:** Displays a large, clear photo with high-contrast text:
   > **"This is Sarah, Your daughter"**
4. **Story Question:** Displays a bold, prominent card:
   > **"Tell me about your favorite childhood pet."**

### Step 3: Recording the Story
1. Prompt instructs: **"Tap Button to Speak"**.
2. A single, giant $88\times88\text{px}$ microphone button (`🎤`) is centered below the prompt.
3. Patient taps microphone button $\rightarrow$ Button turns into a glowing stop icon (`⏹️`) indicating *"Recording... Tap to Finish"*.
4. Patient shares memory and taps the stop button.

### Step 4: Playback & Confirmation
1. Audio playback controls appear with options:
   - **"Save My Story ✓"** (Large green $64\text{px}$ button)
   - **"Record Again 🔄"** (Secondary retry button)
2. Patient listens to playback and taps **"Save My Story ✓"**.

### Step 5: Completion & Zero Dead-End State
1. Screen transitions to a calm green checkmark screen displaying:
   > **"Thank You! Your story has been saved for your family. Have a wonderful day!"**
2. No further action or navigation is required. The screen is complete.
