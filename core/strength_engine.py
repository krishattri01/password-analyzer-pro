import re
import math


class StrengthEngine:
    """
    Calculates password strength score, entropy, and estimated crack time.
    Completely independent of GUI — pure logic only.
    """

    # Brute force guesses per second (modern GPU cluster)
    GUESSES_PER_SECOND = 1_000_000_000  # 1 billion/sec (offline attack)

    def analyze(self, password: str) -> dict:
        """
        Master method — runs full analysis and returns a result dictionary.
        Call this from the GUI with the current password string.
        """
        if not password:
            return self._empty_result()

        char_pool      = self._get_char_pool(password)
        entropy        = self._calc_entropy(password, char_pool)
        score          = self._calc_score(password)
        label, color   = self._score_label(score)
        crack_time     = self._crack_time(entropy)
        char_checks    = self._char_checks(password)

        return {
            "password"    : password,
            "length"      : len(password),
            "entropy"     : round(entropy, 2),
            "score"       : score,
            "label"       : label,
            "color"       : color,
            "crack_time"  : crack_time,
            "char_pool"   : char_pool,
            "char_checks" : char_checks,
        }

    # ------------------------------------------------------------------ #
    #  Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _get_char_pool(self, password: str) -> int:
        """Returns the size of the character pool used in the password."""
        pool = 0
        if re.search(r'[a-z]', password): pool += 26
        if re.search(r'[A-Z]', password): pool += 26
        if re.search(r'[0-9]', password): pool += 10
        if re.search(r'[^a-zA-Z0-9]', password): pool += 32
        return pool

    def _calc_entropy(self, password: str, pool: int) -> float:
        """
        Shannon entropy formula: L * log2(pool)
        Higher entropy = harder to crack.
        """
        if pool == 0:
            return 0.0
        return len(password) * math.log2(pool)

    def _calc_score(self, password: str) -> int:
        """
        Returns a score from 0–100 based on multiple criteria.
        Each criterion adds points; penalties applied for bad patterns.
        """
        score = 0
        length = len(password)

        # --- Length points ---
        if length >= 6:  score += 10
        if length >= 8:  score += 10
        if length >= 12: score += 15
        if length >= 16: score += 10
        if length >= 20: score += 5

        # --- Character variety points ---
        has_lower   = bool(re.search(r'[a-z]', password))
        has_upper   = bool(re.search(r'[A-Z]', password))
        has_digit   = bool(re.search(r'[0-9]', password))
        has_special = bool(re.search(r'[^a-zA-Z0-9]', password))

        if has_lower:   score += 10
        if has_upper:   score += 10
        if has_digit:   score += 10
        if has_special: score += 15

        # --- Bonus: all 4 types used ---
        types_used = sum([has_lower, has_upper, has_digit, has_special])
        if types_used == 4: score += 5

        # --- Penalties ---
        if bool(re.search(r'(.)\1{2,}', password)):    score -= 10  # aaa
        if bool(re.search(r'(012|123|234|345|456|567|678|789|890|abc|bcd|cde|def)', password.lower())):
            score -= 10  # sequential

        return max(0, min(score, 100))  # clamp 0–100

    def _score_label(self, score: int) -> tuple:
        """Maps numeric score to human-readable label and hex color."""
        if score < 20:  return ("Very Weak",   "#E53935")
        if score < 40:  return ("Weak",         "#FB8C00")
        if score < 60:  return ("Fair",         "#FDD835")
        if score < 80:  return ("Strong",       "#43A047")
        return              ("Very Strong",  "#00897B")

    def _crack_time(self, entropy: float) -> str:
        """Estimates time to brute-force based on entropy."""
        if entropy == 0:
            return "Instant"

        combinations = 2 ** entropy
        seconds = combinations / (2 * self.GUESSES_PER_SECOND)

        if seconds < 1:          return "Less than a second"
        if seconds < 60:         return f"{int(seconds)} seconds"
        if seconds < 3600:       return f"{int(seconds // 60)} minutes"
        if seconds < 86400:      return f"{int(seconds // 3600)} hours"
        if seconds < 2_592_000:  return f"{int(seconds // 86400)} days"
        if seconds < 31_536_000: return f"{int(seconds // 2_592_000)} months"
        years = seconds / 31_536_000
        if years < 1_000:        return f"{int(years)} years"
        if years < 1_000_000:    return f"{years/1_000:.1f}K years"
        return "Millions+ years"

    def _char_checks(self, password: str) -> dict:
        """Returns a dict of which character types are present."""
        return {
            "Lowercase letters" : bool(re.search(r'[a-z]', password)),
            "Uppercase letters" : bool(re.search(r'[A-Z]', password)),
            "Numbers"           : bool(re.search(r'[0-9]', password)),
            "Special characters": bool(re.search(r'[^a-zA-Z0-9]', password)),
            "12+ characters"    : len(password) >= 12,
            "16+ characters"    : len(password) >= 16,
        }

    def _empty_result(self) -> dict:
        """Returns a safe empty result when password is blank."""
        return {
            "password": "", "length": 0, "entropy": 0.0,
            "score": 0, "label": "None", "color": "#9E9E9E",
            "crack_time": "—", "char_pool": 0,
            "char_checks": {
                "Lowercase letters": False, "Uppercase letters": False,
                "Numbers": False, "Special characters": False,
                "12+ characters": False, "16+ characters": False,
            }
        }