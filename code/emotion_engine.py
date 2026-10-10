import re
import math


class PlayerEmotionEngine:
    """
    Bidirectional emotion engine.
    Detects the PLAYER's mood from their text and instructs the
    Dungeon Master how to adapt its storytelling in real time.

    All fixes applied:
    - Word boundary matching  (no substring false positives)
    - Letters-only caps ratio (ignores punctuation / spaces)
    - Logarithmic intensity   (proper data normalization)
    - Unused pattern keys removed
    - Emotional persistence   (3-turn streak detection)
    """

    PATTERNS = {
        'excited': {
            'keywords':    ['charge', 'attack', 'rush', 'go', 'now', 'yes', 'do it', 'lets go'],
            'punctuation': r'!+',
            'caps_ratio':  0.3,
            'short_burst': 3,
        },
        'fearful': {
            'keywords':    ['scared', 'afraid', 'hide', 'run', 'flee', 'escape', 'help', 'please', 'dont'],
            'punctuation': r'\.\.\.',
            'uncertainty': ['maybe', 'perhaps', 'not sure', 'i think'],
        },
        'cautious': {
            'keywords':   ['careful', 'check', 'look', 'listen', 'wait', 'plan', 'scout', 'investigate'],
            'questions':  r'\?',
            'deliberate': ['should', 'could', 'would', 'consider'],
        },
        'angry': {
            'keywords':    ['kill', 'destroy', 'hate', 'damn', 'stupid', 'idiot', 'crush', 'break'],
            'punctuation': r'!{2,}',
            'caps_ratio':  0.4,
        },
        'sad': {
            'keywords':    ['sad', 'sorry', 'miss', 'lost', 'alone', 'grief', 'cry', 'tears'],
            'resignation': ['whatever', 'doesnt matter', 'pointless'],
        },
        'determined': {
            'keywords':   ['must', 'will', 'shall', 'defeat', 'save', 'protect', 'find', 'rescue'],
            'commitment': ['no matter', 'whatever it takes', 'never give up'],
        },
    }

    DM_INSTRUCTIONS = {
        'excited': {
            'tone':      'Player is RECKLESS and EAGER. Raise stakes, add chaos, offer high-risk high-reward choices.',
            'mechanics': 'More combat. Higher danger. World mirrors their wild energy.',
        },
        'fearful': {
            'tone':      'Player is SCARED. Offer a sliver of hope or an unexpected ally. Build psychological dread.',
            'mechanics': 'Safe choices have hidden costs. Shadows move. Paranoia rises.',
        },
        'cautious': {
            'tone':      'Player is METHODICAL. Reward their patience with hidden details and secrets.',
            'mechanics': 'Reveal traps. Unlock secret doors. NPCs respect their deliberation.',
        },
        'angry': {
            'tone':      'Player is ENRAGED. Channel it into visceral confrontation. Consequences follow rage.',
            'mechanics': 'Combat available. Diplomacy harder. Destruction has lasting scars.',
        },
        'sad': {
            'tone':      'Player is MELANCHOLIC. Offer beauty in darkness. A kind stranger. A moment of connection.',
            'mechanics': 'NPCs open up. Healing more effective. Redemption arcs unlock.',
        },
        'determined': {
            'tone':      'Player is RESOLUTE. Advance the main quest. Show meaningful progress.',
            'mechanics': 'Quest clues appear. Obstacles fall. The world bends to their will.',
        },
        'neutral': {
            'tone':      'Maintain current narrative atmosphere.',
            'mechanics': 'No special adaptation needed.',
        },
    }

    def analyze(self, text: str) -> dict:
        text_lower = text.lower()
        words      = text.split()
        scores     = {}

        for emotion, patterns in self.PATTERNS.items():
            score = 0
            for kw in patterns.get('keywords', []):
                if re.search(rf'\b{re.escape(kw)}\b', text_lower):
                    score += 2
            punct = patterns.get('punctuation', '')
            if punct and re.search(punct, text):
                score += 1
            for key in ['uncertainty', 'deliberate', 'resignation', 'commitment']:
                for phrase in patterns.get(key, []):
                    if phrase in text_lower:
                        score += 1
            if 'questions' in patterns and re.search(patterns['questions'], text):
                score += 1
            if 'caps_ratio' in patterns:
                letters = [c for c in text if c.isalpha()]
                if letters:
                    ratio = sum(1 for c in letters if c.isupper()) / len(letters)
                    if ratio >= patterns['caps_ratio']:
                        score += 1
            if 'short_burst' in patterns and len(words) <= patterns['short_burst']:
                score += 1
            scores[emotion] = score

        max_score = max(scores.values()) if scores else 0
        if max_score == 0:
            dominant, intensity = 'neutral', 1
        else:
            dominant  = max(scores, key=scores.get)
            intensity = min(3, math.ceil(math.log(1 + max_score) * 1.5))

        return {
            'dominant':         dominant,
            'intensity':        intensity,
            'all_scores':       scores,
            'detected_signals': self._get_signals(dominant, text_lower),
        }

    def _get_signals(self, emotion: str, text: str) -> list:
        signals = []
        for kw in self.PATTERNS.get(emotion, {}).get('keywords', []):
            if re.search(rf'\b{re.escape(kw)}\b', text):
                signals.append(f"'{kw}'")
        return signals[:2]

    def get_dm_instruction(self, emotion: dict) -> dict:
        return self.DM_INSTRUCTIONS.get(emotion['dominant'], self.DM_INSTRUCTIONS['neutral'])

    def build_persistence_note(self, emotion_history: list) -> str:
        if len(emotion_history) < 3:
            return ''
        last3 = emotion_history[-3:]
        if len(set(last3)) == 1 and last3[0] != 'neutral':
            return {
                'angry':      'Player has been angry 3 turns. Reference their simmering fury.',
                'fearful':    'Player has been fearful 3 turns. They are on the edge — let the world feel it.',
                'excited':    'Player has been reckless 3 turns. Chaos is catching up with them.',
                'cautious':   'Player has been cautious 3 turns. Reward their patience with a major discovery.',
                'sad':        'Player has been sad 3 turns. Offer a turning point — hope or catharsis.',
                'determined': 'Player has been determined 3 turns. Deliver a major quest milestone.',
            }.get(last3[0], '')
        return ''